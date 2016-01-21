#!/usr/bin/env python2
import datetime
import docopt
import logging
import os
import stat
import sys
import time
import urllib2

version = '0.12'

__doc__ = """
tapeit.py {version} --- Recording of Internet radio

Records an Internet radio stream for a certain duration and will attempt to
continue recording for the remaining duration in case of a broken internet
stream.

Usage:
  {filename} -o <outfileprefix> [-u <url>|-p <presetname>] [-d <duration>]
             [-t] [-f] [-v ...]
  {filename} (-h | --help)
  {filename} --version

Options:
  -o <outfileprefix>  Prefix for output filenames with appended timestamp.
  -p <presetname>     Radio station preset [default: kalw].
  -u <url>            Radio station URL
  -d <duration>       Duration of recording (minutes) [default: 60].
  -t                  Disable datetime stamp in outfilenameprefix.
  -f                  Force overwriting of outputfiles [default: False].
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
""".format(filename=os.path.basename(__file__), version=version)


presets = {'kalw': 'http://live.str3am.com:2430/kalw',
           'kpfa': 'http://streams1.kpfa.org:8000/kpfa_64'}


def record(url, duration_s, outfileprefix, usedatetimestamp=True,
           forceoverwrite=False, ext='mp3', numretries=0):
    """Records stream from url for a certain duration to files with a prefix
    and optional extension. If an exception is caught the recording will resume
    after a pause."""
    dt_start = datetime.datetime.now()
    datetimestamp = dt_start.strftime('%Y%m%d_%H%M')
    if usedatetimestamp:
        outfilename = outfileprefix + '_' + datetimestamp + '.' + ext
    else:
        outfilename = outfileprefix + '.' + ext
        if numretries > 0:
            count = 1
            while os.path.isfile(outfilename):
                outfilename = outfileprefix + '_' + str(count) + '.' + ext
                count += 1

    if os.path.isfile(outfilename):
        log.info('File already exists: %s' % outfilename)
        if forceoverwrite:
            log.info('  Overwriting file: %s (-f forceoverwrite enabled)'
                     % outfilename)
        else:
            log.error('  Exiting. (Enable overwriting with -f)')
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
        wait_s = 60
        log.info('Waiting for %s seconds and then retry recording...' % wait_s)
        time.sleep(wait_s)

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
    numretries = 0
    maxnumretries = 10
    minrecordingtime_s = 30
    while t_current - t_start < datetime.timedelta(seconds=duration_s):
        durationleft_s = duration_s - (t_current - t_start).total_seconds()
        log.info('Recording started, duration remaining: %ss' % durationleft_s)
        if numretries >= maxnumretries:
            log.warning('Maximum number of retries exceeded: %s'
                      % maxnumretries)
            log.warning('  Exiting.')
            break
        elif durationleft_s > minrecordingtime_s: # Avoid short recordings
            record(args['-u'], durationleft_s, args['-o'],
                   usedatetimestamp=(not args['-t']),
                   forceoverwrite=args['-f'], numretries=numretries)
        else:
            break
        numretries += 1
        log.info('Number of retries: %s' % numretries)
        t_current = datetime.datetime.now()

    log.info('Recording ended')
    log.debug('Processing time={0:.2f} s'.format(time.time() - start_time))
    log.debug('%s ended' % os.path.basename(__file__))
