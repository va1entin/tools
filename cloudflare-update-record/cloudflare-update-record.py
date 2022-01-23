#!/usr/bin/env python3
# Based on https://gist.github.com/benkulbertis/fff10759c2391b6618dd

# See for configuration: https://valh.io/p/python-script-for-cloudflare-dns-record-updates-dyndns/

import argparse
import logging
import re
import requests
import sys
import yaml


log_levels = {'crit': logging.CRITICAL, 'warn': logging.WARN, 'info': logging.INFO, 'debug': logging.DEBUG}


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Path to config file', default='cloudflare-update-record_config.yaml')
    parser.add_argument('-4', '--ipv4', help='Set IPv4 address', action='store_true')
    parser.add_argument('-6', '--ipv6', help='Set IPv6 address', action='store_true')
    parser.add_argument('-4p', '--ipv4-provider', help='Provider for IPv4 address', default='https://ipv4.icanhazip.com')
    parser.add_argument('-6p', '--ipv6-provider', help='Provider for IPv6 address', default='https://ipv6.icanhazip.com')
    parser.add_argument('-v', '--log-level', help=f'Log level, possible choices: {log_levels}', default='info')
    parser.add_argument('-l', '--log-file', help='Log file', default='cloudflare-update-record.log')
    args = parser.parse_args()

    return args


def setup_logging(args):
    if args.log_level not in log_levels.keys():
        logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels['info'])
        logging.warning(f'Specified log level {args.log_level} is not allowed, see output of -h for possible values')
    else:
        logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels[args.log_level])
        logging.debug(f'Set log level {args.log_level}')


def get_ip(version, args):
    if version == 4:
        try:
            request_successful, response = make_request('get', args.ipv4_provider)
        except:
            logging.exception(f'Could not connect to {args.ipv4_provider} with IPv{version}')
            return False
    elif version == 6:
        try:
            request_successful, response = make_request('get', args.ipv6_provider)
        except:
            logging.exception(f'Could not connect to {args.ipv6_provider} with IPv{version}')
            return False
    if request_successful:
        ip = re.sub(r'\n', '', response.text)
        return ip
    else:
        if version == 4:
            logging.critical(f'Unsuccessful request; current IPv{version} address could not be obtained from {args.ipv4_provider}, dumping response:\n{response.content}')
        elif version == 6:
            logging.critical(f'Unsuccessful request; current IPv{version} address could not be obtained from {args.ipv6_provider}, dumping response:\n{response.content}')
        return False


def make_request(kind, url, headers=None, data=None, exit_on_fail=False):
    if kind == 'get':
        response = requests.get(url, headers=headers, data=data)
    elif kind == 'put':
        response = requests.put(url, headers=headers, data=data)

    if response.status_code == 200:
        return True, response
    else:
        logging.critical(f'{kind} request failed: {url}\n{response.content}')
        if exit_on_fail:
            sys.exit(1)
        return False, response


def check_ip(current_ip_address, version):
    try:
        with open(f'cloudflare-update-record_ip{version}.txt', 'r') as f:
            old_ip = f.read()
        if current_ip_address == old_ip:
            return False
        else:
            return True
    except FileNotFoundError:
        logging.info(f'Could not find file cloudflare-update-record_ip{version}.txt, continuing...')
        return True


def get_config(args):
    try:
        with open(args.config, 'r') as stream:
            config = yaml.safe_load(stream)
    except FileNotFoundError:
        logging.critical(f'Could not find config file at {args.config} - exiting...')
        sys.exit(1)

    logging.debug(f'Config:\n{config}')

    request_successful, zone_id_response = make_request('get', f'https://api.cloudflare.com/client/v4/zones?name={config["zone_name"]}', headers={"Authorization": f"Bearer {config['read_token']}", "Content-Type": "application/json"}, exit_on_fail=True)
    config['zone_identifier'] = zone_id_response.json()['result'][0]['id']

    request_successful, record_id_response = make_request('get', f'https://api.cloudflare.com/client/v4/zones/{config["zone_identifier"]}/dns_records?name={config["record_name"]}', headers={"Authorization": f"Bearer {config['read_token']}", "Content-Type": "application/json"}, exit_on_fail=True)
    try:
        config['record_identifier'] = record_id_response.json()['result'][0]['id']
    except IndexError:
        logging.critical(f'Could not find id of DNS record. "Results" in API response were empty. Please make sure that the specified DNS record already exists and config {args.config} is correct. Try again after.')
        sys.exit(1)

    return config


def update_record(config, ip, record_type):
    request_successful, response = make_request('put', f'https://api.cloudflare.com/client/v4/zones/{config["zone_identifier"]}/dns_records/{config["record_identifier"]}', headers={"Authorization": f"Bearer {config['edit_token']}", "Content-Type": "application/json"}, data=f'{{"id": "{config["zone_identifier"]}", "type": "{record_type}", "name": "{config["record_name"]}","content": "{ip}"}}')

    if request_successful:
        logging.info(f'DNS {record_type} record update succeeded, IP changed to: {ip}')
    else:
        logging.critical(f'DNS {record_type} record update failed, dumping API response:\n{response.content}')
        sys.exit(1)


def write_ip(ip, version):
    logging.debug(f'Writing IPv{version} address to file: {ip}')
    with open(f'cloudflare-update-record_ip{version}.txt', 'w') as f:
        f.write(ip)


def main(ip_version, record_type, args):
    current_ip_address = get_ip(ip_version, args)
    if current_ip_address:
        ip_different = check_ip(current_ip_address, ip_version)
        if ip_different:
            config = get_config(args)
            update_record(config, current_ip_address, record_type)
            write_ip(current_ip_address, ip_version)
        else:
            logging.info(f'IPv{ip_version} address has not changed - skipping...')


if __name__ == '__main__':
    args = setup_parser()
    setup_logging(args)
    if not args.ipv4 and not args.ipv6:
        logging.critical('Neither -4 nor -6 parameter is set - exiting...')
        sys.exit(1)
    if args.ipv4:
        main(4, 'A', args)
    if args.ipv6:
        main(6, 'AAAA', args)
