import csv
from datetime import date
from glob import glob
import os
import pygame
import sys

input_tld = "gr"


def get_output_file_from_country(country_tld, consolidated=False):
    return "mobfriendly-{}{}.csv".format(
        country_tld,
        "-consolidated" if consolidated else ""
    )

output_file = get_output_file_from_country(input_tld)

screencap_width = 360
screencap_height = 640
right_panel_offset = 520
screencap_small_width = 90
screencap_small_height = 160

LEFT_BUTTON = 1


class SiteInfo(object):
    def __init__(self, url, friendly=None, load_useful=None, load_whole=None,
                 broken=False, global_rank=None, country_rank=None):
        self.url = url
        self.friendly = friendly
        self.load_useful = load_useful
        self.load_whole = load_whole
        self.broken = broken
        self.global_rank = global_rank
        self.country_rank = country_rank

    @property
    def date_accessed(self):
        # TODO: actually vary
        return date(2015, 7, 17)

    @property
    def tld(self):
        return self.url.split(".")[-1]

    @property
    def img_path(self):
        return '{tld}/{url}.png'.format(tld=self.tld, url=self.url)

    def get_small_imgs(self):
        """

        :return: A list of tuples in the form of (p, i), where p is the path
         and i is the integer (the number of milliseconds).
        """
        progress_filepaths = glob("{tld}/{url}/*.png.jpg".format(tld=self.tld,
                                                                 url=self.url))

        def int_from_path(path):
            filename_with_ext = os.path.split(path)[1]
            # There are two extenstions (.png and .jpg).
            filename = os.path.splitext(
                os.path.splitext(filename_with_ext)[0])[0]
            return int(filename)

        progress_filepaths.sort(key=int_from_path)
        return [(p, int_from_path(p)) for p in progress_filepaths]

    def load_img(self):
        return pygame.image.load(self.img_path)

    def generate_small_imgs(self):
        for ix, small_img_tuple in enumerate(self.get_small_imgs()):
            if ix >= 32:
                break

            path, time = small_img_tuple

            img_small = pygame.image.load(path)
            # img_small = pygame.transform.smoothscale(img_small,
            #                                          (screencap_small_width,
            #                                           screencap_small_height))

            font = pygame.font.Font(None, 30)
            text = font.render(" {} ".format(time),
                               1, (10, 10, 10))
            pos_text = text.get_rect()
            pos_text.topleft = 0, 0
            img_small.blit(text, pos_text)

            yield img_small

    def zero_out(self):
        self.friendly = None
        self.load_useful = None
        self.load_whole = None
        self.broken = False

    CsvColumns_v1 = [
        "URL",
        "Friendly",
        "LoadToUseful",
        "LoadWhole",
        "Broken"
    ]

    CsvColumns_v2 = [
        "URL",
        "Friendly",
        "LoadToUseful",
        "LoadWhole",
        "Broken",
        "GlobalRank",
        "CountryRank"
    ]

    @classmethod
    def from_dict(cls, d):
        o = cls(d["URL"])
        o.update_from_dict(d)
        return o

    def update_from_dict(self, d):
        """
        :type d: dict
        """
        assert d["URL"] == self.url

        def get_true_false_none(key):
            return (True if d[key] == "True" else
                    False if d[key] == "False" else None)

        def get_int_or_none(key):
            if d[key] == "":
                return None
            return int(d[key])

        self.friendly = get_true_false_none("Friendly")
        self.load_useful = get_int_or_none("LoadToUseful")
        self.load_whole = get_int_or_none("LoadWhole")
        self.broken = d["Broken"] == "True"

        if "GlobalRank" in d:
            self.global_rank = get_int_or_none("GlobalRank")
        if "CountryRank" in d:
            self.country_rank = get_int_or_none("CountryRank")


def find_site_by_url(sites, url):
    """
    :rtype: SiteInfo
    """
    candidates = [s for s in sites
                  if s.url == url]
    if len(candidates) != 1:
        return None
    return candidates[0]


def get_sites_from_csv(f, sites=None):
    """
    :rtype list[SiteInfo]
    """
    if sites is None:
        sites = []
        updating = False
    else:
        updating = True
    reader = csv.DictReader(f)
    for row in reader:
        if updating:
            site = find_site_by_url(sites, row["URL"])
            if not site:
                print("No site for record {}".format(row["URL"]))
                continue
            site.update_from_dict(row)
        else:
            site = SiteInfo.from_dict(row)
            sites.append(site)
    return sites


def save(sites, filename):
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(SiteInfo.CsvColumns_v1)
        for site in sites:
            writer.writerow([
                site.url,
                site.friendly,
                site.load_useful,
                site.load_whole,
                site.broken
            ])
    print("Saved")


