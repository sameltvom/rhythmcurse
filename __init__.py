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
import rhythmdb

class ClientThread(Thread):
	def __init__(self, file, clientSocket, shell, clients, keepOn):
		Thread.__init__(self)
		self.file = file
		self.shell = shell
		self.clientSocket = clientSocket
		self.clients = clients
		self.keepOn = keepOn

	def help(self):
		self.clientSocket.send("Commands:\r\n")
		self.clientSocket.send("play -> play\r\n")
		self.clientSocket.send("pause -> pause\r\n")
		self.clientSocket.send("prev -> previous song\r\n")
		self.clientSocket.send("next -> next song\r\n")
		self.clientSocket.send("list -> list all selected songs\r\n")



	def run(self):
		self.file.write("Client thread, hello\n")
		self.file.flush()

		self.clientSocket.send("You are connected to rhythmcurse\r\n")
		
		self.file.write("Client thread, hello done\n")
		self.file.flush()
		
		
		self.help()


		self.clientSocket.send("> ")
		self.file.write("Waiting for a clients command\n")
		self.file.flush()

		localKeepOn = True

		while self.keepOn[0] and localKeepOn:
			# This is a complicated recv. If we get a timeout,
			# continue so we can check condition
			try:
				command = self.clientSocket.recv(1024)
			except socket.timeout:
				self.file.write("Got timeout\n")
				self.file.flush()
				continue
			except:
				self.file.write("Exception here\n")
				self.file.flush()
				try:
					self.clientSocket.close()
					return
				except:
					pass


			self.file.write("Got command\n")
			self.file.flush()
			if not command:
				self.file.write("Got NO command\n")
				self.file.flush()

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
			elif command == "list":
				try:
					# TODO: replace with song listing
					reply = ""
					id = 0
					for row in self.shell.props.selected_source.props.query_model:
					 	entry = row[0]
						reply += "%d " % (id,)
					 	reply += self.shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE)
						reply += "\r\n"	
						id+=1
				except:
					reply = "couldn't do list\r\n"

			elif command == "quit":
				reply = "quiting...\r\n"
				localKeepOn = False
				# break
			elif command == "help":
				self.help()
				gtk.gdk.threads_leave()
				continue
			else:
				reply = "I don't know that command\r\n"
			# let the lock go
			gtk.gdk.threads_leave()

			self.clientSocket.send(reply)
			self.file.write("A client sends: "+command+"\n")
			self.file.flush()

			self.clientSocket.send("> ")
			self.file.write("Waiting for a clients command\n")
			self.file.flush()

		try:
			self.file.write("Closing down socket\n")
			self.file.flush()

			self.clientSocket.close()
		except:
			self.file.write("Couldn't close down client socket")
			self.file.flush()
		self.file.write("A client closes connection\n")
		self.file.flush()

		try:
			del self.clients[self.clientSocket]
			self.file.write("Client removes it self from list\n")
			self.file.flush()
		except:
			self.file.write("Client cant' remove it self from list\n")
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
		while self.keepOn[0]:
			clientSocket, addr = self.serverSocket.accept()
			self.file.write("A new client connected\n")
			self.file.flush()

			clientSocket.settimeout(1)

			if self.keepOn[0]:
				client = ClientThread(self.file, clientSocket, self.shell, self.clients, self.keepOn)
				client.start()

				# save socket and thread so they can be destroyed in deactivate
				self.clients[clientSocket] = client
			else:
				try:
					self.file.write("Closing down socket waker\n")
					self.file.flush()

					clientSocket.close()
				except:
					self.file.write("Couldn't close down waker socket")
					self.file.flush()




		self.file.write("Server thread done\n")
		self.file.flush()

		try:
			self.serverSocket.close()
			self.file.write("Server socket closed\n")
			self.file.flush()

		except:
			self.file.write("Couldn't close down server socket\n")
			self.file.flush()




class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)
	def activate(self, shell):
		self.file = open("/tmp/rhythmcurse.log", "w")
		self.shell = shell
		self.file.write("rhythmcurse log\n")
		self.file.flush()



		# so that we can close all sockets and kill all threads
		self.clientSocketsAndThreads = {}

	
		# creating server socket
		self.HOST = ''
		self.PORT = 5000

		# the condition for the while loop in server thread
		# make a list with one bool, so we can pass a reference to it
		self.keepOn = [True]
		try:
			self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.serverSocket.bind((self.HOST, self.PORT))
			self.serverSocket.listen(1)

			# creating server thread
			self.server = ServerThread(self.file, self.serverSocket, self.shell, self.clientSocketsAndThreads, self.keepOn)
			self.server.start()
		except socket.error, msg:
			self.file.write("There was an error binding the server socket\n")
			self.file.flush()

	def deactivate(self, shell):
		self.file.write("Deactivating...\n")
		self.file.flush()

		self.keepOn[0] = False
		try:
			# Wake up the server thread so it can quit
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(('localhost', 5000))
			
			s.close()
			self.file.write("Waker done\n");
			self.file.flush()

		except:
			self.file.write("Couldn't connect waker\n");
			self.file.flush()


		del self.shell
		
		self.file.write("Number of clients: %d\n" % (len(self.clientSocketsAndThreads),))
		self.file.flush()

		for aSocket,aThread in self.clientSocketsAndThreads.iteritems():
			try:
				self.file.write("Closing down a socket\n")
				self.file.flush()
				aSocket.close()
				# we ignore the thread for now
			except:
				self.file.write("Problem closing socket\n")
				self.file.flush()

		self.clientSocketsAndThreads.clear()
		
		self.file.close()
		del self.file

