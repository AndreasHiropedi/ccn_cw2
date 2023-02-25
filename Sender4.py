# Andreas Hiropedi 2015345

import sys
import time
import os
import select
import heapq as heap
from socket import *


# retrieve data from command line
host = sys.argv[1]
port = int(sys.argv[2])
file_name = sys.argv[3]
retry_timeout = int(sys.argv[4])
window_size = int(sys.argv[5])

# open file reader and socket
f = open(file_name, "rb")
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# initialise the buffer, ack buffer, sequence number, end of file flag,
# and the sequence number of first package not ACK-ed,
# and read in first 1KB of data
buf = 1024
ack_buf = 2
first_packet_not_ACKed = 0
sequence_no = 0
end_of_file_byte = (0).to_bytes(1, byteorder="big", signed=False)
data = f.read(buf)

# initialise the timeout and timer flags, and the window packet sequence
timed_out = False
timer = False
window_packet_sequence = []

# get the file size, and start the timer
file_size = os.path.getsize(file_name)
start_time = time.time()

while data or window_packet_sequence:
    # check if there is space in the window
    if sequence_no < first_packet_not_ACKed + window_size and data:
        # create the packet as Sequence number + End of file flag + Payload data
        packet = sequence_no.to_bytes(2, byteorder="big", signed=False)
        packet += end_of_file_byte
        packet += data
        
        # append the packet to the window sequence (mark it as not ACK-ed), and sent it
        heap.heappush(window_packet_sequence, (sequence_no, packet, False))
        s.sendto(packet, (host, port))
        # print("Packet sent " + str(sequence_no))

        # update the timer and time sent if the window is filled
        if first_packet_not_ACKed == sequence_no:
            time_sent = time.time()
            timer = True

        # read the next 1KB of data, and check if the end of the file was reached
        data = f.read(buf)
        if len(data) < buf:
            end_of_file_byte = (1).to_bytes(1, byteorder="big", signed=False)

        # check if sequence number is greater than or equal to maximum possible
        if sequence_no >= (2 ** 16 - 1):
            sequence_no = 0
        else:
            sequence_no += 1

    if timer:
        if not timed_out:
            # compute the time left before a timeout occurs
            retry_timeout_milliseconds = retry_timeout / 1000.0
            time_before_timeout = retry_timeout_milliseconds - (time.time() - time_sent)
            
            if time_before_timeout > 0:
                # check if there is any data to be received
                thereIsData = select.select([s], [], [], 0)
                if thereIsData[0]:
                    # if there is data to be received, then retrieve it
                    ack_data, addr = s.recvfrom(ack_buf)
                    int_ack_data = int.from_bytes(ack_data, byteorder='big')
                    # print("ACK received " + str(int_ack_data))
                    
                    # check if the packet about to be ACK-ed is in window
                    if first_packet_not_ACKed <= int_ack_data < sequence_no:
                        for i in range(len(window_packet_sequence)):
                            # split triple into individual components
                            seq_no = window_packet_sequence[i][0]
                            packet = window_packet_sequence[i][1]
                            isACKed = window_packet_sequence[i][2]
                            # check packet was not already ACK-ed, then mark it as ACK-ed
                            if not isACKed and seq_no == int_ack_data:
                                window_packet_sequence[i] = (seq_no, packet, True)

                    # check if ACK corresponds to the first unACKed packet
                    if first_packet_not_ACKed == int_ack_data and window_packet_sequence:
                        # remove all consecutive ACK-ed packets
                        first_unacknowledged_packet = heap.heappop(window_packet_sequence)
                        # get ACK-ed flag for the current packet being considered
                        isACKed = first_unacknowledged_packet[2]
                        while isACKed and window_packet_sequence:
                            first_unacknowledged_packet = heap.heappop(window_packet_sequence)

                        # if packet is unACKed add it back to the window
                        if not isACKed:
                            heap.heappush(window_packet_sequence, first_unacknowledged_packet)
                            # update the sequence number of first package not ACK-ed
                            first_packet_not_ACKed = first_unacknowledged_packet[0]
                        else:
                            first_packet_not_ACKed = first_unacknowledged_packet[0] + 1
            else:
                timed_out = True

        else:
            # reset the timer, time sent, and timeout flag
            time_sent = time.time()
            timer = True
            timed_out = False
            # and retransmit all packets that haven't been ACK-ed
            for i in range(len(window_packet_sequence)):
                # split triple into individual components
                seq_no = window_packet_sequence[i][0]
                packet = window_packet_sequence[i][1]
                isACKed = window_packet_sequence[i][2]
                if not isACKed:
                    s.sendto(packet, (host, port))
                    # print("Packet retransmitted " + str(seq_no))
        
# compute the total time elapsed, and print the data for the sheet
total_time = time.time() - start_time
print("Throughput: " + str(int(file_size / (1000 * total_time))))

# close file reader and socket
s.close()
f.close()
