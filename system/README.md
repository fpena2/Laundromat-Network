## Configuration 

* Enable the I2C interface on the Raspberry Pi using `raspi-config`
* Install the ADC library:
    ```
    $ pip3 install ADS1115==0.2.1
    ```

### Connect the ADC to the Pi as follows:
* ADS1x15 VDD to Raspberry Pi 3.3V
* ADS1x15 GND to Raspberry Pi GND
* ADS1x15 SCL to Raspberry Pi SCL
* ADS1x15 SDA to Raspberry Pi SDA
