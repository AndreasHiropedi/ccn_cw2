# Andreas Hiropedi 2015345

import sys
import time
import os
from socket import *
import select

# retrieve data from command line
host = sys.argv[1]
port = int(sys.argv[2])
file_name = sys.argv[3]
retry_timeout = int(sys.argv[4])

# open file reader and socket
f = open(file_name, "rb")
s = socket(AF_INET, SOCK_DGRAM)

# initialise the buffer, ack size, sequence number, end of file flag,
# and retransmissions counter, and read in first 1KB of data
buf = 1024
ack_buf = 2
sequence_no = 0
end_of_file = 0
total_retransmissions = 0
data = f.read(buf)

# get the file size, and start the timer
file_size = os.path.getsize(file_name)
start_time = time.time()

while data:
    # create the packet as Sequence number + End of file flag + Payload data
    packet = sequence_no.to_bytes(2, byteorder="big", signed=False)
    packet += end_of_file.to_bytes(1, byteorder="big", signed=False)
    packet += data

    # initialise the ACK flag as false
    is_ack = False

    while not is_ack:
        # send packet and start timer
        s.sendto(packet, (host, port))
        time_when_sent = time.time()
        # print("Packet sent " + str(sequence_no))

        # check if there is any data to be received
        thereIsData = select.select([s], [], [], retry_timeout / 1000.0)
        if thereIsData[0]:
            # if there is data to be received, then retrieve it
            ack_data, addr = s.recvfrom(ack_buf)
            # if the ack matches the sequence number, then it has been received correctly
            if ack_data == sequence_no.to_bytes(2, 'big'):
                is_ack = True
                # print("ACK received " + str(sequence_no))
                break
        # if there isn't, then a timeout occurred, so increment the number of retransmissions            
        else:
            total_retransmissions += 1
            # print("Retransmission occurred")

    # read the next 1KB of data, and check if the end of the file was reached
    data = f.read(buf)
    if len(data) < 1024:
        end_of_file = 1
    # check if sequence number is greater than or equal to maximum possible
    if sequence_no >= (2 ** 16 - 1):
        sequence_no = 0
    else:
        sequence_no += 1

# compute the total time elapsed, and print the data for the sheet
total_time = time.time() - start_time
print("Retransmissions: " + str(total_retransmissions))
print("Throughput: " + str(int(file_size / (1000 * total_time))))

# close file reader and socket
s.close()
f.close()
