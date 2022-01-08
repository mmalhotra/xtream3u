import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import bs4

from constants import DEFAULT_HEADERS

class Daddy:
    def __init__(self, urls):
        self.urls = urls
        self.channels = {}
        self.categories_to_program = {}
        self.program_to_channel = {}

    def get_channels(self, urls=None, force=None):
        if self.channels and not force:
            return self.channels
        for url in (urls or self.urls):
            resp = requests.get(url, headers=DEFAULT_HEADERS)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all("a"):
                if a.get("href") and "/stream/" in a.get("href"):
                    a_url = urljoin(resp.url, a.get("href"))
                    name = a.string or self.channels.get(a_url, {}).get("name")
                    if name:
                        self.channels.setdefault(a_url, {})["name"] = name
                        if "24-hours" in url:
                            self.channels[a_url].setdefault("categories", []).append("24/7")
            for h4 in soup.find_all("h4"):
                if "alternative player" in h4.text.lower():
                    continue
                category = h4.text.strip(" |")
                p = h4.find_next("p")
                while p and p.name == "p":
                    if p.name == "p":
                        p_soup = BeautifulSoup(str(p), 'html.parser')
                        sibling = p_soup.find("hr")
                        program_name = None
                        while sibling:
                            if isinstance(sibling, bs4.element.NavigableString) and sibling.text.strip(" ") !=  "|":
                                program_name = sibling.text.strip()
                                time_stuff = program_name[:5]
                                if len(time_stuff.split(":")) == 2:
                                    hh = time_stuff.split(":")[0]
                                    mm = time_stuff.split(":")[1]
                                    try:
                                        hh = int(hh) - 6
                                        if hh < 0:
                                            hh += 24
                                        program_name = "{}:{} {}".format(str(hh).zfill(2), mm, program_name[5:].strip())
                                    except (TypeError, ValueError):
                                        pass
                                self.categories_to_program.setdefault(category, []).append(program_name)
                            if isinstance(sibling, bs4.element.Tag):
                                for a in sibling.find_all("a"):
                                    if a.get("href") and "/stream/" in a.get("href"):
                                        a_url = urljoin(resp.url, a.get("href"))
                                        name = a.string or self.channels.get(a_url, {}).get("name")
                                        if category:
                                            self.channels[a_url].setdefault("categories", []).append(category)
                                        if program_name:
                                            self.channels[a_url].setdefault("programs", []).append(program_name)
                                            self.program_to_channel.setdefault(program_name, {})[a_url] = name
                            sibling = sibling.nextSibling
                    p = p.nextSibling
        return self.channels

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1].startswith("http"):
        test_urls = sys.argv[1:]
    else:
        raise ValueError("No argument")
    stream = Daddy(test_urls)
    for channel_url, channel_dict in stream.get_channels().items():
        print("{}\t{}\t{}\t{}".format(channel_dict["name"], channel_url, ";".join(channel_dict.get("categories", [])), ";".join(channel_dict.get("programs", []))))
