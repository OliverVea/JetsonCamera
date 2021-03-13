from event import Event

import Jetson.GPIO as gpio
from threading import Thread
import time

class Switch:
    EVENT_INITIALIZED = Event.get_event_code('Switch Initialized', verbose=False)
    EVENT_STARTED = Event.get_event_code('Switch Started', verbose=False)
    EVENT_STOPPED = Event.get_event_code('Switch Stopped', verbose=False)
    EVENT_CHANGED = Event.get_event_code('Switch Changed', verbose=True)
    EVENT_ON = Event.get_event_code('Switch On', verbose=False)
    EVENT_OFF = Event.get_event_code('Switch Off', verbose=False)

    def __init__(self, pin_number, pin_cleanup: int = 1, sample_frequency: float = 50, debounce_delay: float = 0.05):
        self.pin = pin_number
        self.cleanup = pin_cleanup
        self.sample_period = 1 / sample_frequency
        self.delay = debounce_delay

        self.run = False
        self.state = -1
        self.thread = None

        Event.dispatch(Switch.EVENT_INITIALIZED, pin=pin_number, caller=self)

    def __del__(self):
        if self.cleanup >= 1:
            gpio.cleanup(self.pin)

    def _update(self, state):
        if state != self.state:
            Event.dispatch(Switch.EVENT_CHANGED, state=state, previous_state=self.state, caller=self)

            self.state = state

            if state:
                Event.dispatch(Switch.EVENT_ON, caller=self)
            else:
                Event.dispatch(Switch.EVENT_OFF, caller=self)

            if self.delay > 0:
                time.sleep(self.delay)

    def _task(self):
        while self.run:
            state = gpio.input(self.pin)
            self._update(state)
            time.sleep(self.sample_period)

    def is_running(self):
        return self.thread != None

    def start(self):
        if self.is_running():
            print(f'Could not start Switch thread (pin {self.pin}) as it is already running.')
            return

        gpio.setup(self.pin, gpio.IN)
        
        self.run = True
        self.thread = Thread(target=Switch._task, args=(self,))
        self.thread.start()

        Event.dispatch(Switch.EVENT_STARTED, caller=self)

        state = gpio.input(self.pin)
        self._update(state)


    def stop(self):
        if not self.is_running():
            print(f'Could not stop Switch thread (pin {self.pin}) as it is not running.')
            return

        self.run = False
        self.thread.join()
        self.thread = None

        if self.cleanup >= 2:
            gpio.cleanup(self.pin)
        
        Event.dispatch(Switch.EVENT_STOPPED, caller=self)

        self.state = -1


if __name__ == '__main__':
    from led import LED, Pattern

    gpio.cleanup()
    gpio.setmode(gpio.BOARD)

    led = LED(11, initial_pattern=Pattern.OFF)
    led.start()

    def handler_on(event, args):
        global led
        led.pattern = Pattern.ON

    def handler_off(event, args):
        global led
        led.pattern = Pattern.OFF

    Event.register(Switch.EVENT_ON, handler_on)
    Event.register(Switch.EVENT_OFF, handler_off)

    switch = Switch(7)
    switch.start()
    
    input()

    switch.stop()
    led.stop()