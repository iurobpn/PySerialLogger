clear all;
close all;

%chose the dir and file
dirname = '~/tmp/'
filename = 'data.2015.4.8_19:33.bin';
file=strcat(dirname,filename);

%choose the types, and remeber to fill the strings with spaces to have 
%the same size
tipos=cellstr(['uint32 ';'int32  ';'float32';'float32']);
data=read_binary_file(file,tipos);
plot_data(data,1,3)