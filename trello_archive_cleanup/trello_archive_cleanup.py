#!/usr/bin/env python3

import argparse
import logging
import re
import requests


log_levels = {'crit': logging.CRITICAL, 'warn': logging.WARN, 'info': logging.INFO, 'debug': logging.DEBUG}


def setup_parser():
    ''' Parse arguments '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--api-key', help='Trello API key.', required=True)
    parser.add_argument('-t', '--api-token', help='Trello API token.', required=True)
    parser.add_argument('-b', '--board-id', help='Board ID to delete cards from (optional)')
    parser.add_argument('-v', '--log-level', help=f'Log level, possible choices: {list(log_levels)}', default='info')
    parser.add_argument('-l', '--log-file', help='Log file', default='trello_archive_cleanup.log')
    parser.add_argument('-f', '--no-dry-run', help='Actually delete cards.', action='store_true')
    args = parser.parse_args()
    return args

def setup_logging(args):
    ''' Set log level and file '''
    if args.log_level not in log_levels:
        logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels['info'])
        logging.warning(f'Specified log level "{args.log_level}" is not allowed, see output of -h for possible values')
    else:
        logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels[args.log_level])
        logging.debug(f'Set log level "{args.log_level}"')

def setup_base_headers():
    ''' Setup request header to include in every request '''
    global base_headers
    base_headers = {'Accept': 'application/json'}

def get_boards(args):
    ''' Get all boards IDs and names '''
    boards = []
    api_boards = requests.get(f"https://api.trello.com/1/members/me/boards?fields=name&key={args.api_key}&token={args.api_token}", headers=base_headers)
    member_id = get_member_id(args)
    for board in api_boards.json():
        if can_delete_cards_on_board(board, member_id, args):
            boards.append({'id': board['id'], 'name': board['name']})
    return boards

def get_board_name(args):
    ''' Get board name by given board ID '''
    board_name = requests.get(f"https://api.trello.com/1/boards/{args.board_id}/name?key={args.api_key}&token={args.api_token}", headers=base_headers)
    board_name = board_name.json()['_value']
    logging.info(f"Found name '{board_name}' for board with ID '{args.board_id}'")
    return board_name

def can_delete_cards_on_board(board, member_id, args):
    ''' Check whether our user has the right membership on found boards to actually delete cards '''
    logging.debug(f"Starting membership evaluation for board with ID '{board['id']}' and name '{board['name']}'...")
    board_memberships = requests.get(f"https://api.trello.com/1/boards/{board['id']}/memberships?key={args.api_key}&token={args.api_token}", headers=base_headers)
    for board_membership in board_memberships.json():
        if board_membership['idMember'] == member_id and board_membership['memberType'] == 'admin':
            logging.debug(f"User with member ID '{board_membership['idMember']}' can delete cards on board with ID '{board['id']}' and name '{board['name']}'.")
            return True
    logging.warning(f"User with member ID '{board_membership['idMember']}' can't delete cards on board with ID '{board['id']}' and name '{board['name']}'.")
    return False

def get_member_id(args):
    ''' Get ID of user to whom API key and API token belong to '''
    member = requests.get(f"https://api.trello.com/1/members/me?key={args.api_key}&token={args.api_token}", headers=base_headers)
    member_id = member.json()['id']
    return member_id

def get_cards(board_id, args):
    ''' Get closed/archived cards on board with given ID '''
    cards = []
    api_cards = requests.get(f"https://api.trello.com/1/boards/{board_id}/cards/closed?key={args.api_key}&token={args.api_token}", headers=base_headers)
    for card in api_cards.json():
        cards.append({'id': card['id'], 'name': card['name']})
    return cards

def delete_card(card_id, args):
    ''' Delete a card by given ID '''
    requests.delete(f"https://api.trello.com/1/cards/{card_id}?key={args.api_key}&token={args.api_token}", headers=base_headers)

def main():
    args = setup_parser()
    setup_logging(args)
    setup_base_headers()
    # Get Trello boards
    if args.board_id:
        logging.info(f"Board ID was given. Only processing board with ID '{args.board_id}'.")
        board_name = get_board_name(args)
        boards = [{'id': args.board_id, 'name': board_name}]
    else:
        boards = get_boards(args)
    for board in boards:
        # Get and delete archived cards in boards
        logging.info(f"Getting archived cards from board with ID '{board['id']}' and name '{board['name']}'...")
        cards = get_cards(board['id'], args)
        logging.info(f"Starting to delete cards from board with ID '{board['id']}' and name '{board['name']}'...")
        for card in cards:
            logging.info(f"\tDeleting card with ID '{card['id']}' and name '{card['name']}'...")
            if args.no_dry_run:
                delete_card(card['id'], args)
        logging.info(f"Done for board with ID '{board['id']}' and name '{board['name']}'.")
        logging.info('')
    if not args.no_dry_run:
        logging.info('DRY RUN! Nothing was actually deleted.')


if __name__ == '__main__':
    main()
