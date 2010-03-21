# maybe a plugin...
import socket
import rb
from threading import Thread

class ServerThread(Thread):
	def __init__(self, file, serverSocket):
		Thread.__init__(self)
		self.file = file
		self.serverSocket = serverSocket
		self.file.write("Creating thread...\n")
		self.file.flush()

	def run(self):
		self.file.write("Starting network...\n")
		self.file.flush()
		print "mylplugin now starting network!\n"


		print "mylplugin now waiting for connections!\n"

		self.file.write("We are now waiting for connections...\n")
		self.file.flush()
		while 1:
			socket, addr = self.serverSocket.accept()
			data = socket.recv(1024)
			socket.send(data)
			self.file.write("A client sends: "+data)
			self.file.flush()


class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)
	def activate(self, shell):
		print "myplugin: Hello from myplugin!\n"
		self.file = open("/tmp/myplugin-file.txt", "w")
		self.shell = shell
		self.file.write("myplugin with network")
		self.file.flush()
	
		# creating server socket
		HOST = ''
		PORT = 5000
		self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.serverSocket.bind((HOST, PORT))
		self.serverSocket.listen(1)

		# creating server thread
		self.server = ServerThread(self.file, self.serverSocket)
		self.server.start()

	def deactivate(self, shell):
		del self.server
		self.serverSocket.close()
		del self.shell
		self.file.write("Bye bye!")
		self.file.close()
		del self.file
	
