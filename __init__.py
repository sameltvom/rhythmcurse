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
import rb
import time

class ClientThread(Thread):
	def __init__(self, clientSocket, shell, clients, keepOn):
		Thread.__init__(self)
		self.shell = shell
		self.clientSocket = clientSocket
		self.clients = clients
		self.keepOn = keepOn

	def help(self):
		self.clientSocket.send("Commands:\r\n")
		self.clientSocket.send("play <id>       -> plays the id given by \"list\"\r\n")
		self.clientSocket.send("pause           -> pause\r\n")
		self.clientSocket.send("resume          -> resume playing\r\n")
		self.clientSocket.send("prev            -> previous song\r\n")
		self.clientSocket.send("next            -> next song\r\n")
		self.clientSocket.send("list            -> list all selected songs\r\n")
		self.clientSocket.send("artist          -> list all artists\r\n")
		self.clientSocket.send("set artist <id> -> select an artist to play\r\n")
		self.clientSocket.send("all artists     -> select all artists\r\n")
		self.clientSocket.send("+               -> increase volume\r\n")
		self.clientSocket.send("-               -> decrease volume\r\n")
		self.clientSocket.send("\r\n")
		self.clientSocket.send("> ")


	def run(self):
		print "Client thread, hello"
		
		
		print "Client thread, hello done"
		
		
		# self.clientSocket.send("You are connected to rhythmcurse\r\n")
		# self.help()


		print "Waiting for a clients command"

		localKeepOn = True

		fs = self.clientSocket.makefile()

		while self.keepOn[0] and localKeepOn:
			# This is a complicated recv. If we get a timeout,
			# continue so we can check condition
			try:
				#command = self.clientSocket.recv(1024)
				command = fs.readline()
			except socket.timeout:
				# print "Got timeout"
				continue
			except:
				print "Exception here"
				try:
					self.clientSocket.close()
					return
				except:
					pass


			print "Got command #%s#" % (command)
			if not command:
				print "Got NO command"

				break
				
			command = command.strip()
			print "Command  stripped #%s#" % (command)
			# make sure to get the gdk lock since
			# gtk isn't thread safe
			gtk.gdk.threads_enter()
			if command.startswith("play"):
				try:
					if len(command.split("play ")) == 2:
						songId = int(command.split("play ")[1])
					else:
						songId = 0 

					# TODO: Make this better
					i = 0
					reply = "couldn't find song"
					#for row in self.shell.props.selected_source.props.query_model:
					for row in self.shell.props.library_source.props.query_model:
						if i == songId:
						 	entry = row[0]
							self.shell.get_player().play_entry(entry)
						 	reply = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST) + " - "
						 	reply += self.shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE)
							reply += "\r\n"	
							break
						i+=1
				except:
					reply = "couldn't play id %s\r\n" %(songId, )
			elif command == "resume":
				try:
					self.shell.props.shell_player.play()
					reply = "press play on tape\r\n"
				except:
					reply = "couldn't resume playing\r\n"
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
					reply = ""
					id = 0
					
					self.clientSocket.send("LIST LIST_BGN\r\n")
					#for row in self.shell.props.selected_source.props.query_model:
					for row in self.shell.props.library_source.props.query_model:
					 	entry = row[0]
						reply = "LIST LIST_ITM "
						reply += "%d - " % (id,)
					 	reply += self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)+" - "
					 	reply += self.shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE)
						reply += "\r\n"	
						self.clientSocket.send(reply)
						id+=1
					self.clientSocket.send("LIST LIST_END\r\n")

					reply = ""
				except:
					reply = "couldn't do list\r\n"
			elif command == "all artists":
				try:
					# reset to all artists
					for p in self.shell.props.library_source.get_property_views():
                                                if p.props.prop == rhythmdb.PROP_ARTIST:
                                                        p.set_selection([""])
							break      
				
					reply = ""		
				except:
					reply = "couldn't list artists\r\n"
			elif command == "artist":
				try:
					# find all artists
					artists = set()
					#for row in self.shell.props.selected_source.props.query_model:
					for row in self.shell.props.library_source.props.base_query_model:
					 	entry = row[0]
					 	artist = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)
						artists.add(artist)
					id = 0

					# sorted list
					artists_sorted = sorted(artists)
					self.clientSocket.send("ARTIST ARTIST_BGN\r\n")
					for artist in artists_sorted:
						reply = "ARTIST ARTIST_ITM %d - %s\r\n" % (id, artist)
						self.clientSocket.send(reply)
						id+=1
					self.clientSocket.send("ARTIST ARTIST_END\r\n")
										
					reply = ""		
				except:
					reply = "couldn't list artists\r\n"
			elif command.startswith("set artist "):
				try:
					if len(command.split("set artist ")) == 2:
						artistId = int(command.split("set artist ")[1])
						
						artists = set()
						for row in self.shell.props.library_source.props.base_query_model:
						 	entry = row[0]
						 	artist = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)
							artists.add(artist)

						i = 0
						# sorted list
						artists_sorted = sorted(artists)

						for s in artists_sorted:
							if i == artistId:
								artist = s
								break
							i+=1
					else:
						artist = ""
						
					for p in self.shell.props.library_source.get_property_views():
	            			 	if p.props.prop == rhythmdb.PROP_ARTIST:
							p.set_selection([artist])	
							break
						
					reply = "set artist %s\r\n" % (artist,)
				except:
					reply = "couldn't set artists\r\n"

			elif command == "all albums":
				try:
					# reset to all albums
					for p in self.shell.props.library_source.get_property_views():
                                                if p.props.prop == rhythmdb.PROP_ALBUM:
                                                        p.set_selection([""])
							break      
					reply = ""		
				except:
					reply = "couldn't list albums\r\n"
			elif command == "album":
				try:
					# get selected artists	
					for p in self.shell.props.library_source.get_property_views():
	            			 	if p.props.prop == rhythmdb.PROP_ARTIST:
							artists_selected = p.get_selection()	
							break
					
					# find all albums
					albums = set()
					
					for row in self.shell.props.selected_source.props.base_query_model:
					 	entry = row[0]
					 	artist = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)
						# if no artists is selected (i.e. all artists are selected)
						# or if the artists for this entry is the selected artist
						if not artists_selected or artist in artists_selected:
					 		album = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ALBUM)
							albums.add(album)
					id = 0

					# sorted list
					albums_sorted = sorted(albums)
					self.clientSocket.send("ALBUM ALBUM_BGN\r\n")
					for album in albums_sorted:
						reply = "ALBUM ALBUM_ITM %d - %s\r\n" % (id, album)
						self.clientSocket.send(reply)
						id+=1
					self.clientSocket.send("ALBUM ALBUM_END\r\n")
										
					reply = ""		
				except:
					reply = "couldn't list albums\r\n"
			elif command.startswith("set album "):
				try:
					if len(command.split("set album ")) == 2:
						albumId = int(command.split("set album ")[1])
						
						albums = set()

						for row in self.shell.props.selected_source.props.base_query_model:
						 	entry = row[0]
						 	artist = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)
							# if no artists is selected (i.e. all artists are selected)
							# or if the artists for this entry is the selected artist
							if not artists_selected or artist in artists_selected:
						 		album = self.shell.props.db.entry_get(entry, rhythmdb.PROP_ALBUM)
								albums.add(album)
	
						i = 0
						# sorted list
						albums_sorted = sorted(albums)

						for s in albums_sorted:
							if i == albumId:
								album = s
								break
							i+=1
					else:
						album = ""
						
					for p in self.shell.props.library_source.get_property_views():
	            			 	if p.props.prop == rhythmdb.PROP_ALBUM:
							p.set_selection([album])	
							break
						
					reply = "set album %s\r\n" % (album,)
				except:
					reply = "couldn't set albums\r\n"

			elif command.startswith("+"):
				try:
					self.shell.props.shell_player.set_volume_relative(0.1)
					reply = "increased volume\r\n"
				except:
					reply = "couldn't increase volume\r\n"
			elif command.startswith("-"):
				try:
					self.shell.props.shell_player.set_volume_relative(-0.1)
					reply = "decreased volume\r\n"
				except:
					reply = "couldn't decrease volume\r\n"
			elif command == "quit":
				reply = "quiting...\r\n"
				localKeepOn = False
				# break
			elif command == "help":
				self.help()
				gtk.gdk.threads_leave()
				continue
			else:
				reply = "I don't know that command: %s\r\n" % (command)
			# let the lock go
			gtk.gdk.threads_leave()

			self.clientSocket.send(reply)
			#self.clientSocket.flush()
			print "A client sends: "+command+""

			#self.clientSocket.send("> ")
			#print "Waiting for a clients command"

		try:
			print "Closing down socket"

			self.clientSocket.close()
		except:
			print "Couldn't close down client socket"
		print "A client closes connection"

		try:
			del self.clients[self.clientSocket]
			print "Client removes it self from list"
		except:
			print "Client cant' remove it self from list"