def main():
    white = (255, 255, 255)
    w = 1400
    h = 800
    pygame.init()
    screen = pygame.display.set_mode((w, h))
    screen.fill(white)

    def show_text(msg, x, y, color, size, surface=None):
        if not surface:
            surface = screen
        font = pygame.font.Font(None, size)
        text = font.render(" {} ".format(msg), 1, (10, 10, 10))
        pos_text = text.get_rect()
        pos_text.topleft = x, y
        pygame.draw.rect(surface, color, pos_text)
        surface.blit(text, pos_text)

    def show_text_at_pct(msg, x_pct, y_pct, color=(30, 255, 30), size=36):
        scr_rect = screen.get_rect()
        x, y = x_pct * scr_rect.width, y_pct * scr_rect.height
        show_text(msg, x, y, color, size)

    def generate_small_offsets():
        x, y = right_panel_offset, 50
        ix = 0
        while True:
            yield ix, (x, y)
            ix += 1
            x += screencap_small_width
            if x + screencap_small_width > w:
                x = right_panel_offset
                y += screencap_small_height

    def show_site(site):
        """
        :type site: SiteInfo
        """
        screen.fill(white)

        img = site.load_img()
        screen.blit(img, (0, 0))

        # gen_offsets = generate_small_offsets()
        # for small_img in site.generate_small_imgs():
        #     _, (x, y) = gen_offsets.next()
        #     screen.blit(small_img, (x, y))

        pygame.display.flip()

    def show_status(site):
        """
        :type site: SiteInfo
        """
        if site.friendly is None:
            show_text_at_pct("Is this mobile friendly? Use arrows: <- YES NO ->",
                      0.5, 0, color=(200, 200, 200))
        elif site.friendly is True:
            show_text_at_pct("Friendly!", 0.5, 0.03, color=(30, 255, 30))
        else:
            show_text_at_pct("Unfriendly!", 0.5, 0.03, color=(255, 30, 30))

        if site.load_useful:
            show_text_at_pct("Useful load: {}".format(site.load_useful), 0.5, 0.95,
                      color=(30, 255, 30))

        if site.broken:
            show_text_at_pct("Broken!", 0.9, 0.95, color=(255, 30, 30))
        else:
            show_text_at_pct("Works", 0.9, 0.95, color=white)

        # TODO load_whole - just information

        pygame.display.flip()

    # sites_urls = ["seznam.cz", "google.cz", "centrum.cz"]
    filepaths = glob("{tld}/*.png".format(tld=input_tld))
    filenames_with_ext = (os.path.split(p)[1] for p in filepaths)
    sites_urls = [os.path.splitext(p)[0] for p in filenames_with_ext]

    sites = [SiteInfo(url) for url in sites_urls]

    try:
        with open(output_file, "r") as f:
            print("Reading latest state from {}.".format(output_file))
            sites = get_sites_from_csv(f, sites=sites)
    except IOError:
        print "No prior file {}".format(output_file)
        pass

    index = 0
    current = sites[index]
    gen_offsets = generate_small_offsets()
    gen_small_imgs = current.generate_small_imgs()

    show_site(current)
    show_status(current)

    pygame.event.get()  # Consume events before going to the loop.

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
                    current.zero_out()

                if event.key == pygame.K_LEFT:
                    current.friendly = True
                elif event.key == pygame.K_RIGHT:
                    current.friendly = False

                if event.key == pygame.K_x:
                    current.zero_out()
                    current.broken = True

                if event.key == pygame.K_s:
                    save(sites, output_file)

                if (event.key == pygame.K_RETURN or event.key == pygame.K_DOWN or
                        event.key == pygame.K_UP):
                    # print friendly, load_useful, load_whole
                    # save(index, friendly, load_useful, load_whole, broken)
                    index += -1 if event.key == pygame.K_UP else 1
                    index %= len(sites)
                    current = sites[index]
                    show_site(current)

                    gen_offsets = generate_small_offsets()
                    gen_small_imgs = current.generate_small_imgs()

                show_status(current)

            if event.type == pygame.MOUSEBUTTONUP and event.button == LEFT_BUTTON:
                mx, my = event.pos
                print mx, my
                for ix, (x, y) in generate_small_offsets():
                    if ix > 100:
                        current.load_useful = None
                        break
                    if (x <= mx <= x + screencap_small_width and
                            y <= my <= y + screencap_small_height):
                        current.load_useful = (ix + 1) * 250
                        break
                show_status(current)

        if gen_small_imgs is not None and gen_offsets is not None:
            try:
                _, (x, y) = gen_offsets.next()
                small_img = gen_small_imgs.next()
                screen.blit(small_img, (x, y))
                pygame.display.flip()
            except StopIteration:
                gen_small_imgs = None
                gen_offsets = None

        pygame.time.wait(10)


if __name__ == "__main__":
    main()