import board

ow_bus = None
ds18 = None


def _init():
    global ow_bus, ds18
    if ow_bus is None:
        from adafruit_onewire.bus import OneWireBus

        ow_bus = OneWireBus(board.D12)
    if ds18 is None:
        from adafruit_ds18x20 import DS18X20

        ds18 = DS18X20(ow_bus, ow_bus.scan()[0])


def read_temperature():
    _init()

    # ... in Fahrenheits
    return (ds18.temperature * 9 / 5) + 32
