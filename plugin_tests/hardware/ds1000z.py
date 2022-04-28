from autopilot.hardware import Hardware
from ds1054z import DS1054Z as DS1054Z_

class SCPI(Hardware):
    """Metaclass for SCPI-based hardware devices"""


class DS1054Z(SCPI):
    """
    The `Rigol DS1054 Oscilloscope <https://www.rigolna.com/products/digital-oscilloscopes/1000z/`_

    See the `Wiki page <https://wiki.auto-pi-lot.com/index.php/Rigol_DS1054Z>`_ for more information
    """

    def __init__(self, ip:str, **kwargs):
        super(DS1054Z, self).__init__(**kwargs)

        self.ip = ip
        self.scope = DS1054Z_(self.ip)

    def __getattr__(self, item:str):
        """If we don't have the method in this class, try and use the device's methods"""
        return getattr(self.scope, item)