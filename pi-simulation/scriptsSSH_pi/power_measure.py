from pysnmp.hlapi import *
import datetime
import time
import csv

resolution = 5 #delay between each SNMP requests in seconds

myFile = open('power.csv', 'w') #file for writing power  measurements

writer= csv.writer(myFile, delimiter=',')

row = ["UnixTimeStamp","Outlet A22","Outlet A22"] 
writer.writerow(row)
	
while True:

	errorIndication, errorStatus, errorIndex, varBinds = next(
	    getCmd(SnmpEngine(),
	    	   UsmUserData('admin', 'greencloud2019', 'greencloud2019'),
	           #CommunityData('public', mpModel=0),
	           UdpTransportTarget(('192.168.0.200', 161)), # We made a daisy chain of EPDUs, and 192.168.0.200 is the host <0>
	           ContextData(),
	           ObjectType(ObjectIdentity('.1.3.6.1.4.1.534.6.6.7.1.2.1.8.0')),    	#SNMP Query timeanddate
	           ObjectType(ObjectIdentity('.1.3.6.1.4.1.534.6.6.7.6.5.1.3.0.22')),	#SNMP Query Outlet 22 power From EPDU 0
	           ObjectType(ObjectIdentity('.1.3.6.1.4.1.534.6.6.7.6.5.1.3.1.22')),	#SNMP Query Outlet 22 power From EPDU 1

	           )
	)
	
	row = ['-1','-1','-1','-1','-1']			 # Any error or connection loss we write down -1 in all columns
	if errorIndication:
	    print(errorIndication)

	elif errorStatus:
	    print('%s at %s' % (errorStatus.prettyPrint(),
	                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		
	else:
		timestamp = str(varBinds[0]).split('=', 1)[1].strip()
		Y = int(timestamp[0:6],16)
		M = int(timestamp[6:8],16)
		D = int(timestamp[8:10],16)
		h = int(timestamp[10:12],16)
		m = int(timestamp[12:14],16)
		s = int(timestamp[14:16],16)
		dt = datetime.datetime.combine(datetime.date(Y,M,D), datetime.time(h, m, s)) - datetime.datetime(1970,1,1)
		row = [str(dt.total_seconds()),
			   str(varBinds[1]).split('=', 1)[1].strip(),
			   str(varBinds[2]).split('=', 1)[1].strip()]
		print(row)
		
	writer.writerow(row)
	myFile.flush()		  
				
	time.sleep(resolution)
	

