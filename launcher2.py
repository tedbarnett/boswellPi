# Thanks to Sam Machin for "AlexaPi" inspiration

#! /usr/bin/env python
import RPi.GPIO as GPIO
import time
import sys
import subprocess, os
import pygame
from pygame.locals import *
import os
import random
import alsaaudio
import wave
from creds import *
import requests
import json
import re

import Tkinter # needed for message boxes
from memcache import Client

# Button setup: GPIO buttons are: 27, 23, 22, 17 (from bottom to top)
talkbutton = 27 # press to talk to Alexa (bottom button)
recordstartbutton = 23 # press to start recording an interview (release to stop)
recordstopbutton = 22 # press to stop recording (not yet implemented)
quit_button = 17 # press to quit BoswellPi (top button)

#Setup
device = "plughw:1" # Name of microphone/soundcard in arecord -L
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
	with open(path+'audio/recording.wav') as inf: # not clear if it should be "/audio/recording.wav"
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

if __name__ == "__main__":
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(talkbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(recordstartbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(recordstopbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(quit_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while internet_on() == False:
        print "."

os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
os.environ["SDL_MOUSEDRV"] = "TSLIB"

# Initialize pygame (Raspberry Pi display and audio)
pygame.init()
pygame.display.init()
pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag

# Initialize variables
current_question = 0
change_question = False
last = GPIO.input(talkbutton)
lastvalrecordstart = GPIO.input(recordstartbutton)
need_to_launch_Alexa = True # Send "open boswell" first time talkbutton is pressed and released

# Set up all questions (THB: Replace with load-from-database)
img_names = []
sound_names = []
qcodes = []

img_names.append("images/judy_wedding_photo.png")
sound_names.append("audio/silence.ogg")
qcodes.append("judywed1961")

# img_names.append("images/john_quinn.png")
# sound_names.append("audio/alexa-please_tell_me_about.ogg")
# qcodes.append("jquinn1961")

# img_names.append("images/question01.png")
# sound_names.append("audio/willa_question01.ogg")
# qcodes.append("worldchange")
#

max_question = len(img_names)
print "max_question = " , max_question

# Display startup screen
imgSurf = pygame.image.load ('images/boswell_startup_screen.png')
pygame.mixer.music.load("audio/silence.ogg")
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode ( imgSurf.get_size(), pygame.FULLSCREEN )
screen.blit ( imgSurf, ( 0, 0 ) )
pygame.display.flip()
pygame.mixer.music.play()

while pygame.mixer.music.get_busy() == True:
	continue

# THB To Do: Pass startup request wav to Boswell ("Open Boswell")
# THB To Do: Use MQTT to send status to Node-RED Boswell Skill
# THB: See http://stackoverflow.com/questions/30447215/why-cant-i-use-python-mosquitto-on-the-raspberry-pi

while True:
# listen for buttons for recording or Alexa dialog first...
	val = GPIO.input(talkbutton)
	if val != last:
		last = val
#		print "TALKbutton changed"
		if val == 1 and recorded == True:
			print "need_to_launch_Alexa",need_to_launch_Alexa
			if need_to_launch_Alexa == True:
				rf = open(path+'audio/open_boswell.wav', 'w')
				need_to_launch_Alexa = False
				print "Changed need_to_launch_Alexa",need_to_launch_Alexa
			if need_to_launch_Alexa == False:
				rf = open(path+'audio/recording.wav', 'w')
			rf.write(audio)
			rf.close()
			inp = None
			alexa() # call Alexa with recording.wav
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

#   Check recordstartbutton button
# THB To Do: use recordstopbutton to end recording instead of releasing recordstartbutton
	valrecordstart = GPIO.input(recordstartbutton)
	if valrecordstart != lastvalrecordstart:
		lastvalrecordstart = valrecordstart
#       valrecordstart # changes to 0 when pressed down, 1 when released
		COLOR = (0,0,0) # black is default
		if valrecordstart == 0:
			# Draw a red circle
			COLOR  = (  255,   0, 0) # Red circle
		pos = (290,30)
		pygame.draw.circle(screen, COLOR, pos, 20, 0)
		pygame.display.update()
		if valrecordstart == 1:
			screen.fill( (0,0,0) )
			pygame.display.update()
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

	quit_state = GPIO.input(quit_button)
	if quit_state == False:
		pygame.quit()
		sys.exit(0)
	if change_question == True:
		change_question = False
		current_question = current_question + 1
		if current_question > max_question:
			current_question = 1

		imgSurf = pygame.image.load (img_names[current_question-1]) # load the appropriate image
		pygame.mixer.music.load(sound_names[current_question-1]) # load the question audio

		screen = pygame.display.set_mode ( imgSurf.get_size(), pygame.FULLSCREEN )
		screen.blit ( imgSurf, ( 0, 0 ) )
		pygame.display.flip()
		pygame.display.update()

		pygame.mixer.music.play()
		while pygame.mixer.music.get_busy() == True:
			continue
	for event in pygame.event.get():
		if event.type == pygame.MOUSEBUTTONDOWN and change_question == False:
			change_question = True
