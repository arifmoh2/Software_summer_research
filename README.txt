Libraries Needed To Run Python files:

pyqtgraph
PyQt5
numpy
sys
csv
socket
time
scipy
multiprocessing
tkinter
fractions
scipy
serial

All these libraries except pyqtgraph can be installed using pip.
Once pyqt5 has been installed, pyqtgraph can be installed from
http://pyqtgraph.org/

######################################################################

NOTE:

The files must be run on python 3.5 or higher. 'RealTimeGUI.py'
displays the data only through the ethernet. To use the GUI
simply click the file. Make sure that the ethernet port IP 
address is set to 192.168.1.12. 

The 'RealTimeGUI.py' file is one part of the system and will not 
interact with the signal generator. The 'SignalGenGUI.py' has the code
to interact with the signal generator via USB. By default, the 
USB port is set to COM4. To change it, you can simply modify the
code on line 82.

The 'CombinedIntegratedGUI.py' file has both the systems combined.
It will ask you for the correct COM port and then connect to it. 
Therefore, the code does NOT need to be modified.

For any of these files to work it is crucial that the hash tables 
are in the same folder as the python files. These hash tables are 
stored in 'directout.csv' and 'unsigneddirect.csv'.

The sampling rate is predefined to work with the FPGA where the decimation
filter counter size is set to 500. If the hardware parameters are changed,
the sampling frequency would need to be changed in the program in 
'RealTimeGUI.py' (line 187) & 'CombinedIntegratedGUI.py'(line 192).

If the signal generator hardware has not properly been set up on the
Nexys 4 FPGA, the Signal Generator GUI will freeze. in the 
'CombinedIntegratedGUI.py' file, this will have no effect on the
Real Time Display.

