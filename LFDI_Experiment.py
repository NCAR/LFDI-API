
import numpy as np
import Hardware_API.LFDI_API as LFDI
import time
import Hardware_API.Spectrograph as Spectrograph
import os
import datetime
from functools import partial


def Temp_Compensation(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI, start_temp, end_temp, step, tolerance, folder):
    print(f"Start Temp {start_temp}")
    print(f"End Temp {end_temp}")
    print(f"Step Temp {step}")
    #Create a list of temperatures to cycle through
    temperatures = np.arange(start_temp, end_temp, step)
    #Create a list to store the filenames of the images
    filenames = []
    #Cycle through the temperatures. Take a measurement while the temperature is moving hold at each temperature for 5 minutes
    for temperature in temperatures:
        #Set the temperature
        LFDI_TCB.set_controller_setpoint(controller_number = 1, setpoint = temperature)
        LFDI_TCB.set_controller_enable(controller_number = 1, enable = True)
        temporal_resolution = 1*60 #1 minute
        #Continuously output until we reach the set point
        while not TCB_at_temp(temperature, LFDI_TCB, tolerance):
            now = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, temporal_resolution))
            #Take a measurement
            #Get the Current Temp From LFDI
            current_temp = LFDI_TCB.Controllers[1].temp().strip(' ')
            #Format the Current Temp to be a string with 2 decimal places
            current_temp = f"{float(current_temp):.2f}"
            os.rename(spectrometer.current_crosssection, f"{folder}/Slew_{str(time.time())}_{str(current_temp)}C_AutoV.csv")
        print(f"Reached {temperature}C")
        print("Waiting 5 minutes")
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 300
        while not wait_time(now, seconds_to_wait):
            current_time = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, temporal_resolution))
            current_temp = LFDI_TCB.get_average_temperature().strip(' ')
            #Format the Current Temp to be a string with 2 decimal places
            current_temp = f"{float(current_temp):.2f}"
            os.rename(spectrometer.current_crosssection, f"{folder}/Hold_{str(time.time())}_{str(current_temp)}C_AutoV.csv")
        print("Finished Waiting")
        print(f"Finished {temperature}C")
    return
#Sweep the temperature of the TCB and the Voltage applied from the DAC; take an image at each state
def SquareWave_Sweep(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI, start_temp: float, end_temp: float, step_temp:float ,start_voltage:float, end_voltage:float, step_voltage:float, tolerance:float, folder:os.path):
    print(f"Start Temp {start_temp}")
    print(f"End Temp {end_temp}")
    print(f"Step Temp {step_temp}")
    print(f"Start Voltage {start_voltage}")
    print(f"End Voltage {end_voltage}")
    print(f"Step Voltage {step_voltage}")
    #Create a list of temperatures to cycle through
    temperatures = np.arange(start_temp, end_temp, step_temp)
    voltages = np.arange(start_voltage, end_voltage, step_voltage)
    #Create a list to store the filenames of the images
    
    #Cycle through the temperatures
    for temperature in temperatures:
        #Set the temperature
        LFDI_TCB.set_target_temperature(temperature)
        LFDI_TCB.set_enable(True)
        #Continuously output until we reach the set point
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(TCB_at_temp, temperature, LFDI_TCB, tolerance))
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 300 #wait for 5 minutes
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))
        for voltage in voltages:
            #Rename the spectrometers current image, graph and Crosssection with the temperature and move them to the experiment folder
            lfdi.set_DAC(0, voltage)
            seconds_to_wait = 10
            spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))
            os.rename(spectrometer.current_image, f"{folder}/{str(temperature)}C_{voltage}V.tif")
            os.rename(spectrometer.current_graph, f"{folder}/{str(temperature)}C_{voltage}V.png")
            os.rename(spectrometer.current_crosssection, f"{folder}/{str(temperature)}C_{voltage}V.csv")
            print(f"Finished Voltage {voltage}V")
        print(f"Finished {temperature}C")
    return

#Cycle through Temperatures and take an image at each temperature
def temperature_cycle(spectrometer,LFDI_TCB, start_temp, end_temp, step, tolerance, folder):
    print(f"Start Temp {start_temp}")
    print(f"End Temp {end_temp}")
    print(f"Step Temp {step}")
    #Create a list of temperatures to cycle through
    temperatures = np.arange(start_temp, end_temp, step)
    #Create a list to store the filenames of the images
    
    #Cycle through the temperatures
    for temperature in temperatures:
        #Set the temperature
        LFDI_TCB.set_target_temperature(temperature)
        LFDI_TCB.set_enable(True)
        #Continuously output until we reach the set point
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(TCB_at_temp, temperature, LFDI_TCB, tolerance))
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 300 #wait for 5 minutes
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))

        #Rename the spectrometers current image, graph and Crosssection with the temperature and move them to the experiment folder
       # os.rename(spectrometer.current_image, f"{folder}/{str(temperature)}C.tif")
        os.rename(spectrometer.current_graph, f"{folder}/{str(temperature)}C.png")
        os.rename(spectrometer.current_crosssection, f"{folder}/{str(temperature)}C.csv")
        print(f"Finished {temperature}C")
    return

