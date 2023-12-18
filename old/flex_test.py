#We are using an ADC0831-N 
#This is an 8 bit serial single channel ADC

import RPi.GPIO as GPIO
import time

# Set the GPIO numbering mode
GPIO.setmode(GPIO.BCM)

# Replace these with your GPIO pin numbers
CLOCK_PIN = 23  # GPIO pin for the clock signal
INPUT_PIN = 24  # GPIO pin for the serial input
ENABLE = 25 #GPIO pin for enabling all of the ADC, Active LOW

# Set up the GPIO pins
GPIO.setup(CLOCK_PIN, GPIO.OUT)
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(ENABLE, GPIO.OUT)

# Function to pulse the clock pin
def pulse_clock_and_sample():
    GPIO.output(CLOCK_PIN, GPIO.HIGH)
    input = GPIO.input(INPUT_PIN)
    GPIO.output(CLOCK_PIN, GPIO.LOW)
    return input


def setup_adc():
    GPIO.output(ENABLE, True)
    time.sleep(0.0050)
    time.sleep(0.0050)
    GPIO.output(ENABLE, False)
    time.sleep(0.050)



# Main loop
adc_val = []
try:
    setup_adc()
    while True:
        if(len(adc_val) > 7): #if we have our 8th bit
            bit_string = f"{adc_val[7]}{adc_val[6]}{adc_val[5]}{adc_val[4]}{adc_val[3]}{adc_val[2]}{adc_val[1]}{adc_val[0]}"
            decimal = decimal_number = int(bit_string, 2)
            print(f"value obtained : {decimal}")
            adc_val.clear() #clear the string

        input = pulse_clock_and_sample()
        adc_val.append(input)
        print(f"Input state: {input}")

except KeyboardInterrupt:
    GPIO.cleanup()  # Clean up GPIO on CTRL+C exit

GPIO.cleanup()  # Clean up GPIO on normal exit
