#! /bin/env/python

import visa as v 
import time as t
from numpy import *

rm = v.ResourceManager('@py')

thorlabs = rm.get_instrument('USB0::0x1313::0x804A::M00248997::INSTR')

#change the value of the current

val = linspace(0,0.1,10)
for i in range(len(val)):
    thorlabs.write('SOUR:CURR %f\n' %val[i])
    t.sleep(1)
#thorlabs.write('*IDN?\n')
print thorlabs.read()

if __name__=="__main__":
   pass
   # thorlabs_talk()
