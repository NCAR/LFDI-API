#Connect to Comport
#Print what is comming in on the port
#import pyseria
import serial
import argparse
import sys
import time
import os

#Get the port from the command line
# parser = argparse.ArgumentParser(description='Connect to a comport and print the output')
# parser.add_argument('port', help='The port to connect to')
# args = parser.parse_args()

#Connect to the port
ser = serial.Serial('Com14', 115200, timeout=1)
ser.flush()

# [TX] - $VNRRG,79*7D
# [TX] - $VNWRG,79,0,0,FB,80,01,0009,0001,0010,0102,0613,0010,0031*78
# [TX] - $VNBOM,5*41
# [TX] - $VNWRG,79,0,0,0*64
# [TX] - $VNRRG,86*7D
# [TX] - $VNRRG,98*72

#Print the output
while True:
    #Write the Above to the Device
    ser.write(b'$VNRRG,79*7D\n')
    ser.write(b'$VNWRG,79,0,0,FB,80,01,0009,0001,0010,0102,0613,0010,0031*78\n')
    ser.write(b'$VNBOM,5*41\n')
    ser.write(b'$VNWRG,79,0,0,0*64\n')
    ser.write(b'$VNRRG,86*7D\n')
    ser.write(b'$VNRRG,98*72\n')
    #ser.write(b'$VNWRG,75,3,0,1A,0040,01C0,0002*6F54')
    print("here")
    #Wait for data to come in
    
    line = ser.readline()
    # only print lines starting with \xfa
    print("Line: ", line)
    if line.startswith(b'\xfa'):
        print(line)
        #Flush
        ser.flush()
    time.sleep(1)
    #Write line of bytes to file
    with open("output.txt", "a") as f:
        #write bytes
        f.write(str(line))

