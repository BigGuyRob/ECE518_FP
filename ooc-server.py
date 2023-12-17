
import bluetooth
import mouse
import json
import matplotlib.pyplot as plt
import tkinter 
import time
plt.ion()
plt.figure(figsize=(25,6))
plt.show()
root = tkinter.Tk()
max_width = root.winfo_screenwidth()
max_height = root.winfo_screenheight()


server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

bluetooth.advertise_service(server_sock, "SampleServer", service_id=uuid,
                            service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                            profiles=[bluetooth.SERIAL_PORT_PROFILE],
                            # protocols=[bluetooth.OBEX_UUID]
                            )

print("Waiting for connection on RFCOMM channel", port)

client_sock, client_info = server_sock.accept()
print("Accepted connection from", client_info)
roll_axis = []
pitch_axis = []
mouse_x_axis  = []
mouse_y_axis = []
timestamps = []

STEP_SIZE = 20

DOWN_ROLL = -20
UP_ROLL = 20
RIGHT_PITCH = 40
LEFT_PITCH = -40

def move_mouse(roll, pitch, mouse_pos_x, mouse_pos_y):
    if(roll > UP_ROLL):
        mouse_pos_y -= STEP_SIZE
        if(mouse_pos_y < 0):
            mouse_pos_y = 0
        print("UP")
    elif(roll < DOWN_ROLL):
        mouse_pos_y +=STEP_SIZE
        if(mouse_pos_y > max_height):
            mouse_pos_y = max_height    
        print("DOWN")


    if(pitch > RIGHT_PITCH):
        print("RIGHT")
        mouse_pos_x += STEP_SIZE
        if(mouse_pos_x > max_width):
            max_pos_x = max_width
    elif(pitch < LEFT_PITCH):
        print("LEFT")
        mouse_pos_x -=STEP_SIZE
        if(mouse_pos_x < 0):
            mouse_pos_x = 0


    
    mouse.move(mouse_pos_x,mouse_pos_y)
    return mouse_pos_x, mouse_pos_y

st = time.time()
mouse_pos_x, mouse_pos_y = 0,0
try:
    while True:
        
        data = client_sock.recv(1024)
        data = data.decode('utf-8')
        print(data)
        data = f"{data.split('}')[0]}{'}'}"
        data = json.loads(data)
        roll = data['roll']
        pitch = data['pitch']
        dt = time.time() - st
        roll_axis.append(float(roll))
        pitch_axis.append(float(pitch))
        timestamps.append(float(dt))
        #print(f"roll:{roll}, pitch:{pitch}")
        mouse_pos_x, mouse_pos_y = move_mouse(roll, pitch, mouse_pos_x, mouse_pos_y)
        mouse_x_axis.append(mouse_pos_x)
        mouse_y_axis.append(mouse_pos_y)
        plt.pause(0.01)
        plt.plot(timestamps, roll_axis,  color="blue")
        plt.plot(timestamps, pitch_axis,  color= "green")
        plt.plot(timestamps, mouse_x_axis,  color = "red")
        plt.plot(timestamps, mouse_y_axis,  color = "orange")

        print(f"x: {mouse_pos_x}, y: {mouse_pos_y}")
        
        if not data:
            break
        #print("Received", data)
except OSError:
    pass

print("Disconnected.")

client_sock.close()
server_sock.close()
print("All done.")
