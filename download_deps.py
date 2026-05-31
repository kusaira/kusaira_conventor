import urllib.request
import zipfile
import os

print("Скачиваю FFmpeg...")
urllib.request.urlretrieve("https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip", "ffmpeg.zip")

print("Распаковываю FFmpeg...")
with zipfile.ZipFile("ffmpeg.zip", 'r') as zip_ref:
    for file in zip_ref.namelist():
        if "ffmpeg.exe" in file:
            with open("ffmpeg.exe", "wb") as f:
                f.write(zip_ref.read(file))
            break

print("Скачиваю MKVToolNix...")
urllib.request.urlretrieve("https://github.com/nmaier/mkvtoolnix-releases/releases/download/release-84.0/mkvtoolnix-64-bit-84.0.zip", "mkvtoolnix.zip")

print("Распаковываю MKVToolNix...")
with zipfile.ZipFile("mkvtoolnix.zip", 'r') as zip_ref:
    for file in zip_ref.namelist():
        if file.endswith("mkvmerge.exe"):
            with open("mkvmerge.exe", "wb") as f:
                f.write(zip_ref.read(file))
            break

print("Готово!")
