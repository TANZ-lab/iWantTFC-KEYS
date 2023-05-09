# -*- coding: utf-8 -*-
# Module: IWANTTFC-KEYS-L3
# Created on: 29-03-2023
# Authors: TANZ
# Version: 1.0

import base64
import requests
import json
import os
import sys
import xmltodict
import shutil
import subprocess
import glob
from pywidevine.cdm import cdm, deviceconfig
from base64 import b64encode
from pywidevine.decrypt.wvdecrypt import WvDecrypt
from contextlib import redirect_stdout

##### COLOR SETTINGS #####
os.system('')
GREEN = '\033[32m'
MAGENTA = '\033[35m'
YELLOW = '\033[33m'
RED = '\033[31m'
CYAN = '\033[36m'
CYAN_BRIGHT = '\033[1;36m'
RESET = '\033[0m'

currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)

############## Setup Binaries #################

mkvmergeexe = dirPath + '/bin/mkvmerge.exe'
m3u8re = dirPath + '/bin/RE.exe'
mediainfo = dirPath + '/bin/mediainfo.exe'
ffmpeg = dirPath + 'bin/ffmpeg.exe'
mp4decryptexe = dirPath + 'bin/mp4decrypt.exe'
cachePath = dirPath + '/cache'

###############################################

headers = {
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
    'Referer': 'https://www.iwanttfc.com/',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    'Content-Type': 'application/x-www-form-urlencoded',
}

mpd_url = input(f"{YELLOW}\nEnter MPD URL: {RESET}")
license = input(f"{YELLOW}\nEnter License URL: {RESET}")

try:
    shutil.rmtree(cachePath)
    if not os.path.exists(cachePath):
        os.makedirs(cachePath)
except:
    shutil.rmtree(cachePath)

def get_pssh(mpd_url):
    r = requests.get(url=mpd_url)
    r.raise_for_status()
    xml = xmltodict.parse(r.text)
    mpd = json.loads(json.dumps(xml))
    tracks = mpd['MPD']['Period']['AdaptationSet']
    for video_tracks in tracks:
        if video_tracks['@contentType'] == 'video':
            for t in video_tracks["ContentProtection"]:
                if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                    pssh = t["cenc:pssh"]
    return pssh

def empty_folder(folder):
    files = glob.glob('%s/*'%folder)
    for f in files:
        os.remove(f)

def divider():
    count = int(shutil.get_terminal_size().columns)
    count = count - 1
    print ('-' * count)

######################### GETTING KEYS ##############################

pssh = get_pssh(mpd_url)
print(f"\n{CYAN}[+] PSSH: " + pssh + f"{RESET}")
wvdecrypt = WvDecrypt(pssh)
raw_challenge = wvdecrypt.get_challenge()
response = requests.post(license, headers=headers, data=raw_challenge)
license_b64 = b64encode(response.content)
wvdecrypt.update_license(license_b64)
keys = wvdecrypt.start_process()
print("")
print(f"{GREEN}[+] OBTAINED KEYS: ")
for key in keys:
    print(f'{YELLOW}--key {key}{RESET}')

