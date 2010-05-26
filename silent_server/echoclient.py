# Echo client program
import socket
import sys

HOST = 'localhost'
PORT = 5005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# Waiting here...
line = sys.stdin.readline()


# I will keep on forever since I'm a stupid client!
s.close()
