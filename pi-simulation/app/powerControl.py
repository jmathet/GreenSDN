#!/usr/bin/env python

from deviceList.deviceList_Pi import *
import os

coreSwitchPosition = [10,1] # Core switches positions in the tower
aggrSwitchPosition = [9,7,4,2] # Aggregation switches positions in the tower

def powerControl(NCore, NAgg_p):
    NCore = sum(NCore)
    for s in range(len(CORE_DEVICES)): 
        if (s+1 <= NCore): # Turn ON needed switches
            os.system('ssh pi@192.168.0.98 python pi_power_control.py ' + str(coreSwitchPosition[s]) + ' ON')
        else: # Turn OFF needed switches
            os.system('ssh pi@192.168.0.98 python pi_power_control.py ' + str(coreSwitchPosition[s]) + ' OFF')
    for p in range(2): # For pods 1 and 2
        NAgg = NAgg_p[p]
        for s in range(2): # For aggregation switch 1 and 2 of the pod p
            if (s+1 <= NAgg): # Turn ON needed switches
                os.system('ssh pi@192.168.0.98 python pi_power_control.py ' + str(aggrSwitchPosition[p*2+s]) + ' ON')
            else: # Turn OFF needed switches
                os.system('ssh pi@192.168.0.98 python pi_power_control.py ' + str(aggrSwitchPosition[p*2+s]) + ' OFF')