# tools

This repository collects utilities and scripts for specific use cases small enough to not really need their own repo. Each tool lives in its own folder and should usually be self-explanatory through its `--help` output.

## backup_ts
Create a timestamped backup of a basic Teamspeak installation (DB dump + podman volume), encrypt it with a public key and upload it to a cloud remote via rclone.

## clean_rclone_remote_date_folders
Remove old date-named folders from an rclone remote.

## cloudflare_update_record
Update a Cloudflare DNS A/AAAA record with the host's current external IP (supports local cache, custom IP address providers and YAML config).

## cping
Wait until a TCP port on a host is reachable via nmap to detect when a service is back online after restart. One of my first little scripts ever.

## gitlab_runner_cleanup
List and optionally delete offline or not-connected GitLab runners via the GitLab API.

## google_location_timeline_car_trip_analysis
Analyze Google/Android Location Timeline JSON exports to find days with more than x km traveled by car. Vibe-coded for the most part.

## set-windows-wallpaper
PowerShell function to set the Windows desktop wallpaper and style.

## tag_dat
Very simple and fast way to tag audio files in various formats with album, artist, title and track number. Supports Azure AI for title and track number inference from file names.

## trello_archive_cleanup
Delete archived Trello cards.

## ydl
Wrapper around yt-dlp for downloading audio from YouTube with playlist detection and download archive, opinionated audio format as well as file name templates.


# Archive

These tools have not seen updates or usage in a while but are kept for reference and might or might not still work as intended.

## events_today
Query a CalDAV server and print events for today from configured calendars.

## letsencrypt_renewal
Build/verify a LE certificate using acme_tiny, check validity, symlink accordingly and reload services.

## mail_dat
Send PGP-encrypted emails via SMTP.
