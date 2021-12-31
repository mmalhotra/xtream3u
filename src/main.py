import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from constants import DEFAULT_HEADERS

class Daddy:
    def __init__(self, url):
        self.url = url
        self.channels = []

    def get_channels(self, url=None, force=None):
        if self.channels and not force:
            return self.channels
        resp = requests.get(url or self.url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all("a"):
            if a.get("href") and "/stream/" in a.get("href") and a.string and "CH-" in a.string:
                self.channels.append((a.string, urljoin(resp.url, a.get("href"))))
        return self.channels

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1].startswith("http"):
        test_url = sys.argv[1]
    else:
        raise ValueError("No argument")
    stream = Daddy(test_url)
    for channel_grp in stream.get_channels():
        print("{}\t{}".format(channel_grp[0], channel_grp[1]))
