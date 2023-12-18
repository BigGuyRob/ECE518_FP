#Connections
#MPU6050 - Raspberry pi
#VCC - 5V  (2 or 4 Board)
#GND - GND (6 - Board)
#SCL - SCL (5 - Board)
#SDA - SDA (3 - Board)


from Kalman import KalmanAngle
import smbus			#import SMBus module of I2C
import time
import math
import sys
import bluetooth
import json
import spidev
import time
import math


gyroXAngle = 0
gyroYAngle = 0
compAngleX = 0
compAngleY = 0

timer = time.time()
delay = 0.01
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 400000 #31.25 * 1000 * 13
addr = None
adc1 = "d 0"
adc2 = "d 1"
adc3 = "u 0"
adc4 = "u 1"
adc5 = "u 2"
bus0 = [adc1,adc2]
bus1 = [adc3, adc4, adc5]
canon_byte_map = {
     adc1 : "f1",
     adc2 : "f2",
     adc3 : "f3",
     adc4 : "f4",
     adc5 : "f5"
}

kalmanX = KalmanAngle()
kalmanY = KalmanAngle()

RestrictPitch = True	#Comment out to restrict roll to ±90deg instead - please read: http://www.freescale.com/files/sensors/doc/app_note/AN3461.pdf
radToDeg = 57.2957786
kalAngleX = 0
kalAngleY = 0
#some MPU6050 Registers and their Address
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47

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

def extract_finger_sensor_data():
    data = {}
    for p in bus0:
        value = read_adc(p)
        #print(f"{p} {value}")
        data.update({canon_byte_map[p] : value})
        time.sleep(delay)
    for p in bus1:
        value = read_adc(p)
        #print(f"{p} {value}")
        data.update({canon_byte_map[p] : value})
        time.sleep(delay)
    return data

#Read the gyro and acceleromater values from MPU6050
def MPU_Init():
	#write to sample rate register
	bus.write_byte_data(DeviceAddress, SMPLRT_DIV, 7)

	#Write to power management register
	bus.write_byte_data(DeviceAddress, PWR_MGMT_1, 1)

	#Write to Configuration register
	#Setting DLPF (last three bit of 0X1A to 6 i.e '110' It removes the noise due to vibration.) https://ulrichbuschbaum.wordpress.com/2015/01/18/using-the-mpu6050s-dlpf/
	bus.write_byte_data(DeviceAddress, CONFIG, int('0000110',2))

	#Write to Gyro configuration register
	bus.write_byte_data(DeviceAddress, GYRO_CONFIG, 24)

	#Write to interrupt enable register
	bus.write_byte_data(DeviceAddress, INT_ENABLE, 1)


def read_raw_data(addr):
	#Accelero and Gyro value are 16-bit
        high = bus.read_byte_data(DeviceAddress, addr)
        low = bus.read_byte_data(DeviceAddress, addr+1)

        #concatenate higher and lower value
        value = ((high << 8) | low)

        #to get signed value from mpu6050
        if(value > 32768):
                value = value - 65536
        return value

