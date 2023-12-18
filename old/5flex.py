import spidev
import time

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 400000 #31.25 * 1000 * 13

adc1 = "d 0"
adc2 = "d 1"
adc3 = "u 0"
adc4 = "u 1"
adc5 = "u 2"
bus0 = [adc1,adc2]
bus1 = [adc3, adc4, adc5]
def read_adc(cs):
	int_cs = int(cs.split(" ")[1])
	if(cs in bus0):
		spi.open(0,int_cs)
	elif(cs in bus1):
		spi.open(1,int_cs)

	spi.max_speed_hz = 400000
	resp = spi.xfer([0x08, 0x00])
	value = ((resp[0] & 3) << 8) + resp[1]
	spi.close()
	return value


try:
	while True:
		for p in bus0:
			value = read_adc(p)
			#print(f"{p} {value}")
			time.sleep(0.5)
		for p in bus1:
			value = read_adc(p)
			print(f"{p} {value}")
			time.sleep(0.5)

except KeyboardInterrupt:
	spi.close()
