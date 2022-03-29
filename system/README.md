## Configuration 
* Use Raspberry Pi OS with desktop (Debian version: 11 (bullseye) or newer) 
* Enable the I2C interface on the Raspberry Pi using `raspi-config`
* Install the following libraries:
    ```
    $ sudo pip install adafruit-circuitpython-ads1x15
    $ pip install python-socketio
    ```

### Connect the ADC to the Pi as follows:
* ADS1x15 VDD to Raspberry Pi 3.3V
* ADS1x15 GND to Raspberry Pi GND
* ADS1x15 SCL to Raspberry Pi SCL
* ADS1x15 SDA to Raspberry Pi SDA
