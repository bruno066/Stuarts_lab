#!/usr/bin/python

import socket
from optparse import OptionParser
import sys
import time
from numpy import zeros,ones,linspace

PORT=9221

class TTITGF3162():
        def __init__(self,channel=None,query=None,command=None,IP_ADDRESS=None,offset=None,amplitude=None,frequency=None):
            self.command = None
            if not(IP_ADDRESS):
                print '\nYou must provide an address...\n'
                sys.exit()
            
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((IP_ADDRESS,PORT))
            
            if query:
                self.command = query
                print '\nAnswer to query:',self.command
                self.write(self.command)
                rep = self.read()
                print rep,'\n'
                self.exit()
            elif command:
                self.command = command
                print '\nExecuting command',self.command
                self.write(self.command)
                print '\n'
                self.exit()
            
            if amplitude:
                self.write('AMPL '+amplitude)
            if frequency:
                self.write('FREQ '+frequency)
            if offset:
                self.write('DCOFFS '+offset)
            
            #self.exit()

        def write(self,query):
            self.s.send(query+'\n')
            
        def read(self):
            rep = self.s.recv(1000)
            return rep

        def exit(self):
            sys.exit()

        def idn(self):
            self.inst.write('*IDN?')
            self.read()
            
            
if __name__ == '__main__':

    usage = """usage: %prog [options] arg
               
               EXAMPLES:
                   set_TTITGF3162 -f 80000000 -a 20
                   set_TTITGF3162 -f 80e6 -a 20  
                   Note that both lines are equivalent
                   
                   Set the frequency to 80MHz and the power to 20dBm.
               """
               
    parser = OptionParser(usage)
    parser.add_option("-c", "--command", type="str", dest="com", default=None, help="Set the command to use." )
    parser.add_option("-q", "--query", type="str", dest="que", default=None, help="Set the query to use." )
    parser.add_option("-o", "--offset", type="str", dest="off", default=None, help="Set the offset value." )
    parser.add_option("-a", "--amplitude", type="str", dest="amp", default=None, help="Set the amplitude." )
    parser.add_option("-f", "--frequency", type="str", dest="freq", default=None, help="Set the frequency." )
    parser.add_option("-i", "--ip_address", type="str", dest="ip_address", default='169.254.62.40', help="Set the Ip address to use for communicate." )
    (options, args) = parser.parse_args()
    
        ### Compute channels to acquire ###
    if (len(args) == 0) and (options.com is None) and (options.que is None):
        print '\nYou must provide at least one channel\n'
        sys.exit()
    elif len(args) == 1:
        chan = []
        temp_chan = args[0].split(',')                  # Is there a coma?
        for i in range(len(temp_chan)):
            chan.append('CHN' + temp_chan[i])
    else:
        chan = []
        for i in range(len(args)):
            chan.append('CHN' + str(args[i]))
    print chan
    ### Start the talker ###
    TTITGF3162(channel=chan,query=options.que,command=options.com,IP_ADDRESS=options.ip_address,offset=options.off,amplitude=options.amp,frequency=options.freq)