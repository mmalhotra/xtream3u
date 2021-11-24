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

    def authenticate(self):
        resp = requests.get(self.get_authenticate_url())
        self.cc.authData = resp.json()
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

    def streams(self, stream_type):
        the_url = ""
        if stream_type == Xtream.liveType:
            the_url = self.get_live_streams_url()
        elif stream_type == Xtream.vodType:
            the_url = self.get_vod_streams_url()
        elif stream_type == Xtream.seriesType:
            the_url = self.get_series_url()

        return requests.get(the_url)

    def streams_by_category(self, stream_type, category_id):
        the_url = ""
        if stream_type == Xtream.liveType:
            the_url = self.get_live_streams_url_by_category(category_id)
        elif stream_type == Xtream.vodType:
            the_url = self.get_vod_streams_url_by_category(category_id)
        elif stream_type == Xtream.seriesType:
            the_url = self.get_series_url_by_category(category_id)

        return requests.get(the_url)

    def series_info_by_id(self, series_id):
        """
        The seasons array, might be filled or might be completely empty.
        If it is not empty, it will contain the cover, overview and the air date of the selected season.
        In your APP if you want to display the series, you have to take that from the episodes array.
        """
        return requests.get(self.get_series_info_url_by_id(series_id))

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
        url = (
            "%s/player_api.php?username=%s&password=%s&action=%s&stream_id=%s&limit=%s"
            % (
                self.server,
                self.username,
                self.password,
                "get_short_epg",
                stream_id,
                limit,
            )
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
