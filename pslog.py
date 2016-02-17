#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################
## Serial Logger for Data Aquisition
#    File: slog.py
#    Author: Iuro Nascimento
#    Date(dd/mm/yyyy): 14/01/2015
#    Finish date: 19/01/2015
########################################################

import sys
import os
import serial
import signal
import argparse
import struct
from datetime import datetime, time, date
from options import Options
from net_process import UDPServer
from net_process import TCPServer

# global variables some are defined in main()
data_list=[]
pack_size=0
ser = serial.Serial()
main_pid = 0

# Parsing of command line arguments
parser = argparse.ArgumentParser(description="Log serial data received with the format |0xFFFF | lenght(1 byte) | checksum1(1 byte) | checksum2(1 byte) | into a binary file with the format: | data_size(in bytes, 4bytes) | raw_binary_data |. The purpose of this script is to log data from microcontrollers with in a more secure way than just throwing data over the serial port and reading on the computer with any verification whatsoever.")
parser.add_argument("-p", "--serialport", type=str, help="(default=/dev/ttyACM0)",default=None)
parser.add_argument("-n", "--data_size", type=int, help="the number of data 'points'to be received(default=0, no limite, hit Ctrl+c to quit and save the data to file)",default=None)
parser.add_argument("-f", "--output_file", type=str, help="name of the binary data file to be created(default=data.bin)",default=None)
parser.add_argument("-b", "--baudrate", type=int,help="(default=115200)",default=None)
parser.add_argument("-d", "--datetime", help="turn off the date, time and .bin extension at the and of filename",action='store_true',default=None)
parser.add_argument("-r", "--repeat", help="print the receive data directly to stdout",action='store_true',default=None)
parser.add_argument("-t", "--tcp", help="start a TCP server do distribute readed data",action='store_true',default=None)
parser.add_argument("-u", "--udp", help="start a UDP server do distribute readed data",action='store_true',default=None)
parser.add_argument("-v", "--verbose", help="More information on connections, sending and receiving data are printed on stdout",action='store_true',default=None)
parser.add_argument("-P", "--net_port", type=int,help="TCP or UDP port (default=5353)",default=None)

# update options from any source(config file or shell)
def update_options(args):
  #global variables
  global baud_rate
  global outfile
  global data_size
  global port
  global dtime
  global repeat
  global tcp
  global udp
  global verbose
  global net_port

  if args.baudrate != None:
    baud_rate=args.baudrate
  elif 'baud_rate' not in globals():
    baud_rate=None
  if args.output_file != None:
    outfile=args.output_file
  elif 'outfile' not in globals():
    outfile=None
  if args.data_size != None:
    data_size=args.data_size
  elif 'data_size' not in globals():
    data_size=None
  if args.serialport != None:
    port=args.serialport
  elif 'port' not in globals():
    port=None
  if args.datetime != None:
    dtime=args.datetime
  elif 'dtime' not in globals():
    dtime=None
  if args.repeat != None:
    repeat=args.repeat
  elif 'repeat' not in globals():
    repeat=None
  if args.tcp != None:
    tcp=args.tcp
  elif 'tcp' not in globals():
    tcp=None
  if args.udp != None:
    udp=args.udp
    if udp and tcp != None:
      tcp=False
  elif 'udp' not in globals():
    udp=None
  if args.verbose != None:
    verbose=args.verbose
  elif 'verbose' not in globals():
    verbose=None
  if args.net_port != None:
    net_port=args.net_port
  elif 'net_port' not in globals():
    net_port=None


def format_filename(filename,extension):
  if not dtime:
    current_date=datetime.today()
    hour=current_date.hour
    minute=current_date.minute
    day=current_date.day
    month=current_date.month
    year=current_date.year
    filename='.'.join([filename,str(year),str(month),str(day)]) + '_' + ':'.join([str(hour),str(minute)]) + extension
  if filename == "data":
    filename += extension

  return filename


def save_to_binary_file(outfile):
  if not len(data_list):
    if main_pid == os.getpid():
      print("no data to save")
    return

  filename = format_filename(outfile,'.bin')
  print("\nsaving data to binary file",filename)
  binfile = open(filename, 'wb')
  binfile.write(struct.pack('i',len(data_list)))
  for pack in data_list:
    binfile.write(pack)
  binfile.close


