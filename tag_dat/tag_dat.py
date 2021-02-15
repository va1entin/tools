#!/usr/bin/env python3

# Simple tool to modify audio file tags using mutagen -> https://github.com/quodlibet/mutagen

import argparse
import mutagen
import re
import os


def setup_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-ar', '--artist', help='Artist name')
    parser.add_argument('-al', '--album', help='Album name')
    parser.add_argument('-nt', '--no-title', action='store_true', help="Don't set title from file name", default=False)
    parser.add_argument('-p', '--path', help="Path to get files from")
    parser.add_argument('-f', '--file', help="File to edit")
    parser.add_argument('-dr', '--dry-run', action='store_true', help="Don't save changes to file(s), activates verbose logging", default=False)
    parser.add_argument('-de', '--debug', action='store_true', help="Debug output", default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose logging, defaults to True if debug is True", default=False)

    args = parser.parse_args()

    if not args.file and not args.path:
        args.path = '.'

    if args.debug or args.dry_run:
        args.verbose = True

    return args


def set_tags(args, file):
    if args.verbose:
        print(f'Reading file {file}')

    title = re.sub(r'\.[a-zA-Z0-9]*$', '', file)
    try:
        m_file = mutagen.File(file)
    except mutagen.wave.error:
        print('E: mutagen.wave.error - problematic wave file found.')
        print('Ignoring...')
        print('')
        return

    if args.debug:
        print(f'File object has type: {type(m_file)}')
        print('Read from file:')
        print(m_file)

    if (isinstance(m_file, mutagen.flac.FLAC) or
            isinstance(m_file, mutagen.oggopus.OggOpus) or
            isinstance(m_file, mutagen.oggvorbis.OggVorbis)):
        if args.artist:
            m_file['artist'] = args.artist
        if args.album:
            m_file['album'] = args.album
        if not args.no_title:
            m_file['title'] = title
    elif isinstance(m_file, mutagen.mp3.MP3):
        if args.artist:
            m_file.tags.add(mutagen.id3.TPE1(text=[args.artist]))
        if args.album:
            m_file.tags.add(mutagen.id3.TALB(text=[args.album]))
        if not args.no_title:
            m_file.tags.add(mutagen.id3.TIT2(text=[title]))
    else:
        print(f'E: Unknown file type: {type(m_file)}')
        print('Ignoring...')
        print('')
        return

    if args.verbose:
        if args.no_title:
            print('Not setting title because flag -nt, --no-title is set...')
        print('Modified file object:')
        print(m_file)
    if not args.dry_run:
        print(f'Saving changes to {file}')
        m_file.save()
    else:
        print(f'Dry run. Not writing changes to {file}')
    print('')


def main(args):
    if args.file:
        set_tags(args, args.file)
    if args.path:
        os.chdir(args.path)
        files = [f for f in os.listdir('.')]
        for file in files:
            set_tags(args, file)


if __name__ == "__main__":
    args = setup_parser()
    main(args)
