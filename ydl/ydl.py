#!/usr/bin/env python3

import argparse
import re
import youtube_dl


BASE_OUTPUT_TEMPLATE = '%(title)s.%(ext)s'


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='?', help='YouTube URL')
    parser.add_argument('-d', '--output-dir', help='Directory to put downloaded files into')
    parser.add_argument('-v', '--verbose', help='Get verbose output', action='store_true')
    args = parser.parse_args()
    return args

def run_ydl(ydl_opts, url):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    args = setup_parser()
    if args.url:
        # print(args.url)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus'
            }]
        }
        if args.verbose:
            ydl_opts.update({'verbose': 'true'})
        output_template = ""
        if args.output_dir:
            output_template = f'{args.output_dir}'
            if not output_template.endswith('/'):
                output_template += '/'
        if re.match(r'.*(\?|&)list=.*', args.url):
            print("Is a YouTube playlist url...")
            output_template += '%(playlist_index)s_'
        else:
            print("Is an individual YouTube video...")
        output_template += BASE_OUTPUT_TEMPLATE
        ydl_opts.update({'outtmpl': output_template})
        run_ydl(ydl_opts, args.url)
    else:
        print("No URL provided!")


if __name__ == '__main__':
    main()
