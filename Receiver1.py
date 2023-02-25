# Andreas Hiropedi 2015345

from socket import *
import sys

# read in data from command line, and set buffer size to 1KB
port = int(sys.argv[1])
file_name = sys.argv[2]
buf = 1024

# initialise the socket, file writer, and end of file flag    
s = socket(AF_INET,SOCK_DGRAM)
s.bind(('', port))
f = open(file_name, 'wb')
eof_byte_flag = (1).to_bytes(1, 'big')

try:
    while True:
        # read in data from sender (ensure buffer accounts for extra 3 bytes
        # from sequence number and end of file flag)
        data, address = s.recvfrom(buf+3)
        # check if there is still data to be processed
        if data is None:
            break
        else:
            # break down the package into sequence number, end of file flag, and payload
            data_array = bytearray(data)
            eof_byte = bytes(data_array[2])
            payload = bytes(data_array[3:])
            f.write(payload)
            
            # if end of file has been reached, break the loop
            if eof_byte == eof_byte_flag:
                break
            else:
                s.settimeout(5)       

# if timeout occurs, close socket and file
except timeout:
    s.close()
    f.close()
