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
  {filename} (-r | --random) [-v ...]
  {filename} (-h | --help)
  {filename} --version

Options:
  -l, --list         List available channels.
  -q <quality>       Audio stream quality, low/high/highest [default: highest].
  -p <playername>    Player for audio stream [default: mplayer].
  -r, --random       Play a random channel.
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

    if args['--random']:
        args['<channel>'] = random.choice(data.keys())
        log.debug('Found random channel: %s' % args['<channel>'])

    if args['<channel>']:
        log.debug('Attempting find channel: %s' % args['<channel>'])
        selected = None
        # Try matching the id
        try:
            for channel in data.keys():
                if channel == args['<channel>']:
                    selected = data[channel]
                    break
            log.debug('Could not match channel perfectly, trying fuzzy match')
            for field in ['id', 'title']:
                if selected is None:
                    for channel in data.keys():
                        pattern = re.compile(args['<channel>'], re.IGNORECASE)
                        match = pattern.search(data[channel][field])
                        if match is not None:
                            selected = data[channel]
                            log.debug('Found channel: %s' % selected['id'])
                            break
        except Exception as ex:
            log.exception('%s' % ex)
            sys.exit(1)
        else:
            if selected is None:
                message = 'Could not find the specified channel: %s' \
                    % args['<channel>']
                log.debug(message)
                print(message)
                sys.exit(1)

            log.debug('Found channel: %s' % selected['id'])
            log.debug(selected)
            log.debug('Attempting play channel: %s' % selected['id'])
            qualities = ['highest', 'high', 'low']
            quality_index = qualities.index(args['-q'])

            url = None
            while True:
                log.debug('Attempting to get url for quality: %s' %
                          qualities[quality_index])
                for playlist in selected['playlists']:
                    if playlist['quality'] == qualities[quality_index]:
                        url = playlist['url']
                        break
                if url is not None:
                    log.debug('Url found: %s for playlist %s' % (url, playlist))
                    break
                elif quality_index < len(qualities):
                    log.debug('Could not get %s quality' %
                              qualities[quality_index])
                    quality_index += 1

            if url is None:
                log.error('Could not find url')
                sys.exit(1)

            print(termcolor.colored('SomaFM: %s' % selected['title'], 'red',
                                    attrs=['bold'])),
            print('(press "q" to exit)')
            player_process = subprocess.Popen(['mplayer', url],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)
            try:
                #player_process.communicate()
                for line in player_process.stdout:
                    if line.startswith('ICY Info:'):
                        icy_info = line.split(':', 1)[1].strip()
                        attrs = dict(re.findall("(\w+)='([^']*)'", icy_info))
                        colors = ['grey', 'red', 'green', 'yellow', 'blue',
                                  'magenta', 'cyan', 'white']
                        random_color = random.choice(colors)
                        timestamp = time.strftime("%H:%M")
                        print(timestamp),
                        print(termcolor.colored(attrs.get('StreamTitle', '(none)'),
                                                random_color))
            except KeyboardInterrupt:
                log.debug('KeyboardInterrupt received. Closing player_process')
                player_process.send_signal(signal.SIGINT)
                player_process.wait()
            except:
                log.debug('Interrupt received. Closing player_process')

    log.debug('Processing time={0:.2f} s'.format(time.time() - start_time))
    log.debug('%s ended' % os.path.basename(__file__))
