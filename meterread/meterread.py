#! /usr/bin/python3

import serial
import re
import sys

SOH = b"\x01"  # Start of header
STX = b"\x02"  # Frame start char
ETX = b"\03"  # Frame end char
EOT = b"\04"  # End of transmission
ACK = b"\x06"
NACK = b"\x15"


def messageverify(message, checkc) -> bool:
    bcc = 0
    for b in message:
        x = b & 0x7F
        bcc ^= x
        bcc &= 0x7F
    checkis = bcc.to_bytes(length=1, byteorder="big")
    return (checkis == checkc)


def main():

    messageelement = re.compile('1-0:([\d.]+)\\*255\\(([\d.]+)')
    goodmessage = False
    maxtries = 3

# Connect to the meter via the serial interface and wait till we recieve a valid message
# message starts with a STX and ends with ETX and check character
# we retry reading upto 3 times till we get a good message

    try:
        portcon = serial.Serial('/dev/ttyUSB0', baudrate=9600, bytesize=7, parity='E', timeout=5)
    except serial.serialutil.SerialException:
        print('< unable to open serial port ttyUSB0', file=sys.stderr)
        return 404
    while maxtries > 0:
        portcon.write(b'/?!\r\n')
        maxtries -= 1
        try:
            message = portcon.read(size=1024)
        except serial.serialutil.SerialException:
            print('< read error', file=sys.stderr)
        else:
            print('< ', message, file=sys.stderr)
            if len(message) > 100:
                if (message.find(STX) >= 0) & (message.find(STX) < message.find(ETX)):
                    me1 = message.split(STX, 1)[1]
                    me2, chk = me1.split(ETX, 1)
                    if me2:
                        if messageverify(me2+ETX, chk):
                            print('< Message OK', file=sys.stderr)
                            goodmessage = True
                            maxtries = 0
                            portcon.write(ACK)
                        else:
                            print('< Message NOT OK', file=sys.stderr)
                            portcon.write(NACK)

# so now we have a good message need to parse the reading valuse out
    readingdate = 'YYYMMDD'
    readingtime = 'HHMMSS'
    readingimport = '0'
    readingexport = '0'
    if goodmessage:
        elements = messageelement.findall(me2.decode())
        jsonstring = '"datetime":"{isodate}","import":{rimport},"export":{rexport}'
        for ele in elements:
            if ele[0] == '0.9.2':
                readingdate = ele[1]
            elif ele[0] == '0.9.1':
                readingtime = ele[1]
            elif ele[0] == '1.8.0':
                readingimport = ele[1].lstrip('0')
            elif ele[0] == '2.8.0':
                readingexport = ele[1].lstrip('0')
        isodate = '20' + readingdate[1:3] + '-' + readingdate[3:5] + '-' + readingdate[5:7]
        isodate += 'T' + readingtime[:2] + ':' + readingtime[2:4] + ':' + readingtime[4:6] + 'Z'
        print('{' + jsonstring.format(isodate=isodate, rimport=readingimport, rexport=readingexport) + '}')
    else:
        print('< Failed to read meter after 3 attempts')
    return

#  b'/ISk5MT174-0002\r\n\x021-0:0.9.2*255(0220127)\r\n1-0:0.9.1*255(105644)\r\n1-0:1.8.0*255(0000502.853*kWh)\r\n1-0:2.8.0*255(0098697.318*kWh)\r\n!\r\n\x03\x19'
# {"date":"2022-01-28T17:13:02Z","import":502.853,"export":100056.776}


if __name__ == '__main__':
    main()
