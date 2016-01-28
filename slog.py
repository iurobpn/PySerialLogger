#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################
## Serial Logger for Data Aquisition
#    File: slog.py
#    Author: Iuro Nascimento
#    Date(dd/mm/yyyy): 14/01/2015
#    Finish date: 19/01/2015
#######################################################

import sys
import serial
import signal
import argparse
import struct
from datetime import datetime, time, date
import binascii
#from servo import process

#parsing of command line arguments
parser = argparse.ArgumentParser(description="Log serial data received with the format |0xFFFF | lenght(1 byte) | checksum1(1 byte) | checksum2(1 byte) | into a binary file with the format: | data_size(in bytes, 4bytes) | raw_binary_data |. The purpose of this script is to log data from microcontrollers with in a more secure way than just throwing data over the serial port and reading on the computer with any verification whatsoever.")
parser.add_argument("-p", "--serialport", type=str, help="(default=/dev/ttyACM0)",default="/dev/ttyUSB0")
parser.add_argument("-n", "--data_size", type=int, help="the number of data 'points'to be received(default=0, no limite, hit Ctrl+c to quit and save the data to file)",default=0)
parser.add_argument("-f", "--output_file", type=str, help="name of the binary data file to be created(default=data.bin)",default="data")
parser.add_argument("-b", "--baudrate", type=int,help="(default=115200)",default=115200)
parser.add_argument("-d", "--datetime", help="turn off the date, time and .bin extension at the and of filename",action='store_true')
parser.add_argument("-r", "--repeat", help="print the receive data directly to stdout",action='store_true')
args=parser.parse_args()

#global variables
baud_rate=args.baudrate
outfile=args.output_file
data_size=args.data_size
port=args.serialport
dtime=args.datetime
repeat=args.repeat
data_list=[]
pack_size=0

def save_data():
  global outfile
  if not len(data_list):
    return
  if not dtime:
    current_date=datetime.today()
    hour=current_date.hour
    minute=current_date.minute
    day=current_date.day
    month=current_date.month
    year=current_date.year
    outfile='.'.join([outfile,str(year),str(month),str(day)]) + '_' + ':'.join([str(hour),str(minute)]) + '.bin'
  if outfile == "data":
    outfile +='.bin'

  binfile = open(outfile, 'wb')
  binfile.write(struct.pack('i',len(data_list)))
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
    print(byte,end=' ')
  print(' ')

#checksum - make the sum of verification of the received packages
#data is a bytes object with all the bytes but the header and checksum ones
#use the raw buffer as parameter, without the header.
def checksum1(buffer):
  #assert(type(buffer).__name__=='bytes')
  #assert(not buffer.isdigit())

  cksum=0
#  data=buffer[2:]
  data=buffer[:-2]
  
  for byte in data: #byte é um INTEIRO!!!
    cksum=cksum^int(byte)
  cksum=cksum&0xFE
  #assert(type(cksum).__name__=='int')
  return cksum



#checksum2 - more of the checksum
#int has to be an integer 
def checksum2(checksum1):
  #assert(type(checksum1).__name__=='int')
  return (~checksum1) & 0xFE;


#check the integrity of a received package
def check_package(buffer):
  assert(type(buffer).__name__=='bytes')
  assert(len(buffer)>2)

  cksum1_received=int(buffer[-2])
  cksum2_received=int(buffer[-1])
  
  cksum1_calculated=checksum1(buffer)
  cksum2_calculated=checksum2(cksum1_calculated)
  #print('cksum received: (', cksum1_received, ', ', cksum2_received,')')
  #print('cksum calculated: (', cksum1_calculated, ', ', cksum2_calculated,')')

  return cksum1_calculated==cksum1_received and cksum2_calculated==cksum2_received

def print_data(data):
  for byte in data:
    print(byte,end=' ')
  print(' ')




#sweet receiver, read from serial port and write to a binary file
#port: is de address of the serial
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
  try:
    ser.open()
  except:
    print('Error: could not open serial port ',port,'. Try to use another port with "-p port" option.')
    exit(1)
  print("Serial port ",port,"conected at",baud_rate,"bps, waiting for data.")
  print("Hit 'ctrl+c' to save the data and exit at any time.")
  
  #counter of how many data has been received
  i=0

  #open the data file
  while (data_size==0) or (i<data_size):
    #verify 
    num_bytes=0;
    while not num_bytes: num_bytes=ser.inWaiting();#wait for a byte
    buffer=ser.read(1)
    #print('Head: ', i , ' ', buffer , ' ', receive_data.last )
    #check the header: 0xFFFF
    if (ord(int2bytes(buffer))==0xFF) and (ord(int2bytes(receive_data.last)) == 0xFF):
      tmp=ser.read(1)
      #print(tmp)
      pack_size=ord(tmp)
      if num_bytes<(2+pack_size):
        num_bytes=0
        while num_bytes<(pack_size-1): num_bytes=ser.inWaiting();
      buffer=int2bytes(pack_size) + ser.read(pack_size-1)

      #remove the checksum received
      
      log_print='%d-' % (i)
      print(log_print,end=' ')
      
      if check_package(buffer):
        i+=1
        data=buffer[0:-2]#remove 2 checksum bytes
        data=data[1:]#remove size byte
        #restart the 'last' var so the header will not be wrongly found
        receive_data.last=0
        data_list.append(data)
        print('Data:' , end=' ')
        print_data(data)
      else:
        print('error: lost data')
    else:
      #since the header doesnt match, read another byte and try again with the current byte as the last
      receive_data.last=buffer#at this point, buffer is a single byte, and may or may not be matched one of the header bytes
      #print('not a package')
  ser.close()


def repeater():
  #opens and configures the serial port
  ser = serial.Serial()
  ser.port=port
  ser.baudrate=baud_rate
  ser.timeout=None
  try:
    ser.open()
  except:
    print('Error: could not open serial port ',port,'. Try to use another port with "-p port" option.')
    exit(1)
  print("Hit 'ctrl+c' to save the data and exit at any time.")

  data_list = b''
  while 1:
    num_bytes=0;
    while not num_bytes: 
        num_bytes=ser.inWaiting()#wait for a byte
    buffer=ser.read(num_bytes)
    print(byte2str(buffer),end='')
    # print(buffer)
    data_list += buffer


def byte2str(byte):
    out = ''
    for ch in byte:
        out+=chr(ch)
    return out

def main():
  signal.signal(signal.SIGINT, signal_handler)

  #number of packages received
  if repeat:
    repeater()
  else:
    receive_data()
    save_data()


if __name__ == "__main__":
  main();
