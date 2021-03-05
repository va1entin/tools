#!/usr/bin/env python3

import argparse
import gnupg # python3-gnupg
import logging

from email.mime.base import MIMEBase
from email.message import Message
from smtplib import SMTP_SSL as SMTP


# mkdir ~/gpghome ; chmod 700 ~/gpghome ; gpg --homedir ~/gpghome --import ~/my_pub_key.asc ; gpg --homedir ~/gpghome --edit-key to_address@example.com -> trust -> 5 -> y -> save
# For Gmail: allow "less secure apps" in google account: https://myaccount.google.com/u/1/lesssecureapps

def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--from-address', help='From email address', type=str, required=True)
    parser.add_argument('-t', '--to-address', help='To email address', type=str, required=True)
    parser.add_argument('-s', '--subject', help='Mail subject', type=str, required=True)
    parser.add_argument('-u', '--url', help='SMTP server url', type=str, required=True)
    parser.add_argument('-g', '--gpg-home', help='GPG home dir', type=str, required=True)
    parser.add_argument('-p', '--password', help='SMTP password for user with from email address', type=str, required=True)
    parser.add_argument('-m', '--message', help='Message to send', type=str, required=True)
    parser.add_argument('-l', '--log-file', help='Log file to use', type=str, required=False, default='mail_dat.log')
    parser.add_argument('-sd', '--smtp-debug', help='Activate debug mode for SMTP connection', action='store_true', required=False, default=False)
    args = parser.parse_args()
    return args


def setup_logging(args):
    logging.basicConfig(filename=args.log_file, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def get_gpg_cipher_text(string_to_encrypt, args):
    logging.info(f'Encrypting message using key "{args.to_address}" from gpghome "{args.gpg_home}"...')
    gpg = gnupg.GPG(gnupghome=args.gpg_home)
    encrypted = gpg.encrypt(string_to_encrypt, args.to_address)
    if encrypted.status != "encryption ok":
        logging.critical(f'ERROR while encrypting message\n{encrypted.stderr}')
    else:
        logging.info('Message encrypted successfully!')
    return str(encrypted)


def get_email_string(args):
    msg = Message()
    msg.add_header(_name="Content-Type", _value="multipart/mixed", protected_headers="v1")
    msg["From"] = args.from_address
    msg["To"] = args.to_address

    msg_text = Message()
    msg_text.add_header(_name="Content-Type", _value="multipart/mixed")
    msg_text.add_header(_name="Content-Language", _value="en-US")

    msg_body = Message()
    msg_body.add_header(_name="Content-Type", _value="text/plain", charset="utf-8")
    msg_body.add_header(_name="Content-Transfer-Encoding", _value="quoted-printable")
    msg_body.set_payload(args.message + 2*"\n")

    msg_text.attach(msg_body)
    msg.attach(msg_text)

    pgp_msg = MIMEBase(_maintype="multipart", _subtype="encrypted", protocol="application/pgp-encrypted")
    pgp_msg["From"] = args.from_address
    pgp_msg["To"] = args.to_address
    pgp_msg["Subject"] = args.subject

    pgp_msg_part1 = Message()
    pgp_msg_part1.add_header(_name="Content-Type", _value="application/pgp-encrypted")
    pgp_msg_part1.add_header(_name="Content-Description", _value="PGP/MIME version identification")
    pgp_msg_part1.set_payload("Version: 1" + "\n")

    pgp_msg_part2 = Message()
    pgp_msg_part2.add_header(_name="Content-Type", _value="application/octet-stream", name="encrypted.asc")
    pgp_msg_part2.add_header(_name="Content-Description", _value="OpenPGP encrypted message")
    pgp_msg_part2.add_header(_name="Content-Disposition", _value="inline", filename="encrypted.asc")
    pgp_msg_part2.set_payload(get_gpg_cipher_text(msg.as_string(), args))

    pgp_msg.attach(pgp_msg_part1)
    pgp_msg.attach(pgp_msg_part2)

    return pgp_msg.as_string()


def send_mail(args):
    logging.info('Generating email...')
    enc_msg = get_email_string(args)

    logging.info(f'Opening SMTP connection to "{args.url}"')
    conn = SMTP(args.url)
    logging.info(f'SMTP debugging set to "{args.smtp_debug}"')
    conn.set_debuglevel(args.smtp_debug)

    logging.info(f'SMTP login with "{args.from_address}"')
    conn.login(args.from_address, args.password)

    logging.info(f'Sending email from "{args.from_address}" to "{args.to_address}"')
    conn.sendmail(args.from_address, args.to_address, enc_msg)
    logging.info('Closing SMTP connection...')
    conn.quit()


def main():
    args = setup_parser()
    setup_logging(args)
    send_mail(args)


if __name__ == '__main__':
    main()
