#    Rhythmcurse - A command line interface to Rhythmbox
#    Copyright (C) 2010 Samuel Skånberg 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import rb
from threading import Thread



class ClientThread(Thread):
	def __init__(self, file, clientSocket, shell):
		Thread.__init__(self)
		self.file = file
		self.shell = shell
		self.clientSocket = clientSocket
	
	def run(self):
		print "A new client connection established"

		while 1:
			command = self.clientSocket.recv(1024)
			if not command:
				break
				
			command = command.strip()
			if command == "play":
				reply = "press play on tape"
				self.shell.props.shell_player.play()
			elif command == "pause":
				reply = "press pause"
				self.shell.props.shell_player.pause()
			elif command == "next":
				reply = "next song"
				self.shell.props.shell_player.do_next()
			elif command == "prev":
				reply = "previous song"
				self.shell.props.shell_player.do_previous()

			else:
				reply = "I don't know that command"

			self.clientSocket.send(reply)
			self.file.write("A client sends: "+command)
			self.file.flush()

		self.file.write("A client closes connection\n")
		self.file.flush()


class ServerThread(Thread):
	def __init__(self, file, serverSocket, shell):
		Thread.__init__(self)
		self.file = file
		self.serverSocket = serverSocket
		self.shell = shell
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
			self.file.write("A new client connected\n")
			self.file.flush()

			client = ClientThread(self.file, socket, self.shell)
			client.start()

class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)
	def activate(self, shell):
		print "myplugin: Hello from myplugin!\n"
		self.file = open("/tmp/myplugin-file.txt", "w")
		self.shell = shell
		self.file.write("myplugin with network\n")
		self.file.flush()

		# is used to find a file in the plugin dir
		#path = self.find_file("hej.txt")
		#self.file.write("path: "+path)
		#self.file.flush()

	
		# creating server socket
		HOST = ''
		PORT = 5000
		self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.serverSocket.bind((HOST, PORT))
		self.serverSocket.listen(1)

		# creating server thread
		self.server = ServerThread(self.file, self.serverSocket, self.shell)
		self.server.start()

	def deactivate(self, shell):
		del self.server
		self.serverSocket.close()
		del self.shell
		self.file.write("Bye bye!")
		self.file.close()
		del self.file
	
