# various-scripts-audio
Scripts for all sorts of audio-related purposes

## somafm.py --- Playing SomaFM internet radio from the command line
Plays SomaFM from the commandline using mplayer.

    somafm.py 0.1 --- playing SomaFM internet radio from the command line

    Usage:
      somafm.py (-l | --list) [-v ...]
      somafm.py <channel> [-q <quality>] [-p <playername>] [-v ...]
      somafm.py (-h | --help)
      somafm.py --version

    Options:
      -l, --list         List available channels.
      -q <quality>       Audio stream quality, low/high/highest [default: highest].
      -p <playername>    Player for audio stream [default: mplayer].
      -h, --help         Show this screen.
      --version          Show version.
      -v                 Print info (-vv for printing lots of info (debug)).

    Examples:
      somafm.py -l
      somafm.py dronezone

## tapeit.py --- Recording of internet radio
Records an Internet radio stream for a certain duration. Will attempt to
continue recording for the remaining duration in case of a broken internet
stream.

    tapeit.py 0.13 --- Recording of Internet radio

    Records an Internet radio stream for a certain duration and will attempt to
    continue recording for the remaining duration in case of a broken internet
    stream.

    Usage:
      tapeit.py -o <outfileprefix> [-u <url>|-p <presetname>] [-d <duration>]
                 [-t] [-f] [-v ...]
      tapeit.py (-h | --help)
      tapeit.py --version

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
      tapeit.py -p kalw -o ~/media/radio/kalw_bluegrass_signal -d 90
      tapeit.py -u http://live.str3am.com:2430/kalw -o ~/media/radio/kalw

# License
Copyright (C) 2016 Thomas Boevith

License: GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it. There is NO
WARRANTY, to the extent permitted by law.

For details please see LICENSE file.
