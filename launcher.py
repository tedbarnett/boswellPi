import RPi.GPIO as GPIO
import time
import sys
import subprocess, os
import signal
import pygame
from pygame.locals import *

pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag

os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
os.environ["SDL_MOUSEDRV"] = "TSLIB"

pygame.init()  #initialize pygame
pygame.display.init()
GPIO.setmode(GPIO.BCM)

# set up buttons to monitor (compare to boswell.py though!)
quit_button = 17
current_question = 0
change_question = False
GPIO.setup(quit_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up all questions
img_names = []
sound_names = []
qcodes = []

img_names.append("images/john_quinn.png")
sound_names.append("audio/alexa-please_tell_me_about.ogg")
qcodes.append("jquinn1961")

img_names.append("images/judy_wedding_photo.png")
sound_names.append("audio/silence.ogg")
qcodes.append("judywed1961")

img_names.append("images/question01.png")
sound_names.append("audio/willa_question01.ogg")
qcodes.append("worldchange")

img_names.append("images/question03.png")
sound_names.append("audio/silence.ogg")
qcodes.append("neighborhood")

img_names.append("images/question04.png")
sound_names.append("audio/alexa-earliestmemory.ogg")
qcodes.append("earliestmemory")

img_names.append("images/question05.png")
sound_names.append("audio/alexa-bestfriend.ogg")
qcodes.append("bestfriend")

max_question = len(img_names)
print "max_question = " , max_question


# Display logo screen
imgSurf = pygame.image.load ('images/boswell_startup_screen.png')
pygame.mixer.music.load("audio/silence.ogg")
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode ( imgSurf.get_size(), pygame.FULLSCREEN )
screen.blit ( imgSurf, ( 0, 0 ) )
pygame.display.flip()
pygame.mixer.music.play()

rpistr = "sudo python boswell.py"
p=subprocess.Popen(rpistr,shell=True, preexec_fn=os.setsid)

while pygame.mixer.music.get_busy() == True:
	continue

while True:
	quit_state = GPIO.input(quit_button)
	if quit_state == False:
		os.killpg(p.pid, signal.SIGTERM)
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
		if event.type == pygame.MOUSEBUTTONDOWN:
#			pos = (pygame.mouse.get_pos() [0], pygame.mouse.get_pos() [1])
			change_question = True
