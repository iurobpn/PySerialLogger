#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

typedef struct _pis
{
	float pi1;
	float pi2;
	float pi3;
} Pis;

uint8_t checksum1(uint8_t *buffer);
uint8_t checksum2(uint8_t checksum1);
uint8_t* serialize(void* msg, int size);
void print_data(uint8_t *buffer);
void send_data(uint8_t *BUFFER,int size);
	
int main() {
	//data to send
	Pis msg;
	msg.pi1 = 3.14159265;
	msg.pi2 = 3.14159265/2.0;
	msg.pi3 = 3.14159265/4.0;
	int size = sizeof(Pis);
	uint8_t *buffer = serialize((void*)&msg,size);
	send_data(buffer,size);
}

void send_data(uint8_t* buffer, int size)
{
	/**
	 * Send data to serial port - hardware/software dependent.
	 * in arduino, you could make:
	 * Serial.write(buffer,size);
	 */
}

uint8_t checksum1(uint8_t *buffer)
{
  uint8_t i, chksum=0;
  uint8_t n = buffer[2]-2+2;//-1-> tira o checksum  2->por começar em buffer[2]
  /* o buffer é passado inteiro, com o cabeçalho */
  for(i=2;i<n;i++) {
    chksum=chksum^buffer[i];
  }

  return chksum&0xFE;
}

uint8_t checksum2(uint8_t checksum1)
{
	return (~checksum1) & 0xFE;
}

uint8_t* serialize(void* msg, int size)
{
	uint8_t *BUFFER = (uint8_t*) malloc((size+5)*sizeof(uint8_t));
	//Header
	BUFFER[0]=0xFF;
	BUFFER[1]=0xFF;
//struct size + 2 bytes of checksum + 1 bytes of the data length
	//BUFFER[2] is size from itself to the last checksum
	BUFFER[2]=size+3;
	//copy data to buffer
	memcpy((BUFFER+3),&msg,size);
	//calculate the checksums and append to the end of the buffer
	BUFFER[size+3]=checksum1(BUFFER);
	BUFFER[size+4]=checksum2(BUFFER[size+3]);
}

void print_data(uint8_t *BUFFER)
{
	printf("Data: ");
	int size=BUFFER[2]+2, i;
	for(i=0;i<size;i++)
	{
		printf("%d ",BUFFER[i]);
	}
	printf("\n");
}