######################################################################
confirm = input(f"{CYAN_BRIGHT}\nYou want download this movie?{RESET}{RED} y/n {RESET}{CYAN_BRIGHT}> {RESET}")
if confirm == 'y':
    import argparse
    arguments = argparse.ArgumentParser()
    arguments.add_argument("-q", dest="quality", help="choose quality", default='1080')
    arguments.add_argument("-g", dest="group", help="group release", default='NOGRP')
    args = arguments.parse_args()

    title = license.split("=")[-3].replace("&UserAuthentication","").title()
    path = r'KEYS\\'
    with open(path+ "IWANTTFC_KEYS.txt", 'a') as f:
        with redirect_stdout(f):
            f.write('\n')
            f.write('\n' + title)
            for key in keys:
                f.write('\n' + key)

    def download_drm(mpd_url):
        reso = args.quality
        settings_video = 'res="{res}*":codec=avc1:for=best'.format(res=reso)
        download = ([m3u8re, mpd_url, '--save-name', title.replace(' ','.').replace('-','.'),
            '--tmp-dir', "cache/", '--save-dir', "cache/", '--key-text-file', path + 'IWANTTFC_KEYS.txt', '--sub-format', "SRT",
            '--write-meta-json', "false", '-sv', settings_video, '-sa', "all", '-ss', "all", '--mp4-real-time-decryption', "True"])
        subprocess.run(download)
        divider()

    download_drm(mpd_url)

    ############### GLOBAL FILES ###############
    for vid in glob.glob("cache/*.mp4"):
        out_video = vid

    AUD = ""
    for aud in glob.glob("cache/*.m4a"):
        out_audio = aud
        AUD += f" --default-track 0:yes {aud}"

    ############################################# MEDIA INFO #######################################################

    mediainfo_output_audio = subprocess.Popen([mediainfo, '--Output=JSON', '-f', out_audio], stdout=subprocess.PIPE)
    mediainfo_json_audio = json.load(mediainfo_output_audio.stdout)
    mediainfo_audio = mediainfo_json_audio

    mediainfo_output_video = subprocess.Popen([mediainfo, '--Output=JSON', '-f', out_video], stdout=subprocess.PIPE)
    mediainfo_json_video = json.load(mediainfo_output_video.stdout)
    mediainfo_video = mediainfo_json_video

    for v in mediainfo_video['media']['track']:
        if v['@type'] == 'Video':
            video_res = v['Height']
            video_resw = v['Width']
            video_format = v['Format']

    video_codec = ''
    if video_format == "AVC":
        video_codec = 'H.264'
    elif video_format == "HEVC":
        video_codec = 'HEVC'

    if video_res == "2160" or video_resw == "3840":
        vid_res = "2160p"
    elif video_res == "1080" or video_resw == "2048":
        vid_res ="1080p"
    elif video_res == "1080" or video_resw == "1920":
        vid_res ="1080p"
    elif video_res == "720" or video_resw == "1280":
        vid_res = "720p"
    elif video_res == "576":
        vid_res = "576p"
    elif video_res == "540":
        vid_res = "540p"
    elif video_res == "480":
        vid_res = "480p"
    elif video_res == "360":
        vid_res = "360p"
    elif video_res == "270":
        vid_res = "270p"
    elif video_res == "240":
        vid_res = "240p"

    for m in mediainfo_audio['media']['track']:
        if m['@type'] == 'Audio':
            codec_name = m['Format_String']
            channels_number = m['Channels']
        elif m['@type'] == 'Audio' and m['ID'] =='1':
            codec_name = m['Format_String']
            channels_number = m['Channels']
        elif m['@type'] == 'Audio' and m['ID'] =='2':
            codec_name = m['Format_String']
            channels_number = m['Channels']
    
    audio_codec = ''
    audio_channels = ''
    if codec_name == "AAC":
        audio_codec = 'AAC'
    elif codec_name == "AAC LC":
        audio_codec = "AAC"
    elif codec_name == "AAC LC SBR PS":
        audio_codec = "AAC"
    elif codec_name == "AC-3":
        audio_codec = "DD"
    elif codec_name == "E-AC-3":
        audio_codec = "DDP"
    elif codec_name == "E-AC-3 JOC":
        audio_codec = "DDP5.1.Atmos"
    elif codec_name == "MLP FBA":
        audio_codec = "TrueHD"
    elif codec_name == "DTS XLL":
        audio_codec = "DTS-HD.MA"
    
    if channels_number == "2":
        audio_channels = "2.0"
    elif channels_number == "6":
        audio_channels = "5.1"
    elif channels_number == "8":
        audio_channels = "7.1"

    if audio_codec == "DDP5.1.Atmos":
        audio_ = "DDP5.1.Atmos"
    else:
        audio_ = audio_codec + audio_channels

    output = "{}.{}.IWT.WEB-DL.{}.{}-{}".format(title.replace(' ','.'), vid_res, audio_, video_codec, args.group)
    SUBS = ""
    for sub in glob.glob("cache/*.srt"):
        lang = os.path.basename(sub).split('.')[-2]
        SUBS += f" --default-track 0:no --language 0:{lang} {sub}"

    ############## MERGING ALL DATA #################
    print("")
    print(f"{YELLOW}[+] Merging ..... ")
    mkvmerge = [mkvmergeexe, 
        '--ui-language','en', 
        '--output',
        'downloads/'+ output +'.mkv',
        '--title', output,
        '--default-track', '0:yes',
        '--compression', '0:none', 
        '--language', '0:und', out_video]

    for subtitle in SUBS.split(" "):
        if len(subtitle) == 0:
            continue
        mkvmerge.append(subtitle)

    for audio in AUD.split(" "):
        if len(audio) == 0:
            continue
        mkvmerge.append(audio)

    subprocess.run(mkvmerge)
    print("")
    print(f"{RED}[+] Cleaning Temp Folder!{RESET}")
    empty_folder(cachePath)
    print(f"{GREEN}[+] All Done :){RESET}")
else:
    sys.exit()