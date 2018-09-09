# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import sys
import csv
from socket import *
import time
from scipy.fftpack import fft
from multiprocessing import Process, freeze_support
from tkinter import *
from fractions import Fraction
from tkinter import Tk, font
from tkinter import ttk
import serial 

from scipy.signal import butter, lfilter, freqz
from scipy.signal import savgol_filter
from scipy import signal



class Plot2D():
    def __init__(self, maxY, maxX, numberpackets, samplefreq):
        #Initializing stuff for plots
        self.traces = dict()
        self.samplefreq = samplefreq
        self.CHUNK = 130*numberpackets       #Samples per batch
        self.t = np.arange(0, self.CHUNK, 1)/self.samplefreq #Defining time domain - I get 130*500 points at the sample frequency rate
        self.f = (np.linspace(0, 1, self.CHUNK ) * self.samplefreq)[0:int(self.CHUNK/2)]
        
        #Setting GUI parameters
        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'w')
        self.app = QtGui.QApplication([])
      
        self.win = pg.GraphicsWindow(title="Impedance Imager")
        self.win.resize(1000,600)
        self.win.setWindowTitle('Real Time Oscilloscope')
        
        #Setting socket parameters
        self.host="192.168.1.12"
        self.port = 5010  
        
        
        #Reading Hashtables
        with open('directout.csv', mode='r') as infile:
            reader = csv.reader(infile)
            self.directout = {}
            for row in reader:
                if row != []:
                    k, v = row
                    self.directout[k] = v
    
        with open('unsigneddirect.csv', mode='r') as infile:
            reader = csv.reader(infile)
            self.unsigneddirectout = {}
            for row in reader:
                if row != []:
                    k, v = row
                    self.unsigneddirectout[k] = v      
                    
                    
        self.sock = socket(AF_INET,SOCK_DGRAM) 
        self.sock.bind((self.host,self.port))
        self.addr = (self.host,self.port)
        self.rt = self.win.addPlot(title='Realtime & Reference', row = 1, col = 1)
        self.rt.addLegend()
        self.rt.setYRange(-maxY, maxY, padding=0)
        #self.rt.setXRange(0, maxX, padding=0)
        
        self.amplitude = self.win.addPlot(title='Amplitude', row = 2, col = 1)
        self.phs = self.win.addPlot(title='Phase', row = 3, col = 1)
        self.fft = self.win.addPlot(title='Fourier Transform', row = 4, col = 1)
        self.fft.setYRange(0, 0.5, padding=0)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
            

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'realtime':
                self.traces[name] = self.rt.plot(pen='b', width=3, name='Realtime Signal')
            if name == 'ref':
                self.traces[name] = self.rt.plot(pen='c', width=3, name='Reference Signal')            
            if name == 'amplitude':
                self.traces[name] = self.amplitude.plot(pen='k', width=3)
            if name == 'phs':
                self.traces[name] = self.phs.plot(pen='r', width=3)      
            if name == 'fft':
                self.traces[name] = self.fft.plot(pen='k', width=3)                 
            

                
    def update(self):
        
        phaselist = []
        amplitudelist = []
        rtlist = []
        reflist = []        
        
        counter = 0 
        numberpackets = self.CHUNK/130
        self.sock.close()
        self.sock=socket(AF_INET,SOCK_DGRAM) 
        self.sock.bind((self.host,self.port))        
        data,addr = self.sock.recvfrom(1040)
        newlist = []
        while counter < numberpackets:
            if data:
                data,addr = self.sock.recvfrom(1040)
                z=list(data)
                newlist.extend(z)
                counter += 1
            


        #Looking up hashtable
        self.sock.close()
        counter = 0
        z = newlist 
        for i in range (0,int(130*numberpackets)):
            
            # Takes in a list of 1040 elements in the form [Amplitdue, Amplitude, Phase, Phase, Realtime data, Realtimedata, FFT, FFT.......]
            amp = self.unsigneddirectout[ str( (z[8*i], z[8*i+1]) )]
            amplitudelist.append(int(amp)/2**8)

            phs = self.directout[str( (z[8*i+2], z[8*i+3]) )]
            phaselist.append((int(phs)/2**13)*180/(np.pi))

            rt = self.directout[str( (z[8*i+4], z[8*i+5]) )]
            rtlist.append(int(rt))

            ref = self.directout[str( (z[8*i+6], z[8*i+7]) )]
            reflist.append(int(ref))        



        
        def butter_highpass(cutoff, fs, order=5):
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
            return b, a
        
        def butter_highpass_filter(data, cutoff, fs, order=5):
            b, a = butter_highpass(cutoff, fs, order=order)
            y = signal.filtfilt(b, a, data)
            return y

        #For noise reduction and getting rid of DC offset
        rtlist = self.smooth(rtlist, 500)        
        rtlist = butter_highpass_filter(rtlist, 200, self.samplefreq)

        #Using built in fft function and getting rid of negative frequencies 
        fouriertransform=fft(np.array(rtlist))
        fouriertransform=np.abs(fouriertransform[0:int(self.CHUNK/2)]) * 2 /(self.CHUNK*255) #for re normalizing np.abs(fouriertransform) * 2 /(self.CHUNK*255) # 


        self.set_plotdata(name='realtime', data_x=self.t, data_y=rtlist )
        self.set_plotdata(name='ref', data_x=self.t, data_y=reflist)
        self.set_plotdata(name='phs', data_x=self.t, data_y=phaselist)
        self.set_plotdata(name='amplitude', data_x=self.t, data_y=amplitudelist)
        self.set_plotdata(name='fft', data_x=self.f[0:650], data_y=fouriertransform[0:650])
        
       

            
    def smooth(self, y, box_pts):
        #Moving average filter
        box = np.ones(box_pts)/box_pts
        y_smooth = np.convolve(y, box, mode='same')
        return y_smooth
    
    def animation(self):
        timer=QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


def start_plotting():
    p = Plot2D(255, 650, 500, 100*10000)#Yrange, Xrange, numberpackets, sampling frequency
    p.animation()    

    


## Start Qt event loop unless running in interactive mode or using pyside.

if __name__ == '__main__':
    
    start_plotting()

    
