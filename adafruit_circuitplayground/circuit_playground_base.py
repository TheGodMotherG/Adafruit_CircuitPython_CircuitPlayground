# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
# Copyright (c) 2017-2019 Kattni Rembor for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# We have a lot of attributes for this complex library.
# pylint: disable=too-many-instance-attributes

"""
`adafruit_circuitplayground.circuit_playground_base`
====================================================

CircuitPython base class for Circuit Playground.

* `Circuit Playground Express <https://www.adafruit.com/product/3333>`_
* `Circuit Playground Bluefruit <https://www.adafruit.com/product/4333>`_.

* Author(s): Kattni Rembor, Scott Shawcroft
"""

import adafruit_lis3dh
import adafruit_thermistor
import analogio
import board
import busio
import digitalio
import neopixel
import touchio
import gamepad


__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CircuitPlayground.git"


class Photocell:
    """Simple driver for analog photocell on the Circuit Playground Express and Bluefruit."""
    # pylint: disable=too-few-public-methods
    def __init__(self, pin):
        self._photocell = analogio.AnalogIn(pin)

    # TODO(tannewt): Calibrate this against another calibrated sensor.
    @property
    def light(self):
        """Light level."""
        return self._photocell.value * 330 // (2 ** 16)


class CircuitPlaygroundBase:     # pylint: disable=too-many-public-methods
    """Circuit Playground base class."""
    def __init__(self):
        self._a = digitalio.DigitalInOut(board.BUTTON_A)
        self._a.switch_to_input(pull=digitalio.Pull.DOWN)
        self._b = digitalio.DigitalInOut(board.BUTTON_B)
        self._b.switch_to_input(pull=digitalio.Pull.DOWN)
        self.gamepad = gamepad.GamePad(self._a, self._b)

        # Define switch:
        self._switch = digitalio.DigitalInOut(board.SLIDE_SWITCH)
        self._switch.switch_to_input(pull=digitalio.Pull.UP)

        # Define LEDs:
        self._led = digitalio.DigitalInOut(board.D13)
        self._led.switch_to_output()
        self._pixels = neopixel.NeoPixel(board.NEOPIXEL, 10)

        # Define sensors:
        self._temp = adafruit_thermistor.Thermistor(board.TEMPERATURE, 10000, 10000, 25, 3950)
        self._light = Photocell(board.LIGHT)

        # Define touch:
        # Initially, self._touches stores the pin used for a particular touch. When that touch is
        # used for the first time, the pin is replaced with the corresponding TouchIn object.
        # This saves a little RAM over using a separate read-only pin tuple.
        # For example, after `cpx.touch_A2`, self._touches is equivalent to:
        # [None, board.A1, touchio.TouchIn(board.A2), board.A3, ...]
        # Slot 0 is not used (A0 is not allowed as a touch pin).
        self._touches = [None, board.A1, board.A2, board.A3, board.A4, board.A5, board.A6, board.TX]
        self._touch_threshold_adjustment = 0

        # Define acceleration:
        self._i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
        self._int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        self._lis3dh = adafruit_lis3dh.LIS3DH_I2C(self._i2c, address=0x19, int1=self._int1)
        self._lis3dh.range = adafruit_lis3dh.RANGE_8_G

        # Initialise tap:
        self._detect_taps = 1
        self.detect_taps = 1

    @property
    def detect_taps(self):
        """Configure what type of tap is detected by ``cpx.tapped``. Use ``1`` for single-tap
        detection and ``2`` for double-tap detection. This does nothing without ``cpx.tapped``.

        .. image :: ../docs/_static/accelerometer.jpg
          :alt: Accelerometer

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          cpx.detect_taps = 1
          while True:
            if cpx.tapped:
              print("Single tap detected!")

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          cpb.detect_taps = 1
          while True:
            if cpb.tapped:
              print("Single tap detected!")
        """
        return self._detect_taps

    @detect_taps.setter
    def detect_taps(self, value):
        self._detect_taps = value
        if value == 1:
            self._lis3dh.set_tap(value, 90, time_limit=4, time_latency=50, time_window=255)
        if value == 2:
            self._lis3dh.set_tap(value, 60, time_limit=10, time_latency=50, time_window=255)

    @property
    def tapped(self):
        """True once after a detecting a tap. Requires ``cpx.detect_taps``.

        .. image :: ../docs/_static/accelerometer.jpg
          :alt: Accelerometer

        Tap the Circuit Playground once for a single-tap, or quickly tap twice for a double-tap.

        To use with Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          cpx.detect_taps = 1

          while True:
              if cpx.tapped:
                  print("Single tap detected!")

        To use with Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          cpb.detect_taps = 1

          while True:
              if cpb.tapped:
                  print("Single tap detected!")

        To use single and double tap together, you must have a delay between them. It
        will not function properly without it. This example uses both by counting a
        specified number of each type of tap before moving on in the code.

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          # Set to check for single-taps.
          cpx.detect_taps = 1
          tap_count = 0

          # We're looking for 2 single-taps before moving on.
          while tap_count < 2:
              if cpx.tapped:
                  tap_count += 1
          print("Reached 2 single-taps!")

          # Now switch to checking for double-taps
          tap_count = 0
          cpx.detect_taps = 2

          # We're looking for 2 double-taps before moving on.
          while tap_count < 2:
              if cpx.tapped:
                 tap_count += 1
          print("Reached 2 double-taps!")
          print("Done.")

        """
        return self._lis3dh.tapped

    @property
    def acceleration(self):
        """Obtain data from the x, y and z axes.

        .. image :: ../docs/_static/accelerometer.jpg
          :alt: Accelerometer

        This example prints the values. Try moving the board to see how the
        printed values change.

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              x, y, z = cpx.acceleration
              print(x, y, z)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              x, y, z = cpb.acceleration
              print(x, y, z)
        """
        return self._lis3dh.acceleration

    def shake(self, shake_threshold=30):
        """Detect when device is shaken.

        :param int shake_threshold: The threshold shake must exceed to return true (Default: 30)

        .. image :: ../docs/_static/accelerometer.jpg
          :alt: Accelerometer

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.shake():
                  print("Shake detected!")

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.shake():
                  print("Shake detected!")

        Decreasing ``shake_threshold`` increases shake sensitivity, i.e. the code
        will return a shake detected more easily with a lower ``shake_threshold``.
        Increasing it causes the opposite. ``shake_threshold`` requires a minimum
        value of 10 - 10 is the value when the board is not moving, therefore
        anything less than 10 will erroneously report a constant shake detected.

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.shake(shake_threshold=20):
                  print("Shake detected more easily than before!")
        """
        return self._lis3dh.shake(shake_threshold=shake_threshold)

    def _touch(self, i):
        if not isinstance(self._touches[i], touchio.TouchIn):
            # First time referenced. Get the pin from the slot for this touch
            # and replace it with a TouchIn object for the pin.
            self._touches[i] = touchio.TouchIn(self._touches[i])
            self._touches[i].threshold += self._touch_threshold_adjustment
        return self._touches[i].value

    # We chose these verbose touch_A# names so that beginners could use it without understanding
    # lists and the capital A to match the pin name. The capitalization is not strictly Python
    # style, so everywhere we use these names, we whitelist the errors using:
    @property
    def touch_A1(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A1.

        .. image :: ../docs/_static/capacitive_touch_pad_A1.jpg
          :alt: Capacitive touch pad A1

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A1:
                  print('Touched pad A1')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A1:
                  print('Touched pad A1')
        """
        return self._touch(1)

    @property
    def touch_A2(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A2.

        .. image :: ../docs/_static/capacitive_touch_pad_A2.jpg
          :alt: Capacitive touch pad A2

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A2:
                  print('Touched pad A2')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A2:
                  print('Touched pad A2')
        """
        return self._touch(2)

    @property
    def touch_A3(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A3.

        .. image :: ../docs/_static/capacitive_touch_pad_A3.jpg
          :alt: Capacitive touch pad A3

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A3:
                  print('Touched pad A3')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A3:
                  print('Touched pad A3')
        """
        return self._touch(3)

    @property
    def touch_A4(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A4.

        .. image :: ../docs/_static/capacitive_touch_pad_A4.jpg
          :alt: Capacitive touch pad A4

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A4:
                  print('Touched pad A4')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A4:
                  print('Touched pad A4')
        """
        return self._touch(4)

    @property
    def touch_A5(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A5.

        .. image :: ../docs/_static/capacitive_touch_pad_A5.jpg
          :alt: Capacitive touch pad A5

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A5:
                  print('Touched pad A5')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A5:
                  print('Touched pad A5')
        """
        return self._touch(5)

    @property
    def touch_A6(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad A6.

        .. image :: ../docs/_static/capacitive_touch_pad_A6.jpg
          :alt: Capacitive touch pad A6

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A6:
                  print('Touched pad A6')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_A6:
                  print('Touched pad A6')
        """
        return self._touch(6)

    @property
    def touch_TX(self):  # pylint: disable=invalid-name
        """Detect touch on capacitive touch pad TX (also known as A7 on the Circuit Playground
        Express) Note: can be called as ``touch_A7`` on Circuit Playground Express.

        .. image :: ../docs/_static/capacitive_touch_pad_A7.jpg
          :alt: Capacitive touch pad TX

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.touch_A7:
                  print('Touched pad A7')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.touch_TX:
                  print('Touched pad TX')
        """
        return self._touch(7)

    def adjust_touch_threshold(self, adjustment):
        """Adjust the threshold needed to activate the capacitive touch pads.
        Higher numbers make the touch pads less sensitive.

        :param int adjustment: The desired threshold increase

        .. image :: ../docs/_static/capacitive_touch_pads.jpg
          :alt: Capacitive touch pads

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          cpx.adjust_touch_threshold(200)

          while True:
              if cpx.touch_A1:
                  print('Touched pad A1')

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          cpb.adjust_touch_threshold(200)

          while True:
              if cpb.touch_A1:
                  print('Touched pad A1')
        """
        for touch_in in self._touches:
            if isinstance(touch_in, touchio.TouchIn):
                touch_in.threshold += adjustment
        self._touch_threshold_adjustment += adjustment

    @property
    def pixels(self):
        """Sequence-like object representing the ten NeoPixels around the outside
        of the Circuit Playground. Each pixel is at a certain index in the sequence
        as labeled below. Colors can be RGB hex like 0x110000 for red where each
        two digits are a color (0xRRGGBB) or a tuple like (17, 0, 0) where (R, G, B).
        Set the global brightness using any number from 0 to 1 to represent a
        percentage, i.e. 0.3 sets global brightness to 30%.

        See `neopixel.NeoPixel` for more info.

        .. image :: ../docs/_static/neopixel_numbering.jpg
          :alt: NeoPixel order diagram

        Here is an example that sets the first pixel green and the ninth red.

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          cpx.pixels.brightness = 0.3
          cpx.pixels[0] = 0x003000
          cpx.pixels[9] = (30, 0, 0)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          cpb.pixels.brightness = 0.3
          cpb.pixels[0] = 0x003000
          cpb.pixels[9] = (30, 0, 0)

        """
        return self._pixels

    @property
    def button_a(self):
        """``True`` when Button A is pressed. ``False`` if not.

        .. image :: ../docs/_static/button_a.jpg
          :alt: Button A

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.button_a:
                  print("Button A pressed!")

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.button_a:
                  print("Button A pressed!")
        """
        return self._a.value

    @property
    def button_b(self):
        """``True`` when Button B is pressed. ``False`` if not.

        .. image :: ../docs/_static/button_b.jpg
          :alt: Button B

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              if cpx.button_b:
                  print("Button B pressed!")

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              if cpb.button_b:
                  print("Button B pressed!")
        """
        return self._b.value

    @property
    def were_pressed(self):
        """Returns a set of the buttons that have been pressed

        .. image :: ../docs/_static/button_b.jpg
          :alt: Button B

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx

          while True:
              print(cpx.were_pressed)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb

          while True:
              print(cpb.were_pressed)
        """
        ret = set()
        pressed = self.gamepad.get_pressed()
        for button, mask in (('A', 0x01), ('B', 0x02)):
            if mask & pressed:
                ret.add(button)
        return ret

    @property
    def switch(self):
        """``True`` when the switch is to the left next to the music notes.
        ``False`` when it is to the right towards the ear.

        .. image :: ../docs/_static/slide_switch.jpg
          :alt: Slide switch

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx
         import time

          while True:
              print("Slide switch:", cpx.switch)
              time.sleep(1)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb
          import time

          while True:
              print("Slide switch:", cpb.switch)
              time.sleep(1)
        """
        return self._switch.value

    @property
    def temperature(self):
        """The temperature in Celsius.

        .. image :: ../docs/_static/thermistor.jpg
          :alt: Temperature sensor

        Converting this to Fahrenheit is easy!

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx
          import time

          while True:
              temperature_c = cpx.temperature
              temperature_f = temperature_c * 1.8 + 32
              print("Temperature celsius:", temperature_c)
              print("Temperature fahrenheit:", temperature_f)
              time.sleep(1)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb
          import time

          while True:
              temperature_c = cpb.temperature
              temperature_f = temperature_c * 1.8 + 32
              print("Temperature celsius:", temperature_c)
              print("Temperature fahrenheit:", temperature_f)
              time.sleep(1)
        """
        return self._temp.temperature

    @property
    def light(self):
        """The light level.

        .. image :: ../docs/_static/light_sensor.jpg
          :alt: Light sensor

        Try covering the sensor next to the eye to see it change.

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx
          import time

          while True:
              print("Light:", cpx.light)
              time.sleep(1)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb
          import time

          while True:
              print("Light:", cpb.light)
              time.sleep(1)
        """
        return self._light.light

    @property
    def red_led(self):
        """The red led next to the USB plug marked D13.

        .. image :: ../docs/_static/red_led.jpg
          :alt: D13 LED

        To use with the Circuit Playground Express:

        .. code-block:: python

          from adafruit_circuitplayground.express import cpx
          import time

          while True:
              cpx.red_led = True
              time.sleep(1)
              cpx.red_led = False
              time.sleep(1)

        To use with the Circuit Playground Bluefruit:

        .. code-block:: python

          from adafruit_circuitplayground.bluefruit import cpb
          import time

          while True:
              cpb.red_led = True
              time.sleep(1)
              cpb.red_led = False
              time.sleep(1)
        """
        return self._led.value

    @red_led.setter
    def red_led(self, value):
        self._led.value = value