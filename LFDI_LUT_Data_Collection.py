# This Will Collect all the Data needed for the LUT in the embedded system
# All Data Collected here will need to be ran through level 2 processing
# The Experimental Setup should be as follows:

# 660nm LED  --->   LFDI Optical Stack ---> Spectrometer -->Zwo Camera --> PC

# A TMP117 Board should be attached tot he outside of the Optical Stack with the metallic side making contact with the stack
# A Band heater should be wrapped around the stack and the TMP117 to heat to the desired temperature
# On the side of the LFDI Carriage should be the Tuning Control board.
# The Tuning Control board will have the Following Connections when looking at the Face
# Over top of all of this should be the Isolating Control Box

#    Below is the assumed Labeling of the Header Pins Where * represents the holes in the header
#     1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
#   A *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  
#   B *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *
#   C *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *
#   D *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *

# There are 2 Different Power sources you will connect to the header
# 3.3V Power, Heater Power

# The 3.3V Lab bench supply will be set to 3.3V and Limited to 150mA
# the 3.3V Will be connected to the following pins
# +3.3V to C24
# Return to A15

# The Heater Power Supply will be set to 9V and limited to 2A (This is Subject to Change due to the power draw of the heater)
# The Heater Power Supply will be connected to the following pins
# +Heater_Power to B23
# Return to B15

# For this Experiment the Tuning Control board will also be connected to the folowing Devices
# +/-15V rails (For the Dac)            Connection P9   (Please Check Connections against Schematic before Powering on)
# TMP117 (For Temperature Readings)     Connection P5   (Assumed address for the TMP117 is 0x00 and connected to the Bus on the back of the board)
# Heater (For heating the Stack)        Connection P13  (Heater number 1)
# USB (For Communication with the PC)   Connction J4    (Assumed COM port is COM3 but this could vary depending on what is connected)

# The General Idea of the Experiment is to Sweep through the Voltages and Temperatures and record the data
# This Data can then be used to Model the retardance Curve at a Control Temperature in the Embedded Software
# The model Can then be offset for the Different Temperatures


# This Experiment Running Software Will Run through a few Different Calibration routines before Beging the experiment
# This will help with ensuring the Acton spectrometer is in the Correct Configuration and that the LED is not Saturating the Camera

# For the First Calibration routine you will be asked to replace the 660nm LED with a H-Alpha Lamp.
# This will be used to calibrate the spectrometer to the H-Alpha Line
# The H-Aplha Line Should be Roughly Centered in the Output Image of the Spectrometer

#Replace the H-Alpha Lamp with the 660nm LED
#for the Second Calibration you will be asked to Adjust the Gain of the Camera

#For the next Calibration you will be asked to Adjust the brightness of the LED


import numpy as np
import Hardware_API.LFDI_API as LFDI
import time
import Hardware_API.Spectrograph as Spectrograph
import os
import datetime
from functools import partial


# Check to see if the TCB temp is at the set point
def TCB_at_temp(temp, LFDI_TCB, tolerance):
    #Get the current temperature
    try:
        current_temp = float(LFDI_TCB.Controllers[0].average)
    except ValueError as e:
        print(f"Value Error {e} board request may have desynced")
        return False
    
    #Check if the current temperature is within the tolerance of the set point
    print(f"Sensor at {current_temp} waiting for {(temp - tolerance)} - {(temp + tolerance)}")
    if (current_temp > (temp - tolerance)) and (current_temp < (temp + tolerance)):
        return True
    else:
        return False
    
    # wait for a certain time from the input time
def wait_time(start, wait_time):
    #Get the current time
    current_time = time.time()
    #Check if the current time is greater than the input time plus the wait time
    if current_time > (start + wait_time):
        return True
    else:
        return False


