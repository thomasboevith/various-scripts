#!/usr/bin/env python2
import docopt
import json
import logging
import os
import random
import re
import requests
import signal
import subprocess
import sys
import termcolor
import time

version = '0.1'

__doc__ = """
somafm.py {version} --- playing SomaFM internet radio from the command line

Usage:
  {filename} (-l | --list) [-v ...]
  {filename} <channel> [-q <quality>] [-p <playername>] [-v ...]
  {filename} (-h | --help)
  {filename} --version

Options:
  -l, --list         List available channels.
  -q <quality>       Audio stream quality, low/high/highest [default: highest].
  -p <playername>    Player for audio stream [default: mplayer].
  -h, --help         Show this screen.
  --version          Show version.
  -v                 Print info (-vv for printing lots of info (debug)).

Examples:
  {filename} -l
  {filename} dronezone

Inspired by https://gist.github.com/yourcelf/4992005

Copyright (C) 2016 Thomas Boevith

License: GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it. There is NO
WARRANTY, to the extent permitted by law.
""".format(filename=os.path.basename(__file__), version=version)


if __name__ == '__main__':
    start_time = time.time()
    args = docopt.docopt(__doc__, version=str(version))

    log = logging.getLogger(os.path.basename(__file__))
    formatstr = '%(asctime)-15s %(name)-17s %(levelname)-5s %(message)s'
    if args['-v'] >= 2:
        logging.basicConfig(level=logging.DEBUG, format=formatstr)
    elif args['-v'] == 1:
        logging.basicConfig(level=logging.INFO, format=formatstr)
    else:
        logging.basicConfig(level=logging.WARNING, format=formatstr)

    log.debug('%s started' % os.path.basename(__file__))
    log.debug('docopt args=%s' % str(args).replace('\n', ''))

    # Get channel information
    channels_url = 'http://somafm.com/channels.json'
    log.debug('Requesting %s' % channels_url)
    r = requests.get(channels_url)
    status_code = r.status_code
    content = r.content
    log.debug('Status code: %s OK' % status_code)
    if status_code != 200:
        log.debug('Could not get content. Exitting.')
        sys.exit(1)

    jsondata = json.loads(content)
    # Make a dictionary with channel id as key
    data = {}
    for channel in jsondata['channels']:
        data[channel['id']] = channel

    if args['--list']:
        log.debug('Listing channels')
        print(termcolor.colored('Channel', 'red')),
        print(termcolor.colored('Title', 'green')),
        print(termcolor.colored('Description', 'white'))
        print(79*'-')
        for channel_id in sorted(data):
            print(termcolor.colored(channel_id, 'red')),
            print(termcolor.colored(data[channel_id]['title'], 'green')),
            print(termcolor.colored(data[channel_id]['description'], 'white'))

    if args['<channel>']:
        log.debug('Attempting find channel: %s' % args['<channel>'])
        # Try matching the id
        try:
            for channel in data.keys():
                if channel == args['<channel>']:
                    selected = data[channel]
                    break
            log.debug('Could not match channel perfectly, trying fuzzy match')
            for channel in data.keys():
                pattern = re.compile(args['<channel>'], re.IGNORECASE)
                id_match = pattern.match(data[channel]['id'])
                title_match = pattern.match(data[channel]['title'])
                if (id_match is not None) or (title_match is not None):
                    selected = data[channel]
                    break
        except:
            message = 'Could not find the specified channel: %s' \
                % args['<channel>']
            log.debug(message)
            print(message)
            sys.exit(1)
        else:
            log.debug('Found channel: %s' % selected['id'])
            log.debug('Attempting play channel: %s' % selected['id'])
            log.debug('Attempting to get url for quality: %s' % args['-q'])
            url = None
            while url is None:
                for playlist in selected['playlists']:
                    if playlist['quality'] == args['-q']:
                        url = playlist['url']
                        log.debug('Found url for quality %s: %s' \
                                                           % (args['-q'], url))
                        break
                log.info('Could not get url for quality: %s' % args['-q'])
                for quality in ['highest', 'high', 'low']:
                    log.debug('Attempting to get url for quality: %s' \
                                                                     % quality)
                    for playlist in selected['playlists']:
                        if playlist['quality'] == args['-q']:
                            url = playlist['url']
                            break

            print('Playing %s' % selected['title'])
            #log.debug('Running command: %s' % cmd)
            player_process = subprocess.Popen(['mplayer', url], \
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            for line in player_process.stdout:
                if line.startswith('ICY Info:'):
                    icy_info = line.split(':', 1)[1].strip()
                    attrs = dict(re.findall("(\w+)='([^']*)'", icy_info))
                    colors = ['grey', 'red', 'green', 'yellow', 'blue', \
                                  'magenta', 'cyan', 'white']
                    random_color = random.choice(colors)
                    print(termcolor.colored(attrs.get('StreamTitle', '(none)'),
                                       random_color))

    log.debug('Processing time={0:.2f} s'.format(time.time() - start_time))
    log.debug('%s ended' % os.path.basename(__file__))
