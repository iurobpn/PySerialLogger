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
import serial
import signal
import argparse
import struct
from datetime import datetime, time, date
import threading
import socket
import select
import queue

# Global variables associated to class TCPServer
# message_queues = {}
TIMEOUT=1000
# Commonly used flag setes
READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT


################# Classe UDPServer ########################################
class UDPServer (threading.Thread):
  def __init__(self, port):
    threading.Thread.__init__(self)
    self.port=port
    # self.soc = socket.socket()
    self.clients = []
    self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.message_queue = queue.Queue()

  def broadcast(self, msg):
    if self.clients and msg:
      for client in self.clients:
        self.udp_server.sendto(msg,client)
        if verbose:
          print('sending "%s" to %s' % (msg, client))

  def run(self):
    host = ''                   # Get local machine name
    try:
      self.udp_server.bind((host, self.port))        # Bind to the port
      self.udp_server.setblocking(0)
    except Exception as er:
      print(str(er))
      exit(1)

    # Set up the poller
    poller = select.poll()
    poller.register(self.udp_server, READ_ONLY | READ_WRITE)
    fd_to_socket = { self.udp_server.fileno(): self.udp_server,}

    print("UDP server running")
    while True:
      if mutex.acquire(False):
        if kill_server:
          mutex.release()
          break

        mutex.release()

      events = poller.poll(TIMEOUT)
      for fd, flag in events:
        # Retrieve the actual socket from its file descriptor
        s = fd_to_socket[fd]
        # Handle inputs
        if flag & (select.POLLIN | select.POLLPRI):
          if s is self.udp_server:
            # A "readable" udp_server socket is ready to accept a connection
            data, addr = s.recvfrom(1024) # Establish connection with client.
            print('new client from', addr)
            self.clients.append(addr)
        elif flag & select.POLLOUT:
          # Socket is ready to send data, if there is any to send.
          # self.message_queue.put(b'any data\n')
          if not self.message_queue.empty():
            # try:
            next_msg = self.message_queue.get_nowait()
            # except queue.Empty:
              # No messages waiting so stop checking for writability.
              # print('output queue for', s.getpeername(), 'is empty')
              # poller.modify(s, READ_ONLY)
              # pass
            # else:
            self.broadcast(next_msg)

  def add_message(self,msg):
    if msg:
      self.message_queue.put(msg)


################## Fim da classe UDPserver ################################


################# Classe TCPServer ########################################
# thread class for a tcp server
class TCPServer (threading.Thread):
  def __init__(self, port):
    threading.Thread.__init__(self)
    self.port=port
    self.message_queues = {}

  def run(self):
    try:
      server = socket.socket()         # Create a socket object
      host = ''                   # Get local machine name
      server.bind((host, self.port))        # Bind to the port
      server.listen(5)                 # Now wait for client connection.
    except Exception as er:
      print(str(er))
      exit(1)

    poller = select.poll()
    poller.register(server, READ_ONLY)
    fd_to_socket = { server.fileno(): server,}
    print("TCP server running")

    while True:
      if mutex.acquire(False):
        if kill_server:
          mutex.release()
          break

        mutex.release()

      events = poller.poll(TIMEOUT)
      for fd, flag in events:
        # Retrieve the actual socket from its file descriptor
        s = fd_to_socket[fd]
        # Handle inputs
        if flag & (select.POLLIN | select.POLLPRI):
          if s is server:
            # A "readable" server socket is ready to accept a connection
            connection, client_address = server.accept()
            print('new connection from', client_address)
            connection.setblocking(0)
            fd_to_socket[ connection.fileno() ] = connection
            poller.register(connection, READ_WRITE)

            # Give the connection a queue for data we want to send
            self.message_queues[connection] = queue.Queue()
          else:
            try:
              data = s.recv(1024)
            except:
              poller.unregister(s)
              s.close()
            else:
              if data:
                # A readable client socket has data
                if verbose:
                  print('received "%s" from %s' % (data, s.getpeername()))
                self.message_queues[s].put(data)
                # Add output channel for response
                poller.modify(s, READ_WRITE)
              else:
                # Interpret empty result as closed connection
                print('closing', client_address, 'after reading no data')
                # Stop listening for input on the connection
                poller.unregister(s)
                s.close()
                # Remove message queue
                del self.message_queues[s]
        elif flag & select.POLLHUP:
          # Client hung up
          print('closing', 'after receiving HUP')
          # Stop listening for input on the connection
          poller.unregister(s)
          s.close()
        elif flag & select.POLLOUT:
          # Socket is ready to send data, if there is any to send.
          # self.message_queues[s].put(b'any data\n')
          if not self.message_queues[s].empty():
          # try:
            # TODO send all queue messages at once or not, maybe let to next call
            next_msg = self.message_queues[s].get_nowait()
          # except queue.Empty:
            # No messages waiting so stop checking for writability.
            # print('output queue for', s.getpeername(), 'is empty')
            # poller.modify(s, READ_ONLY)
          #   pass
          # else:
            try:
              if verbose:
                print('sending "%s" to %s' % (next_msg, s.getpeername()))
              s.send(next_msg)
            except:
              poller.unregister(s)
              s.close()

    #end of while True:
    poller.unregister(server)
    server.close()
    print("Leaving TCP server")
    #### end of ethod run() #####

  def add_message_to_queues(self,msg):
    for k in self.message_queues:
      self.message_queues[k].put(msg)

