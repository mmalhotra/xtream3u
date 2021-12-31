from main import Daddy
from stream import Stream
import sys

template = """#EXTINF:0 tvg-id="{}" tvg-logo="{}" group-title="Daddy",{}\n{}|Referer={}\n"""

with open("daddy.m3u", "w", encoding="u8") as fd:
    fd.write("#EXTM3U\n")
    daddy = Daddy(sys.argv[1])
    all_channels = daddy.get_channels()
    for channel_name, channel_url in all_channels:
        try:
            stream = Stream(channel_url)
            stream_url = stream.get_m3u8()
            fd.write(template.format("", "", channel_name, stream_url, stream.get_second_iframe_src()))
        except:
            print("Skipping {}\t{}".format(channel_name, channel_url))
