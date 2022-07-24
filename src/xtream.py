"""
MIT License

Copyright (c) 2018 Chaz Larson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Note: The API Does not provide Full links to the requested stream.
      You have to build the url to the stream in order to play it.

For Live Streams the main format is
           http(s)://domain:port/live/self.username/self.password/streamID.ext
           ( In  allowed_output_formats element you have the available ext )

For VOD Streams the format is:

            http(s)://domain:port/movie/self.username/self.password/streamID.ext
            ( In  target_container element you have the available ext )

For Series Streams the format is

            http(s)://domain:port/series/self.username/self.password/streamID.ext
            ( In  target_container element you have the available ext )


If you want to limit the displayed output data, you can use params[offset]=X & params[items_per_page]=X on your call.

Authentication returns information about the account and self.server:

"""
import requests
import json
import os
from urllib.parse import urlunsplit, urljoin, urlparse, urlunparse


class XCCache:
    authData = {}


class Xtream:
    liveType = "Live"
    vodType = "VOD"
    seriesType = "Series"

    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.cc = XCCache()
        self.live_formats_pref = []

    def get_root_url(self):
        scheme = self.cc.authData["server_info"]["server_protocol"]
        netloc = "{url}:{port}".format(
            url=self.cc.authData["server_info"]["url"], port=self.cc.authData["server_info"]["port"]
        )
        return urlunsplit((scheme, netloc, "", "", ""))

    def get_authenticated_url_format_string(self):
        """
        returns http(s)://domain:port/{stream_type}/username/password/{stream_id}.{stream_ext}
        """
        return urljoin(
            self.get_root_url(),
            "/".join(["{stream_type}", self.username, self.password, "{stream_id}.{stream_ext}"]),
        )

    def _post_process_response(func):
        def process_response(*args, **kwargs):
            resp = func(*args, **kwargs)
            if resp.headers.get("content-type") != "application/json" or not isinstance(
                args[0], Xtream
            ):
                return resp
            the_json = resp.json()
            list_iter = the_json
            if not isinstance(the_json, list):
                list_iter = [the_json]
            format_string_url = args[0].get_authenticated_url_format_string()
            for stream_info in list_iter:
                if isinstance(stream_info, dict) and "stream_id" in stream_info:
                    stream_type = stream_info.get("stream_type")
                    if stream_type == Xtream.liveType.lower() and args[0].live_formats_pref:
                        stream_f_dict = {"stream_ext": args[0].live_formats_pref[0]}
                        stream_f_dict.update(stream_info)
                        stream_info["stream_link"] = format_string_url.format(**stream_f_dict)
                    elif stream_type == "movie" and "container_extension" in stream_info:
                        stream_f_dict = {"stream_ext": stream_info["container_extension"]}
                        stream_f_dict.update(stream_info)
                        stream_info["stream_link"] = format_string_url.format(**stream_f_dict)
                elif "episodes" in stream_info:
                    for season_num, episodes_list in stream_info["episodes"].items():
                        for episode_info in episodes_list:
                            stream_f_dict = {
                                "stream_ext": episode_info["container_extension"],
                                "stream_id": episode_info["id"],
                                "stream_type": "series",
                            }
                            stream_f_dict.update(stream_info)
                            episode_info["stream_link"] = format_string_url.format(**stream_f_dict)
                if "series_id" in stream_info:
                    stream_info["series_info"] = args[0].get_series_info_url_by_id(stream_info["series_id"])
            return the_json

        return process_response

    def authenticate(self):
        resp = requests.get(self.get_authenticate_url())
        self.cc.authData = resp.json()
        self.live_formats_pref = sorted(self.cc.authData["user_info"]["allowed_output_formats"])
        return resp

    def categories(self, stream_type):
        the_url = ""
        if stream_type == Xtream.liveType:
            the_url = self.get_live_categories_url()
        elif stream_type == Xtream.vodType:
            the_url = self.get_vod_cat_url()
        elif stream_type == Xtream.seriesType:
            the_url = self.get_series_cat_url()

        return requests.get(the_url)

    @_post_process_response
    def streams(self, stream_type):
        the_url = ""
        if stream_type == Xtream.liveType:
            the_url = self.get_live_streams_url()
        elif stream_type == Xtream.vodType:
            the_url = self.get_vod_streams_url()
        elif stream_type == Xtream.seriesType:
            the_url = self.get_series_url()

        return requests.get(the_url)

    @_post_process_response
    def streams_by_category(self, stream_type, category_id):
        the_url = ""
        if stream_type == Xtream.liveType:
            the_url = self.get_live_streams_url_by_category(category_id)
        elif stream_type == Xtream.vodType:
            the_url = self.get_vod_streams_url_by_category(category_id)
        elif stream_type == Xtream.seriesType:
            the_url = self.get_series_url_by_category(category_id)

        return requests.get(the_url)

    @_post_process_response
    def series_info_by_id(self, series_id):
        """
        The seasons array, might be filled or might be completely empty.
        If it is not empty, it will contain the cover, overview and the air date of the selected season.
        In your APP if you want to display the series, you have to take that from the episodes array.
        """
        return requests.get(self.get_series_info_url_by_id(series_id))

    @_post_process_response
    def vod_info_by_id(self, vod_id):
        return requests.get(self.get_vod_info_url_by_id(vod_id))

    def live_epg_by_stream(self, stream_id):
        """
        GET short_epg for LIVE Streams (same as stalker portal, prints the next X EPG that will play soon)
        """
        return requests.get(self.get_live_epg_url_by_stream(stream_id))

    def live_epg_by_stream_and_limit(self, stream_id, limit):
        return requests.get(self.get_live_epg_url_by_stream_and_limit(stream_id, limit))

    def all_live_epg_by_stream(self, stream_id):
        """
        GET ALL EPG for LIVE Streams (same as stalker portal, but it will print all epg listings regardless of the day)
        """
        return requests.get(self.get_all_live_epg_url_by_stream(stream_id))

    def all_epg(self):
        return requests.get(self.get_all_epg_url())

    def get_authenticate_url(self):
        url = "%s/player_api.php?username=%s&password=%s" % (
            self.server,
            self.username,
            self.password,
        )
        return url

    def get_live_categories_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_live_categories",
        )
        return url

    def get_live_streams_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_live_streams",
        )
        return url

    def get_live_streams_url_by_category(self, category_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&category_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_live_streams",
            category_id,
        )
        return url

    def get_vod_cat_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_vod_categories",
        )
        return url

    def get_vod_streams_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_vod_streams",
        )
        return url

    def get_vod_streams_url_by_category(self, category_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&category_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_vod_streams",
            category_id,
        )
        return url

    def get_series_cat_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_series_categories",
        )
        return url

    def get_series_url(self):
        url = "%s/player_api.php?username=%s&password=%s&action=%s" % (
            self.server,
            self.username,
            self.password,
            "get_series",
        )
        return url

    def get_series_url_by_category(self, category_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&category_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_series",
            category_id,
        )
        return url

    def get_series_info_url_by_id(self, series_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&series_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_series_info",
            series_id,
        )
        return url

    def get_vod_info_url_by_id(self, vod_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&vod_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_vod_info",
            vod_id,
        )
        return url

    def get_live_epg_url_by_stream(self, stream_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&stream_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_short_epg",
            stream_id,
        )
        return url

    def get_live_epg_url_by_stream_and_limit(self, stream_id, limit):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&stream_id=%s&limit=%s" % (
            self.server,
            self.username,
            self.password,
            "get_short_epg",
            stream_id,
            limit,
        )
        return url

    def get_all_live_epg_url_by_stream(self, stream_id):
        url = "%s/player_api.php?username=%s&password=%s&action=%s&stream_id=%s" % (
            self.server,
            self.username,
            self.password,
            "get_simple_data_table",
            stream_id,
        )
        return url

    def get_all_epg_url(self):
        url = "%s/xmltv.php?username=%s&password=%s" % (
            self.server,
            self.username,
            self.password,
        )
        return url


