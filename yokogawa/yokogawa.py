#!/usr/bin/env python
import socket
import sys
import time
from optparse import OptionParser
import commands as C
from numpy import savetxt

HOSTNAME="169.254.166.207"

class Yokogawa():
    def __init__(self, filename=None,query=None,command=None,FORCE=False,SAVE=True):
        ### Establish the connection ###
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOSTNAME, 10001))
        self.send('OPEN "anonymous"')
        ans = self.recv(1024)

        if not ans=='AUTHENTICATE CRAM-MD5.':
            print "problem with authentication"
            sys.exit(1)
        self.send(" ")
        ans = self.recv(1024)
        if not ans=='ready':
            print "problem with authentication"
            sys.exit(1)

        if query:
            self.command = query
            print '\nAnswer to query:',self.command
            rep = self.query(self.command)
            print rep,'\n'
            sys.exit()
        elif command:
            self.command = command
            print '\nExecuting command',self.command
            self.scope.write(self.command)
            print '\n'
            sys.exit()

        if filename:
            self.lambd,self.amp = self.get_data()
            self.lambd = [eval(self.lambd[i]) for i in range(len(self.lambd))]
            self.amp = [eval(self.amp[i]) for i in range(len(self.amp))]
            ### TO SAVE ###
            if SAVE:
                temp_filename = filename + '_YOKO'
                temp = C.getoutput('ls').splitlines()                           # if file exist => exit
                for i in range(len(temp)):
                    if temp[i] == temp_filename and not(FORCE):
                        print '\nFile ', temp_filename, ' already exists, change filename, remove old file or use -F option to overwrite\n'
                        sys.exit()

                savetxt(temp_filename,(self.lambd,self.amp))

                
    def get_data(self):
        X = self.query(":TRAC:DATA:X? TRA", length=100000).split(',')
        data = self.query(":TRAC:DATA:Y? TRA", length=100000).split(',')
        return X,data

    def send(self, msg):
        msg=msg+"\n"
        self.sock.send(msg)

    def recv(self, length=2048):
        msg=''
        while not msg.endswith('\r\n'):
            msg=msg+self.sock.recv(length)
        msg = msg[:-2]
        return msg

    def query(self,msg,length=2048):
        """Sends question and returns answer"""
        self.send(msg)
        time.sleep(1)
        return(self.recv(length))

    def makesweep(self):
        """Trigger a single sweep"""
        self.mode('1')
        self.send('INIT')

    def mode(self,mode=None):
        """Sets or queries mode. Returns mode in any case"""
        if mode is not None:
            self.send('INIT:SMOD '+mode)
        return self.query('INIT:SMOD?')


if __name__=="__main__":
    
    usage = """usage: %prog [options] arg

               EXAMPLES:
                   get_YOKO -o filename
               Record the spectrum and create one file with two columns lambda,spectral amplitude

               """
    parser = OptionParser(usage)
    parser.add_option("-c", "--command", type="str", dest="com", default=None, help="Set the command to use." )
    parser.add_option("-q", "--query", type="str", dest="que", default=None, help="Set the query to use." )
    parser.add_option("-o", "--filename", type="string", dest="filename", default=None, help="Set the name of the output file" )
    parser.add_option("-F", "--force", type="string", dest="force", default=None, help="Allows overwriting file" )
    (options, args) = parser.parse_args()

    
    Yokogawa(query=options.que,command=options.com,filename=options.filename,FORCE=options.force)
