#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Serial Logger for Data Aquisition
#file: dasl.py
#Author: Iuro Nascimento
#Date(dd/mm/yyyy): 14/01/2015

import sys
import serial
import struct
from servo import process

def int2bytes(i):
  if type(i).__name__=='int':
    return bytes([i])
  if type(i).__name__=='bytes':
    return i;
  else:
    return None

def print_data(data):
  for byte in data:
    print(int(byte),end=' ')
  print(' ')

def teste():
  struct.pack('f', 3.141592654)
  struct.unpack('f', '\xdb\x0fI@')
  struct.pack('4f', 1.0, 2.0, 3.0, 4.0)

def checksum(data):
  cksum=0
  for byte in data:
    cksum=cksum^int(byte)
  cksum=cksum&0xFE
  return cksum


def receive_data(port,baud_rate,size,outfile):
  #var local
  if "last" not in receive_data.__dict__: receive_data.last = b'\x00'
  ser = serial.Serial()
  ser.port=port
  ser.baudrate=baud_rate
  ser.timeout=None
  ser.open()
  i=0#counter of how many data has been received
  log = open(outfile, 'wb')#log file for writing the data
  print('Entering main while')
  while i<size:
    #print('%d- ' % (i))
    num_bytes=0;
    while num_bytes<3: num_bytes=ser.inWaiting();
    
    buffer=ser.read(1)
#    print(type(buffer).__name__)
    print('Head: ', i , ' ', buffer , ' ', receive_data.last )
    if (ord(int2bytes(buffer))==0xFF) and (ord(int2bytes(receive_data.last)) == 0xFF):
      #print('enter header if')
      data_size=ord(ser.read(1))
      #print(size)
      if num_bytes<(2+data_size):
        num_bytes=0
        while num_bytes<(data_size-1): num_bytes=ser.inWaiting();
      buffer=int2bytes(data_size) + ser.read(data_size-1)
      print(type(buffer[-1]).__name__)
      cksum_received=int(buffer[-1])
      
      data=buffer[0:-1]
      print('size: ',end=' ')
      print(data_size)
      print('Data:' , end=' ')
      print_data(data)
      cksum_calculated=checksum(data)
      print('cksum received:', cksum_received, ', cksum calculated:', cksum_calculated)
      #print(type(cksum_calculated).__name__)
      if cksum_received==cksum_calculated:
        i+=1
        #pdata=process(data)#pdata is a list o bytes, 4 per item if float data is present
        #map(int2bytes,pdata)
        #pdata=sum(pdata)#it may be seen redundant now, but in the future others types may be in use
        log_print='%d- ' % (i)
        
        log.write(data)
        print(log_print)
        receive_data.last=0
      else:
        print('error: lost data')
    else:
      receive_data.last=buffer
      print('not a package')
  ser.close()
  log.close()


def main():
  args = sys.argv[1:]
  usage = "usage: dasl.py [port(/dev/ttyACM0) baud_rate(115200) data_size output_file(serial.log)]"
  #if not args:
  #  print usage;
  #  sys.exit(1)

  if len(args) > 0:
    port = args[0]
  else:
    port = '/dev/ttyACM0'

  if len(args) > 1:
    baud_rate = args[1]
  else:
    baud_rate = 115200

  if len(args) > 2:
    data_size = args[2]
  else:
    data_size = 100

  if len(args) > 3:
    outfile = args[3]
  else:
    outfile = 'data.bin'#name of the binary file where to store the data
  #number of packages received
  receive_data(port,baud_rate,data_size,outfile)


if __name__ == "__main__":
  main();
