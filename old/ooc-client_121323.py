import sys
from mpu6050 import mpu6050
import bluetooth
import json
import spidev
import time
import math
import angle_meter
addr = None
#imu = mpu6050(0x68)
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
canon_byte_map = {
     adc1 : "f1",
     adc2 : "f2",
     adc3 : "f3",
     adc4 : "f4",
     adc5 : "f5"
}


def read_imu_data():
    # Read accelerometer, gyro, and temp data
    accel_data = imu.get_accel_data()
    gyro_data = imu.get_gyro_data()
    temp = imu.get_temp()
    ret_data = {
        'axl' : accel_data,
        'gro' : gyro_data,
        'tmp' : temp
    }
    return ret_data

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
        time.sleep(0.2)
    for p in bus1:
        value = read_adc(p)
        #print(f"{p} {value}")
        data.update({canon_byte_map[p] : value})
        time.sleep(0.2)
    return data

def calculate_orientation(accel_data):
    ax, ay, az = accel_data['x'], accel_data['y'], accel_data['z']

    # Calculate the angles of rotation
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

    # Convert to degrees
    roll = math.degrees(roll)
    pitch = math.degrees(pitch)
    #pi/180
    return {'roll' : roll, 'pitch' : pitch}

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
    st = time.time()
    finger_data = extract_finger_sensor_data()
    #orientation_data = read_imu_data()
    sent_data = {}
    #sent_data.update(orientation_data)
    #sent_data.update(finger_data)
    dt = time.time() - st
    #orientation = calculate_orientation(sent_data['axl'])
    orientation = angle_meter.calculate_from_raw_data()
    sent_data.update(orientation)
    time.sleep(0.2)
    ret = json.dumps(sent_data).encode('utf-8')
    if not ret:
         break
    print(ret)
    sock.send(ret)

sock.close()
print("disconnected, program over")