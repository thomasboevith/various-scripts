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
cliradio.py {version} --- play internet radio streams on the commandline

Usage:
  {filename} (-l | --list) [-c <channelfilename>] [-v ...]
  {filename} <channel> [-c <channelfilename>] [-p <playername>] [-v ...]
  {filename} (-r | --random) [-v ...]
  {filename} (-h | --help)
  {filename} --version

Options:
  -l, --list            List available channels.
  -p <playername>       Player for audio stream [default: mplayer].
  -r, --random          Play a random channel.
  -c <channelfilename>  Specify channel filename.
  -h, --help            Show this screen.
  --version             Show version.
  -v                    Print info (-vv for printing lots of info (debug)).

Examples:
  {filename} -l
  {filename} wfmu
  {filename} -c cliradio.json -l
  {filename} -c cliradio.json -r

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
    if args['-c']:
        with open(args['-c']) as jsonfile:
            jsondata = json.load(jsonfile)
            log.debug('JSON data: %s ' % jsondata)
    else:
        # Get channel information
        channels_url = 'https://raw.githubusercontent.com/thomasboevith/various-scripts-audio/master/cliradio.json'
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
        print(79 * '-')
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
            log.debug('Could not match channel perfectly, trying fuzzy' \
                                                                  + ' search')
            for field in ['id', 'title']:
                if selected is None:
                    log.debug('Fuzzy search in field: %s' % field)
                    for channel in data.keys():
                        pattern = re.compile(args['<channel>'], re.IGNORECASE)
                        match = pattern.search(data[channel][field])
                        log.debug(data[channel][field])
                        if match is not None:
                            selected = data[channel]
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

            url = selected['playlists'][0]['url']
            log.debug('Attempting to play url: %s' % url)

            print(termcolor.colored(selected['title'], 'red', attrs=['bold'])),
            print('(press "q" to exit)')
            player_process = subprocess.Popen(['mplayer', '-playlist', url],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)
            try:
                for line in player_process.stdout:
                    if line.startswith('ICY Info:'):
                        icy_info = line.split(':', 1)[1].strip()
                        attrs = dict(re.findall("(\w+)='([^']*)'", icy_info))
                        colors = ['grey', 'red', 'green', 'yellow', 'blue',
                                  'magenta', 'cyan', 'white']
                        random_color = random.choice(colors)
                        timestamp = time.strftime("%H:%M")
                        print(timestamp),
                        print(termcolor.colored(attrs.get('StreamTitle',
                                                      '(none)'), random_color))
            except KeyboardInterrupt:
                log.debug('KeyboardInterrupt received. Closing player_process')
                player_process.send_signal(signal.SIGINT)
                player_process.wait()
            except:
                log.debug('Interrupt received. Closing player_process')

    log.debug('Processing time={0:.2f} s'.format(time.time() - start_time))
    log.debug('%s ended' % os.path.basename(__file__))
