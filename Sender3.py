# Andreas Hiropedi 2015345

import sys
import time
import os
import select
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

# initialise the buffer, ack buffer, sequence number, end of file flag,
# and the sequence number of first package not ACK-ed,
# and read in first 1KB of data
buf = 1024
ack_buf = 2
sequence_no = 0
end_of_file_byte = 0
first_packet_not_ACKed = 0
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
        packet += end_of_file_byte.to_bytes(1, byteorder="big", signed=False)
        packet += data

        # append the packet to the window sequence, and sent it
        window_packet_sequence.append(packet)
        s.sendto(packet, (host, port))
        # print("Packet sent " + str(sequence_no))

        # update the timer and time sent if the window is filled
        if first_packet_not_ACKed == sequence_no:
            time_sent = time.time()
            timer = True

        # check if sequence number is greater than or equal to maximum possible
        if sequence_no >= (2 ** 16 - 1):
            sequence_no = 0
        else:
            sequence_no += 1

        # read the next 1KB of data, and check if the end of the file was reached
        data = f.read(buf)
        if len(data) < 1024:
            end_of_file_byte = 1

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

                    # and adjust the window to accommodate for the ACK-ed packages
                    start_index = int_ack_data + 1 - first_packet_not_ACKed
                    window_packet_sequence = window_packet_sequence[start_index:]
                    first_packet_not_ACKed = int_ack_data + 1
                    # check if the current package has not been ack-ed, and adjust the timer and time sent
                    if first_packet_not_ACKed == sequence_no:
                        timer = False
                    else:
                        time_sent = time.time()
                        timer = True
            else:
                timed_out = True
        else:
            # reset the timer, time sent, and timeout flag
            time_sent = time.time()
            timer = True
            timed_out = False
            # retransmit the packages still left in the window sequence that haven't been ACK-ed
            for packet in window_packet_sequence:
                seq_no = int.from_bytes(packet[:2], byteorder='big')
                s.sendto(packet, (host, port))
                # print("Packet retransmitted " + str(seq_no))

# compute the total time elapsed, and print the data for the sheet
total_time = time.time() - start_time
print("Throughput: " + str(int(file_size / (1000 * total_time))))

# close file reader and socket
s.close()
f.close()
