#!/usr/bin/python

import vxi11 as v
from optparse import OptionParser
import sys
import commands as C
import time

IP = '169.254.166.206'

class Lecroy():
        def __init__(self,channel=None,filename=None,query=None,command=None,FORCE=False,PRINT=False):
            
            ### Initiate communication ###
            self.command = command
            self.scope = v.Instrument(IP)
            
            ### Format of answers ###
            self.scope.write('CFMT DEF9,BYTE,BIN')
            self.scope.write('CHDR SHORT')
            
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
                
            self.prev_trigg_mode = self.query('TRMD?')
            
            if filename:
                self.single()
                while self.query('TRMD?') != 'TRMD STOP':
                    time.sleep(0.05)
                    pass
                else:
                    print '\nStart acquisition ...'
                    
                ### Check if channels are active ###
                for i in range(len(channel)):
                    temp = self.query(channel[i]+':TRA?')
                    if temp.find('ON') == -1:
                        print '\nWARNING:  Channel',channel[i], 'is not active  ===>  exiting....\n'
                        sys.exit()
                ### Acquire and save datas ###
                for i in range(len(channel)):
                    print 'trying to get channel',channel[i]
                    self.get_data(chan=channel[i],filename=filename,SAVE=True,FORCE=FORCE)
            else:
                print 'If you want to save, provide an output file name'
            
            ### Run the scope BACK in the previous trigger mode###
            self.run()
            
        
        def query(self, cmd, nbytes=1024):
            """Send command 'cmd' and read 'nbytes' bytes as answer."""
            self.scope.write(cmd)
            r = self.scope.read(nbytes)
            return r
        

        def get_data(self,chan='C1',filename='test_save_file_',PLOT=False,SAVE=False,LOG=True,FORCE=False):
            self.data = self.query_data(chan)
            print len(self.data)
            ### TO SAVE ###
            if SAVE:
                temp = C.getoutput('ls').splitlines()                           # if file exist => exit
                for i in range(len(temp)):
                    temp_filename = filename + '_lecroy' + chan
                    if temp[i] == temp_filename and not(FORCE):
                        print '\nFile ', temp_filename, ' already exists, change filename or remove old file\n'
                        sys.exit()
                
                f = open(filename + '_lecroy' + chan,'w')                   # Save data
                f.write(self.data)
                f.close()
                
                if LOG:
                    self.preamb = self.get_log_data(chan)             # Save scope configuration
                    f = open(filename + '_lecroy' + chan + '.log','w')
                    f.write(self.preamb)
                    f.close()
                print  chan + ' saved'
        
        
        def get_log_data(self,chan):
            rep = self.query(chan+":INSP? 'WAVEDESC'")
            return rep          
        
        def stop(self):
            self.scope.write("TRMD STOP")
        def single(self):
            self.scope.write("TRMD SINGLE")
        def run(self):
            self.scope.write(self.prev_trigg_mode)
        
        def query_data(self, chan, fname=None, force=None,):
            ## trigger SINGLE
            chan = str(chan)
            self.scope.write(chan+':WF? DAT1')
            data = self.scope.read_raw()
            return data[data.find('#')+11:-1]

        
if __name__ == '__main__':

    usage = """usage: %prog [options] arg

               EXAMPLES:
                   get_lecroy 1 -o filename
               Record the first channel and create two files name filename_lecroy and filename_lecroy.log

               """
    parser = OptionParser(usage)
    parser.add_option("-c", "--command", type="str", dest="com", default=None, help="Set the command to use." )
    parser.add_option("-q", "--query", type="str", dest="que", default=None, help="Set the query to use." )
    parser.add_option("-o", "--filename", type="string", dest="filename", default=None, help="Set the name of the output file" )
    parser.add_option("-F", "--force", type="string", dest="force", default=None, help="Allows overwriting file" )
    (options, args) = parser.parse_args()
    
    ### Compute channels to acquire ###
    if (len(args) == 0) and (options.com is None) and (options.que is None):
        print '\nYou must provide at least one channel\n'
        sys.exit()
    elif len(args) == 1:
        chan = []
        temp_chan = args[0].split(',')                  # Is there a coma?
        for i in range(len(temp_chan)):
            chan.append('C' + temp_chan[i])
    else:
        chan = []
        for i in range(len(args)):
            chan.append('C' + str(args[i]))
    print 'Channel(s):   ', chan
    
    ### Start the talker ###
    Lecroy(channel=chan,query=options.que,command=options.com,filename=options.filename,FORCE=options.force)
    
