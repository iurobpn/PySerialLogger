#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Serial Logger for Data Aquisition
#file: dasl.py
#Author: Iuro Nascimento
#Date(dd/mm/yyyy): 14/01/2015

import sys
import serial
import struct

def teste():
    struct.pack('f', 3.141592654)
    struct.unpack('f', '\xdb\x0fI@')
    struct.pack('4f', 1.0, 2.0, 3.0, 4.0)




def main():
  args = sys.argv[1:]
  usage = "usage: dasl.py [port baud_rate output_file]"
  #if not args:
  #  print usage;
  #  sys.exit(1)


  #leitura de um arquivo srt. A saida eh determinada pelo numero de arquivos
  # dados como argumentos. Se somente foi passado um argumento, a saida vai para
  # a tela. Se foram passados 2 arquivos, o segundo recebera os resultados.
  if len(args) > 0:
    port = args[0]
  else:
    port = '/dev/ttyACM0'

  if len(args) > 1:
    baud_rate = args[1]
  else:
    baud_rate = 115200

  if len(args) > 2:
    outfile = args[2]
  else:
    outfile = 'serial.log'

  ser = serial.Serial(port,baud_rate)
  while 1:
      n=0
      while not n: n=ser.inWaiting();
      print(ser.read(n))
  ser.close()

if __name__ == "__main__":
  main();
