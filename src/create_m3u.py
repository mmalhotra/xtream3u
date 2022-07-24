from main import Daddy
from stream import Stream
import sys
import tqdm
import traceback

template = """#EXTINF:0 tvg-id="{}" tvg-logo="{}" group-title="{}",{}\n{}|Referer={}\n"""
daddy = Daddy(sys.argv[1:])
all_channels = daddy.get_channels()
print("Found {} channels!".format(len(all_channels)))
if len(all_channels) > 1:
    with open("daddy.m3u", "w", encoding="u8") as fd:
        fd.write("#EXTM3U\n")
        for channel_url, channel_dict in tqdm.tqdm(sorted(all_channels.items(), key=lambda x:x[1]["name"])):
            try:
                stream = Stream(channel_url)
                stream_url = stream.get_m3u8()
                channel_dict["stream_url"] = stream_url
                channel_dict["stream_referer"] = stream.get_second_iframe_src()
                channel_name = channel_dict["name"]
                if "24/7" in channel_dict.get("categories", ["24/7"]):
                    category = "daddy"
                    if "24/7" in channel_dict.get("categories", []):
                        category = "24/7"
                    fd.write(template.format("", "", category, channel_name, stream_url, channel_dict["stream_referer"]))
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                print(traceback.print_exc())
                print("Skipping {}\t{}\t:{}".format(channel_dict, channel_url, e))

        for category, programs in sorted(daddy.categories_to_program.items(), key=lambda x:x[0]):
            for program in sorted(set(programs)):
                header = False
                for program_channel_url, program_channel_name in sorted(daddy.program_to_channel.get(program, {}).items(), key=lambda x:x[1]):
                    channel_dict = all_channels.get(program_channel_url)
                    if not channel_dict or not channel_dict.get("stream_url"):
                        continue
                    if not header:
                        fd.write(template.format("", "", category, program, channel_dict["stream_url"], channel_dict["stream_referer"]))
                        header = True
                    fd.write(template.format("", "", category, program_channel_name, channel_dict["stream_url"], channel_dict["stream_referer"]))
else:
    print("Not enough channels to dump")
