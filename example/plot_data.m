%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ProVANT 2015
% Constrole dos Servos
% Author: Iuro Nascimento
% Date(dd/mm/yyyy): 06/04/2015
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function plot_data(data,xpos,ypos)
%% plot data from  read_binary_data function and plots xpos column x 
% ypos column as a dicrete using stem

n=data(:,xpos);
y=data(:,ypos);
stem(n,y)
grid