################## Fim da classe TCPserver ################################


#parsing of command line arguments
parser = argparse.ArgumentParser(description="Log serial data received with the format |0xFFFF | lenght(1 byte) | checksum1(1 byte) | checksum2(1 byte) | into a binary file with the format: | data_size(in bytes, 4bytes) | raw_binary_data |. The purpose of this script is to log data from microcontrollers with in a more secure way than just throwing data over the serial port and reading on the computer with any verification whatsoever.")
parser.add_argument("-p", "--serialport", type=str, help="(default=/dev/ttyACM0)",default="/dev/ttyUSB0")
parser.add_argument("-n", "--data_size", type=int, help="the number of data 'points'to be received(default=0, no limite, hit Ctrl+c to quit and save the data to file)",default=0)
parser.add_argument("-f", "--output_file", type=str, help="name of the binary data file to be created(default=data.bin)",default="data")
parser.add_argument("-b", "--baudrate", type=int,help="(default=115200)",default=115200)
parser.add_argument("-d", "--datetime", help="turn off the date, time and .bin extension at the and of filename",action='store_true')
parser.add_argument("-r", "--repeat", help="print the receive data directly to stdout",action='store_true')
parser.add_argument("-t", "--tcp", help="start a TCP server do distribute readed data",action='store_true')
parser.add_argument("-u", "--udp", help="start a UDP server do distribute readed data",action='store_true')
parser.add_argument("-v", "--verbose", help="More information on connections, sending and receiving data are printed on stdout",action='store_true')
parser.add_argument("-P", "--net_port", type=int,help="TCP or UDP port (default=5353)",default=5353)
args=parser.parse_args()

#global variables
baud_rate=args.baudrate
outfile=args.output_file
data_size=args.data_size
port=args.serialport
dtime=args.datetime
repeat=args.repeat
tcp=args.tcp
udp=args.udp
verbose=args.verbose
net_port=args.net_port
data_list=[]
pack_size=0
kill_server=False

#synchronization variables
# cv = threading.Condition
mutex = threading.Lock()
# TCP server

tcp_server = TCPServer(net_port)
udp_server = UDPServer(net_port)

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


def save_to_binary_file():
  global outfile

  # print("text file")

  if not len(data_list):
    print("no data to save")
    return

  filename = format_filename(outfile,'.bin')
  print("saving data to binary file",filename)
  binfile = open(filename, 'wb')
  binfile.write(struct.pack('i',len(data_list)))
  for pack in data_list:
    binfile.write(pack)
  binfile.close


