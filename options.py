#!/usr/bin/env python3

import os

class Options:
  options_dict={'serialport' : '-p', 'data_size': '-n', 'output_file': '-f', 'baudrate': '-b', 'datetime': '-d', 'repeat': '-r', 'tcp': '-t', 'udp': '-u', 'verbose': '-v', 'net_port': '-P'}
  types  ={'serialport' : 'str', 'data_size': 'int', 'output_file': 'str', 'baudrate': 'int', 'datetime': 'bool', 'repeat': 'bool', 'tcp': 'bool', 'udp': 'bool', 'verbose': 'bool', 'net_port': 'int'}

  def __init__(self):
    self.raw_options = []
    self.opt_list = []
    self.opt_dict = {}

  # read option from a configuration file
  # return dict
  def read(self,filename):
    if not filename:
      print('Error: invalid file name')
      return None
    filename=filename.strip()
    if filename[0] == '~':
      filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
      return None
    file = open(filename, 'r')
    # valid_options  =['serialport', 'data_size', 'output_file', 'baudrate', 'datetime', 'repeat', 'tcp', 'udp', 'verbose', 'net_port']
    opt_list = []

    for line in file:
      line = line.strip()
      if line[0] == '#':
        continue
      line = [s.strip() for s in line.split('=')]

      if len(line) != 2:
        continue

      if line[0] in self.types.keys():
        opt_list.extend(line)
      self.raw_options = opt_list

    return opt_list

  def get_dict_options(self):
    if not self.raw_options:
      return {}
    opt_dict = {}
    for i in range(0, len(self.raw_options), 2):
      if self.types[self.raw_options[i]] == 'int':
        try:
          aux = int(self.raw_options[i+1])
        except:
          pass
        else:
          opt_dict[self.raw_options[i]] = aux
      elif self.types[self.raw_options[i]] == 'bool':
        if self.raw_options[i+1].lower() == 'true':
          opt_dict[self.raw_options[i]] = True
        elif self.raw_options[i+1].lower() == 'false':
          opt_dict[self.raw_options[i]] = False
      else:
        opt_dict[self.raw_options[i]] = self.raw_options[i+1]
      self.opt_dict = opt_dict

    return opt_dict

  def get_list_options(self):

    opt_list = []
    for i in range(0,len(self.raw_options),2):
      if self.raw_options[i] in self.types.keys():
        if self.types[self.raw_options[i]] == 'int':
          try:
            int(self.raw_options[i+1])
          except:
            pass
          else:
            opt_list.append(self.options_dict[self.raw_options[i]])
            opt_list.append(self.raw_options[i+1])
        elif self.types[self.raw_options[i]] == 'bool':
          if self.raw_options[i+1].lower() == 'true':
            opt_list.append(self.options_dict[self.raw_options[i]])
        else:
          opt_list.append(self.options_dict[self.raw_options[i]])
          opt_list.append(self.raw_options[i+1])

    self.opt_list = opt_list

    return opt_list

  def clear():
    self.raw_options = []
    self.opt_dict = {}
    self.opt_list = []

if __name__ == '__main__':
  opt = Options()
  opt.read('~/.pslogrc')
  L = opt.get_list_options()
  d = opt.get_dict_options()
  print(L)
  print(d)
