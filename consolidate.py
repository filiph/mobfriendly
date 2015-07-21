import csv
from rank import SiteInfo, get_sites_from_csv, find_site_by_url

input_tld = "cz"
manual_filename = "mobfriendly-{}.csv".format(input_tld)
loadtimes_filename = "loadtimes.csv"
alexa_filename = "top-1m-sites-alexa.csv"

output_filename = "mobfriendly-{}-consolidated.csv".format(input_tld)


def main():
    with open(manual_filename, "r") as f:
        m_sites = get_sites_from_csv(f)

    with open(loadtimes_filename, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 2:
                continue
            url = row[0]
            loadtime = int(row[1])
            site = find_site_by_url(m_sites, url)
            if not site:
                continue
            site.load_whole = loadtime

    count = 0
    with open(alexa_filename, "r") as f:
        reader = csv.reader(f)
        country_ranks = {}
        for row in reader:
            if len(row) != 2:
                continue

            global_rank = int(row[0])
            url = row[1]

            site = find_site_by_url(m_sites, url)
            if not site:
                continue

            tld = url.split(".")[-1]
            if tld not in country_ranks:
                country_ranks[tld] = []
            country_ranks[tld].append(url)
            country_rank = len(country_ranks[tld])

            site.global_rank = global_rank
            site.country_rank = country_rank

            count += 1
            if count >= len(m_sites):
                break

    with open(output_filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(SiteInfo.CsvColumns_v2)
        for site in m_sites:
            writer.writerow([
                site.url,
                site.friendly,
                site.load_useful,
                site.load_whole,
                site.broken,
                site.global_rank,
                site.country_rank
            ])


if __name__ == "__main__":
    main()