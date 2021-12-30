#! /usr/bin/python3

import serial

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
    print('Check Char is:',checkis,' expecting:',checkc)
    return (checkis==checkc)


def main():
    portcon = serial.Serial('/dev/ttyUSB0',baudrate=9600, bytesize=7, parity='E', timeout=5)
    portcon.write(b'/?!\r\n')
    print('> /?!<CR><LF>')
    ident = portcon.readline()
    print('< ',ident)
    while True:
        prelim = portcon.read_until(terminator=STX, size=1024)
        print('< ',prelim)
        message = portcon.read_until(terminator=ETX, size=1024)
        print('< ',message)
        checkc = portcon.read(size=1)
        print('< Check character', checkc)
        if messageverify(message,checkc):
            portcon.write(ACK+b'0Z0\r\n')
            print('> <ACK>0Z0<CR><LF>')
        else:
            portcon.write(NACK)
            print('> NACK')

    return

# mess = b'1-0:0.9.2*255(0211227)\r\n1-0:0.9.1*255(120524)\r\n1-0:1.8.0*255(0000501.088*kWh)\r\n!\r\n\x03'
# messageverify(mess,b'v')

if __name__ == '__main__':
    main()