# Andreas Hiropedi 2015345

import sys
from socket import *

# read in data from the command line
port = int(sys.argv[1])
file_name = sys.argv[2]

# open file writer, and initialise socket
f = open(file_name, 'wb')
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind(('', port))

# initialise buffer, end of file flag and sequence number
buf = 1024
end_of_file = False
sequence_no = 0

while not end_of_file:
    # get packet and address from sender (account for 3 added bytes)
    data, address = s.recvfrom(buf + 3)

    # break the packet down into sequence number, end of file byte, and payload
    ack = data[:2]
    end_of_file_byte = data[2]
    payload = data[3:]
    # print("Packet received " + str(int.from_bytes(ack, byteorder="big", signed=False)))

    # send ack back to the sender
    s.sendto(ack, address)
    # print("ACK sent " + str(int.from_bytes(ack, byteorder="big", signed=False)))

    if sequence_no.to_bytes(2, byteorder="big", signed=False) == ack:
        # if the end of file is reached, update the boolean flag
        if end_of_file_byte == 1:
            end_of_file = True
        # write the payload to the file, and increment the sequence number    
        f.write(payload)
        # check if sequence number is greater than or equal to maximum possible
        if sequence_no >= (2 ** 16 - 1):
            sequence_no = 0
        else:
            sequence_no += 1

# close the socket and file writer
s.close()
f.close()
