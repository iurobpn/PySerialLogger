%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ProVANT 2015
% Constrole dos Servos
% Author: Iuro Nascimento
% Date(dd/mm/yyyy): 06/04/2015
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function data = read_binary_file(filename,types)
%% read data from a binary file
% filename - name of the file to be read
% type - types of the data in the file, just for a row of data
% return data - matrix with the data in columns, each row is one package
% received
if nargin <= 0
    fprintf('Erro: nao foram informados os tipos\n')
    return
end

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