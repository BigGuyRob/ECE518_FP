
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

FLEX_THRESHOLD = 500
right_click_group_keys = [0, 1]
RIGHT_CLICK_FLAG = False
LAST_RIGHT_CLICK = False
left_click_group_keys = [3,4]
LEFT_CLICK_FLAG = False
LAST_LEFT_CLICK = False

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


def check_right_clicks(adcs):
    rc = False
    for adc in right_click_group_keys:
            val = adcs[adc]
            #we want all to be off if it was previously on
            if(val > FLEX_THRESHOLD):
                rc = True
            else:
                rc = False
    
    if(rc):
        if(RIGHT_CLICK_FLAG):
            #do nothing, we dont want to click again if we havent debounced
            pass
        else:
            RIGHT_CLICK_FLAG = True
            mouse.right_click() #if we are debounced, click
    else:#the buttons are off
        RIGHT_CLICK_FLAG = False #we can set the click flag to false and not click


def check_left_clicks(adcs):
    lc = False
    for adc in left_click_group_keys:
            val = adcs[adc]
            #we want all to be off if it was previously on
            if(val > FLEX_THRESHOLD):
                lc = True
            else:
                lc = False
    
    if(lc):
        if(LEFT_CLICK_FLAG):
            #do nothing, we dont want to click again if we havent debounced
            pass
        else:
            LEFT_CLICK_FLAG = True
            #mouse.cl() #if we are debounced, click
    else:#the buttons are off
        LEFT_CLICK_FLAG = False #we can set the click flag to false and not click


def check_bends(adcs):
    for adc in adcs:
        val = float(adc.split(":")[1])
        if(val > FLEX_THRESHOLD):
            print(f"bent {adc}")

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
        f1 = f"f1:{data['f1']}"
        f2 = f"f2:{data['f2']}"
        f3 = f"f3:{data['f3']}"
        f4 = f"f4:{data['f4']}"
        f5 = f"f5:{data['f5']}"
        adcs = [f1,f2,f3,f4,f5]
        #check_right_clicks(adcs)
        #check_left_clicks(adcs)
        check_bends(adcs)
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
