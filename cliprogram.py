import socket
import sys


HOST = 'localhost'    # The remote host
PORT = 5000              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print "You are connected"
while 1:
	command = sys.stdin.readline()
	s.send(command)
	data = s.recv(1024)
	print 'Received: '+ repr(data)

s.close()


