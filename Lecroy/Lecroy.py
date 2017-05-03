#!/usr/bin/python

import vxi11 as v
from optparse import OptionParser
import sys
import commands as C
import time
from numpy import fromstring,int8,int16,float64,sign

IP = '169.254.166.206'

class Lecroy():
        def __init__(self,channel=None,encoding='BYTE',spe_mode=None,filename=None,query=None,command=None,FORCE=False,PRINT=False):
            if encoding=='BYTE':dtype=int8;NUM=256;LIM=217.          # 15% less than the maximal number possible
            elif encoding=='WORD':dtype=int16;NUM=65536;LIM=55700.   # 15% less than the maximal number possible
            
            ### Initiate communication ###
            self.command = command
            self.scope = v.Instrument(IP)
            
            ### Format of answers ###
            self.scope.write('CFMT DEF9,'+encoding+',BIN')
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
                    
                ### Check if channels are active ###
                for i in range(len(channel)):
                    temp = self.query(channel[i]+':TRA?')
                    if temp.find('ON') == -1:
                        print '\nWARNING:  Channel',channel[i], 'is not active  ===>  exiting....\n'
                        sys.exit()
                ### Acquire and save datas ###
                for i in range(len(channel)):
                    ### Allow auto scaling the channel gain and offset ###
                    k = 1
                    if spe_mode:
                        while k <= eval(spe_mode):
                            stri = self.query('C3:PAVA? MIN,MAX')
                            temp2 = 'MIN,'
                            temp3 = stri.find(temp2)
                            temp4 = stri.find(' V')
                            mi    = eval(stri[temp3+len(temp2):temp4])
                            stri = stri[temp4+len(' V'):]
                            temp2 = 'MAX,'
                            temp3 = stri.find(temp2)
                            temp4 = stri.find(' V')
                            ma    = eval(stri[temp3+len(temp2):temp4])
                            diff = abs(mi) + abs(ma)
                            #print 'prev_amp:  ',diff
                            temp2  = channel[i]+':VDIV'
                            temp2_o  = channel[i]+':OFST'
                            print 'MIN,MAX:   ',mi,ma
                            ### To modify offset ###
                            try:
                                val = round((-1)*diff/2. + abs(mi),3)
                                self.scope.write(temp2_o+' '+str(val))
                            except:
                                pass
                            ########################
                            ### To modify amplitude ###
                            FACT = 6
                            new_channel_amp  = round(diff/FACT,3)
                            
                            #temp2  = channel[i]+':VDIV'
                            #temp3  = self.query(temp2+'?')
                            #temp4 = temp3[(temp3.find(temp2+' ')+len(temp2+' ')):]
                            #prev_channel_amp = eval(temp4[:temp4.find('V')])
                            #print 'prev_amp:  ',prev_channel_amp
                            
                            #temp2_o  = channel[i]+':OFST'
                            #temp3_o  = self.query(temp2_o+'?')
                            #temp4_o = temp3_o[(temp3_o.find(temp2_o+' ')+len(temp2_o+' ')):]
                            #prev_channel_offset = eval(temp4_o[:temp4_o.find('V')])
                            
                            ##print 'after_chan_amp:  ',new_channel_amp,'\n'
                            #print (NUM/2.-10)*prev_channel_amp-prev_channel_offset, ma
                            
                            if new_channel_amp<0.005:        # if lower than the lowest possible 5mV/div
                                new_channel_amp = 0.005
                            #elif  ma > ((NUM/2.-10)*tt3-tt3_o):
                                #print 'AAAAAAAAAAAAAAAAAAA'
                                #new_channel_amp = new_channel_amp*4       # test amplitude
                                #k = k-1
                            self.scope.write(temp2+' '+str(new_channel_amp))
                            ########################
                            self.single()
                            while self.query('TRMD?') != 'TRMD STOP':
                                time.sleep(0.05)
                                pass
                            
                            print k,eval(spe_mode)
                            k = k+1
                            
                        ### END of spe_mode #################################
                    
                    print 'trying to get channel',channel[i]
                    self.get_data(chan=channel[i],filename=filename,SAVE=True,FORCE=FORCE)
            else:
                print 'If you want to save, provide an output file name'
            
            ### Run the scope BACK in the previous trigger mode###
            self.run()
            
        
        def query(self, cmd, nbytes=1000000):
            """Send command 'cmd' and read 'nbytes' bytes as answer."""
            self.scope.write(cmd)
            r = self.scope.read(nbytes)
            return r
        

        def get_data(self,chan='C1',filename='test_save_file_',PLOT=False,SAVE=False,LOG=True,FORCE=False,RET=False):
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
            if RET:
                return self.data
        
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
    parser.add_option("-e", "--encoding", type="string", dest="encoding", default='BYTE', help="For mofifying the encoding format of the answer" )
    parser.add_option("-m", "--spe_mode", type="string", dest="spe_mode", default=None, help="For allowing auto modification of the vertical gain" )
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
    Lecroy(channel=chan,encoding=options.encoding,spe_mode=options.spe_mode,query=options.que,command=options.com,filename=options.filename,FORCE=options.force)
    
