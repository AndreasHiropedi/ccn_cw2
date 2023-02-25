# Andreas Hiropedi 2015345

import sys
import heapq as heap
from socket import *


# retrieve data from command line
port = int(sys.argv[1])
file_name = sys.argv[2]
window_size = int(sys.argv[3])

# open file writer and set up socket
f = open(file_name, 'wb')
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind(('', port))

# initialise the buffer, end of file flag,
# sequence number of first packet not received
# and a list of tuples to keep track of all packets in the buffer
buf = 1024
end_of_file_flag = False
first_packet_not_received = 0
packets_still_buffered = []

while not end_of_file_flag or packets_still_buffered:
    # get packet and address from sender (account for 3 added bytes)
    data, address = s.recvfrom(buf + 3)

    # retrieve the sequence number and end of file byte
    current_sequence_no = int.from_bytes(data[:2], byteorder='big')
    end_of_file_byte = data[2]
    payload = data[3:]
    # print("Packet received " + str(current_sequence_no))

    # check packet received is within the received window
    if first_packet_not_received <= current_sequence_no < first_packet_not_received + window_size:

        # if the end of file is reached, update the boolean flag
        if end_of_file_byte == 1:
            end_of_file_flag = True

        # check packet is in the buffer (if not, add it)
        if not (current_sequence_no, payload) in packets_still_buffered:
            heap.heappush(packets_still_buffered, (current_sequence_no, payload))

        # check packet is the next one to be written to file
        if current_sequence_no == first_packet_not_received:
            # loop until all packets before the first packet not received have been written to the file
            while packets_still_buffered[0][0] == first_packet_not_received:
                # get the current (sequence number, payload) pair
                current_pair = heap.heappop(packets_still_buffered)
                # retrieve the payload of the current packet
                current_packet_payload = current_pair[1]
                # write it to the file
                f.write(current_packet_payload)
                # increment the sequence number of first packet not received
                first_packet_not_received += 1
                # if all packets have been accounted for, then exit the loop
                if not packets_still_buffered:
                    break

        # send the ACK for current package
        ack_data = current_sequence_no.to_bytes(2, byteorder="big", signed=False)
        s.sendto(ack_data, address)
        # print("ACK sent " + str(int.from_bytes(ack_data, byteorder="big", signed=False)))

    # check if current packet is before the first packet not received
    elif current_sequence_no < first_packet_not_received:
        # and resend ACKs for all packets before that packet
        ack_data = current_sequence_no.to_bytes(2, byteorder="big", signed=False)
        s.sendto(ack_data, address)
        # print("ACK retransmitted " + str(int.from_bytes(ack_data, byteorder="big", signed=False)))

# resend final ACKs for the previous window to ensure sender closes the connection
prev_window_start = first_packet_not_received - window_size
for i in range(window_size):
    for packet in range(prev_window_start, first_packet_not_received):
        ack_data = packet.to_bytes(2, byteorder="big", signed=False)
        s.sendto(ack_data, address)
        # print("ACK final resend " + str(int.from_bytes(ack_data, byteorder='big')))

# close file writer and socket
s.close()
f.close()
