# PySerialLogger
A Serial Logger for data aquisition from microcontrollers written in python.[^1]

The data is sent from a microcontroller or other device to a serial port in form of a package. The package format is described as header(2 bytes) and data(variable length).

| 0xFFFF | data_length(1 byte) | data(variable length) | checksum(2 bytes) |

0xFFFF is 2 bytes long, and is the package's header. From the data length forward is all the bytes considered data, so the data_length contains the size from itself until the checksum bytes.

slog reads data with this format from the serial port or the default serial port (/dev/USB0) and write all the data into a binary file. The name of the file can be given through configuration, and a data and time can be appended to name, or disabled. The format of the file is the length of data or the number of data points or packages received, and then the data is stored sequentially. Use:

``` bash
$ ./slog.py -h
```
for more information about other possible configurations such as port, baudrate and others.

## Instalation ##

You need to install python 3.* and the pyserial module for python 3.*. In ubuntu:

``` bash
$ sudo apt-get update
$ sudo apt-get install python3 python3-serial

```

I recommend that you make a symlink in '/usr/local/bin/' to have a liberty to use this script in any directory and just to type 'slog'. You can make a clone of this repo in  directory, 'dir', and make a symlink as in the code below.


``` bash
$ sudo ln -s path-to-dir/dir/pyseriallogger/slog.py /usr/local/bin/slog
```

In my case:

``` bash
$ sudo ln -s /home/myusername/git/pyseriallogger/slog.py /usr/local/bin/slog
```


## Implementation ##

An example of implementation in c for the packing of the data to be sent is giving below:

``` c
#include <stdint.h>

uint8_t cksum1(uint8_t buffer[]) {
  uint8_t i, chksum=0;
  uint8_t n = BUFFER[2];//-2-> tira o checksum  2->por começar em buffer[2]
  /* o buffer é passado inteiro, com o cabeçalho */
  for(i=2;i<n;i++) {
    chksum=chksum^buffer[i];
  }
  return chksum&0xFE;
}

uint8_t cksum2(uint8_t checksum1)
{
	return (~checksum1) & 0xFE;
}

void serialize_struct(uint8_t *buffer, SomeStruct some_struct)
{
	int size = sizeof(some_struct);
    //The header
	buffer[0]=0xFF;
	buffer[1]=0xFF;
	//size
	buffer[2]=size+3;
	//copy data to buffer
	memcpy((buffer+3),&some_struct,size);
	//append the checksums to the end of the buffer
	buffer[size+3]=cksum1(buffer);
	buffer[size+4]=cksum2(buffer[size+3]);
	
	return buffer;
}

int main()
{
    //initialize the struct to pass, the format doesnt matter
    SomeStruct ss = {3.1416,3.1416,3.1416}; 
    uint8_t *buffer = (uint8_t*) malloc(SIZE*sizeof(uint8_t));
    serialize_struct(buffer,ss);
    send_to_serial(buffer);//hardware and/or software dependent
}
```


An example of matlab code from reading the binary data file and transforming all the data in form of a matrix where each row is one package received with the data as specified by types. Types are a cellstr(['uint32','float32',...]) where all the strings have the same size, so fill with spaces at the end of the strings. More types on the documentation page of the fread function on matlab site: http://www.mathworks.com/help/matlab/ref/fread.html

``` matlab
function data = read_binary_file(filename,types)
%% read data from a binary file
% filename - name of the file to be read
% type - types of the data in the file, just for a row of data
% return data - matrix with the data in columns, each row is one package
% received

fd=fopen(filename,'r');
if fd==-1
    fprintf('Erro: nao foi possivel abrir o arquivo.\n')
    return
end
L=length(types)
C=fread(fd,1,'int32')
for i=1:C;
    for j=1:L
        data(i,j)=fread(fd,1,types{j});
    end
end
fclose(fd);
```
find this code and more on the example directory.

## Final Remarks ##
This is just an improvised help on how to use this software, it may contain minor error on the code, since I dont exactly use this code. The example directory has a better code. A "plot_data.m" is a handy function to a fast plot of the data. I'm not a native english speaker, so please forgive any possible mistakes in this text.
