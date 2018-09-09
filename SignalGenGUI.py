from tkinter import *
from fractions import Fraction
from tkinter import Tk, font
from tkinter import ttk
import serial 
import socket

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
    ser.port = 'COM4'
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