if __name__ == "__main__":
    xtream_server, xtream_un, xtream_pwd = None, None, None
    if os.environ.get("XTREAM_URL"):
        parsed = urlparse(os.environ["XTREAM_URL"])
        fake_url = list(parsed)
        for p_idx in range(2, len(fake_url)):
            fake_url[p_idx] = ""
        state = "un"
        for p_val in parsed.path.split("/"):
            if p_val:
                if state == "un":
                    xtream_un = p_val
                    state = "pwd"
                elif state == "pwd":
                    xtream_pwd = p_val
                    state = "fin"
            if state == "fin":
                break
        xtream_server = urlunparse(fake_url)
    else:
        xtream_server, xtream_un, xtream_pwd = (
            os.environ["XTREAM_SERVER"],
            os.environ["XTREAM_UN"],
            os.environ["XTREAM_PWD"],
        )
    xtream = Xtream(xtream_server, xtream_un, xtream_pwd)
    rs = xtream.authenticate()
    print(rs.json())
    print(xtream.get_root_url())

    def get_categories_lookup(stream_type):
        return {
                cat["category_id"] : cat
                    for cat in xtream.categories(stream_type).json()
                }
    vod_cats = get_categories_lookup(xtream.vodType)
    live_cats = get_categories_lookup(xtream.liveType)
    series_cats = get_categories_lookup(xtream.seriesType)

    def add_category_info(stream, cats):
        stream_cat = stream.get("category_id")
        cat = cats.get(stream_cat)
        if cat:
            stream["category"] = cat
        return stream

    with open(
        os.path.join(
            os.environ.get("XTREAM_DUMP_PATH", "/tmp"), "{}_live.txt".format(xtream_un)
        ),
        "w",
    ) as fd:
        dsa = [add_category_info(x, live_cats) for x in xtream.streams(xtream.liveType)]
        json.dump(dsa, fd, indent=4, sort_keys=True)
    with open(
        os.path.join(
            os.environ.get("XTREAM_DUMP_PATH", "/tmp"), "{}_movies.txt".format(xtream_un)
        ),
        "w",
    ) as fd:
        dsa = [add_category_info(x, vod_cats) for x in xtream.streams(xtream.vodType)]
        json.dump(dsa, fd, indent=4, sort_keys=True)
    with open(
        os.path.join(
            os.environ.get("XTREAM_DUMP_PATH", "/tmp"), "{}_series.txt".format(xtream_un)
        ),
        "w",
    ) as fd:
        dsa = [add_category_info(x, series_cats) for x in xtream.streams(xtream.seriesType)]
        json.dump(dsa, fd, indent=4, sort_keys=True)
    # ra = xtream.categories(xtream.liveType)
    # dsa = xtream.streams_by_category(xtream.liveType, 1)
    print("breakpoint")
