#    Rhythmcurse - A command line interface to Rhythmbox
#    Copyright (C) 2010 Samuel Skanberg 
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
import sys
import rb
from threading import Thread
import gtk


class ClientThread(Thread):
	def __init__(self, file, clientSocket, shell):
		Thread.__init__(self)
		self.file = file
		self.shell = shell
		self.clientSocket = clientSocket

	def help(self):
		self.clientSocket.send("Commands:\r\n")
		self.clientSocket.send("play -> play\r\n")
		self.clientSocket.send("pause -> pause\r\n")
		self.clientSocket.send("prev -> previous song\r\n")
		self.clientSocket.send("next -> next song\r\n")


	def run(self):
		self.file.write("Client thread...\n")
		self.file.flush()

		#command = self.clientSocket.recv(1024)
		self.clientSocket.send("You are connected to rhythmcurse\r\n")
		
		help()

		keepOn = True

		while keepOn:
			self.file.write("Waiting for a clients command\n")
			self.file.flush()

			command = self.clientSocket.recv(1024)
			self.file.write("Got command\n")
			self.file.flush()
			if not command:
				break
				
			command = command.strip()
			# make sure to get the gdk lock since
			# gtk isn't thread safe
			gtk.gdk.threads_enter()
			if command == "play":
				try:
					self.shell.props.shell_player.play()
					reply = "press play on tape\r\n"
				except:
					reply = "couldn't play\r\n"
			elif command == "pause":
				try:
					self.shell.props.shell_player.pause()
					reply = "press pause\r\n"
				except:
					reply = "couldn't pause\r\n"
			elif command == "next":
				try:
					self.shell.props.shell_player.do_next()
					reply = "next song\r\n"
				except:
					reply = "couln't do next\r\n"
			elif command == "prev":
				try:
					self.shell.props.shell_player.do_previous()
					reply = "previous song\r\n"
				except:
					reply = "couldn't do previous\r\n"
			elif command == "quit":
				reply = "quiting...\r\n"
				keepOn = False
			elif command == "help":
				help()
				continue
			else:
				reply = "I don't know that command\r\n"
			# let the lock go
			gtk.gdk.threads_leave()

			self.clientSocket.send(reply)
			self.file.write("A client sends: "+command+"\n")
			self.file.flush()
		try:
			self.clientSocket.close()
		except:
			self.file.write("Couldn't close down client socket")
		self.file.write("A client closes connection\n")
		self.file.flush()


class ServerThread(Thread):
	def __init__(self, file, serverSocket, shell, clients, keepOn):
		Thread.__init__(self)
		self.file = file
		self.serverSocket = serverSocket
		self.shell = shell
		self.clients = clients
		self.keepOn = keepOn
		self.file.write("Creating thread...\n")
		self.file.flush()

	def run(self):
		self.file.write("Starting network...\n")
		self.file.flush()

		self.file.write("We are now waiting for connections...\n")
		self.file.flush()
		while self.keepOn:
			socket, addr = self.serverSocket.accept()
			self.file.write("A new client connected\n")
			self.file.flush()

			client = ClientThread(self.file, socket, self.shell)
			client.start()

			# save socket and thread so they can be destroyed in deactivate
			self.clients.append((socket, client))

class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)
	def activate(self, shell):
		self.file = open("/tmp/myplugin-file.txt", "w")
		self.shell = shell
		self.file.write("myplugin with network\n")
		self.file.flush()

		# so that we can close all sockets and kill all threads
		self.clientSocketsAndThreads = []
		# is used to find a file in the plugin dir
		#path = self.find_file("hej.txt")
		#self.file.write("path: "+path)
		#self.file.flush()

	
		# creating server socket
		self.HOST = ''
		self.PORT = 5000

		# the condition for the while loop in server thread
		self.keepOn = True
		try:
			self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			self.serverSocket.bind((self.HOST, self.PORT))
			self.serverSocket.listen(1)

			# creating server thread
			self.server = ServerThread(self.file, self.serverSocket, self.shell, self.clientSocketsAndThreads, self.keepOn)
			self.server.start()
		except socket.error, msg:
			self.file.write("There was an error binding the server socket\n")

	def deactivate(self, shell):
		# the server thread should exit
		self.keepOn = False
		try:
			self.file.write("Creating socket...\n");
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.file.write("Waking up thread, connecting to localhost at port %d\n" % (self.PORT,));
			s.connect(('localhost', 5000))
			self.file.write("Waking up server thread\n");
			s.close()
			self.file.write("Socket closed now\n");

		except:
			self.file.write("Couldn't connect to server to wake it up\n");


		try:
			self.serverSocket.close()
			self.file.write("Server socket closed down\n")
		except:
			self.file.write("Couldn't close down server socket\n")

		#try:
		#	self.server.exit()
		#	self.file.write("Server thread killed\n")
		#except:
		#	self.file.write("Couldn't kill server thread\n")
		#del self.server

		del self.shell
		self.file.write("Closing down...\n")
		#self.file.write(clientSocketsAndThreads)
		for (socket,thread) in self.clientSocketsAndThreads:
			try:
				self.file.write("Closing down a socket\n")
				socket.close()
				self.file.write("Closing down a thread\n")
				thread.exit()
			except:
				self.file.write("Problem closing socket and thread\n")
		
		self.file.close()
		del self.file

