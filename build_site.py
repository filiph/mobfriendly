# coding=utf-8
import codecs
from distutils.dir_util import copy_tree

import os
import subprocess
import markdown
from markdown.extensions.smarty import SmartyExtension
from wand.image import Image
from rank import get_sites_from_csv, SiteInfo, get_output_file_from_country

countries = ["cz", "de", "gr", "pl", "uk", "ro"]

html_head = u"""
    <html><head><meta charset="utf-8">
    <title>{title}</title>
    <link href="{css}" rel="stylesheet" type="text/css" />
    <meta name="viewport" content="width=device-width">
    </head><body>"""
html_tail = u"</body>" \
            u"</html>"

UTF8 = "utf-8"


def copy_and_resize_image(site, country_dir):
    """
    :type site: SiteInfo
    """
    new_filename = os.path.join(country_dir, site.url + ".jpg")
    if os.path.exists(new_filename):
        return
    with Image(filename=site.img_path) as original:
        with original.convert("jpg") as jpg:
            jpg.transform(resize='200')
            jpg.compression_quality = 90
            jpg.save(filename=new_filename)


def copy_and_combine_progress(site, directory):
    """
    :type directory: str
    :type site: SiteInfo
    """
    new_filename = os.path.join(directory, site.url + "-progress.jpg")
    if os.path.exists(new_filename):
        return

    # comm = "montage -geometry 100% -tile x1 -label '%[base]ms' *.png.jpg all.jpg"
    args = ["montage", "-geometry", "100%", "-border", "5", "-tile", "x1"]
    small_img_tuples = site.get_small_imgs()
    for path, measure in small_img_tuples[:-1]:
        args.extend(["-label", "{}ms".format(measure)])
        args.append(path)
    path, measure = small_img_tuples[-1]
    args.extend(["-label", "FULL = {}ms".format(measure)])
    args.append(path)

    args.append(new_filename)
    # print args

    try:
        retcode = subprocess.call(args)
        # print retcode
    except OSError as e:
        print "Execution failed:", e


def build_site_index_html(site, directory):
    """
    :type directory: str
    :type site: SiteInfo
    """
    filename = os.path.join(directory, "index.html")
    with open(filename, "w") as f:
        def write(s):
            f.write(s.encode(UTF8))

        write(html_head.format(
            title=u"Mobilní web: " + site.url,
            css=u"../../screencaps.css"
        ))
        write(u"<div class=\"site-index-wrapper\">")
        write(u"<h1>{url}</h1>".format(url=site.url))
        write(u"<div class='{class_f} {class_b}'>".format(
            class_f=u"friendly-yes" if site.friendly else u"friendly-no",
            class_b=u"broken-yes" if site.broken else u""
        ))
        write(u"<img class=\"screencap\" src=\"{url}.jpg\" />".format(
                url=site.url))
        if site.friendly is not None:
            write(u"<p class='friendly {class_s}'>"
                  u"Site was judged mobile <span>{friendly}</span> "
                  u"on {date}.</p>".format(
                friendly=u"friendly" if site.friendly else u"unfriendly",
                class_s=u"friendly-yes" if site.friendly else u"friendly-no",
                date=site.date_accessed
            ))
        if site.broken is not False:
            write(u"<p class='broken'>Site was unavailable or it was not "
                  u"possible to judge mobile friendliness.</p>")

        copy_and_combine_progress(site, directory)
        write(u"<p>Here's how it was loading on a simulated 2G connection.</p>")
        write(u"<img class=\"progress-images\" src=\"{path}\" />".format(
            path=site.url + "-progress.jpg"
        ))
        write(u"<p><small><a href=\"https://stav-mobilniho-webu.appspot.com/\">"
              u"Back to main site</a></small></p>")
        write(u"</div>")
        write(u"</div>")

        write(html_tail)


def build_for_country(country):
    csv_filename = get_output_file_from_country(country,
                                                consolidated=True)
    with open(csv_filename, "r") as f:
        sites = get_sites_from_csv(f)

    sites.sort(key=lambda site: site.country_rank)

    directory = os.path.join("build", country)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Build index.html.
    filename = os.path.join(directory, "index.html")
    with open(filename, "w") as f:
        def write(s):
            f.write(s.encode(UTF8))

        write(html_head.format(
            title=u"Mobilní web: " + country,
            css=u"../screencaps.css"
        ))

        write(u"<div class=\"header\">")
        write(u"<h1>.{tld} sites</h1>".format(tld=country))
        write(u"<p><small><a href=\"https://stav-mobilniho-webu.appspot.com/\">"
              u"Back to main site</a></small></p>")
        write(u"</div>")

        for site in sorted(sites, key=lambda site: site.country_rank):
            assert isinstance(site, SiteInfo)
            site_directory = os.path.join(directory, site.url)
            if not os.path.exists(site_directory):
                os.makedirs(site_directory)

            write(u"<div class='site {class_f} {class_b}'>".format(
                class_f=u"friendly-yes" if site.friendly else u"friendly-no",
                class_b=u"broken-yes" if site.broken else u""
            ))
            write(u"<a href=\"{subdir}/\">".format(
                subdir=site.url
            ))
            copy_and_resize_image(site, site_directory)
            write(u"<img class='screencap' src=\"{url}/{url}.jpg\" />".format(
                url=site.url))
            write(u"<p class='url'>{url}</p>".format(url=site.url))
            if site.friendly is not None:
                write(u"<p class='friendly {class_s}'>{friendly}</p>".format(
                    friendly=u"Friendly" if site.friendly else u"Unfriendly",
                    class_s=u"friendly-yes" if site.friendly else u"friendly-no"
                ))
            if site.broken is not False:
                write(u"<p class='broken'>Broken</p>")
            write(u"</a>")
            write(u"</div>")

            # Build example.cz/index.html
            build_site_index_html(site, site_directory)

        write(html_tail)


TEMPLATE_STRING = u"<% TEXT %>"


def build_main():
    # Copy files
    # site_filenames = []
    # for dirpath, _, filenames in os.walk('site'):
    #     for filename in filenames:
    #         path = os.path.join(dirpath, filename)
    #         site_filenames.append(path)
    #
    #
    copy_tree("site", "build")

    with codecs.open("site/index.template.html", "r", UTF8) as f:
        index_template = f.read()

    assert isinstance(index_template, unicode)
    offset = index_template.find(TEMPLATE_STRING)

    index_head = index_template[:offset].strip()
    index_tail = index_template[offset + len(TEMPLATE_STRING):].strip()

    with codecs.open("article.md", "r", UTF8) as f:
        article_md = f.read()

    # Czech-style SmartyPants subs
    smart_ext = SmartyExtension(substitutions={
        'left-single-quote': '&sbquo;',  # sb is not a typo!
        'right-single-quote': '&lsquo;',
        'left-double-quote': '&bdquo;',
        'right-double-quote': '&ldquo;'
    })

    article_html = markdown.markdown(article_md,
                                     extensions=[
                                         "markdown.extensions.toc",
                                         "markdown.extensions.extra",
                                         smart_ext
                                     ],
                                     output_format="html5")

    output_index_path = os.path.join("build", "index.html")
    with codecs.open(output_index_path, "w", UTF8) as f:
        f.write(index_head)
        f.write(u"\n")
        f.write(article_html)
        f.write(u"\n")
        f.write(index_tail)


def main():
    for country in countries:
        build_for_country(country)

    build_main()


if __name__ == "__main__":
    main()