def save_to_text_file(outfile):
  buffer=byte2str(data_list)
  if not len(buffer):
    if main_pid == os.getpid():
      print("no data to save")
    return

  filename = format_filename(outfile,'.txt')
  print("\nsaving data to text file",filename)
  txtfile = open(filename, 'w')
  txtfile.write(buffer)
  txtfile.close()


def signal_handler(signal, frame):
  # global tcp_server
  # global udp_server
  # global ser

  if repeat:
    save_to_text_file(outfile)
  else:
    save_to_binary_file(outfile)

  try:
    tcp_server.terminate()
  except:
    pass

  try:
    udp_server.terminate()
  except:
    pass

  if main_pid == os.getpid():
    ser.close()
    print("\nExiting due to user hit of Ctrl+c")
  sys.exit(0)


#convert from int to bytes
def int2bytes(i):
  if type(i).__name__=='int':
    return bytes([i])
  if type(i).__name__=='bytes':
    return i;
  else:
    return None


# Test function to verify the data at the debug time
def print_data(data):
  for byte in data:
    print(byte,end=' ')
  print(' ')


#checksum - make the sum of verification of the received packages
#data is a bytes object with all the bytes but the header and checksum ones
#use the raw buffer as parameter, without the header.
def checksum1(buffer):
  assert(type(buffer).__name__ == 'bytes')

  cksum=0
  data=buffer[:-2]

  for byte in data: #byte é um INTEIRO!!!
    cksum=cksum^byte
  cksum=cksum&0xFE
  assert(type(cksum).__name__=='int')
  return cksum


#checksum2 - more of the checksum
#int has to be an integer
def checksum2(checksum1):
  assert(type(checksum1).__name__=='int')
  return (~checksum1) & 0xFE;


#check the integrity of a received package
def check_package(buffer):
  assert(type(buffer).__name__=='bytes')
  assert(len(buffer)>2)

  cksum1_received=buffer[-2]
  cksum2_received=buffer[-1]

  cksum1_calculated=checksum1(buffer)
  cksum2_calculated=checksum2(cksum1_calculated)
  if verbose:
    print('cksum received: (', cksum1_received, ', ', cksum2_received,')')
    print('cksum calculated: (', cksum1_calculated, ', ', cksum2_calculated,')')

  return cksum1_calculated==cksum1_received and cksum2_calculated==cksum2_received


## Receiver, read from serial port and write to a binary file
# port: is de address of the serial
# baud_rate: is the baud rate of the serial port
# size: the number of data points to receive
# outfile: name of the file to write the data
def receive_data(ser):
  global data_list
  #last serves as to check the header, making possible to head one byte
  #at a time to check for the reader.
  if "last" not in receive_data.__dict__: receive_data.last = b'\x00'
  # global ser
  #opens and configures the serial port
  ser.port=port
  ser.baudrate=baud_rate
  if verbose:
    print("[ Port:",port,",","Baudrate:",baud_rate,"]")
  ser.timeout=None
  try:
    ser.open()
  except:
    print('Error: could not open serial port ',port)
    print('Try to use another serial port with "-p port" option')
    exit(1)
  print("Serial port ",port,"conected at",baud_rate,"bps, waiting for data.")
  print("Hit 'ctrl+c' to save the data and exit at any time.")

  #counter of how many data has been received
  i=0

  #open the data file
  while (data_size==0) or (i<data_size):
    #verify
    buffer=b'\x00'
    num_bytes=0;
    while not num_bytes:
      try:
        num_bytes=ser.inWaiting();#wait for a byte
      except Exception as er:
        print(str(er))
        exit(1)

    try:
      buffer=ser.read(1)
    except:
      if verbose:
        print("Error reading serial port")
      exit(1)
    assert(len(buffer)==1)
    assert(len(receive_data.last)==1)
    #check the header: 0xFFFF
    if verbose:
      print('Head: ', i , ' ', buffer , ' ', receive_data.last )
    if (buffer[0] == 0xFF) and (receive_data.last[0] == 0xFF):
      try:
        tmp=ser.read(1)
      except:
        if verbose:
          print("Error reading serial port")
        exit(1)
      #print(tmp)
      pack_size=tmp[0]
      assert(pack_size>=0)
      if num_bytes<(2+pack_size):
        num_bytes=0
        while num_bytes<(pack_size-1):
          try:
            num_bytes=ser.inWaiting();
          except:
            if verbose:
              print("Error reading serial port")
            exit(1)
      try:
        buffer=int2bytes(pack_size) + ser.read(pack_size-1)
      except:
        if verbose:
          print("Error reading serial port")
        exit(1)

      assert(len(buffer)>0)

      #remove the checksum received
      log_print='%d-' % (i)
      print(log_print,end=' ')

      if check_package(buffer):
        i+=1
        data=buffer[1:-2]#remove 2 checksum bytes and remove size byte
        #restart the 'last' var so the header will not be wrongly found
        receive_data.last=b'\x00'
        data_list.append(data)
        print('Data:' , end=' ')
        print_data(data)
        add_message_to_server(data)
      else:
        receive_data.last = b'\x00'
        print('error: lost data')
    else:
      assert(len(buffer)==1)
      assert(len(receive_data.last)==1)
      #since the header doesnt match, read another byte and try again with the current byte as the last
      receive_data.last=buffer#at this point, buffer is a single byte, and may or may not be matched one of the header bytes
      if verbose:
        print('not a package')
  ser.close()


