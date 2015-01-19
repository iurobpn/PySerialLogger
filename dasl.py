#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Serial Logger for Data Aquisition
#file: dasl.py
#Author: Iuro Nascimento
#Date(dd/mm/yyyy): 14/01/2015

import sys
import serial
import signal
import argparse
import struct
#from servo import process

#parsing of command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--serialport", type=str, help="(default=/dev/ttyACM0)",default="/dev/ttyACM0")
parser.add_argument("-n", "--data_size", type=int, help="the number of data 'points'to be received(default=0, no limite, hit Ctrl+c to quit and save the data to file)",default=20)
parser.add_argument("-f", "--output_file", type=str, help="name of the binary data file to be created(default=data.bin)",default="data.bin")
parser.add_argument("-b", "--baudrate", type=int,help="(default=115200)",default=115200)
args=parser.parse_args()

#global variables
baud_rate=args.baudrate
outfile=args.output_file
data_size=args.data_size
port=args.serialport
data_list=[]
pack_size=0

def save_data():
  binfile = open(outfile, 'wb')
  binfile.write(struct.pack('i',len(data_list)))
  #binfile.write(struct.pack('i',pack_size))
  for pack in data_list:
    binfile.write(pack)
  binfile.close

def signal_handler(signal, frame):
  save_data()
  print("\nexiting due to user hit of Ctrl+c")
  sys.exit(0)

#convert from int to bytes
def int2bytes(i):
  if type(i).__name__=='int':
    return bytes([i])
  if type(i).__name__=='bytes':
    return i;
  else:
    return None

#test function to verify the data at the debug time
def print_data(data):
  for byte in data:
    print(int(byte),end=' ')
  print(' ')

#only to test future conversion to and from floats, never realy implemented or tested
def teste():
  struct.pack('f', 3.141592654)
  struct.unpack('f', '\xdb\x0fI@')
  struct.pack('4f', 1.0, 2.0, 3.0, 4.0)

#checksum - make sum of verification of the received packages
#data is a bytes object with all the bytes but the header and checksum ones
def checksum(data):
  cksum=0
  for byte in data:
    cksum=cksum^int(byte)
  cksum=cksum&0xFE
  return cksum


#sweet receiver, read from serial port and write to a binary file
#port: is de address of the serial port
#baud_rate: is the baud rate of the serial port
#size: the number of data points to receive
#outfile: name of the file to write the data
def receive_data():
  #last serves as to check the header, making possible to head one byte
  #at a time to check for the reader.
  if "last" not in receive_data.__dict__: receive_data.last = b'\x00'

  #opens and configures the serial port
  ser = serial.Serial()
  ser.port=port
  ser.baudrate=baud_rate
  ser.timeout=None
  ser.open()
  
  #counter of how many data has been received
  i=0

  #open the data file
  log = open(outfile, 'wb')
  while (data_size==0) or (i<data_size):
    #verify 
    num_bytes=0;
    while not num_bytes: num_bytes=ser.inWaiting();#wait for a byte
    buffer=ser.read(1)
    #print('Head: ', i , ' ', buffer , ' ', receive_data.last )
    #check the header: 0xFFFF
    if (ord(int2bytes(buffer))==0xFF) and (ord(int2bytes(receive_data.last)) == 0xFF):
      pack_size=ord(ser.read(1))
      if num_bytes<(2+pack_size):
        num_bytes=0
        while num_bytes<(pack_size-1): num_bytes=ser.inWaiting();
      buffer=int2bytes(pack_size) + ser.read(pack_size-1)
      cksum_received=int(buffer[-1])
      
      #remove the checksum received
      data=buffer[0:-1]
      log_print='%d-' % (i)
      print(log_print,end=' ')
      print('Data:' , end=' ')
      print_data(data)
      cksum_calculated=checksum(data)
      data=data[1:]#remove the size byte
      #print('cksum received:', cksum_received, ', cksum calculated:', cksum_calculated)
      if cksum_received==cksum_calculated:
        i+=1
        data_list.append(data)
        #restart the 'last' var so the reader will not be wrongly found
        receive_data.last=0
      else:
        print('error: lost data')
    else:
      #since the header doesnt match, read another byte and try again with the current byte as the last
      receive_data.last=buffer#at this point, buffer is a single byte, and may or may not be matched one of the header bytes
      #print('not a package')
  ser.close()
  log.close()


def main():
  signal.signal(signal.SIGINT, signal_handler)

  #number of packages received
  receive_data()
  save_data()


if __name__ == "__main__":
  main();
