import urllib.request
import py7zr
import os

print("Скачиваю MKVToolNix 84.0 7z...")
url = "https://mkvtoolnix.download/windows/releases/84.0/mkvtoolnix-64-bit-84.0.7z"
urllib.request.urlretrieve(url, "mkvtoolnix.7z")

print("Распаковываю MKVToolNix...")
with py7zr.SevenZipFile("mkvtoolnix.7z", mode='r') as z:
    for name in z.getnames():
        if name.endswith("mkvmerge.exe"):
            print("Найдено:", name)
            z.extract(targets=[name], path="extracted_mkv")
            break

import shutil
if os.path.exists("extracted_mkv"):
    for root, dirs, files in os.walk("extracted_mkv"):
        for file in files:
            if file == "mkvmerge.exe":
                shutil.move(os.path.join(root, file), "mkvmerge.exe")
                break
    shutil.rmtree("extracted_mkv")

print("Готово!")
