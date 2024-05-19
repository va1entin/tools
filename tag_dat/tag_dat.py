#!/usr/bin/env python3

# Simple tool to modify audio file tags using mutagen -> https://github.com/quodlibet/mutagen

import argparse
import os
import re

import mutagen
from openai import OpenAI

OPENAI_MODEL = "gpt-3.5-turbo"

def setup_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--path', help="Path to get files from")
    parser.add_argument('-f', '--file', help="File to edit")

    parser.add_argument('-ar', '--artist', help='Artist name')
    parser.add_argument('-al', '--album', help='Album name')

    title_group = parser.add_mutually_exclusive_group()
    title_group.add_argument('-ft', '--filename-title', action='store_true', help="Set title from file name (takes exact filename without file type ending: my_file.mp3 -> my_file)", default=False)
    title_group.add_argument('-ftai', '--filename-title-with-ai', action='store_true', help="Set title from file name using AI to figure out what the title is", default=False)
    title_group.add_argument('-t', '--title', help="Set title to given value")
    #parser.add_argument('-rft', '--rename-file-to-title', action='store_true', help="Rename file to title", default=False)

    tracknumber_group = parser.add_mutually_exclusive_group()
    tracknumber_group.add_argument('-tn', '--tracknumber', help="Track number")
    tracknumber_group.add_argument('-tnai', '--tracknumber-with-ai', action='store_true', help="Set track number from file name using AI to figure out what the track number is", default=False)

    parser.add_argument('-dr', '--dry-run', action='store_true', help="Don't save changes to file(s), activates verbose logging", default=False)
    parser.add_argument('-de', '--debug', action='store_true', help="Debug output", default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose logging, defaults to True if debug is True", default=False)

    args = parser.parse_args()

    if not args.file and not args.path:
        args.path = '.'

    if args.debug or args.dry_run:
        args.verbose = True

    return args


def check_openai_api_key():
    print('Checking OPENAI_API_KEY environment variable...')
    if args.filename_title_with_ai:
        print('  because --filename-title-with-ai is set.')
    if args.tracknumber_with_ai:
        print('  because --tracknumber-with-ai is set.')
    if os.environ.get('OPENAI_API_KEY'):
        try:
            openai = OpenAI()
            # add a test call to the OpenAI API here
            #print('OpenAI API key is valid.')
            return openai
        except Exception as e:
            print('E: Invalid OPENAI_API_KEY - here is the exception from OpenAI:')
            print(e)
            exit(1)
    else:
        print('E: OPENAI_API_KEY environment variable not set.')
        exit(1)


def get_user_consent(prompt):
    user_consent = input(f'{prompt} [y/N] ')
    if user_consent.lower() == 'y':
        return True
    else:
        return False


def get_tag_from_ai(openai, filename, tag_type, model=OPENAI_MODEL):
    print(f'Trying to get {tag_type} for file "{filename}" using AI...')
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are part of a music file tagging script. I'm sending you a file name and you should respond with what you think is the {tag_type} based on this file name. Give me only the {tag_type} to put into the file tags and nothing else. If you think there is no {tag_type} in the file name, just respond with 'no {tag_type}'. If the user asks you about the track number, your response should not include leading zeros."},
                {"role": "user", "content": f"Please get the {tag_type} for my file with name {filename}"},
            ],
        )
        tag_prediction = response.choices[0].message.content
    except Exception as e:
        print(f'E: Exception from OpenAI while getting {tag_type} for file "{filename}":')
        print(e)
        exit(1)

    if tag_prediction == f'no {tag_type}':
        print(f'  AI couldn\'t find a {tag_type} in the file name.')
        user_wants_to_add_tag = get_user_consent(f'  Do you want to add a {tag_type} yourself?')
        if user_wants_to_add_tag:
            return input(f'  Please enter the {tag_type}: ')
    else:
        print(f'  AI predicted {tag_type} "{tag_prediction}" from file name "{filename}"')
        user_wants_to_modify_tag = get_user_consent(f'  Do you want to modify this {tag_type}?')
        if user_wants_to_modify_tag:
            return input(f'  Please enter the modified {tag_type}: ')
        else:
            print(f'  Using AI predicted {tag_type}.')
            return tag_prediction


def get_track_title_from_ai(openai, filename):
    return get_tag_from_ai(openai, filename, 'track title')


def get_track_number_from_ai(openai, filename):
    track_number = get_tag_from_ai(openai, filename, 'track number')
    return track_number.lstrip('0')


def set_tags(args, file, openai):
    if args.verbose:
        print(f'Reading file {file}')

    try:
        m_file = mutagen.File(file)
    except mutagen.wave.error:
        print('E: mutagen.wave.error - problematic wave file found.')
        print('Ignoring...')
        print('')
        return

    if args.filename_title:
        filename_title = re.sub(r'\.[a-zA-Z0-9]*$', '', file)

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

        if args.tracknumber:
            m_file['tracknumber'] = args.tracknumber
        elif args.tracknumber_with_ai:
            m_file['tracknumber'] = get_track_number_from_ai(openai, file)

        if args.filename_title:
            m_file['title'] = filename_title
        elif args.filename_title_with_ai:
            m_file['title'] = get_track_title_from_ai(openai, file)
        elif args.title and args.file:
            m_file['title'] = args.title
    elif isinstance(m_file, mutagen.mp3.MP3):
        if m_file.tags is None:
            m_file.tags = mutagen.id3.ID3()
        if args.artist:
            m_file.tags.add(mutagen.id3.TPE1(text=[args.artist]))
        if args.album:
            m_file.tags.add(mutagen.id3.TALB(text=[args.album]))

        if args.tracknumber:
            m_file.tags.add(mutagen.id3.TRCK(text=[args.tracknumber]))
        elif args.tracknumber_with_ai:
            m_file.tags.add(mutagen.id3.TRCK(text=[get_track_number_from_ai(openai, file)]))

        if args.filename_title:
            m_file.tags.add(mutagen.id3.TIT2(text=[filename_title]))
        elif args.filename_title_with_ai:
            m_file.tags.add(mutagen.id3.TIT2(text=[get_track_title_from_ai(openai, file)]))
        elif args.title and args.file:
            m_file.tags.add(mutagen.id3.TIT2(text=[args.title]))
    else:
        print(f'E: Unknown file type: {type(m_file)}')
        print('Ignoring...')
        print('')
        return

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
    try:
        if args.filename_title_with_ai or args.tracknumber_with_ai:
            openai = check_openai_api_key()
        else:
            openai = None
        if args.file:
            set_tags(args, args.file, openai)
        if args.path:
            os.chdir(args.path)
            files = [f for f in os.listdir('.')]
            for file in files:
                set_tags(args, file, openai)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        exit(1)


if __name__ == "__main__":
    args = setup_parser()
    main(args)