# The Following Function is the Experiment that will be ran to Collect all the Data
# @param spectrometer: The Spectrometer Object
# @param LFDI_TCB: The LFDI_TCB Object
# @param start_temp: (Float) The Starting Temperature for the Sweep
# @param end_temp: (Float) The Ending Temperature for the Sweep
# @param step_temp: (Float) The Step Size for the Temperature Sweep
# @param start_voltage: (Float) The Starting Voltage for the Sweep
# @param end_voltage: (Float) The Ending Voltage for the Sweep
# @param step_voltage: (Float) The Step Size for the Voltage Sweep
# @param tolerance: (Float) The Tolerance for the Temperature
# @param folder: (path) The Folder to save the data to
# @return None
# This will go through the array of temperatures and the array of Voltages step by step and capture Spectra Output to the Experiment Folder
def Total_Data_Collection(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI.LFDI_TCB, start_temp: float, end_temp: float, 
                          step_temp: float, tolerance: float, start_voltage: float, end_voltage: float, 
                          step_voltage : float, folder, compensator_number = 4, controller_number = 1):
    
    
    # print the parameters 
    print(f"Start Temp {start_temp}")
    print(f"End Temp {end_temp}")
    print(f"Step Temp {step_temp}")
    print(f"Start Voltage {start_voltage}")
    print(f"End Voltage {end_voltage}")
    print(f"Step Voltage {step_voltage}")
    
    
    # Create a list of temperatures to cycle through
    # Go from the low temperature to the high temperature
    temperatures = np.arange(start_temp, end_temp, step_temp)
    print(f"Temps: {temperatures}")
    
    # Create a list of the Voltages to cycle through
    voltages = np.arange(start_voltage, end_voltage, step_voltage)
    print(f"Voltages: {voltages}")
    
    # Create a file to store the data
    filename = f"{folder}\\TCB_Out.tsv"
    file = open(filename, "w")
    file.write(f"{LFDI_TCB.header_format}\n")
    file.close()

    # First go through the temperatures without the Compensation Algorythm
    # Cycle through the temperatures. Take a measurement while the temperature is moving hold at each temperature for 5 minutes
    #Tun on the output for the First Compensator
    
    # Go through the temperatures
    LFDI_TCB.set_controller_enable(controller_number=controller_number, enable=True)
    for temperature in temperatures:
        # Change to a known state
        LFDI_TCB.set_compensator_voltage(compensator_number, 3)
        LFDI_TCB.set_compensator_enable(compensator_number, True)

        
        # Set the temperature
        LFDI_TCB.set_controller_setpoint(controller_number=controller_number, setpoint=temperature)
        
        
        temporal_resolution = 10*60 # 10 minute
        #While we are waiting for the TCB to reach the Temperature take an image every Minute
        while not TCB_at_temp(temperature, LFDI_TCB, tolerance):
            # Get the Current time and output the spectrograph for a minute
            now = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, temporal_resolution))
            # Take a measurement
            # Get the Current Temp From LFDI
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[controller_number-1].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"{folder}\\Slew_{str(time.time())}_{LFDI_TCB.Compensators[compensator_number-1].voltage}V_{current_temp}C_CompOff_0nm.png"
            os.rename(spectrometer.current_image, filename)
        

        print(f"Reached {temperature}C")
        print("Waiting 30 minutes")
        #Wait For the Crystal to warm through out, Testing Shows for the Epoxied stage this should Take ~ 15 min 
        now = time.time()
        seconds_to_wait = 1800 #wait for 30 min
        while not wait_time(now, seconds_to_wait):
            current_time = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, temporal_resolution))
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[controller_number-1].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"{folder}\\Hold_{str(time.time())}_{LFDI_TCB.Compensators[compensator_number-1].voltage}V_{current_temp}C_CompOff_0nm.png"
            os.rename(spectrometer.current_image, filename)

        print("Finished Waiting")
        print("Cycling through Voltages")
        for voltage in voltages:
            # Set the voltage
            LFDI_TCB.set_compensator_voltage(compensator_number, voltage)
            # Wait for the voltage to settle
            time.sleep(1)
            # Take a measurement
            now = time.time()
            spectrometer.single_output()
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[controller_number-1].average
            voltage = LFDI_TCB.Compensators[compensator_number-1].voltage
            current_temp = f"{float(current_temp):.2f}"
            filename = f"{folder}\\Hold_{str(time.time())}_{voltage}V_{current_temp}C_CompOff_0nm.png"
            while not os.path.exists(spectrometer.current_image):
                time.sleep(5)
            os.rename(spectrometer.current_image, filename)

        print(f"Finished {temperature}C")
    print("Finished Temp Cycle")



from DataCollection.LFDI_Experiment import make_experiment_folder
from DataCollection.LFDI_Experiment import calibrate_LED, calibrate_camera
if __name__ == "__main__":
    # Create the Spectrometer
    try:
        spectrometer = Spectrograph.Spectrometer()
        spectrometer.camera.auto_exposure = False
        spectrometer.camera.set_exposure(.20)
        spectrometer.camera.set_binning(4)
        spectrometer.camera.set_gain(300)

    except Exception as e:
        print(f"Could not connect to Spectrometer Camera {e}")
        exit()
    
    # Create the LFDI_TCB
    try:
        lfdi = LFDI.LFDI_TCB("COM6", 9600)
        # Setup Initial PID Values
        lfdi.set_controller_kd(controller_number=1, kd=0.75)
        lfdi.set_controller_ki(controller_number=1, ki=0)
        lfdi.set_controller_kp(controller_number=1, kp=5)
    # Except if we can't connect to the LFDI_TCB
    except Exception as e:
        print(f"Could not connect to LFDI_TCB On Com6 {e}")
        exit()
        
    beginning_temp = 25.5
    
    lfdi.get_info()
    
    # Create folder
    folder = make_experiment_folder()
    # Calibrate the Spectrometer
    #calibrate_spectrometer(spectrometer, folder)
    
    #calibrate_LED(spectrometer, folder)
    #calibrate_camera(spectrometer)
    spectrometer.camera.set_exposure(0.05)
    # Cycle through the temperatures
    # SquareWave_Sweep(spectrometer, lfdi, float(ambient_temperature), 30, .5, start_voltage=0, end_voltage=10, step_voltage=.1, tolerance=0.1, folder=folder)
    # Temp_Compensation(spectrometer, lfdi, float(ambient_temperature), 30, 1, tolerance=0.5, folder=folder)
    # Run_Endurance_Test(spectrometer=spectrometer, LFDI_TCB=lfdi,tolerance=.5, folder= folder)
    Total_Data_Collection(spectrometer=spectrometer, LFDI_TCB=lfdi, start_temp=float(beginning_temp), end_temp=30, step_temp=.25, tolerance=.125, start_voltage = 0 , end_voltage = 17.9, step_voltage = .1, folder=folder, compensator_number=4)




