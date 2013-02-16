#!/usr/bin/env python2
"""A simple command line interface torrent application.
   The client is limited to a single torrent."""

import argparse
import sys
import time
import libtorrent

DESTINATION = r'C:\cygwin\home\lhackenberg\code\python\quickTorrent'

STATE_STR = ['queued', 'checking', 'downloading metadata', 'downloading',
             'finished', 'seeding', 'allocating', 'checking fastresume']


def create_session(limit_down=None, limit_up=None, port=None):
    ses = libtorrent.session()

    if port is None:
        ses.listen_on(6881, 6891)
    else:
        ses.listen_on(port, port)

    if limit_down is not None:
        ses.set_download_rate_limit(limit_down)
    if limit_up is not None:
        ses.set_upload_rate_limit(limit_up)

    if ses.is_listening():
        return ses
    else:
        raise RuntimeError('Cannot connect to port %d' % port)


def main():

    # Set up the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Path to the torrent file')
    parser.add_argument('-d', '--destination', default=DESTINATION,
                        help='The download destination')
    parser.add_argument('-l', '--download-limit', dest='limit_down', type=int,
                        default=None, help='Set a maximum download rate')
    parser.add_argument('-p', '--port', type=int, default=None,
                        help='Specify a valid port to listen for connections')
    parser.add_argument('-s', '--seed', default=False, action='store_true',
                        help="Don't close when download is complete")
    parser.add_argument('-u', '--upload-limit', dest='limit_up', type=int,
                        default=None, help='Set a maximum upload rate')
    args = parser.parse_args()

    # Create a new session with the desired parameters
    session = create_session(limit_down=args.limit_down,
                             limit_up=args.limit_up,
                             port=args.port)

    # Open and add the torrent
    with open(args.filename, 'rb') as f:
        e = libtorrent.bdecode(f.read())
    info = libtorrent.torrent_info(e)
    h = session.add_torrent(info, args.destination)
    print('downloading %s:' % h.name())

    # Process the torrent
    try:
        while args.seed or not h.is_seed():
            s = h.status()
            sys.stdout.write('%.2f%% complete (down: %.1f kb/s up: %.1f kb/s '
                             'peers: %d) %s\r'
                             % (s.progress * 100, s.download_rate / 1000,
                                s.upload_rate / 1000, s.num_peers,
                                STATE_STR[s.state]))

            sys.stdout.flush()
            time.sleep(1)

            # Error handling
            while s.error != '':
                sys.stdout.write('error: %s%%' % s.error)
                sys.stdout.flush()
                time.sleep(1)

        sys.stdout.write('%s' % h.name() + ' complete\n')
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()