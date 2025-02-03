#!/usr/bin/env python3

# Simple tool to modify audio file tags using mutagen -> https://github.com/quodlibet/mutagen

import argparse
import os
import re

import mutagen

from openai import AzureOpenAI, OpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

def setup_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--path', help="Path to get files from")
    parser.add_argument('-f', '--file', help="File to edit")

    parser.add_argument('-ar', '--artist', help='Artist name')
    parser.add_argument('-al', '--album', help='Album name')

    ai_client_group = parser.add_mutually_exclusive_group()
    ai_client_group.add_argument('-oai', '--use-openai-api', action='store_true', help='Use OpenAI API for AI-assisted operations', default=False)
    ai_client_group.add_argument('-azoai', '--use-azure-openai-services', action='store_true', help='Use Azure OpenAI API for AI-assisted operations', default=False)
    ai_client_group.add_argument('-azai', '--use-azure-ai-services', action='store_true', help='Use Azure AI Services API for AI-assisted operations', default=False)

    parser.add_argument('-m', '--ai-model', help='AI model to use', default='gpt-4o-mini')

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

def get_environment_variable(var_name, requiring_parameter):
    env_var_value = os.environ.get(var_name)
    if env_var_value:
        return env_var_value
    else:
        print(f'E: Environment variable {var_name} not set but {requiring_parameter} requires it.')
        exit(1)

def get_openai_client(
        model_name,
        api_key=get_environment_variable('OPENAI_API_KEY', '--use-openai-api')
    ):
    print(f'Using OpenAI API with model "{model_name}"')
    return OpenAI(
        api_key = api_key,
    )

def get_azure_openai_client(
        model_name,
        api_key=get_environment_variable('AZURE_OPENAI_API_KEY', '--use-azure-openai-services'),
        endpoint=get_environment_variable('AZURE_OPENAI_ENDPOINT', '--use-azure-openai-services')
    ):
    print(f'Using Azure OpenAI API with deployment "{model_name}"')
    return AzureOpenAI(
        api_key = api_key,
        azure_endpoint = endpoint,
        api_version = '2024-05-01-preview',
    )

def get_azure_ai_client(
        model_name,
        api_key=get_environment_variable('AZURE_AI_KEY', '--use-azure-ai-services'),
        endpoint=get_environment_variable('AZURE_AI_ENDPOINT', '--use-azure-ai-services')
    ):
    if not model_name:
        print('E: Azure AI Services model name not set but --use-azure-ai-services requires it.')
    print(f'Using Azure AI Services with deployment "{model_name}"')
    return ChatCompletionsClient(
        credential = AzureKeyCredential(api_key),
        endpoint = endpoint,
        model = model_name
    )

def get_user_consent(prompt):
    user_consent = input(f'{prompt} [y/N] ')
    if user_consent.lower() == 'y':
        return True
    else:
        return False

def get_chat_completion_openai(openai, model_name, sys_prompt, user_prompt):
    response = openai.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": sys_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )
    return response.choices[0].message.content

def get_chat_completion_azure_ai(azure_ai, sys_prompt, user_prompt):
    response = azure_ai.complete(
        messages=[
            SystemMessage(content=sys_prompt),
            UserMessage(content=user_prompt),
        ]
    )
    return response.choices[0].message.content

