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
    parser.add_argument('-p', '--path', help="Path to get files from", default=".")
    parser.add_argument('-f', '--file', help="File to edit")
    parser.add_argument('-dr', '--dry-run', action='store_true', help="Don't save changes to file(s), activates verbose logging", default=False)
    parser.add_argument('-de', '--debug', action='store_true', help="Debug output", default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose logging, defaults to True if debug is True", default=False)

    args = parser.parse_args()

    if args.debug or args.dry_run:
        args.verbose = True

    return args

def set_tags(args, file):
    if args.verbose:
        print(f'Reading file {file}')

    title = re.sub('\..*$', '', file)
    m_file = mutagen.File(file)

    if args.debug:
        print('Read from file:')
        print(m_file)

    m_file['artist'] = args.artist
    m_file['album'] = args.album
    m_file['title'] = title

    if args.verbose:
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
        files = [f for f in os.listdir(args.path)]
        for file in files:
            set_tags(args, file)

if __name__ == "__main__":
    args = setup_parser()
    main(args)
