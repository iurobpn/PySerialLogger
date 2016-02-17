import multiprocessing as mp
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
class UDPServer (mp.Process):
  def __init__(self, port):
    mp.Process.__init__(self)
    self.port=port
    # self.soc = socket.socket()
    self.clients = []
    self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.message_queue = mp.Queue()

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
            next_msg = self.message_queue.get_nowait()
            self.broadcast(next_msg)

  def add_message(self,msg):
    if msg:
      self.message_queue.put(msg)

################## Fim da classe UDPserver ################################


################# Classe TCPServer ########################################
# thread class for a tcp server
class TCPServer (mp.Process):
  def __init__(self, port):
    mp.Process.__init__(self)
    self.port=port
    self.message_queues = {}
    self.message_queue = mp.Queue()

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
          while not self.message_queue.empty():
            self.add_message_to_queues(self.message_queue.get_nowait())

          if not self.message_queues[s].empty():
          # try:
            # TODO send all queue messages at once or not, maybe let to next call
            next_msg = self.message_queues[s].get_nowait()
            try:
              if verbose:
                print('sending "%s" to %s' % (next_msg, s.getpeername()))
              s.send(next_msg)
            except:
              poller.unregister(s)
              s.close()
          else:
            if verbose:
              print("empty queue")

    #end of while True:
    poller.unregister(server)
    server.close()
    print("Leaving TCP server")
    #### end of method run() #####

  def add_message_to_queues(self,msg):
    for k in self.message_queues:
      self.message_queues[k].put(msg)

  def add_message(self,msg):
    if msg:
      self.message_queue.put(msg)

################## Fim da classe TCPserver ################################
