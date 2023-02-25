import time
import board
import busio

uart = busio.UART(tx=None, rx=board.D13, baudrate=9600)

# Read multiple ultrasonic values and average them out for better
# precision
SONAR_SAMPLES = 7


def _read_me007ys(timeout=1.0):
    ts = time.monotonic()
    buf = bytearray(3)
    idx = 0

    while True:
        # time out while waiting to get valid data
        if time.monotonic() - ts > timeout:
            break

        r = uart.read(1)
        if r is None:
            continue

        c = r[0]
        # print(c)
        if idx == 0 and c == 0xFF:
            buf[0] = c
            idx = idx + 1
        elif 0 < idx < 3:
            buf[idx] = c
            idx = idx + 1
        else:
            chksum = sum(buf) & 0xFF
            if chksum == c:
                return (buf[1] << 8) + buf[2]
            idx = 0


def read_sonar(timeout=3.0):
    values = []
    ts = time.monotonic()
    while len(values) < SONAR_SAMPLES:
        if time.monotonic() - ts > timeout:
            return
        value = _read_me007ys()
        if value is None:
            time.sleep(0.05)
            continue
        values.append(value)
    values.sort()
    count, result = 0, 0
    # Ignore the 2 extremes
    for value in values[1 : len(values) - 1]:
        count += 1
        result += value
    return result // count