def repeater(ser):
  global data_list

  # global data_list
  # opens and configures the serial port
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
    buffer=''
    while not num_bytes:
      try:
        num_bytes=ser.inWaiting()#wait for a byte
      except:
        if verbose:
          print("Error reading serial port")
        exit(1)

    try:
      buffer=ser.read(num_bytes)
    except:
      if verbose:
        print("Error reading serial port")
      exit(1)

    print(byte2str(buffer),end='')
    data_list += buffer
    add_message_to_server(buffer)


def byte2str(byte):
    out = ''
    for ch in byte:
        out+=chr(ch)
    return out


def add_message_to_server(msg):
  if msg:
    if tcp_server.is_alive():
      tcp_server.add_message(msg)
    if udp_server.is_alive():
      udp_server.add_message(msg)


def main():
  global ser
  global tcp_server
  global udp_server
  global baud_rate
  global outfile
  global data_size
  global port
  global dtime
  global repeat
  global tcp
  global udp
  global verbose
  global net_port

  opt = Options()
  if opt.read('.pslogrc'):
    options = opt.get_list_options()
    args = parser.parse_args(options)
    update_options(args)
  elif opt.read('~/.pslogrc'):
    options = opt.get_list_options()
    args = parser.parse_args(options)
    update_options(args)
  args=parser.parse_args()
  update_options(args)

  # verify default options
  if not baud_rate:
    baud_rate=115200
  if not outfile:
    outfile='data'
  if not data_size:
    data_size = 0;
  if not port:
    port='/dev/ttyACM0'
  if dtime == None:
    dtime=False
  if repeat == None:
    repeat=False
  if tcp == None:
    tcp = False
  if udp == None:
    udp = False
  if verbose == None:
    verbose = False
  if not net_port:
    if udp:
      net_port = 5050
    if tcp:
      net_port = 5353
  else:
    net_port = 5353
  if verbose:
    print('Final options:', [baud_rate, outfile, data_size, port, dtime, repeat, tcp, udp, net_port])
  main_pid = os.getpid()

  signal.signal(signal.SIGINT, signal_handler)


  tcp_server = TCPServer(net_port)
  udp_server = UDPServer(net_port)

  if tcp:
    tcp_server.daemon=True
    tcp_server.start()
  elif udp:
    udp_server.daemon=True
    udp_server.start()

  if repeat:
    repeater(ser)
  else:
    receive_data(ser)
    save_to_binary_file()


if __name__ == "__main__":
  main()
  try:
    tcp_server.terminate()
  except:
    pass

  try:
    udp_server.terminate()
  except:
    pass

