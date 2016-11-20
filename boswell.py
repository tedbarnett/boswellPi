#! /usr/bin/env python

import os
import random
import time
import RPi.GPIO as GPIO
import alsaaudio
import wave
from creds import *
import requests
import json
import re
import sys

import Tkinter # needed for message boxes
from memcache import Client

#Settings
talkbutton = 27 #GPIO Pin with button connected (was 18 in original AlexaPi main.py)
recordstartbutton = 23 #GPIO buttons are: 27, 23, 22, 17 (from bottom to top)
recordstopbutton = 22 #GPIO buttons are: 27, 23, 22, 17 (from bottom to top)
offbutton = 17 #GPIO pin to exit app
lights = [24, 25] # GPIO Pins with LED's connected
device = "plughw:1" # Name of your microphone/soundcard in arecord -L

#Setup
recorded = False
recordedinterview = False
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))


def internet_on():
    print "Checking Internet Connection"
    try:
        r =requests.get('https://api.amazon.com/auth/o2/token')
	print "Connection OK"
        return True
    except:
	print "Connection Failed"
    	return False


def gettoken():
	token = mc.get("access_token")
	refresh = refresh_token
	if token:
		return token
	elif refresh:
		payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = json.loads(r.text)
		mc.set("access_token", resp['access_token'], 3570)
		return resp['access_token']
	else:
		return False


def alexa():
	#THB:disabling GPIO.output(24, GPIO.HIGH)
	url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
	headers = {'Authorization' : 'Bearer %s' % gettoken()}
	d = {
   		"messageHeader": {
       		"deviceContext": [
           		{
               		"name": "playbackState",
               		"namespace": "AudioPlayer",
               		"payload": {
                   		"streamId": "",
        			   	"offsetInMilliseconds": "0",
                   		"playerActivity": "IDLE"
               		}
           		}
       		]
		},
   		"messageBody": {
       		"profile": "alexa-close-talk",
       		"locale": "en-us",
       		"format": "audio/L16; rate=16000; channels=1"
   		}
	}
	with open(path+'/audio/recording.wav') as inf:
		files = [
				('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
				('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
				]
		r = requests.post(url, headers=headers, files=files)
	if r.status_code == 200:
		for v in r.headers['content-type'].split(";"):
			if re.match('.*boundary.*', v):
				boundary =  v.split("=")[1]
		data = r.content.split(boundary)
		for d in data:
			if (len(d) >= 1024):
				audio = d.split('\r\n\r\n')[1].rstrip('--')
		with open(path+"audio/response.mp3", 'wb') as f:
			f.write(audio)
		os.system('mpg123 -q {}audio/1sec.mp3 {}audio/response.mp3'.format(path, path))

def start():
	last = GPIO.input(talkbutton)
	lastvalrecordstart = GPIO.input(recordstartbutton)
	while True:
		val = GPIO.input(talkbutton)
		if val != last:
			last = val
			print "TALKbutton changed"
			if val == 1 and recorded == True:
				rf = open(path+'audio/recording.wav', 'w')
				rf.write(audio)
				rf.close()
				inp = None
				alexa()
			elif val == 0:
				inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
				inp.setchannels(1)
				inp.setrate(16000)
				inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
				inp.setperiodsize(500)
				audio = ""
				l, data = inp.read()
				if l:
					audio += data
				recorded = True
		elif val == 0:
			l, data = inp.read()
			if l:
				audio += data

#	        Check recordstartbutton button
		valrecordstart = GPIO.input(recordstartbutton)
		if valrecordstart != lastvalrecordstart:
			lastvalrecordstart = valrecordstart
#			print "valrecordstart = ", valrecordstart # changes to 0 when pressed down, 1 when released

			if valrecordstart == 1 and recordedinterview == True:
				rf = open(path+'recordings/interview tbarnett '+ time.strftime("%Y-%m-%d %H:%M:%S") +'.wav', 'w')
				rf.write(audio)
				rf.close()
				inp = None
				recordlocation = path+'recordings/interview tbarnett '+ time.strftime("%Y-%m-%d %H:%M:%S") +'.wav'
				print "saved recording", recordlocation

			elif valrecordstart == 0:
				inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
				inp.setchannels(1)
				inp.setrate(16000)
				inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
				inp.setperiodsize(500)
				audio = ""
				l, data = inp.read()
				if l:
					audio += data
				recordedinterview = True
		elif valrecordstart == 0:
			l, data = inp.read()
			if l:
				audio += data

if __name__ == "__main__":
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(talkbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(recordstartbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(recordstopbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(offbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while internet_on() == False:
        print "."

    start()
