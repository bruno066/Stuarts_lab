#!/usr/bin/python  
# -*- coding: utf-8 -*-

"""Loot at 2D dynamic or static data"""
from matplotlib.pyplot import axes, plot, figure, draw, show, rcParams
from matplotlib.widgets import Slider, Cursor
from numpy import array, roll, arange, sin, concatenate,\
        fromfile, int8, reshape, memmap, zeros, fromstring
from tempfile import TemporaryFile
from numpy.random import randn
import time
import sys
import commands as C
import matplotlib as mpl
from optparse import OptionParser
import vxi11 as vxi
import gobject

mpl.pyplot.switch_backend('GTkAgg')

class ytViewer(object):
    def __init__(self, chan, host, fold=19277, nmax=100,NORM=True):
        self.UPDATE = True
        self.color      = True
        
        self.flag_save = 1
        self.channel   = chan
        self.t             = time.time()
        self.NORM     = NORM
        self.NMAX     = nmax
        self.fold         = fold
        
        self.remove_len1 = 0 #6500  # 0 previously
        self.remove_len2 = 1 #12300 # 1 previously
        
        try:
            self.sock = vxi.Instrument('169.254.108.195')
            self.sock.write(':WAVeform:TYPE RAW')
            self.sock.write(':WAVEFORM:BYTEORDER LSBFirst')
            self.sock.write(':TIMEBASE:MODE MAIN')
            self.sock.write(':WAVEFORM:SOURCE ' + chan)
            self.sock.write(':WAVEFORM:FORMAT BYTE')
        except:
            print "Wrong IP, Listening port or bad connection \n Check cables first"
        
        self.fig = figure(figsize=(16,7))
        
        self.data                    = randn(self.NMAX*self.fold).reshape(self.NMAX,self.fold)[:,self.remove_len1:-self.remove_len2]
        self.folded_data         = self.data[:,self.remove_len1:-self.remove_len2]
        self.folded_data_orig = self.folded_data[:,self.remove_len1:-self.remove_len2]
        
        self.X0 = 0
        self.Y0 = 0
        
        self.ax = axes([0.1,0.4,0.8,0.47])
        if not self.NORM:
            self.im = self.ax.imshow(self.data, interpolation='nearest', aspect='auto',
		    origin='lower', vmin=0, vmax=255)
        else:
	        self.im = self.ax.imshow(self.data, interpolation='nearest', aspect='auto',
		    origin='lower', vmin=self.data.min(), vmax=self.data.max())

        self.cursor = Cursor(self.ax, useblit=True, color='red', linewidth=2)

        self.axh = axes([0.1,0.05,0.8,0.2])
        self.hline, = self.axh.plot(self.data[self.X0,:])
        self.axh.set_xlim(0,len(self.data[0,:]))
        
        # create 'remove_len1' slider
        self.remove_len1_sliderax = axes([0.1,0.96,0.8,0.02])
        self.remove_len1_slider   = Slider(self.remove_len1_sliderax,'beg',0.,self.fold*(3./4),self.remove_len1,'%d')
        self.remove_len1_slider.on_changed(self.update_tab)
        
        # create 'remove_len2' slider
        self.remove_len2_sliderax = axes([0.1,0.92,0.8,0.02])
        self.remove_len2_slider   = Slider(self.remove_len2_sliderax,'end',0.,self.fold*(3./4),self.remove_len2,'%d')
        self.remove_len2_slider.on_changed(self.update_tab)
        

        cid  = self.fig.canvas.mpl_connect('motion_notify_event', self.mousemove)
        cid2 = self.fig.canvas.mpl_connect('key_press_event', self.keypress)

        self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
        self.plot_circle(0,0,2,fc='#00FF7F')
        mpl.pyplot.axis('off')
        
        self.load_data()

        gobject.idle_add(self.update_plot)
        show()
        
    def load_data(self):
   #     self.processed = randn(1000000)[:self.NMAX*self.fold].reshape(self.NMAX,self.fold)
        self.sock.write(':WAV:DATA?')
        self.bin_data = self.sock.read_raw()[10:]
        self.data = fromstring(self.bin_data, dtype=int8)
        self.processed = self.data[:self.NMAX*self.fold].reshape(self.NMAX,self.fold)[:,self.remove_len1:-self.remove_len2]
        
    def update_tab(self,val):
        self.remove_len1 = int(self.remove_len1_slider.val)
        self.remove_len2 = int(self.remove_len2_slider.val)
        
        self.X0 = 0
        self.Y0 = 0
        self.folded_data = self.folded_data_orig[:,self.remove_len1:-self.remove_len2]
        
        self.im      = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto', origin='lower', vmin=self.data.min(), vmax=self.data.max())
        self.axh = axes([0.1,0.05,0.8,0.2])
        self.axh.clear()
        self.hline, = self.axh.plot(self.folded_data[self.X0,:])

    def update_plot(self):
        while self.UPDATE: 
            self.t = time.time()

            ### receive from pipe ###
            self.stop()
            try:
                self.load_data()
            except:
                print "Waiting for trigger"
            self.run()
            self.folded_data = self.processed
            
            if self.remove_len1!=0 or self.remove_len2!=1: 
                #if self.remove_len2 == 0
                    #len(self.folded_data[:,:][0]
                print '\n', len(self.folded_data[:,self.remove_len1:-self.remove_len2][0])
                self.folded_data = self.folded_data[:,self.remove_len1:-self.remove_len2]
               # self.folded_data = self.folded_data[:,6500:12200]

            print '\nDATA ARE LEN:', len(self.data)
            print 'data loaded, update plot:',time.time()-self.t
            self.t = time.time()
            
            try:
                ### Update picture ###
                self.im.set_data(self.folded_data)
                self.hline.set_ydata(self.folded_data[self.Y0,:])
            except:
                print "Waiting for trigger"
            
            print 'plot updated:',time.time()-self.t
            
            draw()
            
            
            return True
        return False

    def update_cut(self):
        self.hline.set_ydata(self.folded_data[self.Y0,:])

    def treat_array_mod(self):
        """ WARNING TO WRITE """
        pass

    def keypress(self, event):
        if event.key == 'q': # eXit
            del event
            sys.exit()
        elif event.key=='n':
            del event
            self.NORM = not(self.NORM)
            if not self.NORM:
                self.ax.clear()
                self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
                origin='lower', vmin=0, vmax=255)
                self.axh.set_ylim(0, 255)
            else:
                self.ax.clear()
                self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
                origin='lower', vmin=self.folded_data.min(), vmax=self.folded_data.max())
                self.axh.set_ylim(self.folded_data.min(), self.folded_data.max())
        elif event.key == ' ': # play/pause
            params              = self.params
            params['toggle'] = not(params['toggle'])
            self.params        = params
            self.toggle_update()
        elif event.key == 'S':
            params = self.params
            params['SAVE']         = True
            self.params = params
            time.sleep(1)
            filename = 'Image_'+str(self.flag_save)+'_DSA'+str(self.channel)
            self.fig.savefig(filename+'.png')
            self.flag_save = self.flag_save + 1
        else:
            print 'Key '+str(event.key)+' not known'
            
    def mousemove(self, event):
        # called on each mouse motion to get mouse position
        if event.inaxes!=self.ax: return
        self.X0 = int(round(event.xdata,0))
        self.Y0 = int(round(event.ydata,0))
        self.update_cut()
        
    def toggle_update(self):
            self.UPDATE = not(self.UPDATE)
            if self.UPDATE:
                self.run()
                gobject.idle_add(self.update_plot)
            else:
                self.stop()
            self.color  = not(self.color)
            if not(self.color):
                self.patch.remove()
                self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
                self.axe_toggledisplay.clear()
                self.plot_circle(0,0,2,fc='#FF4500')
                mpl.pyplot.axis('off')
                draw()
            else:
                self.patch.remove()
                self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
                self.axe_toggledisplay.clear()
                self.plot_circle(0,0,2,fc='#00FF7F')
                mpl.pyplot.axis('off')
                draw()
                #gobject.idle_add(self.update_plot)
    
    def plot_circle(self,x,y,r,fc='r'):
        """Plot a circle of radius r at position x,y"""
        cir = mpl.patches.Circle((x,y), radius=r, fc=fc)
        self.patch = mpl.pyplot.gca().add_patch(cir)
        
        
    def save(self):
        if self.UPDATE: self.toggle_update()
        filename = 'Image_'+str(self.flag_save)+'_DSA'+str(self.channel)
        print 'Saving to files ', filename
        ff = open(filename,'w')
        ff.write(self.bin_data)
        ff.close()
        self.sock.write(':WAVEFORM:SOURCE ' + self.channel)
        self.sock.write(':WAVEFORM:PREAMBLE?')
        self.preamble = self.sock.read()
        f = open(filename+'_log','w')
        f.write(self.preamble)
        f.close()
        self.ytv.fig.savefig(filename+'.png')

        self.flag_save = self.flag_save + 1        

    def run(self):
        self.sock.write('RUN')
    
    def stop(self):
        self.sock.write('STOP')
        
    
if __name__=='__main__':

    IP = '169.254.108.195'
    
    print '\nWARNING: To test the following functions: - self.save\n'

    usage = """usage: %prog [options] arg
               
               EXAMPLES:
                   scope_DSA -f 1000 -n 2000 1
               Show the interactive space/time diagram for 1000pts folding and 2000 rt


               """
    parser = OptionParser(usage)
    parser.add_option("-f", "--fold", type="int", dest="prt", default=364, help="Set the value to fold for yt diagram." )
    parser.add_option("-n", "--nmax", type="int", dest="nmax", default=560, help="Set the value to the number of roundtrip to plot." )
    (options, args) = parser.parse_args()

    if len(args) == 0:
        print "\nEnter one channel\n"
    elif len(args) == 1:
        chan= 'CHAN' + str(args[0])
    else:
        print "\nEnter ONLY one channel\n"
    
    ### begin TV ###
    ytViewer(chan, host=IP, fold=options.prt, nmax=options.nmax)
      
#        ytExplorer(filename=sys.argv[1], rt=int(sys.argv[2]))


