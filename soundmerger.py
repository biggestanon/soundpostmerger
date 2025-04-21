import os
import re
import urllib.parse
import subprocess
import requests

# setup your directories here
VIDEO_DIR = "./"
AUDIO_DIR = "./soundpost_audio"
OUTPUT_DIR = "./merged"
# run it once with .webm, run it again with .mp4
# doesn't support image based soundposts
VIDEO_EXT = ".webm"

# create output directories if they don't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

""" 
I'm kind of stupid and don't know a good way to do this but to handle mp4 vs webm audio compatability I just run it twice
for both mp4s and webms and manually reencode the audio to something compatible for each
Curse people making webm soundposts with mp3 audio files
"""
if VIDEO_EXT == ".webm":
    audio_codec = "libopus" # use opus for webms, mp3 doesn't work
elif VIDEO_EXT == ".mp4":
    audio_codec = "libmp3lame"  # just use mp3 for mp4s, itjustworks

# main loop, go through every file in the folder
for filename in os.listdir(VIDEO_DIR):
    if not filename.endswith(VIDEO_EXT):
        continue

    # check if the filename contains a [sound=] tag
    match = re.search(r"\[sound=(.*?)\]", filename)
    if not match:
        print(f"Skipping {filename} (no [sound=] tag)")
        continue

    # extract the encoded URL from the filename
    encoded_url = match.group(1)
    decoded_url = urllib.parse.unquote(encoded_url)

    # some soundposts have fucked up URLs that double encode the https://, this checks for it
    if not decoded_url.startswith("http"):
        full_url = "https://" + decoded_url
    else:
        full_url = decoded_url

    # set up audio downloads, will be downloaded with same name as the video
    audio_ext = os.path.splitext(decoded_url)[1]
    audio_filename = os.path.splitext(filename)[0] + audio_ext  
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    # download the audio if it doesn't exist
    if not os.path.exists(audio_path):
        print(f"Downloading audio from: {full_url}")
        try:
            # set up headers to mimic a browser request so catbox doesn't block it
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
            }
            # make the request to download the audio
            response = requests.get(full_url, headers=headers)
            # check if the request was successful
            response.raise_for_status()
            with open(audio_path, "wb") as f:
                # write the successful request to a file
                f.write(response.content)
        except Exception as e:
            print(f"Error downloading {full_url}: {e}")
            continue
    else:
        print(f"Audio already exists: {audio_filename}")


    input_video_path = os.path.join(VIDEO_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)
    print(f"Merging {filename} with {audio_filename}")

    try:
        # run the ffmpeg command
        # ffmpeg -y -i video -i audio -c:v copy -c:a copy output
        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", audio_codec,
            output_path
        ], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to merge {filename} and {audio_filename}")

print("Conversions finished.")
