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
        #self.rt.setYRange(-500, maxY, padding=0)                          #THESE LINES SET THE AXES LIMITS
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
                self.traces[name] = self.amplitude.plot(pen='w', width=3)
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
        
        
        #TO MODIFY SIGN
        
        rtlist = self.smooth(rtlist, 500)        
        rtlist = butter_highpass_filter(rtlist, 200, self.samplefreq)

        
        
        fouriertransform=fft(np.array(rtlist))
        fouriertransform=np.abs(fouriertransform[0:int(self.CHUNK/2)]) * 2 /(self.CHUNK*255) #for re normalizing np.abs(fouriertransform) * 2 /(self.CHUNK*255) # 
      

            
      

        self.set_plotdata(name='realtime', data_x=self.t, data_y=rtlist )
        self.set_plotdata(name='ref', data_x=self.t, data_y=reflist)
        self.set_plotdata(name='phs', data_x=self.t, data_y=phaselist)
        self.set_plotdata(name='amplitude', data_x=self.t, data_y=amplitudelist)
        self.set_plotdata(name='fft', data_x=self.f[0:650], data_y=fouriertransform[0:650])
        
       

            
    def smooth(self, y, box_pts):
        box = np.ones(box_pts)/box_pts
        y_smooth = np.convolve(y, box, mode='same')
        return y_smooth
    
    def animation(self):
        timer=QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


def start_plotting():
    p = Plot2D(500, 650, 500, 100*10000)#Yrange, Xrange, numberpackets, sampling frequency
    p.animation()    

    