#wait for a certain time from the input time
def wait_time(start, wait_time):
    #Get the current time
    current_time = time.time()
    #Check if the current time is greater than the input time plus the wait time
    if current_time > (start + wait_time):
        return True
    else:
        return False

#Check to see if the TCB temp is at the set point
def TCB_at_temp(temp, TCB, tolerance):
    #Get the current temperature
    try:
        current_temp = float(TCB.get_average_temperature())
    except ValueError as e:
        print(f"Value Error {e} board request may have desynced")
        return False
    
    #Check if the current temperature is within the tolerance of the set point
    print(f"Sensor at {current_temp} waiting for {(temp - tolerance)}")
    if (current_temp > (temp - tolerance)) and (current_temp < (temp + tolerance)):
        return True
    else:
        return False

#Make an Experiment folder with date Time stamp
def make_experiment_folder():
    #Create the folder name
    now = datetime.datetime.now()
    folder_name = 'Experiment_' + now.strftime("%Y-%m-%d_%H-%M-%S")
    #Create the folder
    os.mkdir(folder_name)
    #Return the folder name
    return folder_name



#TO-DO Need to make a new thread to poll the LFDI Raw Data and output to a TSV file
def get_LFDI_data(LFDI_TCB, folder):
    #Create a file to store the data
    file = open(f"{folder}/LFDI_Data.tsv", 'w')
    #Write the header
    file.write(LFDI_TCB.get_raw_data_header())
    #Get the data
    data = LFDI_TCB.get_raw_data()
    #Write the data
    file.write(data)

#Function that will guid user through the calibration process
def calibrate_LED(spectrometer, folder):
    print("Adjust the Intensity of the LED until the signal is no longer clipping\r\nClose the Graph when adjusted")
    spectrometer.continuous_output()
    #make a sub folder in the experiment folder to store the calibration images
    os.mkdir(f"{folder}/LED Calibration")
    os.rename(spectrometer.current_image, f"{folder}/LED Calibration/Calibration.tif")
    os.rename(spectrometer.current_graph, f"{folder}/LED Calibration/Calibration.png")
    os.rename(spectrometer.current_crosssection, f"{folder}/LED Calibration/Calibration.csv")
    
    return

if __name__ == "__main__":
    #Create the Spectrometer
    try:
        spectrometer = Spectrograph.Spectrometer()
        spectrometer.camera.auto_exposure = False
    except:
        print("Could not connect to Spectrometer")
        exit()
    tolerance = .5
    #Create the LFDI_TCB
    try: 
        lfdi = LFDI.LFDI_TCB("COM3", 9600)
        lfdi.set_controller_kd(controller_number=1,kd=1)
        lfdi.set_controller_ki(controller_number=1,ki=0)
        lfdi.set_controller_kp(controller_number=1,kp=1)
    except:
        print("Could not connect to LFDI_TCB")
        exit()
    
    #ask the user if they want to sample for ambient temperature or enter it manually
    response = input("Would you like to sample the ambient temperature? [y/n]")
    

    #Sample the ambient temperature
    if response.lower() == 'y':
        #Sample the ambient temperature
        ambient_temperature = None
        #Update all the information we have on the Computer
        lfdi.get_info()
        while ambient_temperature is None:
            ambient_temperature = lfdi.Controllers[0].average()
            time.sleep(1)
            lfdi.get_info()
        print(f"Ambient Temperature: {ambient_temperature}C")
    else:
        #Ask the user to enter the ambient temperature
        ambient_temperature = float(input("Enter the ambient temperature [C]: "))
    
    #Create folder
    folder = make_experiment_folder()
    calibrate_LED(spectrometer, folder)

    
    #Cycle through the temperatures
    #SquareWave_Sweep(spectrometer, lfdi, float(ambient_temperature), 30, .5, start_voltage=0, end_voltage=10, step_voltage=.1, tolerance=0.1, folder=folder)
    Temp_Compensation(spectrometer, lfdi, float(ambient_temperature), 30, .5, tolerance=0.1, folder=folder)
    