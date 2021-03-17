from event import Event
from switch import Switch
from led import LED, Pattern
from video import Video
from webserver import WebServer
from dataserver import DataServer

import Jetson.GPIO as gpio

import time
import os

FRAME_SIZE = (3264, 2464)
FRAME_SIZE_2 = (FRAME_SIZE[0]/2, FRAME_SIZE[1]/2)
FRAME_SIZE_4 = (FRAME_SIZE[0]/4, FRAME_SIZE[1]/4)

#################
##    SETUP    ##
#################

gpio.cleanup()
gpio.setmode(gpio.BOARD)

s_record = Switch(35)

l_r = LED(23, color='red')
l_g = LED(21, color='green', initial_pattern=Pattern.BLINK)

#video = Video(display_size=FRAME_SIZE_4, recording_size=FRAME_SIZE_4)
webserver = WebServer()
dataserver = DataServer()

def start_video(event, args):
    if args['caller'] == s_record:
        l_r.pattern = Pattern.ON
        webserver.stop(block=True)
        webserver.start(recording_size=FRAME_SIZE_4)
        #video.start()

def stop_video(event, args):
    if args['caller'] == s_record:
        l_r.pattern = Pattern.OFF
        webserver.stop(block=True)
        webserver.start(recording_size=None)
        #video.stop()


Event.register(s_record.EVENT_ON, start_video)
Event.register(s_record.EVENT_OFF, stop_video)

dataserver.start()

#################
## START TASKS ##
#################

l_g.start()
l_r.start()

s_record.start()

i = None

while i != 'q':
    i = input("'q' to exit.")

#################
##   CLEANUP   ##
#################

webserver.stop()
dataserver.stop()
s_record.stop()
l_r.stop()
l_g.stop()