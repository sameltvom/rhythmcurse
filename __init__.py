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
	def __init__(self, file, clientSocket, shell, clients, keepOn):
		Thread.__init__(self)
		self.file = file
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
		self.file.write("Client thread, hello\n")
		self.file.flush()

		
		self.file.write("Client thread, hello done\n")
		self.file.flush()
		
		
		# self.clientSocket.send("You are connected to rhythmcurse\r\n")
		# self.help()


		self.file.write("Waiting for a clients command\n")
		self.file.flush()

		localKeepOn = True

		fs = self.clientSocket.makefile()

		while self.keepOn[0] and localKeepOn:
			# This is a complicated recv. If we get a timeout,
			# continue so we can check condition
			try:
				#command = self.clientSocket.recv(1024)
				command = fs.readline()
			except socket.timeout:
				# self.file.write("Got timeout\n")
				# self.file.flush()
				continue
			except:
				self.file.write("Exception here\n")
				self.file.flush()
				try:
					self.clientSocket.close()
					return
				except:
					pass


			self.file.write("Got command #%s#\n" % (command)) 
			self.file.flush()
			if not command:
				self.file.write("Got NO command\n")
				self.file.flush()

				break
				
			command = command.strip()
			self.file.write("Command  stripped #%s#\n" % (command)) 
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
					for row in self.shell.props.selected_source.props.query_model:
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
					for row in self.shell.props.selected_source.props.query_model:
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
				
					# Update the list
					gtk.gdk.threads_leave()
					# python doesn't have Thread.yield as in Java
					time.sleep(0.3)
					gtk.gdk.threads_enter()


					reply = ""		
				except:
					reply = "couldn't list artists\r\n"
			elif command == "artist":
				try:
					# OBS! You must run all artists before

					# reset to all artists
					#for p in self.shell.props.library_source.get_property_views():
                                        #        if p.props.prop == rhythmdb.PROP_ARTIST:
                                        #                p.set_selection([""])
					#		break      
					#
					## update the "set no artist"
					#gtk.gdk.threads_leave()
					## python doesn't have Thread.yield as in Java
					#time.sleep(0.3)
					#gtk.gdk.threads_enter()

					# find all artists
					artists = set()
					for row in self.shell.props.selected_source.props.query_model:
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
										

					# reset the artist
					#for p in self.shell.props.library_source.get_property_views():
                                        #        if p.props.prop == rhythmdb.PROP_ARTIST:
                                        #                p.set_selection(artistNow)
					#		break 
					reply = ""		
				except:
					reply = "couldn't list artists\r\n"
			elif command.startswith("set artist "):
				try:
					# reset to all artists
					for p in self.shell.props.library_source.get_property_views():
                                                if p.props.prop == rhythmdb.PROP_ARTIST:
                                                        p.set_selection([""])
							break      
					
					# update the "set no artist"
					gtk.gdk.threads_leave()
					# python doesn't have Thread.yield as in Java
					time.sleep(0.3)
					gtk.gdk.threads_enter()

					if len(command.split("set artist ")) == 2:
						artistId = int(command.split("set artist ")[1])
						
						artists = set()
						for row in self.shell.props.selected_source.props.query_model:
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
					# OBS! You must run all albums first or all artists

					# reset to all albums
					#for p in self.shell.props.library_source.get_property_views():
                                        #        if p.props.prop == rhythmdb.PROP_ALBUM:
                                        #                p.set_selection([""])
					#		break      
					#
					## update the "set no album"
					#gtk.gdk.threads_leave()
					## python doesn't have Thread.yield as in Java
					#time.sleep(0.3)
					#gtk.gdk.threads_enter()

					# find all albums
					albums = set()
					for row in self.shell.props.selected_source.props.query_model:
					 	entry = row[0]
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
										

					# reset the artist
					#for p in self.shell.props.library_source.get_property_views():
                                        #        if p.props.prop == rhythmdb.PROP_ARTIST:
                                        #                p.set_selection(artistNow)
					#		break 
					reply = ""		
				except:
					reply = "couldn't list albums\r\n"
			elif command.startswith("set album "):
				try:
					# reset to all albums
					for p in self.shell.props.library_source.get_property_views():
                                                if p.props.prop == rhythmdb.PROP_ALBUM:
                                                        p.set_selection([""])
							break      
					
					# update the "set no aalbum"
					gtk.gdk.threads_leave()
					# python doesn't have Thread.yield as in Java
					time.sleep(0.3)
					gtk.gdk.threads_enter()

					if len(command.split("set album ")) == 2:
						albumId = int(command.split("set album ")[1])
						
						albums = set()
						for row in self.shell.props.selected_source.props.query_model:
						 	entry = row[0]
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
			self.file.write("A client sends: "+command+"\n")
			self.file.flush()

			#self.clientSocket.send("> ")
			#self.file.write("Waiting for a clients command\n")
			#self.file.flush()

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
					#self.file.write("Closing down socket waker\n")
					#self.file.flush()

					clientSocket.close()
				except:
					#self.file.write("Couldn't close down waker socket")
					self.file.flush()




		#self.file.write("Server thread done\n")
		#self.file.flush()

		try:
			self.serverSocket.close()
			#self.file.write("Server socket closed\n")
			#self.file.flush()

		except:
			pass
			#self.file.write("Couldn't close down server socket\n")
			#self.file.flush()




class RhythmcursePlugin (rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)



	def artist_changed_callback(self, arg2, arg3):
		self.file.write("artist selection changed\n")
		self.file.flush()

		for client in self.clientSocketsAndThreads:
			client.send("INF_ARTIST INF_ARTIST_OK\r\n")

	def album_changed_callback(self, arg2, arg3):
		self.file.write("album selection changed\n")
		self.file.flush()

		for client in self.clientSocketsAndThreads:
			client.send("INF_ALBUM INF_ALBUM_OK\r\n")

	
	def song_changed_method(self, player, entry):
		self.file.write("song_changed_method called\n")
		self.file.flush()

		for client in self.clientSocketsAndThreads:
			client.send("SONG_CH SONG_CH_OK\r\n")


	def activate(self, shell):
		self.file = open("/tmp/rhythmcurse.log", "w")
		self.shell = shell
		self.file.write("rhythmcurse log\n")
		self.file.flush()

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
		
		#self.file.close()
		#del self.file

