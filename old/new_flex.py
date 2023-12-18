import spidev
import time

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 400000 #31.25 * 1000 * 13


def read_adc():
	resp = spi.xfer([0x08, 0x00])
	value = ((resp[0] & 3) << 8) + resp[1]
	return value


try:
	while True:
		value = read_adc()
		print(value)
		time.sleep(0.2)

except KeyboardInterrupt:
	spi.close()
