from event import Event
from pipeline import Pipeline

import time
import os

from threading import Thread
from datetime import datetime
import cv2
from PIL import Image

class Video:
    EVENT_INITIALIZED = Event.get_event_code('Video Initialized', verbose=False)
    EVENT_STARTED = Event.get_event_code('Video Started', verbose=False)
    EVENT_STOPPED = Event.get_event_code('Video Stopped', verbose=False)
    EVENT_NEW_FRAME = Event.get_event_code('New Video Frame', verbose=False)

    def __init__(self, recording_size: tuple = None, display_size: tuple = None):
        self.recording_size = recording_size
        self.display_size = display_size
        self.thread = None

        Event.dispatch(Video.EVENT_INITIALIZED, caller=self)

    def _task(self):
        vc = cv2.VideoCapture(self.pipeline.get_string(), cv2.CAP_GSTREAMER)

        print('displaying:', self.pipeline.displaying)

        if self.pipeline.displaying:

            then = time.time()
            fps = 21

            font                   = cv2.FONT_HERSHEY_SIMPLEX
            bottomLeftCornerOfText = (2, 14)
            fontScale              = 0.5
            fontColor              = (255,255,255)
            lineType               = 2

        while self.running:
            if self.pipeline.displaying:
                ret_val, img = vc.read()

                Event.dispatch(Video.EVENT_NEW_FRAME, caller=self, ret_val=ret_val, img=img)
            
                now = time.time()
                fps = fps * 0.95 + 0.05 * 1 / (now - then)
                then = now
            else:
                time.sleep(1)
        
        vc.release()
        cv2.destroyAllWindows()

    def is_running(self):
        return self.thread != None

    def start(self, filename: str = None):    
        if self.is_running():
            print('Video is already being recorded.')
            return

        if filename == None:
            date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'/home/oliver/Desktop/JetsonCamera/videos/{date}.yuv'

        self.filename = filename
        self.pipeline = Pipeline(filename=self.filename, display_size=self.display_size, recording_size=self.recording_size)
        self.running = True

        self.thread = Thread(target=Video._task, args=(self,))
        self.thread.start()

        Event.dispatch(Video.EVENT_STARTED, caller=self)

    def stop(self):
        if not self.is_running():
            print(f'Video is already not being recorded.')
            return

        self.running = False

        self.thread.join()
        self.thread = None

        Event.dispatch(Video.EVENT_STOPPED, caller=self, filename=self.filename)