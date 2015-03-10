# youtube-dl-server

Provides web interface to youtube-dl.
> More about youtube-dl https://github.com/rg3/youtube-dl

## Installation

To install on linux machine clone repo and type:

    sudo build_env.sh python3

It will install youtube-dl, curl, ffmpeg create virtual enviroment and install aiohttp

## Requirements

  * python >= 3.4
  * [youtube-dl](https://github.com/rg3/youtube-dl)
  * curl
  * ffmpeg
  * aiohttp

## Usage

To start yds server

    /path/to/project/folder/env/bin/python yds.py [OPTIONS]

Next you need to open Bookmark manager in your browser and create new bookmark. Give it name and in url input paste content of bookmarklet.js

> Note if you provided custom host and port params you need to modify variables HOST and PORT in bookmarklet.js

When you want to download audio from page click on bookmarklet

## OPTIONS

    -h, --help          print this help text and exit
    --host              Host name (default: 127.0.0.1)
    --port              Port number (default: 8070)
    --dest-audio        Folder where yds will download audio files (default: ./downloads/audio)
    --dest-video        Folder where yds will download video files (default: ./downloads/video)
    --certfile          SSL cert file (default: ./ssl/cert.pem)
    --keyfile           SSL key file (default: ./ssl/key.pem)
