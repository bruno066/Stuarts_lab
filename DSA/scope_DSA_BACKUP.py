#!/usr/bin/python  
# -*- coding: utf-8 -*-

"""Loot at 2D dynamic or static data"""
from matplotlib.pyplot import axes, plot, figure, draw, show, rcParams
from matplotlib.widgets import Slider, Cursor
from numpy import array, roll, arange, sin, concatenate,\
        fromfile, int8, reshape, memmap, zeros, fromstring,copy
from tempfile import TemporaryFile
from numpy.random import randn
import time
import sys
import commands as C
import matplotlib as mpl
from optparse import OptionParser
import vxi11 as vxi
import gobject
from matplotlib.font_manager import FontProperties

mpl.style.use('classic')
mpl.pyplot.switch_backend('GTkAgg')

class Scope(object):
    def __init__(self, chan, host, fold=19277, nmax=100,NORM=True,sequence=False):
        self.UPDATE = True
        self.FIRST  = True
        self.color  = True
        
        ### To set the first name that has to be recorded ###
        try:
            L = C.getoutput('ls Image_*_DSACHAN1 | sort -n').splitlines()
            temp = array([eval(L[i].split('_')[1]) for i in range(len(L))])
            self.flag_save = max(temp) + 1
        except:                      # nothing in the folder already
            self.flag_save = 1
        
        self.channel   = chan
        self.t             = time.time()
        self.NORM     = NORM
        self.NMAX     = nmax
        self.fold     = fold
        self.shear    = 0.
        self.sequence = sequence
        self.vmin     = -125
        self.vmax     = 125
        
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
        
        self.load_data()
        self.data        = self.data[:(self.NMAX*self.fold)]
        self.folded_data = self.data.reshape(self.NMAX,self.fold)
        self.folded_data_orig = copy(self.folded_data)
        self.folded_data = self.folded_data[:,self.remove_len1:-self.remove_len2]
        self.Y0 = 0
        
        self.ax = axes([0.1,0.4,0.8,0.47])
        if not self.NORM:
            self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
		    origin='lower', vmin=self.vmin, vmax=self.vmax)
        else:
	        self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
		    origin='lower', vmin=self.folded_data.min(), vmax=self.folded_data.max())

        self.cursor = Cursor(self.ax, useblit=True, color='red', linewidth=2)

        self.axh = axes([0.1,0.05,0.8,0.2])
        self.hline, = self.axh.plot(self.folded_data[self.Y0,:])
        self.axh.set_xlim(0,len(self.folded_data[0,:]))
        if not self.NORM:
            self.axh.set_ylim(self.vmin, self.vmax)
        else:
            self.axh.set_ylim(self.folded_data.min(), self.folded_data.max())
        
        # create 'remove_len1' slider
        self.remove_len1_sliderax = axes([0.1,0.96,0.8,0.02])
        self.remove_len1_slider   = Slider(self.remove_len1_sliderax,'beg',0.,self.fold*(3./4),self.remove_len1,'%d')
        self.remove_len1_slider.on_changed(self.update_tab)
        
        # create 'remove_len2' slider
        self.remove_len2_sliderax = axes([0.1,0.92,0.8,0.02])
        self.remove_len2_slider   = Slider(self.remove_len2_sliderax,'end',1.,self.fold*(3./4),self.remove_len2,'%d')
        self.remove_len2_slider.on_changed(self.update_tab)
        
        # create 'shear' slider
        self.shear_sliderax = axes([0.1,0.88,0.8,0.02])
        self.shear_slider   = Slider(self.shear_sliderax,'Shear',-1,1,self.shear,'%1.2f')
        self.shear_slider.on_changed(self.update_shear)
        
        #if self.sequence:
        font0 = FontProperties()
        font1 = font0.copy()
        font1.set_weight('bold')
        mpl.pyplot.text(-1.1,-27,'Sequence mode:',fontsize=18,fontproperties=font1)
        mpl.pyplot.text(-0.75,-30,'"b" to toggle it then:\n      "y" to save\n      "n" to next',fontsize=18)
        mpl.pyplot.text(0.25,-27,'Useful keys:',fontsize=18,fontproperties=font1)
        mpl.pyplot.text(0.5,-31,'"v" to change vertical/colorscale\n " " to pause\n "S" to save trace and picture\n "q" to exit',fontsize=18)
        
        cid  = self.fig.canvas.mpl_connect('motion_notify_event', self.mousemove)
        cid2 = self.fig.canvas.mpl_connect('key_press_event', self.keypress)

        self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
        self.plot_circle(0,0,2,fc='#00FF7F')
        mpl.pyplot.axis('off')
        
        ### trigger the scope for the first time ###
        self.single()
        
        gobject.idle_add(self.update_plot)
        show()
        
    def load_data(self):
        self.sock.write(':WAV:DATA?')
        self.bin_data = self.sock.read_raw()[10:]
        self.data = fromstring(self.bin_data, dtype=int8)
        
    def update_shear(self,val):
        self.shear = round(self.shear_slider.val,2)
        print 'shear:',self.shear
        self.process_data(self.shear)
        self.norm_fig()
        self.fig.canvas.draw()
        
    def update_tab(self,val):
        self.remove_len1 = int(self.remove_len1_slider.val)
        self.remove_len2 = int(self.remove_len2_slider.val)
        
        self.Y0 = 0
        if self.sequence:
            self.folded_data = self.orig_data[:,self.remove_len1:-self.remove_len2]
        else:
            self.folded_data = self.folded_data_orig[:,self.remove_len1:-self.remove_len2]
        self.norm_fig()
        self.fig.canvas.draw()

    def update_plot(self):
        while self.UPDATE: 
            self.t = time.time()
            if len(self.data)<self.NMAX*self.fold:
                print '\nNumber of point asked for the plot must not exceed the length of datas got from the scope \n\nExiting...\n'
                sys.exit()
            
            ### Verify that the scope has triggered ###
            while self.query(':RSTate?')!= 'STOP\n':
                time.sleep(0.1)
                pass
            
            ### Compute the array to plot ###
            self.load_data()
            self.single()
            self.folded_data   = self.data[:self.NMAX*self.fold].reshape(self.NMAX,self.fold)
            self.process_data(self.shear)

            self.folded_data = self.folded_data[:,self.remove_len1:-self.remove_len2]
            print '\nDATA ARE LEN:', len(self.data)
            print 'data loaded, update plot:',time.time()-self.t
            self.t = time.time()
            
            ### Update picture ###
            self.im.set_data(self.folded_data)
            self.hline.set_ydata(self.folded_data[self.Y0,:])
            print 'plot updated:',time.time()-self.t
            if self.FIRST:
                self.ax.clear()
                self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
                origin='lower', vmin=self.folded_data.min(), vmax=self.folded_data.max())
                self.axh.set_ylim(self.folded_data.min(), self.folded_data.max())
                self.FIRST=False
            
            self.fig.canvas.draw()
            self.fig.canvas.draw()
            draw()
            
            if self.sequence:
                self.orig_data = self.data[:self.NMAX*self.fold].reshape(self.NMAX,self.fold)
                self.orig_data2 = self.orig_data[:,self.remove_len1:-self.remove_len2]
                self.toggle_update()
            return True
        return False


    def process_data(self,val):
        """ Redress data in the space/ti;e diagram """
        if self.sequence:
            dd = self.orig_data.copy()
        else:
            dd = self.folded_data.copy()
        for i in range(0,self.folded_data.shape[0]):
            dd[i,:] = roll(self.folded_data[i,:], int(i*val))
        self.folded_data = dd
        
    def update_cut(self):
        self.hline.set_ydata(self.folded_data[self.Y0,:])

    def keypress(self, event):
        if event.key == 'q': # eXit
            del event
            self.run()
            sys.exit()
        elif event.key == 'b': # switch sequence mode on/off
            self.sequence = not(self.sequence)
            self.toggle_update()
            time.sleep(0.15)
            del event
        elif event.key == 'y':
            if self.sequence:
                self.fig.canvas.draw()
                self.single()
                self.Save()
                self.toggle_update()
                time.sleep(0.15)
            del event
        elif event.key == 'n':
            if self.sequence:
                self.fig.canvas.draw()
                self.toggle_update()
                time.sleep(0.15)
            del event
        elif event.key=='v':
            del event
            self.NORM = not(self.NORM)
            self.norm_fig()
            self.fig.canvas.draw()
        elif event.key == ' ': # play/pause
            if not self.sequence:
                self.toggle_update()
            del event
        elif event.key == 'S':
            self.Save()
        else:
            print 'Key '+str(event.key)+' not known'
    
    def norm_fig(self):
        if not self.NORM:
            self.ax.clear()
            self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
            origin='lower', vmin=self.vmin, vmax=self.vmax)
            self.axh.clear()
            self.hline, = self.axh.plot(self.folded_data[self.Y0,:])
            self.axh.set_ylim(self.vmin, self.vmax)
            self.axh.set_xlim(0, len(self.folded_data[0]))
        else:
            self.ax.clear()
            self.im = self.ax.imshow(self.folded_data, interpolation='nearest', aspect='auto',
            origin='lower', vmin=self.folded_data.min(), vmax=self.folded_data.max())
            self.axh.clear()
            self.hline, = self.axh.plot(self.folded_data[self.Y0,:])
            self.axh.set_ylim(self.folded_data.min(), self.folded_data.max())
            self.axh.set_xlim(0, len(self.folded_data[0]))
        self.fig.canvas.draw()
    
    def mousemove(self, event):
        # called on each mouse motion to get mouse position
        if event.inaxes!=self.ax: return
        self.X0 = int(round(event.xdata,0))
        self.Y0 = int(round(event.ydata,0))
        self.update_cut()
        
    def toggle_update(self):
            self.UPDATE = not(self.UPDATE)
            print self.UPDATE
            if self.UPDATE:
                self.single()
                time.sleep(0.15)
                gobject.idle_add(self.update_plot)
            else:
                self.single()
            self.color  = not(self.color)
            if not(self.color):
                self.patch.remove()
                self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
                self.axe_toggledisplay.clear()
                self.plot_circle(0,0,2,fc='#FF4500')
                mpl.pyplot.axis('off')
                self.fig.canvas.draw()
            else:
                self.patch.remove()
                self.axe_toggledisplay  = self.fig.add_axes([0.43,0.27,0.14,0.1])
                self.axe_toggledisplay.clear()
                self.plot_circle(0,0,2,fc='#00FF7F')
                mpl.pyplot.axis('off')
                self.fig.canvas.draw()
    
    def plot_circle(self,x,y,r,fc='r'):
        """Plot a circle of radius r at position x,y"""
        cir = mpl.patches.Circle((x,y), radius=r, fc=fc)
        self.patch = mpl.pyplot.gca().add_patch(cir)
        
        
    def Save(self):
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
        self.fig.savefig(filename+'.png')
        self.flag_save = self.flag_save + 1   
        if not(self.UPDATE):self.toggle_update()

    def run(self):
        self.sock.write('RUN')
    def single(self):
        self.sock.write('SINGLE')
    def stop(self):
        self.sock.write('STOP')
    def query(self,com):
        self.sock.write(com)
        return self.sock.read_raw()
    
