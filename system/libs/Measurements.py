import time
import board
import busio
from math import sqrt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class Measure():
    def __init__(self) -> None:
        self.FACTOR = 10  # 100A => 10mA => 10V
        self.ERROR = 1.11
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        # Create the ADC object using the I2C bus
        ads = ADS.ADS1115(i2c)
        # Create differential input between channel 0 and 1
        self.chan = AnalogIn(ads, ADS.P0, ADS.P1)

    def milli(self):
        return round(time.time() * 1000)

    def get(self, interval):
        peak_voltage = 0
        t = self.milli()
        while(self.milli() - t < interval):
            voltage = self.chan.voltage
            if voltage > peak_voltage:
                peak_voltage = voltage

        # Coverts voltage to current
        return peak_voltage * self.FACTOR * self.ERROR

