import requests
import copy
import re

from bs4 import BeautifulSoup

from constants import DEFAULT_HEADERS
from utils import remove_comments


class Stream:
    def __init__(self, url):
        self.url = url
        self.first_iframe = None
        self.second_iframe = None
        self.m3u8_url = None

    def get_first_iframe_src(self, url=None, force=None):
        if self.first_iframe and not force:
            return self.first_iframe
        resp = requests.get(url or self.url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        iframe = soup.find("iframe", {"id": "thatframe"})
        self.first_iframe = iframe.get("src")
        return self.first_iframe

    def get_second_iframe_src(self, url=None, force=None):
        if self.second_iframe and not force:
            return self.second_iframe
        if not self.first_iframe:
            self.get_first_iframe_src()
        resp = requests.get(url or self.first_iframe, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for iframe in soup.find_all("iframe"):
            if iframe.get("src"):
                self.second_iframe = iframe.get("src")
                return self.second_iframe

    def get_m3u8(self, url=None, force=None):
        if self.m3u8_url and not force:
            return self.m3u8_url
        my_headers = copy.copy(DEFAULT_HEADERS)
        if not self.second_iframe:
            self.get_second_iframe_src()
        my_headers["Referer"] = self.first_iframe
        resp = requests.get(url or self.second_iframe, headers=my_headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for script in soup.find_all("script"):
            script_text = script.string
            if script_text:
                cleaned_text = remove_comments(script_text)
                for some_url in re.findall(r"source:'(https?.*?)',", cleaned_text, re.MULTILINE|re.DOTALL):
                    self.m3u8_url = some_url
                    return self.m3u8_url

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1].startswith("http"):
        test_url = sys.argv[1]
    else:
        raise ValueError("No url provided")
    stream = Stream(test_url)
    print(stream.get_first_iframe_src())
    print(stream.get_second_iframe_src())
    print(stream.get_m3u8())
    print("""curl "{}" -H "Referer: {}" """.format(stream.get_m3u8(), stream.get_second_iframe_src()))
    print("""{}|Referer={}""".format(stream.get_m3u8(), stream.get_second_iframe_src()))
