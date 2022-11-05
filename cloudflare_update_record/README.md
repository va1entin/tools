# cloudflare_update_record.py

Updates a DNS A or AAAA record on Cloudflare with the system's current external IPv4/v6 address.

It obtains the external IPv4/v6 address from a *provider* (default: https://icanhazip.com), sets it for a specified record and finally writes it to a file to check with next time.

See my [blog post](https://valh.io/p/python-script-for-cloudflare-dns-record-updates-dyndns/) for more information and config instructions.

## Get usage

```bash
cloudflare_update_record.py -h
```

## Update a DNS A record

```bash
cloudflare_update_record.py -4
```

## Update a DNS AAAA record

```bash
cloudflare_update_record.py -6
```

## Config format

```yaml
read_token: "<YOUR READ TOKEN>"
edit_token: "<YOUR EDIT TOKEN>"
zone_name: "<YOUR ZONE NAME>"
record_name: "<YOUR RECORD NAME>" # use "@" for root record
```