if __name__=='__main__':

    IP = '169.254.108.195'
    
    print '\nWARNING: To test the following functions: - self.save\n'

    usage = """usage: %prog [options] arg
               
               EXAMPLES:
                   scope_DSA -f 1000 -n 2000 1
               Show the interactive space/time diagram for 1000pts folding and 2000 rt of channel 1
                   scope_DSA -s -f 1000 -n 2000 2
                Same as before but for channel 2, and trigger the SAVE mode that display pictures one by one waiting for an input from the user side (just precize the -s option wherever you want)

               """
    parser = OptionParser(usage)
    parser.add_option("-f", "--fold", type="int", dest="prt", default=364, help="Set the value to fold for yt diagram." )
    parser.add_option("-n", "--nmax", type="int", dest="nmax", default=560, help="Set the value to the number of roundtrip to plot." )
    parser.add_option("-s", "--seauence", action = "store_true", dest ="sequence", default=False, help="Set saving mode")
    (options, args) = parser.parse_args()

    if len(args) == 0:
        print "\nEnter one channel\n"
    elif len(args) == 1:
        chan= 'CHAN' + str(args[0])
    else:
        print "\nEnter ONLY one channel\n"
    
    ### begin TV ###
    Scope(chan, host=IP, fold=options.prt, nmax=options.nmax,sequence=options.sequence)
      
#        ytExplorer(filename=sys.argv[1], rt=int(sys.argv[2]))


