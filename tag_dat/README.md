# tag_dat.py

Requirements:

* [mutagen](https://github.com/quodlibet/mutagen) in version 1.42.0 or higher

This is a simple Python script to manipulate metadata of audio files.
It iterates over all files in a given path (default: current path), sets the filename (without file ending) as title and given arguments album and artist as audio tags.
The script uses the amazing "mutagen" library under the hood and has a pretty limited scope, because more complex use cases can be implemented quickly using mutagen directly.

```
usage: tag_dat.py [-h] [-ar ARTIST] [-al ALBUM] [-p PATH] [-f FILE] [-dr] [-de] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -ar ARTIST, --artist ARTIST
                        Artist name
  -al ALBUM, --album ALBUM
                        Album name
  -p PATH, --path PATH  Path to get files from
  -f FILE, --file FILE  File to edit
  -dr, --dry-run        Don't save changes to file(s), activates verbose logging
  -de, --debug          Debug output
  -v, --verbose         Verbose logging, defaults to True if debug is True
```
