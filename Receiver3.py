# Andreas Hiropedi 2015345

import sys
from socket import *


# retrieve data from command line
port = int(sys.argv[1])
file_name = sys.argv[2]

# open file writer and set up socket
f = open(file_name, 'wb')
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind(('', port))

# initialise the buffer, end of file flag,
# previous and current sequence numbers, and ack
buf = 1024
end_of_file = False
prev_sequence_no = 0
sequence_no = 0
ack = sequence_no.to_bytes(2, byteorder="big", signed=False)

while not end_of_file:
    # get packet and address from sender (account for 3 added bytes)
    data, address = s.recvfrom(buf + 3)

    # break the packet down into sequence number, end of file byte, and payload
    current_sequence_no = data[:2]
    end_of_file_byte = data[2]
    payload = data[3:]
    # print("Packet received " + str(int.from_bytes(current_sequence_no, byteorder="big", signed=False)))

    if sequence_no.to_bytes(2, byteorder="big", signed=False) == current_sequence_no:
        # if the end of file is reached, update the boolean flag
        if end_of_file_byte == 1:
            end_of_file = True
        # write the payload to the file
        f.write(payload)

        # and send the ACK for that package
        ack = sequence_no.to_bytes(2, byteorder="big", signed=False)
        s.sendto(ack, address)
        # print("ACK sent " + str(int.from_bytes(ack, byteorder="big", signed=False)))

        # update the previous sequence number
        prev_sequence_no = sequence_no
        # check if sequence number is greater than or equal to maximum possible
        if sequence_no >= (2 ** 16 - 1):
            sequence_no = 0
        else:
            sequence_no += 1

    else:
        # resend the ack if there is no acknowledgment of its receipt
        s.sendto(ack, address)
        # print("ACK retransmitted " + str(int.from_bytes(ack, byteorder="big", signed=False)))
    
# close file writer and socket
s.close()
f.close()
