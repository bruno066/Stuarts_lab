#!/usr/bin/python

import visa as v
from optparse import OptionParser
import sys
import time

PORT = '5'

class agilent33220a():
        def __init__(self,query=None,command=None,offset=None,amplitude=None,frequency=None,ramp=None):
            self.command = None
            
            rm = v.ResourceManager('@py')
            self.inst = rm.get_instrument('TCPIP::169.254.2.20::INSTR')
            
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
                self.inst.write('VOLT '+amplitude)
            if offset:
                self.inst.write('VOLT:OFFS '+offset)
            if frequency:
                self.inst.write('FREQ '+frequency)
                
            if ramp:
                self.ramp()
            
            self.exit()
        
        def ramp():
            self.inst.write()
            self.inst.write()
            self.inst.write()
            self.inst.write()

        def write(self,query):
            self.inst.write(query)
            
        def read(self):
            rep = self.inst.read()
            return rep

        def exit(self):
            sys.exit()

        def idn(self):
            self.inst.write('*IDN?')
            self.read()
            
            
if __name__ == '__main__':

    usage = """usage: %prog [options] arg
               
               
               EXAMPLES:
                   


               """
    parser = OptionParser(usage)
    parser.add_option("-c", "--command", type="str", dest="com", default=None, help="Set the command to use." )
    parser.add_option("-q", "--query", type="str", dest="que", default=None, help="Set the query to use." )
    parser.add_option("-r", "--ramp", type="float", dest="ramp", default=None, help="Turn on ramp mode." )
    parser.add_option("-o", "--offset", type="str", dest="off", default=None, help="Set the offset value." )
    parser.add_option("-a", "--amplitude", type="str", dest="amp", default=None, help="Set the amplitude." )
    parser.add_option("-f", "--frequency", type="str", dest="freq", default=None, help="Set the frequency." )
    (options, args) = parser.parse_args()
    
    ### Start the talker ###
    agilent33220a(query=options.que,command=options.com,ramp=options.ramp,offset=options.off,amplitude=options.amp,frequency=options.freq)
