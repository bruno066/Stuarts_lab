# Stuarts_lab
Python based codes to automize Stuart's lab

Available instruments:
	
	Scope:
		- DPO4104     (ethernet)
		- DSA91304a  (ethernet) => codes available also to plot interactively spatio-temporal diagrams
	
	Controller:
		- ITC_4001      (usb)   (very basic, only able to modify the current)
		- SIM900         (GPIB)
		- TGA_12104   (usb)
		- TLB_6700      (usb)
		

Notes:

    - Some of the codes are very basic and/or in test phase => please report problems/suggestions to Bruno
    - All the codes are not very well documented yet.
    - Be sure to have all the necessary python libraries
        notably: pyvisa, pyvisa-py (backend @py de pyvisa), pyusb, appropriate GPIB libraries for your OS (linux-gpib for linux)
        Other helpful libraries: matplotlib, numpy, scipy, time, math, ...
    - Have a look on Prog_Guide folder if you want to implement your own functions and help improve the repository