def get_tag_from_ai(args, filename, tag_type, ai_client, user_modified_ai_responses):
    print(f'Trying to get {tag_type} for file "{filename}" using AI...')
    try:
        sys_prompt = f"You are part of a music file tagging script. I'm sending you a file name and you should respond with what you think is the {tag_type} based on this file name. Give me only the {tag_type} to put into the file tags and nothing else. Don't include quotation marks in the {tag_type}. If you think there is no {tag_type} in the file name, just respond with 'no {tag_type}'. If the user asks you about the track number, your response should not include leading zeros."
        if user_modified_ai_responses:
            print(f'  Previously modified AI responses: {user_modified_ai_responses}')
            sys_prompt += f" Please consider that in previous runs the user has modified one or multiple responses of yours as specified in this JSON data: {user_modified_ai_responses}"
        user_prompt = f"Please get the {tag_type} for my file with name {filename}"

        if args.use_openai_api:
            used_service = 'OpenAI API'
            tag_prediction = get_chat_completion_openai(ai_client, args.ai_model, sys_prompt, user_prompt)
        elif args.use_azure_openai_services:
            used_service = 'Azure OpenAI API'
            tag_prediction = get_chat_completion_openai(ai_client, args.ai_model, sys_prompt, user_prompt)
        elif args.use_azure_ai_services:
            used_service = 'Azure AI Services'
            tag_prediction = get_chat_completion_azure_ai(ai_client, sys_prompt, user_prompt)
    except Exception as e:
        print(f'E: Exception from {used_service} while getting {tag_type} for file "{filename}":')
        print(e)
        exit(1)

    if tag_prediction == f'no {tag_type}':
        print(f'  {args.ai_model} on {used_service} couldn\'t find a {tag_type} in the file name.')
        user_wants_to_add_tag = get_user_consent(f'  Do you want to add a {tag_type} yourself?')
        if user_wants_to_add_tag:
            user_response = input(f'  Please enter the {tag_type}: ')
            user_modified_ai_responses.append({
                'filename': filename,
                'tag_type': tag_type,
                'original_prediction': tag_prediction,
                'modified_prediction': user_response,
            })
            return user_response, user_modified_ai_responses
    else:
        print(f'  {args.ai_model} on {used_service} predicted {tag_type} "{tag_prediction}" from file name "{filename}"')
        user_wants_to_modify_tag = get_user_consent(f'  Do you want to modify this {tag_type}?')
        if user_wants_to_modify_tag:
            user_response = input(f'  Please enter the modified {tag_type}: ')
            user_modified_ai_responses.append({
                'filename': filename,
                'tag_type': tag_type,
                'original_prediction': tag_prediction,
                'modified_prediction': user_response,
            })
            return user_response, user_modified_ai_responses
        else:
            print(f'  Using {args.ai_model} on {used_service} predicted {tag_type}.')
            return tag_prediction, user_modified_ai_responses


def get_track_title_from_ai(args, filename, ai_client, user_modified_ai_responses):
    return get_tag_from_ai(args, filename, 'track title', ai_client, user_modified_ai_responses)


def get_track_number_from_ai(args, filename, ai_client, user_modified_ai_responses):
    track_number, user_modified_ai_responses = get_tag_from_ai(args, filename, 'track number', ai_client, user_modified_ai_responses)
    return track_number.lstrip('0'), user_modified_ai_responses


def set_tags(args, file, ai_client, user_modified_ai_responses=[]):
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
            m_file['tracknumber'], user_modified_ai_responses = get_track_number_from_ai(args, file, ai_client, user_modified_ai_responses)

        if args.filename_title:
            m_file['title'] = filename_title
        elif args.filename_title_with_ai:
            m_file['title'], user_modified_ai_responses = get_track_title_from_ai(args, file, ai_client, user_modified_ai_responses)
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
            tracknumber, user_modified_ai_responses = get_track_number_from_ai(args, file, ai_client)
            m_file.tags.add(mutagen.id3.TRCK(text=[tracknumber]))

        if args.filename_title:
            m_file.tags.add(mutagen.id3.TIT2(text=[filename_title]))
        elif args.filename_title_with_ai:
            title, user_modified_ai_responses = get_track_title_from_ai(args, file, ai_client)
            m_file.tags.add(mutagen.id3.TIT2(text=[title]))
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
    return user_modified_ai_responses


def main():
    args = setup_parser()
    try:
        if args.filename_title_with_ai or args.tracknumber_with_ai:
            user_modified_ai_responses = []
            if args.use_openai_api:
                ai_client = get_openai_client(args.ai_model)
            elif args.use_azure_openai_services:
                ai_client = get_azure_openai_client(args.ai_model)
            elif args.use_azure_ai_services:
                ai_client = get_azure_ai_client(args.ai_model)
        if args.file:
            set_tags(args, args.file, ai_client)
        if args.path:
            os.chdir(args.path)
            files = [f for f in os.listdir('.')]
            for file in files:
                user_modified_ai_responses = set_tags(args, file, ai_client, user_modified_ai_responses)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        exit(1)


if __name__ == "__main__":
    main()
