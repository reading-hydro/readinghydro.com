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
    return (checkis==checkc)


def main():

    messageelement = re.compile('1-0:([\d.]+)\\*255\\(([\d.]+)')
    nomessage = True

# Connect to the meter via the serial interface and wait till we recieve a valid message
# message starts with a STX and ends with ETX and check character
# we retry reading till we get a good message

    portcon = serial.Serial('/dev/ttyUSB0',baudrate=9600, bytesize=7, parity='E', timeout=15)
    while nomessage:
        portcon.write(b'/?!\r\n')
        try:
            message = portcon.read(size=1024)
        except serial.serialutil.SerialException:
            print('< error', file=sys.stderr)
        else:        
            print('< ',message, file=sys.stderr)
            if len(message)>100:
                if (message.find(STX) >= 0) & (message.find(STX) < message.find(ETX)):
                    me1 = message.split(STX,1)[1]
                    me2, chk = me1.split(ETX,1)
                    if me2:
                        if messageverify(me2+ETX, chk):
                            print('Message OK', file=sys.stderr)
                            nomessage = False
                            portcon.write(ACK)
                        else:
                            print('Message NOT OK', file=sys.stderr)
                            portcon.write(NACK)
    
# so now we have a good message need to parse the reading valuse out      
    readingdate = ''
    readingtime = ''
    readingimport = ''
    readingexport = ''
    elements = messageelement.findall(me2.decode())
    jsonstring = '"date":"2{rdate}","time":"{rtime}","import":"{rimport}","export":"{rexport}"'
    for ele in elements:
        if ele[0] == '0.9.2': readingdate=ele[1]
        elif ele[0] == '0.9.1': readingtime=ele[1]
        elif ele[0] == '1.8.0': readingimport=ele[1]
        elif ele[0] == '2.8.0': readingexport=ele[1]
    print('{'+jsonstring.format(rdate=readingdate, rtime=readingtime, rimport=readingimport, rexport=readingexport)+'}')
    return

#  b'/ISk5MT174-0002\r\n\x021-0:0.9.2*255(0220127)\r\n1-0:0.9.1*255(105644)\r\n1-0:1.8.0*255(0000502.853*kWh)\r\n1-0:2.8.0*255(0098697.318*kWh)\r\n!\r\n\x03\x19'

if __name__ == '__main__':
    main()