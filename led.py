from event import Event

import Jetson.GPIO as gpio
from threading import Thread
import time
import math

class Pattern:
    OFF = [(0.0, 1.0)]
    ON  = [(1.0, 1.0)]

    BLINK = [(1.0, 0.2), (0.0, 1.0)]
    PULSE = [(1.0, 1.0), (0.0, 1.0)]  

    def rising(steps):
        return [(i / (steps - 1), 1) for i in range(steps)]

class LED:
    EVENT_INITIALIZED = Event.get_event_code('LED Initialized', verbose=False)
    EVENT_STARTED = Event.get_event_code('LED Started', verbose=False)
    EVENT_STOPPED = Event.get_event_code('LED Stopped', verbose=False)

    # pin cleanup: 0 - never, 1 - when deleted, 2 - when deleted and when stop() is called.
    # pattern_step is time between steps (with scalar 1.0) in seconds.
    def __init__(self, pin_number, initial_pattern: Pattern = Pattern.OFF, pattern_step: float = 0.5, pin_cleanup: int = 0, pwm_frequency: int = 100):
        self.pin = pin_number
        self.pattern = initial_pattern
        self.t = pattern_step
        self.cleanup = pin_cleanup

        self.period = -1
        if pwm_frequency > 0:
            self.period = 1 / pwm_frequency

        self.thread = None
        self.run = False

        Event.dispatch(LED.EVENT_INITIALIZED, pin=pin_number, caller=self)

    def __del__(self):
        if self.cleanup >= 1:
            gpio.cleanup(self.pin)

    def _output(self, state):
        if self.state != state:
            gpio.output(self.pin, state)
            self.state = state

    def _task(self):
        while True:
            for duty_cycle, time_scalar in self.pattern:
                # PWM
                if self.period != -1 and duty_cycle != 0.0 and duty_cycle != 1.0:
                    duty_cycle = (10 ** duty_cycle - 1) / 9

                    current_time = 0
                    while current_time < time_scalar * self.t:
                        # Off period
                        t = (1 - duty_cycle) * self.period

                        if t > 0:
                            self._output(gpio.LOW)
                            time.sleep(t)

                        # On period
                        t = duty_cycle * self.period

                        if t > 0:
                            self._output(gpio.HIGH)
                            time.sleep(t)

                        current_time += self.period

                # No PWM
                else:
                    if duty_cycle >= 0.5:
                            self._output(gpio.HIGH)
                    else:
                            self._output(gpio.LOW)
                    time.sleep(time_scalar * self.t)

                if not self.run:
                    return

    def is_running(self):
        return self.thread != None

    def start(self):
        if self.is_running():
            print(f'Could not start LED thread (pin {self.pin}) as it is already running.')
            return

        gpio.setup(self.pin, gpio.OUT)

        self.state = -1
        self.run = True
        self.thread = Thread(target=LED._task, args=(self,))
        self.thread.start()

        Event.dispatch(LED.EVENT_STARTED, caller=self)

    def stop(self):
        if not self.is_running():
            print(f'Could not stop LED thread (pin {self.pin}) as it is not running.')
            return

        self.run = False
        self.thread.join()
        self.thread = None
        self.state = -1

        if self.cleanup >= 2:
            gpio.cleanup(self.pin)

        Event.dispatch(LED.EVENT_STOPPED, caller=self)

# Demo:
if __name__ == '__main__':
    gpio.setmode(gpio.BOARD)

    leds = [
        LED(11, initial_pattern=Pattern.rising(4), pwm_frequency=100, pattern_step=0.25), 
        LED(15, initial_pattern=Pattern.ON, pwm_frequency=0, pattern_step=1),
    ]

    for led in leds:
        led.start()

    input()

    for led in leds:
        led.stop()