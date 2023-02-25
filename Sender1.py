# Andreas Hiropedi 2015345

from socket import *
import sys
import time

# retrieve data from command line
# and set buffer size to 1KB
host = sys.argv[1]
port = int(sys.argv[2])
file_name = sys.argv[3]
buf = 1024

# open socket and file reader
s = socket(AF_INET,SOCK_DGRAM)
f = open(file_name, 'rb')

# set the sequence number, end of file flag
# and read in the first 1KB of data
sequence_no = 0
sequence_bytes = sequence_no.to_bytes(2, 'big')
end_of_file = (1).to_bytes(1, 'big')
data = f.read(buf)

while data:
    # assemble packet to be sequence number + end of file + data
    packet = sequence_bytes
    packet += end_of_file
    packet += data   

    if s.sendto(packet, (host, port)):

        # check if sequence number is greater than or equal to maximum possible
        if sequence_no >= (2**16 - 1):
            sequence_no = 0
        else:
            sequence_no += 1

        # update sequence number (in bytes) and read next 1KB of data
        sequence_bytes = sequence_no.to_bytes(2, 'big')
        data = f.read(buf)

        # if the size of data is below 1KB, update end of file flag
        if len(data) < 1024:
            end_of_file = (0).to_bytes(1, 'big')
        
        time.sleep(0.1)

# close socket and file reader        
s.close()
f.close()
