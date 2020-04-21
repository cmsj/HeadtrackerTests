import binascii
import hid
import socket
import struct
import sys
import time

DEBUG=0
DEBUG_PACKET=0

OPENTRACK_SOCKET=None
OPENTRACK_IP="127.0.0.1"
OPENTRACK_PORT=4242

def dbg(message):
    if DEBUG:
        print(message)

def process_angle(angle):
    if (angle[0] != 0x55 and angle[1] != 0x53):
        dbg("Skipping non-angle data")
        return

    Data = struct.unpack("<HHH", bytearray(angle[2:8]))
    Roll = Data[0] / 32768.0 * 180
    Pitch = Data[1] / 32768.0 * 180
    Yaw = Data[2] / 32768.0 * 180

    #print("Yaw: %03d Pitch: %03d Roll: %03d" % (Yaw, Pitch, Roll))
    return(Pitch, Roll, Yaw)

def transmit_angles(angles):
    pitch = float(angles[0])
    roll = float(angles[1])
    yaw = float(angles[2])

    packet = struct.pack('dddddd', 0.0, 0.0, 0.0, yaw, pitch, roll)

    OPENTRACK_SOCKET.sendto(packet, (OPENTRACK_IP, OPENTRACK_PORT))

def process_packet(packet):
    if DEBUG_PACKET:
        print(' '.join(format(x, '02x') for x in packet))

    indexes = [ i for i in range(len(packet)) if packet[i] == 0x55 ]

    angles = None

    for index in indexes:
        angles = None
        if index > len(packet)-11:
            # skip if there isn't enough data left to process the field
            continue
        if (packet[index+1] == 0x53):
            dbg("  Processing angle data")
            angles = process_angle(packet[index:index+11])
        else:
            dbg("  Ignoring field: %s" % hex(packet[index+1]))

        if angles:
            transmit_angles(angles)

try:
    OPENTRACK_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Opening the device")

    h = hid.device()
    h.open(0x1920, 0x0100) # Wit-Motion VendorID/ProductID

    print("Manufacturer: %s" % h.get_manufacturer_string())
    print("Product: %s" % h.get_product_string())
    print("Serial No: %s" % h.get_serial_number_string())

    # read back the answer
    print("Entering data read/transmit loop")
    while True:
        d = h.read(250)
        if d:
            process_packet(d)
        else:
            break

    print("Closing the device")
    h.close()

except IOError as ex:
    print(ex)

print("Done")