#This is Michelles GUI for the signal generator  
def basicWindow(COM):
    window = Tk()
    s = ttk.Style()
    s.theme_use('clam')
    
    window.title("Signal Generator")
    window.geometry('475x230')
    window.configure(background="#E8FDEC")
    titleLabel = Label(window, text="Signal Generator", font=("Helvetica Bold", 15), background="#E8FDEC")
    titleLabel.grid(column=1, row=0)
    
    space = Label(window, text= "   ", font=("Helvetica", 10), background="#E8FDEC")
    space.grid(column=1, row=7)
    
    #Frequency
    freqLabel = Label(window, text="Frequency: ", font=("Helvetica", 10), background="#E8FDEC")
    freqLabel.grid(sticky="E", column=0, row=1)
    frequencyBox = ttk.Entry(window,width=38)
    frequencyBox.grid(column=1, row=1)
    frequencyDescription = Label(window, text="(in Hz)", font=("Helvetica", 8), background="#E8FDEC")
    frequencyDescription.grid(sticky="W", column=2, row=1)
    
    #Shape
    shapeLabel = Label(window, text="Shape: ", font=("Helvetica", 10), background="#E8FDEC")
    shapeLabel.grid(sticky="E", column=0, row=2)
    shapeBox = ttk.Entry(window,width=38)
    shapeBox.grid(column=1, row=2)
    shapeDescription = Label(window, text="(0-sinusoid, 1-square, 2-triangle)", font=("Helvetica", 8), background="#E8FDEC")
    shapeDescription.grid(sticky="W", column=2, row=2)
    
    #Amplitude
    ampLabel = Label(window, text="Amplitude: ", font=("Helvetica", 10), background="#E8FDEC")
    ampLabel.grid(sticky="E", column=0, row=3)
    amplitudeBox = ttk.Entry(window,width=38)
    amplitudeBox.grid(column=1, row=3)
    ampDescription = Label(window, text="(decimal value)", font=("Helvetica", 8), background="#E8FDEC")
    ampDescription.grid(sticky="W", column=2, row=3)
    
    #DC Shift
    shiftLabel = Label(window, text="DC Shift: ", font=("Helvetica", 10), background="#E8FDEC")
    shiftLabel.grid(sticky="E", column=0, row=4)
    shiftBox = ttk.Entry(window,width=38)
    shiftBox.grid(column=1, row=4)
    shiftDescription = Label(window, text="(set to 64 for default wave)", font=("Helvetica", 8), background="#E8FDEC")
    shiftDescription.grid(sticky="W", column=2, row=4)
    
    #phase offset
    POFFLabel = Label(window, text="Phase: ", font=("Helvetica", 10), background="#E8FDEC")
    POFFLabel.grid(sticky="E", column=0, row=5)
    POFFBox = ttk.Entry(window,width=38)
    POFFBox.grid(column=1, row=5)
    POFFDescription = Label(window, text="(fraction of pi radians)", font=("Helvetica", 8), background="#E8FDEC")
    POFFDescription.grid(sticky="W", column=2, row=5)
    
    #def sendData(freq, shape, mult, div, shift, poff):
        ##TCP_IP = '192.168.1.10'
        ##TCP_PORT = 7
        ##MESSAGE = str(freq) + "," + str(shape) + "," + str(mult) + "," + str(div) + "," + str(shift) + ",,";
        ##s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ##s.connect((TCP_IP, TCP_PORT))
        ##s.send(MESSAGE.encode())
    
        #UDP_IP = '192.168.1.10'
        #UDP_PORT = 7
        #MESSAGE = str(freq) + "," + str(shape) + "," + str(mult) + "," + str(div) + "," + str(shift) + "," + str(poff) + ",,";
        ##s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ##s.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))
        ##s.close()
        
    def sendData(freq, shape, mult, div, shift, poff):
        ser = serial.Serial()
        ser.baudrate = 9600
        ser.port = COM
        MESSAGE = "," + str(freq) + "," + str(shape) + "," + str(mult) + "," + str(div) + "," + str(shift) + "," + str(poff);
        while len(MESSAGE) < 18:
            MESSAGE = "0" + MESSAGE
    
        ser.open()
        send = ser.write(str(MESSAGE).encode('utf-8'))
        read = ser.read(23) #"signal has been changed" will appear if no error occurs
        #print(read.decode('utf-8'))
        ser.close()    
    
    def clicked():
        if amplitudeBox.get():
            if int(frequencyBox.get()) >= 1000: res = "A " + frequencyBox.get() + "Hz wave has been produced"
            else: res = "   A " + frequencyBox.get() + "Hz wave has been produced   "
            resultLabel = Label(window, text=res, font=("Arial", 10), background="#E8FDEC")
            resultLabel.grid(column=1, row=7)
    
            if frequencyBox.get(): frequency = frequencyBox.get()
            else: frequency = 0
            if shapeBox.get(): shape = shapeBox.get()
            else: shape = 0
            if shiftBox.get(): shift = shiftBox.get()
            else: shift = 0;
            amplitude = amplitudeBox.get()
            mult = Fraction(int(amplitude), 64).numerator
            divide = Fraction(int(amplitude),64).denominator
    
            if POFFBox.get(): poff = POFFBox.get()
            else: poff = 0;
    
            sendData(frequency, shape, mult, divide, shift, poff)
    
            #print info to file
            #file = open("values.txt", "w")
            #file.write(str(frequency) + "\n")
            #file.write(str(shape) + "\n")
            #file.write(str(mult) + "\n")
            #file.write(str(divide) + "\n")
            #file.write(str(shift) + "\n")
            #file.write(str(poff) + "\n")
            #file.close()
    
        else:
            res = "please enter a valid amplitude"
            resultLabel = Label(window, text=res, font=("Helvetica", 10), background="#E8FDEC")
            resultLabel.grid(column=1, row=6)
    
    def quit():
        window.destroy()
    
    runButton = ttk.Button(window, text="Generate Wave", command=clicked)
    runButton.grid(column=1, row=6)
    
    quitButton = ttk.Button(window, text="Quit", command=quit)
    quitButton.grid(column=1, row=8)
    
    frequencyBox.focus()
    window.mainloop()       
    
def start_main(COM):
    process1 = Process(target=start_plotting)
    process1.start()  
    process2 = Process(target=basicWindow(COM))
    process2.start()    


def isvalidport(COM):
    try:
        ser = serial.Serial(COM, 9600)
        ser.close()
        return True
    except serial.serialutil.SerialException:
        return False  



## Start Qt event loop unless running in interactive mode or using pyside.

if __name__ == '__main__':
 
    freeze_support()
        
    COMlist = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6']
    COM = (str(input ("Please enter your valid COM port [COM1, COM2, COM3....]:  ")).upper()).replace(" ", "")
    
    while COM not in COMlist or not isvalidport(COM):
        if COM not in COMlist:
            print ("     Invalid Input, check input format and retry")
        elif not isvalidport(COM):
            print ("     Please make sure device is connected to the COM port and retry")
        print('\n')
        COM = (str(input ("Please enter your valid COM port [COM1, COM2, COM3....]:  ")).upper()).replace(" ", "")
        
    print('\n\n')
    print('Connection Successful')
    input("Click ENTER to begin")

    start_main(COM)

    
   