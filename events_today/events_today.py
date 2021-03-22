#!/usr/bin/env python3

import argparse
import caldav # python3-caldav
import datetime
import logging
import pytz
import vobject


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--url', help='Caldav server URL', required=True)
    parser.add_argument('-u', '--user', help='Caldav user name', required=True)
    parser.add_argument('-p', '--password', help='Password for specified caldav user', required=True)
    parser.add_argument('-c', '--calendars', help='List of calendar (names) to be checked, space-separated', required=True, nargs="*", default=[])
    parser.add_argument('-t', '--timezone', help='Timezone', default="Europe/Berlin")
    parser.add_argument('-l', '--log-file', help='Log file to use', type=str, required=False, default='events_today.log')
    args = parser.parse_args()
    return args


def setup_logging(args):
    logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def get_caldav_client(args):
    try:
        logging.info(f'Opening CalDav connection to "{args.url}"')
        client = caldav.DAVClient(url=args.url, username=args.user, password=args.password)
        return client
    except:
        logging.critical(f'Could not establish connection to server "{args.url}"')
        exit(1)


def get_calendars(client):
    logging.info('Getting CalDav client principal')
    my_principal = client.principal()
    logging.info('Getting CalDav calendars')
    calendars = my_principal.calendars()
    return calendars


def get_vcal_events(calendars, timezone, calendars_to_be_checked):
    today = datetime.datetime.now(pytz.timezone(timezone)).replace(hour=0, minute=0, second=0, microsecond=0)

    if calendars:
        all_vcal_events = {}
        for calendar in calendars:
            if calendar.name in calendars_to_be_checked:
                logging.info(f'Configured calendar "{calendar.name}" was found, getting events...')
                vcal_events = calendar.date_search(today, end=today + datetime.timedelta(days=1))
                if vcal_events:
                    all_vcal_events[calendar.name] = vcal_events
                #all_vcal_events[calendar.name] = calendar.date_search(today + datetime.timedelta(days=1), end=today + datetime.timedelta(days=2))
    else:
        logging.critical("No calendars found. Exiting...")
        exit(1)

    if all_vcal_events.keys():
        logging.info('Got vcal events!')
        return all_vcal_events
    else:
        logging.critical('No calendars with the specified names could be found on the server. Exiting...')
        exit(1)


def decode_vcal_events(vcal_events):
    logging.info('Processing vcal events...')
    decoded_events = {}
    for calendar_name in vcal_events.keys():
        decoded_events[calendar_name] = []
        for event in vcal_events[calendar_name]:
            read_event = vobject.readOne(event.data)
            for component in read_event.components():
                if component.name == 'VEVENT':
                    event_summary = component.summary.valueRepr()
                    event_start = component.dtstart.valueRepr()
                    decoded_events[calendar_name].append(f'{event_summary} starting at {event_start.strftime("%Y-%-m-%d %H:%M")}')
                    logging.info(f'Added event from calendar "{calendar_name}"')
    return decoded_events


def print_events(events):
    for calendar in events.keys():
        logging.info(f'Printing decoded events from calendar "{calendar}"')
        print(calendar)
        for event in events[calendar]:
            print(f'\t{event}')


def main():
    args = setup_parser()
    setup_logging(args)
    client = get_caldav_client(args)
    calendars = get_calendars(client)
    vcal_events = get_vcal_events(calendars, args.timezone, args.calendars)
    decoded_events = decode_vcal_events(vcal_events)
    print_events(decoded_events)


if __name__ == "__main__":
    main()
