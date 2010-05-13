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


HOST = 'localhost'
PORT = 5000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print "You are connected"
print "Commands:"
print "play -> play"
print "pause -> pause"
print "prev -> previous song"
print "next -> next song"
while 1:
	command = sys.stdin.readline()
	s.send(command)
	if command.find("quit") >= 0:
		print 'Quiting...'
		break
	else:
		data = s.recv(1024)
		print 'Received: '+ repr(data)

s.close()


