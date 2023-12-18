from mpu6050 import mpu6050

sensor = mpu6050(0x68)#the address of the device

d = sensor.get_accel_data()
print(d)
