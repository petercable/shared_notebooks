#!/usr/bin/env python
import gzip

from ooi_port_agent.agents import Packet
import sys


def decode(input, out):
    if input.endswith('.gz'):
        opener = gzip.open
    else:
        opener = open
    with opener(input, "rb") as fh:
        while True:
            packet = Packet.packet_from_fh(fh)
            if packet is None:
                break
            out.write(packet.payload)


def main():
    # check that there is only one parameter on the command line
    if len(sys.argv) < 2:
        sys.stderr.write('Expected one or more files to decode, got 0!\n')
        sys.exit(1)

    outfile = sys.argv[1]
    files = sys.argv[2:]

    with open(outfile, 'w') as out:
        for filename in files:
            decode(filename, out)

if __name__ == '__main__':
    main()
