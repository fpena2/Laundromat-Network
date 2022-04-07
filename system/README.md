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

## Running 
The main application can be run with the following command: 
```
$ python run.py 
```
* For offline mode use the ```-f``` flag
    * This mode will prevent the device from sending data to the server
* For development mode use the ```-d``` flag 
    * This mode will force the device to output data to a ```test.csv``` file

The multithread application can spawn 10 clones which send data via the HTTP interface with the following command: 
```
$ python clone.py --pool 10 --type 1
```
* Specify the number of clones with the ```--pool``` argument 
* Specify the type of communication with the ```--type``` argument 
    * HTTP: ```--type 1``` 
    * SOCKETS: ```--type 2```