"""
Thin wrapper around GPIO Zero to match Autopilot's calling conventions
"""
import sys
import typing
from typing import Optional, Union, Tuple, List, Dict, Literal

from autopilot.hardware import Hardware
from gpiozero import DigitalOutputDevice

class Digital_Out_Zero(Hardware):
    """
    A trivial wrapper around :class:`gpiozero.OutputDevice` to use
    RPi.GPIO (and other backends).
    """

    def __init__(self, pin:int, polarity:int=1, zero_kwargs:Optional[dict]=None, **kwargs):
        self._device = None
        super(Digital_Out_Zero, self).__init__(**kwargs)

        if zero_kwargs is None:
            zero_kwargs = {}
        else:
            if 'active_high' in zero_kwargs:
                self.logger.warning("active_high passed in gpiozero kwargs as well as with the polarity argument, using active_high")
                polarity = zero_kwargs['active_high']

        self.pin = int(pin)
        self.polarity = polarity

        self._device = self._init_device(zero_kwargs)

    def _init_device(self, zero_kwargs:Optional[dict]=None) -> DigitalOutputDevice:
        if zero_kwargs is None:
            zero_kwargs = {}
        return DigitalOutputDevice(
            pin=f"BOARD{self.pin}",
            active_high=bool(self.polarity),
            **zero_kwargs
        )

    def set(self, value:bool):
        if value:
            self._device.on()
        else:
            self._device.off()

    def turn(self, direction:str):
        if isinstance(direction, str):
            direction = direction.lower()
        if direction in ('on', True, 1):
            self.set(True)
        elif direction in ('off', False, 0):
            self.set(False)
        else:
            raise ValueError(f"Not sure how to turn pin to direction {direction}")

    def __getattr__(self, item:str):
        """If we don't have the method in this class, try and use the device's methods"""
        return getattr(self._device, item)

    def release(self):
        self._device.close()





