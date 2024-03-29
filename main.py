import alarm
import time
import board
import analogio
import digitalio
import random

from const import deep_sleep_interval, send_packets
from lora import send_report
from sonar import read_sonar
from temperature import read_temperature


def done(bump_sequenace, msg):
    global sequence, relay, blue_led, yellow_led

    blue_led.value, yellow_led.value, relay.value = False, False, False

    time_alarm = alarm.time.TimeAlarm(
        monotonic_time=time.monotonic() + deep_sleep_interval
    )

    if bump_sequenace:
        try:
            alarm.sleep_memory[0] = (sequence + send_packets) % 256
        except (NotImplementedError, IndexError):
            # https://github.com/adafruit/circuitpython/issues/5081
            pass

    print(f"Sleeping {deep_sleep_interval} seconds. {msg}")
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)


# Initialize message id with random in case sleep_memory is
# not available.
sequence = random.randint(0, 255 - send_packets)
try:
    if alarm.wake_alarm:
        sequence = alarm.sleep_memory[0]
    else:
        time.sleep(3)
except (NotImplementedError, IndexError):
    # https://github.com/adafruit/circuitpython/issues/5081
    pass

# The replay controls power to all the gizmos attached.
# Because of that, we must "power it up" before trying to use them!
relay = digitalio.DigitalInOut(board.D9)
relay.direction = digitalio.Direction.OUTPUT
relay.value = True

# give woken up sensors a few seconds to quiesce
time.sleep(2)

blue_led = digitalio.DigitalInOut(board.D5)
blue_led.direction = digitalio.Direction.OUTPUT

yellow_led = digitalio.DigitalInOut(board.D25)
yellow_led.direction = digitalio.Direction.OUTPUT

# STATE 1: SENSORS POWERED UP
blue_led.value, yellow_led.value = False, False

# Battery value is obtained by using a 10k resistor divider
# https://learn.adafruit.com/adafruit-feather-rp2040-pico?view=all#measuring-battery-3122383
# https://learn.sparkfun.com/tutorials/voltage-dividers/all
battery = analogio.AnalogIn(board.A2)
battery_value = battery.value / 10000

temperature = read_temperature()
if not temperature:
    done(False, "failed to read temperature")

# STATE 2: GOT BATTERY AND TEMPERATURE
blue_led.value, yellow_led.value = True, False
time.sleep(1)

distance = read_sonar()
if not distance:
    print("failed to read distance:{distance}. Sensor farther than 4 meters?")
    distance = -1
    # done(False, "failed to read distance")
else:
    # STATE 3: GOT BATTERY, TEMPERATURE AND DISTANCE
    blue_led.value, yellow_led.value = False, True
    time.sleep(1)

send_fails = 0
for i in range(send_packets):
    if not send_report(sequence + i, battery_value, temperature, distance):
        send_fails += 1
    time.sleep(1)

if send_fails:
    done(False, "failed to send report")

# STATE 4: SENT RADIO REPORT
blue_led.value, yellow_led.value = True, True

time.sleep(3)
done(True, "")
