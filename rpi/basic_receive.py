#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2018 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Example for using the RFM9x Radio with Raspberry Pi.

Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Brent Rubell for Adafruit Industries
"""
# Import Python System Libraries
import time

# Import Blinka Libraries
import busio
from digitalio import DigitalInOut, Direction, Pull
import board

# Import the SSD1306 module.
import adafruit_ssd1306

# Import RFM9x
import adafruit_rfm9x

from datetime import datetime
import asyncio
import socket

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)

rfm9x.tx_power = 23
# rfm9x.node = 8
# rfm9x.destination = 1


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.0.0.254", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


curr_values, prev_values = {}, {}
stop_gracefully = False


def stop_basic_receive():
    global stop_gracefully
    stop_gracefully = True


def get_latest():
    global curr_values
    return curr_values


async def refresh_ip():
    global curr_values
    cnt = 0
    while not stop_gracefully:
        if not cnt:
            curr_values["ip"] = get_ip()
        cnt = (cnt + 1) % 120
        await asyncio.sleep(0.5)


async def refresh_display():
    global curr_values, prev_values

    fg_color, bg_color = 0, 1
    while not stop_gracefully:
        await asyncio.sleep(0.5)

        if prev_values == curr_values:
            # noop
            continue

        display.fill(fg_color)

        display.text(f"ip:{curr_values['ip']}", 2, 0, bg_color)
        display.text(
            f"id:{curr_values.get('id','?')} {curr_values.get('rssi','? db')}",
            0,
            10,
            bg_color,
        )
        display.text(f"{curr_values.get('batt','? v')}", 80, 15, bg_color)
        display.text(f"{curr_values.get('temp','? F')}", 2, 20, bg_color)
        display.text(f"{curr_values.get('dist','? mm')}", 47, 25, bg_color)

        display.show()
        prev_values = curr_values.copy()
        fg_color, bg_color = bg_color, fg_color


def parse_packet_text(packet_text):
    global curr_values
    # example packet_text:  'id:227, batt:3.6472 v, temp:59.9 F, dist:183 mm'
    for value in packet_text.split(","):
        kv = value.strip().split(":")
        if len(kv) == 2:
            curr_values[kv[0]] = kv[1]


async def receive_packets(quiet):
    global curr_values, stop_gracefully

    rfm9x.receive_timeut = 2
    while not stop_gracefully:
        await asyncio.sleep(0)
        try:
            packet = rfm9x.receive(with_header=True)
        except (KeyboardInterrupt, SystemExit):
            stop_gracefully = True
            return

        if packet is None:
            continue

        # print("Received (raw header):", [hex(x) for x in packet[0:4]])
        # print("Received (raw payload): {0}".format(packet[4:]))

        try:
            packet_text = str(packet[4:], "ascii")
            parse_packet_text(packet_text)
            curr_values.pop("parse_exception", None)
        except Exception as e:
            packet_text = f"parse_exception: {e}"

        ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if not quiet:
            print(f"{ts} Received RSSI: {rfm9x.last_rssi} -- PAYLOAD: {packet_text}")

        # add additional info to curr_values
        curr_values["rssi"] = f"{rfm9x.last_rssi} dB"
        curr_values["ts"] = ts
        curr_values["len"] = f"{len(packet_text) + 4} bytes"


async def basic_receive_main(quiet=False):
    await asyncio.gather(
        refresh_ip(),
        refresh_display(),
        receive_packets(quiet),
    )


if __name__ == "__main__":
    asyncio.run(basic_receive_main())
