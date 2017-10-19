#!/usr/bin/python

import visa as v
from optparse import OptionParser
import sys
import time

PORT = '5'

class KEOPSYS():
        def __init__(self,query=None,command=None,kar=None,auto_lock=None):
            self.command = None
            
            rm = v.ResourceManager('@py')
            self.INSTR = rm.get_instrument('GPIB::2::INSTR')
            #self.INSTR.write('CEOI ON')

            self.write('*IDN?')
            print '\nCONNECTING to module:',self.read()
            
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
            

            
            self.exit()
        

        
        #def exit(self):
            #self.write('CONAME')
            #sys.exit()

        def write(self,query):
            self.INSTR.write(query)
            
        def read(self):
            rep = self.PID.read()
            return rep

        def idn(self):
            self.ep_out.write('*IDN?\r\n')
            

if __name__ == '__main__':

    usage = """usage: %prog [options] arg
               
               
               EXAMPLES:
                   
                   set_keopsys -a 0.
                Set the value of the keopsys laser diode pump to 0.


               """
    parser = OptionParser(usage)
    parser.add_option("-c", "--command", type="str", dest="com", default=None, help="Set the command to use." )
    parser.add_option("-q", "--query", type="str", dest="que", default=None, help="Set the query to use." )
    parser.add_option("-a", "--amplitude", type="float", dest="amplitude", default=None, help="Modify laser diode pump." )
    (options, args) = parser.parse_args()
    
    ### Start the talker ###
    KEOPSYS(query=options.que,command=options.com,auto_lock=options.autolock)
