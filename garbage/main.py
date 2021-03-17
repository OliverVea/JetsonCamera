import Jetson.GPIO as gpio

import time
from threading import Thread

from camera_process import CameraProcess, CameraProcessOCV

from subprocess import Popen
import os
from datetime import datetime

import cv2

##############
# SETUP CODE #
##############

gpio.setmode(gpio.BCM)

pin_s = 24
pin_r = 23
pin_g = 18

T_THRESH = 2

gpio.setup(pin_s, gpio.IN)
gpio.setup(pin_r, gpio.OUT)
gpio.setup(pin_g, gpio.OUT)

recording = False
process = None
  
start_time = time.time()

pattern = {pin_r: 'off', pin_g: 'short_blink'}

#                 h              w
frame_size = (int(2464/4), int(3264/4))
height, width = frame_size

def send_event(code):
  print(f'[Event] {code} ({len(event_callbacks[code])})')
  for event in event_callbacks[code]:
    event()

#############
# TASK CODE #
#############

camera = CameraProcessOCV(width=width, height=height)

vw = None
run_camera = True
recording = False
def task_camera():
  global camera, run_camera, recording, pattern

  while run_camera:
    if recording:
      if not camera.is_running():
        pattern[pin_r] = 'short_blink'
        time.sleep(0.1)
        continue

      pattern[pin_r] = 'on' 
      img = camera.read()

      if img == None:
        stop_recording()

      if vw != None:
        vw.write(img)

    else:
      pattern[pin_r] = 'off'
      time.sleep(0.1)

def start_recording():
  global camera, recording, vw

  date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
  filename = f'/home/oliver/Desktop/camera_capture/videos/{date}.avi'

  if not camera.is_running():
    camera.start()

  recording = camera.is_running()

  if recording and vw == None:
    fourcc = cv2.VideoWriter.fourcc('M', 'J', 'P', 'G')
    vw = cv2.VideoWriter(filename, apiPreference=cv2.CAP_GSTREAMER, fourcc=fourcc, fps=21, frameSize=frame_size)

def stop_recording():
  global camera, recording, vw

  if camera.is_running():
    camera.stop()

  if vw != None:
    vw.release()
    vw = None

  recording = False

run_led = {pin_r: True, pin_g: True}
def task_led(led):
  global run_led, pattern
  patterns = {'short_blink': [0.05, 0.45], 'on': [0.2, 0], 'off': [0, 0.2], 'fast_blink': [0.2, 0.2]}

  while run_led[led]:
    if not pattern[led] in patterns:
      pattern[led] = 'short_blink'

    if patterns[pattern[led]][0] > 0:
      gpio.output(led, gpio.HIGH)
      time.sleep(patterns[pattern[led]][0])
      
    if patterns[pattern[led]][1] > 0:
      gpio.output(led, gpio.LOW)
      time.sleep(patterns[pattern[led]][1])

run_task_button = True
event_callbacks = {'down': [start_recording], 'long': [], 'up': [stop_recording], 'press': []}
def task_button():
  state = 'neutral'
  t0 = time.time()

  while True:
    button_state = gpio.input(pin_s)

    if state == 'neutral':
      if button_state:
        t0 = time.time()
        send_event('down')

        state = 'engaged'
        print('[State] button_state: neutral -> engaged')

    if state == 'engaged':
      if time.time() - t0 > T_THRESH:
        send_event('long')

        print('[State] button_state: engaged -> down')
        state = 'down'

      elif not button_state:
        send_event('press')

        print('[State] button_state: engaged -> neutral')
        state = 'neutral'

    if state == 'down':
      if not button_state:
        send_event('up')

        print('[State] button_state: down -> neutral')
        state = 'neutral'
  
    time.sleep(0.05)

##################
# STARTING TASKS #
##################

threads = [Thread(target=task_led, args=(pin_g,)), Thread(target=task_led, args=(pin_r,)), Thread(target=task_button, args=())]

for thread in threads:
  thread.start()

for thread in threads:
  thread.join()
