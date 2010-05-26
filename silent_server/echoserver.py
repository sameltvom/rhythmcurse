# Echo server program
import socket
from threading import Thread

HOST = ''
PORT = 5005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

clientSocket, addr = s.accept()
print 'Got a new connection from: ', addr

# Closing it down
clientSocket.close()
