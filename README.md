# PySerialLogger
A Serial Logger for data aquisition from microcontrollers written in python.[^1]
The data is sent from a microcontroller or other device to the serial port in form of a package. The package format is described as header(2 bytes) and data(variable length).

| 0xFFFF | data_length(1 byte) | data(variable length) | checksum(2 bytes) |

0xFFFF is 2 bytes long, and is the header. From the data length forward is all the bytes considered data, so the data_length contains the size from itself until the checksum bytes.

PySerialLogger reads data with this formar from the configured serial port or the default serial port (/dev/USB0) and write all the data into a binary file. The name of the file can be given through configuration, and a data and time can be appended to name, or disabled. The format of the file is the length of data or the number of data points or packages received, and then the data is stored sequentially.

## Implementation ##

An example of implementation in c for the packing of the data is giving below:


C code...


An example of matlab code from reading the binary data file and transforming all the data in float(3 32bit floats) in the form of a matriz where each row is one package received with 3 floats.


matlab code...



[OLa][linkteste]

[linkteste]: www.google.com "Google"

<www.google.com>


[^1]: descricao

```python
def print_str(str):
  print str

```

> quote

    
  
# h1 #

## h2  ##

-------------------------------------------------------------------------------

## h2new ##
