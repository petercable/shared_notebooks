#!/usr/bin/env python

# decode port_agent data log files

import time, sys

SYNC_BYTES = b'\xa3\x9d\x7a'

LENGTH_SYNC_BYTES = len(SYNC_BYTES)
LENGTH_MESSAGE_TYPE = 1
LENGTH_PACKET_SIZE = 2
LENGTH_CHECKSUM = 2
LENGTH_TIMESTAMP = 8
LENGTH_HEADER = LENGTH_SYNC_BYTES + LENGTH_MESSAGE_TYPE + LENGTH_PACKET_SIZE + LENGTH_CHECKSUM + LENGTH_TIMESTAMP

PACKET_SIZE_OFFSET = LENGTH_SYNC_BYTES + LENGTH_MESSAGE_TYPE
CHECKSUM_OFFSET = PACKET_SIZE_OFFSET + LENGTH_PACKET_SIZE
TIMESTAMP_OFFSET = CHECKSUM_OFFSET + LENGTH_CHECKSUM

InputBfr = b''
BytesToRead = LENGTH_SYNC_BYTES   # first thing to look for
MessageType = 0
PacketSize = 0
Checksum = 0
TimeStamp = b''

MessageTypeStr = ['Data From Instrument',
                  'Data From Driver',
                  'Port Agent Command',
                  'Port Agent Status',
                  'Port Agent Fault',
                  'Instrument Command',
                  'Heartbeat',
                  'Pickled Data From Instrument',
                  'Pickled Data From Driver']

# offset in seconds from 1/1/00 to 1/1/70
DeltaOffset = 2208988800

def Convert_64_bit_hex_to_seconds (hexValue):
    # high double-word is seconds, low double-word is fraction of a second
    # returned value seconds is a floating point
    seconds = (hexValue >> 32) + (((float) (hexValue & 0xffffffff)) / pow(2,32))
    return seconds


def ProcesByte (Byte):
    global InputBfr, BytesToRead, MessageType, PacketSize, Checksum, TimeStamp
    
    InputBfr += Byte
    #print ("processing byte <%02X>, InputBfr=<%s>" %(ord(Byte), InputBfr))
    
    if len(InputBfr) == BytesToRead:            # read the number of bytes that are needed for receiving sync, header, or data
        if BytesToRead == LENGTH_SYNC_BYTES:    # looking for sync bytes
            if InputBfr == SYNC_BYTES:
                BytesToRead = LENGTH_HEADER     # sync detected so start looking for header
            else:
                InputBfr = InputBfr[1:]         # sync not detected so throw away oldest byte and keep looking
        elif BytesToRead == LENGTH_HEADER:      # looking for header so print it
            MessageType = ord(InputBfr[LENGTH_SYNC_BYTES])
            PacketSize = (ord(InputBfr[PACKET_SIZE_OFFSET]) * 0xFF) + ord(InputBfr[PACKET_SIZE_OFFSET+1])
            Checksum = InputBfr[CHECKSUM_OFFSET:TIMESTAMP_OFFSET]
            TimeStamp = InputBfr[TIMESTAMP_OFFSET:]
            hexValue = int (TimeStamp.encode('HEX').upper(), 16)
            seconds = Convert_64_bit_hex_to_seconds (hexValue)
            #print ("Hex value %X = %s seconds" % (hexValue, str(seconds)))
            #print ("seconds adjusted = %s" %str(seconds - DeltaOffset)) 
            dateTime = time.ctime (seconds - DeltaOffset)
            #print ("MsgType=%d (%s), DataSize=%d, TimeStamp=%s (%s)"
            #       %(MessageType, MessageTypeStr[MessageType-1], PacketSize-LENGTH_HEADER, TimeStamp.encode('HEX').upper(), dateTime))
            BytesToRead += PacketSize - LENGTH_HEADER  # set BytesToRead to read to end of data
        else:     # data read so print it
            Data = InputBfr[LENGTH_HEADER:]
            #print "Packet Data = <%s>" %Data.encode('HEX').upper(),
            sys.stdout.write(Data)
            # try:
            #     Data.decode('ascii')    # check to see if data might be ascii to see if it's worth printing as a string
            # except UnicodeDecodeError:
            #     pass                    # not ascii so don't bother to print it
            # else:
            #     print "\nPacket Data as string:\n%s" %Data,   # seems that it might be ascii so print it
            # print ("\n")
            # reset globals to look for next packet
            InputBfr = b''
            BytesToRead = LENGTH_SYNC_BYTES


if __name__ == '__main__':
    NumberOfBytesRead = 0
    
    # check that there is only one parameter on the command line
    if len(sys.argv) != 2:
        print ("expecting one command line parameter (the name of the file to decode), got %d" %(len(sys.argv)-1))
        sys.exit(1)
    
    FileName = sys.argv[1]
    
    with open (FileName, "rb") as f:
        while True:
            ByteRead = f.read(1)
            if not ByteRead:
                break
            NumberOfBytesRead += 1
            ProcesByte (ByteRead)
    
    print ("total bytes processed = %d" %NumberOfBytesRead)
