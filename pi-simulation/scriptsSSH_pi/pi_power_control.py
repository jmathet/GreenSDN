#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

print(str(sys.argv))

piNumber = int(sys.argv[1])
power = str(sys.argv[2])

print(str(piNumber) + ' ' + power)

# init list with pin numbers

pinList = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5]

GPIO.setup(pinList[piNumber-1], GPIO.OUT)

if power=='OFF':
    GPIO.output(pinList[piNumber-1], GPIO.HIGH)
    print('POWER OFF')
if power=='ON':
    GPIO.output(pinList[piNumber-1], GPIO.LOW)
    print('POWER ON')