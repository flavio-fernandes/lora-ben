# lora-ben

#### CircuitPython based project for reading distance sensor and advertise it via lora


This project uses [lora](https://learn.adafruit.com/radio-featherwing/circuitpython-for-rfm9x-lora) to periodically send
temperature and distance sensor values.
Since the unit will be kept outdoors, it has a Lithium Ion Polymer Battery with a solar panel. 
In order to conserve energy, it uses [deep sleep](https://learn.adafruit.com/deep-sleep-with-circuitpython) and a relay that
cuts power to the sensors while doing so.

Components on the **Sensor** side:
- [Large Ultrasonic (Sonar) Sensor with Horn and UART Output](https://www.adafruit.com/product/4664)
- [DS18B20 Digital temperature sensor](https://www.adafruit.com/product/374)
- [Adafruit LoRa Radio FeatherWing - RFM95W 900 MHz - RadioFruit](https://www.adafruit.com/product/3231)
- [Adafruit Universal USB / DC / Solar Lithium Ion/Polymer charger - bq24074](https://www.adafruit.com/product/4755)
- [6V 2W Solar Panel - ETFE - Voltaic P126](https://www.adafruit.com/product/5366)
- [3.8 / 1.3mm or 3.5 / 1.1mm to 5.5 / 2.1mm DC Jack Adapter Cable](https://www.adafruit.com/product/2788)
- [Lithium Ion Polymer Battery - 3.7v 2500mAh](https://www.adafruit.com/product/328)
- [Adafruit Non-Latching Mini Relay](https://www.adafruit.com/product/2895) **OR** [Low Signal Relay](https://www.mouser.com/ProductDetail/Panasonic-Industrial-Devices/HY1-4.5V?qs=YINDDaGsG3FSnYZykcV2vQ%3D%3D)
- [Push button](https://www.adafruit.com/product/1445)
- [Adafruit Feather RP2040](https://www.adafruit.com/product/4884) -- or any feather capable of running Circuit Python!

Components on the **Receiver** side:
- [Adafruit LoRa Radio Bonnet with OLED - RFM95W @ 915MHz - RadioFruit](https://www.adafruit.com/product/4074)
- [Raspberry Pi Zero W](https://www.adafruit.com/product/3708) -- or any other Raspberry Pi


![lora-ben](https://live.staticflickr.com/65535/52699508855_88fdb0f980_4k.jpg)

You can see more [pictures of this project here :art:](https://flic.kr/s/aHBqjAtpNE).

**NOTE:** The enclosure for this project is still in progress!

#### Adafruit Show and Tell

Adafruit offers guides along with products that make it easy to build this project.
JP and Erin hosted [Show and Tell](https://www.youtube.com/c/adafruit/videos) on March 22nd, 2023 and
I had the honor of [talking about what I did so far](https://www.youtube.com/watch?v=m7rZJALOhrc&t=999s) to them.

[![lora-ben talk](https://img.youtube.com/vi/m7rZJALOhrc/2.jpg)](https://www.youtube.com/watch?v=m7rZJALOhrc&t=999s)
    
# Installation

## Sensor (sender) Side

### Install CircuitPython

See [CircuitPython Downloads](https://circuitpython.org/downloads?q=rp2040) and follow the steps documented there for the board you are using.

### Remove _all_ files from CIRCUITPY drive

```
# NOTE: Do not do this before backing up all files!!!
>>> import storage ; storage.erase_filesystem()
```

**NOTE:** The deep sleep interval can be adjusted by modifying the [const.py file](https://github.com/flavio-fernandes/lora-ben/blob/main/const.py). This may be a good time to tweak it. :smiley:

### Copying files from cloned repo to CIRCUITPY drive
```
# First, get to the REPL prompt so the board will not auto-restart as
# you copy files into it

# Assuming that CircuitPython board is mounted under /Volumes/CIRCUITPY
$  cd ${THIS_REPO_DIR}
$  [ -e ./code.py ] && \
   [ -d /Volumes/CIRCUITPY/ ] && \
   rm -rf /Volumes/CIRCUITPY/*.py && \
   (tar czf - *.py) | ( cd /Volumes/CIRCUITPY ; tar xzvf - ) && \
   echo ok || echo not_okay
```

### Libraries

Use [circup](https://learn.adafruit.com/keep-your-circuitpython-libraries-on-devices-up-to-date-with-circup)
to install these libraries:

```text
$ python3 -m venv .env && source ./.env/bin/activate && \
  pip install --upgrade pip

$ pip3 install circup

$ for LIB in \
    adafruit_ds18x20 \
    adafruit_rfm9x \
    ; do circup install $LIB ; done
```

This is what it should look like:
```text
$ ls /Volumes/CIRCUITPY/
boot_out.txt	code.py		const.py	lib		lora.py		main.py		settings.toml	sonar.py	temperature.py

$ ls /Volumes/CIRCUITPY/lib
adafruit_bus_device	adafruit_ds18x20.mpy	adafruit_onewire	adafruit_rfm9x.mpy

$ cat /Volumes/CIRCUITPY/boot_out.txt
Adafruit CircuitPython 8.0.3 on 2023-02-23; Adafruit Feather RP2040 with rp2040
Board ID:adafruit_feather_rp2040
UID:...

$ circup freeze | sort
Found device at /Volumes/CIRCUITPY, running CircuitPython 8.0.3.
adafruit_bus_device==5.2.3
adafruit_ds18x20==1.3.16
adafruit_onewire==2.0.4
adafruit_rfm9x==2.2.13
```

At this point, all needed files should be in place and all that is needed is to let
code.py run. From the Circuit Python serial console:

```text
>>  <CTRL-D>
soft reboot
...
```

## Receiver Side

### Install bonnet on Raspberry Pi as [documented here](https://learn.adafruit.com/adafruit-radio-bonnets)

```bash
# update packages
sudo apt-get update && sudo apt-get -y upgrade && sudo apt-get -y dist-upgrade && echo ok

# enable spi and i2c
sudo raspi-config   ;  # select interface-options --> spi and i2c

# install pip3
sudo apt install -y python3-pip git

# clone this repo
$ git clone https://github.com/flavio-fernandes/lora-ben.git

# install needed python dependencies
$ cd lora-ben/rpi && 
  sudo pip3 install -r requirements.txt && \
  echo ok
```

At this point, try running this script to display received packets:

```bash
$ ./basic_receive.py
```

### Using MQTT broker

If there is an MQTT broker you can use, follow these steps in order to publish
the packets received via lora:

```bash
$ vi ./rpi_const.py  ; # edit broker info and anything else

$ vi ./bin/loraben.service  ; # make sure path to start_loraben.sh in this file is proper
 
$ sudo cp -v ./bin/loraben.service /lib/systemd/system/

$ sudo systemctl enable --now loraben.service  ; # start and enable the service

# to Check if all is well, you can try these commanda
$ ./bin/tail_log.sh

$ systemctl status loraben

$ sudo systemctl restart loraben
```

The following commands can be used as a reference for subscribing to the MQTT topics

```bash
# Use this topic to force a refresh on all the topics, instead of waiting for periodic updates
$ mosquitto_pub -i pub_cli -h mqtt  -t "loraben/ping" -n

# Subscribing to loraben, assuming you did not change the prefix in rpi_const.py as mentioned above
$ mosquitto_sub -F '@Y-@m-@dT@H:@M:@S@z : %q : %t : %p' -h mqtt  -t "loraben/#"
2023-02-25T17:50:43-0500 : 0 : loraben/ping :
2023-02-25T17:50:47-0500 : 0 : loraben/msg : {'ip': '192.168.30.217', 'id': '217', 'batt': '4.0864 v', 'temp': '62.6 F', 'dist': '385 mm', 'rssi': '-76 dB', 'ts': '25/02/2023 17:33:57', 'len': '51 bytes'}
2023-02-25T17:50:51-0500 : 0 : loraben/ip : 192.168.30.217
2023-02-25T17:50:55-0500 : 0 : loraben/id : 217
2023-02-25T17:50:59-0500 : 0 : loraben/batt : 4.0864 v
2023-02-25T17:51:03-0500 : 0 : loraben/temp : 62.6 F
2023-02-25T17:51:07-0500 : 0 : loraben/dist : 385 mm
2023-02-25T17:51:11-0500 : 0 : loraben/rssi : -76 dB
2023-02-25T17:51:15-0500 : 0 : loraben/ts : 25/02/2023 17:33:57
2023-02-25T17:51:19-0500 : 0 : loraben/len : 51 bytes

```

