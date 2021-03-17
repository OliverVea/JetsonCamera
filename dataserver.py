from event import Event
from task import Task

from led import LED
from switch import Switch
from video import Video
from webserver import WebServer

from threading import Thread
import socket
import json

# DO this with websockets instead OOOOO DUMBFUUUUUUCK

class DataServer(Task):
    EVENT_INITIALIZED = Event.get_event_code('Dataserver Initialized', verbose=False)
    EVENT_STARTED = Event.get_event_code('Dataserver Started', verbose=False)
    EVENT_STOPPED = Event.get_event_code('Dataserver Stopped', verbose=False)

    def __init__(self, host: str = '', port: int = 8001):
        self.host = host
        self.port = 8001

        self.thread = None
        self.connections = {}

        Event.register(Switch.EVENT_CHANGED, lambda event, args: self._send_update({'key': event, 'pin': args['caller'].pin}))

    def _get_update(self):
        pass

    def _send_update(self, update):
        m = json.dumps(update)

        for addr in self.connections:
            for conn in self.connections[addr]:
                try:
                    conn.send(m)
                except Exception as e:
                    self.connections[addr] = [c for c in self.connections[addr] if c != conn]
                    if len(self.connections[addr]) == 0:
                        del self.connections[addr]
            
        pass

    def _task(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()

            conn, addr = s.accept()

            self.connections.setdefault(addr, []).append(conn)

    def start(self):
        self._start()
        
    def stop(self):
        self._stop()