class ServerThread(Thread):
	def __init__(self, serverSocket, shell, clients, keepOn):
		Thread.__init__(self)
		self.serverSocket = serverSocket
		self.shell = shell
		self.clients = clients
		self.keepOn = keepOn
		print "Creating thread..."

	def run(self):
		print 'Starting network...'
		print "Starting network..."

		print "We are now waiting for connections..."
		while self.keepOn[0]:
			clientSocket, addr = self.serverSocket.accept()
			print "A new client connected"

			clientSocket.settimeout(1)

			if self.keepOn[0]:
				client = ClientThread(clientSocket, self.shell, self.clients, self.keepOn)
				client.start()

				# save socket and thread so they can be destroyed in deactivate
				self.clients[clientSocket] = client
			else:
				try:
					#print "Closing down socket waker"

					clientSocket.close()
				except:
					print "Couldn't close down waker socket"




		#print "Server thread done"

		try:
			self.serverSocket.close()
			#print "Server socket closed"

		except:
			pass
			#print "Couldn't close down server socket"




class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)

	def artist_changed_callback(self, arg2, arg3):
		print "artist selection changed"

		for client in self.clientSocketsAndThreads:
			client.send("INF_ARTIST INF_ARTIST_OK\r\n")

	def album_changed_callback(self, arg2, arg3):
		print "album selection changed"

		for client in self.clientSocketsAndThreads:
			client.send("INF_ALBUM INF_ALBUM_OK\r\n")

	
	def song_changed_method(self, player, entry):
		print "song_changed_method called"

		for client in self.clientSocketsAndThreads:
			client.send("SONG_CH SONG_CH_OK\r\n")


	def activate(self, shell):
		self.shell = shell
		print "rhythmcurse log"

		# so that we can close all sockets and kill all threads
		self.clientSocketsAndThreads = {}

		for p in self.shell.props.library_source.get_property_views():
			if p.props.prop == rhythmdb.PROP_ARTIST:
				p.connect('properties-selected', self.artist_changed_callback)
			if p.props.prop == rhythmdb.PROP_ALBUM:
				p.connect('properties-selected', self.album_changed_callback)
		

		player = shell.get_player()
		self.csi_id = player.connect('playing-song-changed', self.song_changed_method)					


			
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
			self.server = ServerThread(self.serverSocket, self.shell, self.clientSocketsAndThreads, self.keepOn)
			self.server.start()
		except socket.error, msg:
			print "There was an error binding the server socket"

	def deactivate(self, shell):
		print "Deactivating..."

		self.keepOn[0] = False
		try:
			# Wake up the server thread so it can quit
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(('localhost', 5000))
			
			s.close()
			print "Waker done";

		except:
			print "Couldn't connect waker";


		del self.shell
		
		print "Number of clients: %d" % (len(self.clientSocketsAndThreads))

		for aSocket,aThread in self.clientSocketsAndThreads.iteritems():
			try:
				print "Closing down a socket"
				aSocket.close()
				# we ignore the thread for now
			except:
				print "Problem closing socket"

		self.clientSocketsAndThreads.clear()
		
