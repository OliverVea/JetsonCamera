from datetime import datetime

from subprocess import Popen, PIPE, signal

import os

import time

def get_command(filename, width=int(3264/4), height=int(2464/4), record_type='videos'):
  # Video
  filename = filename.replace('_TYPE_', record_type)

  if record_type == 'videos':
    command = f"gst-launch-1.0 --verbose nvarguscamerasrc ! \
    'video/x-raw(memory:NVMM), width=(int)3264, height=(int)2464, format=(string)NV12, framerate=(fraction)21/1' ! \
    nvvidconv ! \
    'video/x-raw, width=(int){width}, height=(int){height}, format=(string)I420' ! \
    y4menc ! \
    filesink location={filename}.yuv -e"

  # Image Sequence
  if record_type == 'images':
    command = f"gst-launch-1.0 --verbose nvarguscamerasrc ! \
    'video/x-raw(memory:NVMM), width=(int)3264, height=(int)2464, format=(string)NV12, framerate=(fraction)21/1' ! \
    nvvidconv ! \
    'video/x-raw, width=(int){width}, height=(int){height}, format=(string)RGBA' ! \
    pngenc ! \
    multifilesink location='{filename}_%05d.png'"

  return command

class CameraProcess:
  def __init__(self, filename: str = None):
    if filename == None:
      date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
      filename = f'/home/oliver/Desktop/camera_capture/_TYPE_/{date}'

    self.filename = filename
    self.popen = None

  def _terminate(self):
    print('[Class] Trying to terminate.')
    if self.popen != None:
      pid = self.popen.pid
      gpid = os.getpgid(pid)
      os.killpg(gpid, signal.SIGINT)
      print(f'[Class] Sending SIGINT to process: pid - {pid}, gpid - {gpid}.')
    else:
      print('[Class] Process is None.')

  def start(self):
    self._terminate()
    self.logfile = open('/home/oliver/Desktop/camera_capture/python_application/log.txt', 'w')

    cmd = get_command(self.filename)

    print(f'[Class] Starting recording. Filename: {self.filename}')

    print(f'[Class] Command:', cmd)

    self.popen = Popen(cmd, universal_newlines=True, stdout=self.logfile, stderr=self.logfile, shell=True, preexec_fn=os.setsid)

  def stop(self):
    self._terminate()
    self.popen = None
    self.logfile.close()
    print(f'[Class] Stopped recording.')

class CameraProcessOCV:
  def _get_pipeline(self, width, height, framerate : int = 21):
    s = (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            0,
            3264,
            2464,
            21,
            width,
            height,
        )
    )
    s = f"nvarguscamerasrc ! \
    video/x-raw(memory:NVMM), width=(int)3264, height=(int)2464, format=(string)NV12, framerate=(fraction){int(framerate)}/1 ! \
    nvvidconv ! video/x-raw, width=(int){int(width)}, height=(int){int(height)}, format=(string)BGRx ! videoconvert ! appsink"
    return s

  def __init__(self, width = int(3264/4), height = int(2464/4)):  
    self.height = height
    self.width = width
    self.vc = None

  def is_running(self):
    return self.vc != None and self.vc.isOpened()

  def start(self):
    if self.is_running():
      print('Video is already being recorded.')
      return True

    try:
      pipeline = self._get_pipeline(self.width, self.height)
      self.vc = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
      time.sleep(0.5)

    except RuntimeError as e:
      print(f'Could not establish camera connection: \'{e}\'')
      return False

    return self.is_running()

  def read(self):
    if not self.is_running():
      return None

    rval, img = self.vc.read()

    if rval == False:
      return None

    return img

  def stop(self):
    if not self.is_running():
      print(f'Video is already not being recorded.')
      return

    if self.is_running():
      self.vc.release()
      self.vc = None
