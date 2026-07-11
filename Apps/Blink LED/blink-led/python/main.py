# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time

led_state = False
i = 0

def loop():
    global led_state, i
    time.sleep(0.1)
    led_state = not led_state
    i += 1
    print("state: ", led_state,"          counter: ", i);
    Bridge.call("set_led_state", led_state)

App.run(user_loop=loop)