def save_to_text_file():

  global outfile
  print("text file")
  buffer=byte2str(data_list)
  if not len(buffer):
    print("no data to save")
    return

  filename = format_filename(outfile,'.txt')
  print("saving data to text file",filename)
  txtfile = open(filename, 'w')
  txtfile.write(buffer)
  txtfile.close()


def signal_handler(signal, frame):
  global kill_server
  global mutex
  global server

  release_server()
  if repeat:
    save_to_text_file()
  else:
    save_to_binary_file()
  print("\nExiting due to user hit of Ctrl+c")
  # server.stop()
  # server.join()
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


## Receiver, read from serial port and write to a binary file
# port: is de address of the serial
# baud_rate: is the baud rate of the serial port
# size: the number of data points to receive
# outfile: name of the file to write the data
def receive_data():
  #last serves as to check the header, making possible to head one byte
  #at a time to check for the reader.
  if "last" not in receive_data.__dict__: receive_data.last = b'\x00'

  #opens and configures the serial port
  ser = serial.Serial()
  ser.port=port
  ser.baudrate=baud_rate
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
      except:
        print("Error reading serial port")
        exit(1)

    try:
      buffer=ser.read(1)
    except:
      print("Error reading serial port")
      exit(1)
    assert(len(buffer)==1)
    assert(len(receive_data.last)==1)
    #check the header: 0xFFFF
    if verbose:
      print('Head: ', i , ' ', buffer , ' ', receive_data.last )
    # if (ord(int2bytes(buffer))==0xFF) and (ord(int2bytes(receive_data.last)) == 0xFF):
    if (buffer[0] == 0xFF) and (receive_data.last[0] == 0xFF):
      try:
        tmp=ser.read(1)
      except:
        print("Error reading serial port")
        exit(1)
      #print(tmp)
      pack_size=ord(tmp)
      assert(pack_size>=0)
      if num_bytes<(2+pack_size):
        num_bytes=0
        while num_bytes<(pack_size-1):
          try:
            num_bytes=ser.inWaiting();
          except:
            print("Error reading serial port")
            exit(1)
      try:
        buffer=int2bytes(pack_size) + ser.read(pack_size-1)
      except:
        print("Error reading serial port")
        exit(1)

      assert(len(buffer)>0)

      #remove the checksum received
      log_print='%d-' % (i)
      print(log_print,end=' ')

      if check_package(buffer):
        i+=1
        data=buffer[0:-2]#remove 2 checksum bytes
        data=data[1:]#remove size byte
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


def repeater():
  global data_list
  #opens and configures the serial port
  ser = serial.Serial()
  ser.port=port
  ser.baudrate=baud_rate
  ser.timeout=None
  try:
    ser.open()
  except:
    print('Error: could not open serial port ',port,'. Try to use another port with "-p port" option.')
    release_server()
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
        print("Error reading serial port")
        exit(1)

    try:
      buffer=ser.read(num_bytes)
    except:
      print("Error reading serial port")
      exit(1)

    print(byte2str(buffer),end='')
    # print(buffer)
    data_list += buffer
    add_message_to_server(buffer)


def byte2str(byte):
    out = ''
    for ch in byte:
        out+=chr(ch)
    return out


def add_message_to_server(msg):
  if msg:
    if tcp_server.isAlive():
      tcp_server.add_message_to_queues(msg)
    if udp_server.isAlive():
      # print("message added",msg)
      udp_server.add_message(msg)


def release_server():
  with mutex:
    kill_server=True


def main():
  signal.signal(signal.SIGINT, signal_handler)

  if tcp:
    tcp_server.daemon=True
    tcp_server.start()
  elif udp:
    udp_server.daemon=True
    udp_server.start()

  #number of packages received
  if repeat:
    repeater()
  else:
    receive_data()
    save_to_binary_file()



if __name__ == "__main__":
  main();

