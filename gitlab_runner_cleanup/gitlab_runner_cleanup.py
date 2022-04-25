#!/usr/bin/env python3

# pip3 install python-gitlab
import argparse
import gitlab
import logging


log_levels = {'crit': logging.CRITICAL, 'warn': logging.WARN, 'info': logging.INFO, 'debug': logging.DEBUG}


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--host', help='GitLab URL', default='https://gitlab.com')
    parser.add_argument('-v', '--log-level', help=f'Log level, possible choices: {list(log_levels)}', default='info')
    parser.add_argument('-f', '--no-dry-run', help='Deactivate dry run and actually delete runners.', action='store_true')
    parser.add_argument('-t', '--token', help='GitLab API token', required=True)
    args = parser.parse_args()
    return args

def setup_logging(args):
    ''' Set log level '''
    if args.log_level not in log_levels:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels['info'])
        logging.warning(f'Specified log level "{args.log_level}" is not allowed, see output of -h for possible values')
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_levels[args.log_level])
        logging.debug(f'Set log level "{args.log_level}"')

def gitlab_auth(args):
    # private token or personal token authentication
    gl = gitlab.Gitlab(args.host, private_token=args.token)
    # make an API request to create the gl.user object. This is mandatory if you
    # use the username/password authentication.
    gl.auth()
    return gl

def get_runners_to_delete(gl):
    logging.info("Retrieving runners to delete...")
    runners_to_delete = []
    runners = gl.runners.list(all=True)
    for runner in runners:
        if (runner.online == None and runner.status == 'not_connected') or (runner.online == False and runner.status == 'offline'):
            runners_to_delete.append(runner)
    return runners_to_delete

def remove_runners(runners_to_delete, args):
    removed_count = 0
    for runner_to_delete in runners_to_delete:
        logging.info(f"Deleting runner... ID: '{runner_to_delete.id}' Name: '{runner_to_delete.description}'")
        if args.no_dry_run:
            try:
                runner_to_delete.delete()
            except gitlab.exceptions.GitlabDeleteError as e:
                logging.error(f"An error occurred trying to delete runner with ID: '{runner_to_delete.id}'.\nException:\n{e}")
        else:
            logging.info("DRY RUN! Not actually deleting runner.")
        logging.info("")
        removed_count += 1
    return removed_count

def main():
    args = setup_parser()
    setup_logging(args)
    gl = gitlab_auth(args)
    runners_to_delete = get_runners_to_delete(gl)
    removed_count = remove_runners(runners_to_delete, args)
    if removed_count >= 1:
        logging.info(f"Deleted {removed_count} runners!")
        if not args.no_dry_run:
            logging.info("DRY RUN! No runners were actually deleted. Give parameter --no-dry-run to actually delete runners.")
    else:
        logging.info("Found no runners with status 'not_connected' or 'offline' to delete.")


if __name__ == "__main__":
    main()
