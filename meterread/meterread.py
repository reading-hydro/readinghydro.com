#! /usr/bin/python3

import serial

SOH = b"\x01"  # Start of header
STX = b"\x02"  # Frame start char
ETX = b"\03"  # Frame end char
EOT = b"\04"  # End of transmission
ACK = b"\x06"
NACK = b"\x15"


def messageverify(meaasge, checkc):
    return True


def main():
    portconnector = serial.Serial('/dev/ttyUSB0',baudrate=9600, bytesize=7, parity='E', timeout=5)
    portconnector.write(b'/?!\r\n')
    print('> /?!<CR><LF>')
    ident = portconnector.readline()
    print('< ',ident)
    portconnector.write(ACK+b'0Z0\r\n')
    print('> <ACK>0Z0<CR><LF>')
    while True:
        prelim = portconnector.read_until(terminator=STX, size=1024)
        print('< ',prelim)
        message = portconnector.read_until(terminator=ETX, size=1024)
        print('< ',message)
        checkc = portconnector.read(size=1)
        print('< Check character', checkc)
        if messageverify(message,checkc):
            portconnector.write(ACK)
            print('> <ACK>')
        else:
            portconnector.write(NACK)
            print('> NACK')

    return


if __name__ == '__main__':
    main()