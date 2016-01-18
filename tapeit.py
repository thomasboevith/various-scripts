#!/usr/bin/env python2
import datetime
import docopt
import logging
import os
import stat
import sys
import time
import urllib2

version = '0.11'

__doc__ = """
tapeit.py {version} --- Recording of Internet radio

Records an Internet radio stream for a certain duration and will attempt to
continue recording for the remaining duration in case of a broken internet
stream.

Usage:
  {filename} (-o <outfileprefix>|-O <outfileprefix>) [-u <url>|-p <presetname>]
             [-d <duration>] [-v ...]
  {filename} (-h | --help)
  {filename} --version

Options:
  -o <outfileprefix>  Prefix for output filenames with appended timestamp.
  -O <outfileprefix>  Prefix for output filenames without appended timestamp.
  -p <presetname>     Radio station preset [default: kalw].
  -u <url>            Radio station URL
  -d <duration>       Duration of recording (minutes) [default: 60].
  -h, --help          Show this screen.
  --version           Show version.
  -v                  Print info (-vv for printing lots of info (debug)).

Examples:
  {filename} -p kalw -o ~/media/radio/kalw_bluegrass_signal -d 90
  {filename} -u http://live.str3am.com:2430/kalw -o ~/media/radio/kalw

Copyright (C) 2016 Thomas Boevith

License: GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it. There is NO
WARRANTY, to the extent permitted by law.

Version description:
0.1 Initial version
0.11 Added option for outfilenameprefix without appended datetimestamp.
""".format(filename=os.path.basename(__file__), version=version)

presets = {'kalw': 'http://live.str3am.com:2430/kalw',
           'kpfa': 'http://streams1.kpfa.org:8000/kpfa_64'}


def record(url, duration_s, outfileprefix, extension='mp3'):
    """Records stream from url for a certain duration to files with a prefix and
    optional extension. If an error is caught the recording will commence after
    a timeout."""
    dt_start = datetime.datetime.now()
    datetimestamp = dt_start.strftime('%Y%m%d_%H%M')
    if args['-o']:
        outfilename = outfileprefix + '_' + datetimestamp + '.' + extension
    elif args['-O']:
        outfilename = outfileprefix + '.' + extension
    if os.path.isfile(outfilename):
        log.error('File already exists: %s. Exiting.' % outfilename)
        sys.exit(1)

    log.info('Recording from url: %s' % url)
    f = file(outfilename, 'wb')
    try:
        u = urllib2.urlopen(url)
        log.info('Writing to outfilename: %s' % outfilename)
        t_start = datetime.datetime.now()
        t_current = datetime.datetime.now()
        while t_current - t_start < datetime.timedelta(seconds=duration_s):
            f.write(u.read(1024))
            t_current = datetime.datetime.now()
        f.close()
    except:
        e = sys.exc_info()[0]
        log.error('Error in record() function: %r' % e)
        log.info('Wait and retry...')
        time.sleep(60)

    if os.stat(outfilename).st_size == 0:
        log.info('Deleting empty file: %s' % outfilename)
        os.remove(outfilename)


if __name__ == '__main__':
    start_time = time.time()
    args = docopt.docopt(__doc__, version=str(version))

    log = logging.getLogger(os.path.basename(__file__))
    formatstr = '%(asctime)-15s %(name)-17s %(levelname)-5s %(message)s'
    if args['-v'] == 2:
        logging.basicConfig(level=logging.DEBUG, format=formatstr)
    elif args['-v'] == 1:
        logging.basicConfig(level=logging.INFO, format=formatstr)
    else:
        logging.basicConfig(level=logging.WARNING, format=formatstr)

    log.debug('%s started' % os.path.basename(__file__))
    log.debug('docopt args=%s' % str(args).replace('\n', ''))

    if args['-p']:
        if args['-p'] in presets:
            args['-u'] = presets[args['-p']]
        else:
            log.error('Preset not found: %s' % args['-p'])

    duration_s = int(float(args['-d']) * 60)
    t_start = datetime.datetime.now()
    t_current = datetime.datetime.now()
    while t_current - t_start < datetime.timedelta(seconds=duration_s):
        durationleft_s = duration_s - (t_current - t_start).total_seconds()
        log.info('Recording started, duration remaining: %ss' % durationleft_s)
        if durationleft_s > 30:  # Only record if more than 30 seconds left
            record(args['-u'], durationleft_s, args['-o'])
        else:
            break
        t_current = datetime.datetime.now()

    log.info('Recording ended')
    log.debug('Processing time={0:.2f} s'.format(time.time() - start_time))
    log.debug('%s ended' % os.path.basename(__file__))