def calculate_from_raw_data(gyroXAngle = gyroXAngle, gyroYAngle = gyroYAngle, compAngleX = compAngleX, compAngleY = compAngleY, kalAngleX = kalAngleX, kalAngleY = kalAngleY):
    accX = read_raw_data(ACCEL_XOUT_H)
    accY = read_raw_data(ACCEL_YOUT_H)
    # Additional code goes here...

    accZ = read_raw_data(ACCEL_ZOUT_H)

    #Read Gyroscope raw value
    gyroX = read_raw_data(GYRO_XOUT_H)
    gyroY = read_raw_data(GYRO_YOUT_H)
    gyroZ = read_raw_data(GYRO_ZOUT_H)

    dt = time.time() - timer

    if (RestrictPitch):
        roll = math.atan2(accY,accZ) * radToDeg
        pitch = math.atan(-accX/math.sqrt((accY**2)+(accZ**2))) * radToDeg
    else:
        roll = math.atan(accY/math.sqrt((accX**2)+(accZ**2))) * radToDeg
        pitch = math.atan2(-accX,accZ) * radToDeg

    gyroXRate = gyroX/131
    gyroYRate = gyroY/131

    if (RestrictPitch):

        if((roll < -90 and kalAngleX >90) or (roll > 90 and kalAngleX < -90)):
            kalmanX.setAngle(roll)
            complAngleX = roll
            kalAngleX   = roll
            gyroXAngle  = roll
        else:
            kalAngleX = kalmanX.getAngle(roll,gyroXRate,dt)

        if(abs(kalAngleX)>90):
            gyroYRate  = -gyroYRate
            kalAngleY  = kalmanY.getAngle(pitch,gyroYRate,dt)
    else:

        if((pitch < -90 and kalAngleY >90) or (pitch > 90 and kalAngleY < -90)):
            kalmanY.setAngle(pitch)
            complAngleY = pitch
            kalAngleY   = pitch
            gyroYAngle  = pitch
        else:
            kalAngleY = kalmanY.getAngle(pitch,gyroYRate,dt)

        if(abs(kalAngleY)>90):
            gyroXRate  = -gyroXRate
            kalAngleX = kalmanX.getAngle(roll,gyroXRate,dt)

    #angle = (rate of change of angle) * change in time
    gyroXAngle = gyroXRate * dt
    gyroYAngle = gyroYAngle * dt

    #compAngle = constant * (old_compAngle + angle_obtained_from_gyro) + constant * angle_obtained from accelerometer
    compAngleX = 0.93 * (compAngleX + gyroXRate * dt) + 0.07 * roll
    compAngleY = 0.93 * (compAngleY + gyroYRate * dt) + 0.07 * pitch

    if ((gyroXAngle < -180) or (gyroXAngle > 180)):
        gyroXAngle = kalAngleX
    if ((gyroYAngle < -180) or (gyroYAngle > 180)):
        gyroYAngle = kalAngleY
        
    return {'roll' : roll, 'pitch' : pitch}  
  
bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
DeviceAddress = 0x68   # MPU6050 device address

MPU_Init()

time.sleep(1)
#Read Accelerometer raw value
accX = read_raw_data(ACCEL_XOUT_H)
accY = read_raw_data(ACCEL_YOUT_H)
accZ = read_raw_data(ACCEL_ZOUT_H)

#print(accX,accY,accZ)
#print(math.sqrt((accY**2)+(accZ**2)))
if (RestrictPitch):
    roll = math.atan2(accY,accZ) * radToDeg
    pitch = math.atan(-accX/math.sqrt((accY**2)+(accZ**2))) * radToDeg
else:
    roll = math.atan(accY/math.sqrt((accX**2)+(accZ**2))) * radToDeg
    pitch = math.atan2(-accX,accZ) * radToDeg

print(roll)
kalmanX.setAngle(roll)
kalmanY.setAngle(pitch)
gyroXAngle = roll
gyroYAngle = pitch
compAngleX = roll
compAngleY = pitch

timer = time.time()
"""MAIN"""
print("Over the Air Computing - Pairing Started")
# search for the SampleServer service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
service_matches = bluetooth.find_service(uuid=uuid, address=addr)

if len(service_matches) == 0:
    print("Couldn't find the SampleServer service.")
    sys.exit(0)

first_match = service_matches[0]
port = first_match["port"]
name = first_match["name"]
host = first_match["host"]

print("Connecting to \"{}\" on {}".format(name, host))

# Create the client socket
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((host, port))


while True:
    timer = time.time()
    finger_data = extract_finger_sensor_data()
    #orientation_data = read_imu_data()
    sent_data = {}
    #sent_data.update(orientation_data)
    sent_data.update(finger_data)
    #orientation = calculate_orientation(sent_data['axl'])
    orientation = calculate_from_raw_data()
    sent_data.update(orientation)
    time.sleep(delay)
    ret = json.dumps(sent_data).encode('utf-8')
    if not ret:
         break
    print(ret)
    sock.send(ret)

sock.close()
print("disconnected, program over")