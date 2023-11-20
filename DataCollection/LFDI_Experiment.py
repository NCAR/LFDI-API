
import numpy as np
import Hardware_API.LFDI_API as LFDI
import time
import Hardware_API.Spectrograph as Spectrograph
import os
import datetime
from functools import partial

# All filenames in the experiment should follow the following convention
# {PREFIX}_{DATETIME}_{VOLTAGE}V_{TEMPERATURE}C_Comp{COMPENSATION}_{WAVELENGTH}nm
# Where [PREFIX] is a general purpose prefix for the file can be used however you want as long as it contains valid file name caracters and no periods, spaces or underscores
# Where [DATETIME] is the date and time of the experiment in the format YYYY-MM-DD_HH-MM-SS
# Where [VOLTAGE] is the Drive Voltage of the optic volts
# Where [TEMPERATURE] is the temperature of the crystal in degrees Celsius
# Where [COMPENSATION] is the the indicator fo if the Compensation Algorythim is on or off [ON/OFF]
# Where [WAVELENGTH] is the wavelength of the light in nanometers ie 656.28 if the compensator was not used this should read 0





# test out the Compensation algos at various temps and wavelengths
def Temp_Compensation(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI, start_temp, end_temp, step, tolerance, folder):
    print(f"Start Temp {start_temp}")
    print(f"End Temp {end_temp}")
    print(f"Step Temp {step}")
    # Create a list of temperatures to cycle through
    # Go from the low temperature to the high temperature then back to the low temperature
    temperatures = np.arange(start_temp, end_temp, step)
    print(f"Temps: {temperatures}")
    temperatures = np.append(temperatures, np.arange(end_temp, start_temp, -step))
    print(f"Temps: {temperatures}")
    wavelengths = np.arange(20, 420, 50)
    # Create a list to store the filenames of the images
    filename = f"{folder}\\TCB_Out.tsv"
    file = open(filename, "w")
    file.write(f"{LFDI_TCB.header_format}\n")
    file.close()
    # Cycle through the temperatures. Take a measurement while the temperature is moving hold at each temperature for 5 minutes
    # Turn on the Auto Compensator Algo on compensator 3
    LFDI_TCB.set_compensator_auto(3)
    # Dummy wave to hold in place
    LFDI_TCB.set_compensator_wavelength(3,100)
    # Enable the Compensator
    LFDI_TCB.set_compensator_enable(3,True)
    
    # Go through all of our wavelengths
    for wavelength in wavelengths:
        # Set the Compensator to the current wavelength
        LFDI_TCB.set_compensator_wavelength(3,wavelength)
        # Go through the temperatures
        for temperature in temperatures:
            # Set the temperature
            LFDI_TCB.set_controller_setpoint(controller_number = 1, setpoint = temperature)
            LFDI_TCB.set_controller_enable(controller_number = 1, enable = True)
            temporal_resolution = 1*60 #1 minute
            # Continuously output until we reach the set point
            while not TCB_at_temp(temperature, LFDI_TCB, tolerance):
                # Get the Current time and output the spectrograph for a minute
                now = time.time()
                spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, temporal_resolution))
                # Take a measurement
                # Get the Current Temp From LFDI
                file = open(filename,"a")
                file.write(f"{LFDI_TCB.get_info()}\n")
                file.close()
                current_temp = LFDI_TCB.Controllers[0].average
                # Format the Current Temp to be a string with 2 decimal places
                current_temp = f"{float(current_temp):.2f}"
                os.rename(spectrometer.current_crosssection, f"{folder}/Slew_{LFDI_TCB.Compensators[2].wave}Pos_{str(time.time())}_{str(current_temp)}C_{LFDI_TCB.Compensators[2].voltage}V.csv")
            print(f"Reached {temperature}C")
            print("Waiting 5 minutes")
            # Wait For the Crystal to warm through out
            now = time.time()
            seconds_to_wait = 300 # wait for 5 min
            while not wait_time(now, seconds_to_wait):
                current_time = time.time()
                spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, temporal_resolution))
                file = open(filename, "a")
                file.write(f"{LFDI_TCB.get_info()}\n")
                file.close()
                current_temp = LFDI_TCB.Controllers[0].average
                # Format the Current Temp to be a string with 2 decimal places
                current_temp = f"{float(current_temp):.2f}"
                os.rename(spectrometer.current_crosssection, f"{folder}/Hold_{LFDI_TCB.Compensators[2].wave}Pos_{str(time.time())}_{str(current_temp)}C_{LFDI_TCB.Compensators[2].voltage}V.csv")
            print("Finished Waiting")
            print(f"Finished {temperature}C")
        print(f"Finished {wavelength}Pos")
    return


def Total_Data_Collection(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI, start_temp: float, end_temp: float, step_temp: float, tolerance: float, start_voltage: float, end_voltage: float, step_voltage : float, folder):
    
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
    LFDI_TCB.set_compensator_enable(3, True)
    # Go through the temperatures
    for temperature in temperatures:
        # Change to a known state
        LFDI.Compensators[2].voltage = 3
        LFDI.Compensators[2].enable = True
        
        # Set the temperature
        LFDI_TCB.set_controller_setpoint(controller_number=1, setpoint=temperature)
        LFDI_TCB.set_controller_enable(controller_number=1, enable=True)
        temporal_resolution = 1*60 # 1 minute
        while not TCB_at_temp(temperature, LFDI_TCB, tolerance):
            # Get the Current time and output the spectrograph for a minute
            now = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, temporal_resolution))
            # Take a measurement
            # Get the Current Temp From LFDI
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[0].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"Slew_{str(time.time())}_{LFDI_TCB.Compensators[2].voltage}V_{current_temp}C_CompOff_0nm.png"
            os.rename(spectrometer.current_image, f"{folder}/{filename}")
        
        print(f"Reached {temperature}C")
        print("Waiting 5 minutes")
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 600 #wait for 10 min
        while not wait_time(now, seconds_to_wait):
            current_time = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, temporal_resolution))
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[0].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"Hold_{str(time.time())}_{LFDI_TCB.Compensators[2].voltage}V_{current_temp}C_CompOff_0nm.png"
            os.rename(spectrometer.current_image, f"{folder}/{filename}")

        print("Finished Waiting")
        print("Cycling through Voltages")
        for voltage in voltages:
            #Set the voltage
            LFDI_TCB.set_compensator_voltage(3, voltage)
            #Wait for the voltage to settle
            time.sleep(2)
            #Take a measurement
            now = time.time()
            spectrometer.single_output()
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[0].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"Hold_{str(time.time())}_{LFDI_TCB.Compensators[2].voltage}V_{current_temp}C_CompOff_0nm.png"
            os.rename(spectrometer.current_image, f"{folder}/{filename}")

        print(f"Finished {temperature}C")
    print("Finished Temp Cycle")


    #Now go through the temperatures with the Compensation Algorythm
    #Cycle through the temperatures. Take a measurement while the temperature is moving hold at each temperature for 5 minutes
    
    LFDI_TCB.set_compensator_enable(3,True)
    LFDI_TCB.toggle_compensator_auto(3)
    LFDI_TCB.set_compensator_wavelength(3, 100)

    #Go through the temperatures
    for temperature in temperatures:
        #Change to a known state
        #Set the temperature
        LFDI_TCB.set_controller_setpoint(controller_number = 1, setpoint = temperature)
        LFDI_TCB.set_controller_enable(controller_number = 1, enable = True)
        temporal_resolution = 1*60
        while not TCB_at_temp(temperature, LFDI_TCB, tolerance):
            #Get the Current time and output the spectrograph for a minute
            now = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, temporal_resolution))
            #Take a measurement
            #Get the Current Temp From LFDI
            file = open(filename,"a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[0].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"Slew_{str(time.time())}_{LFDI_TCB.Compensators[2].voltage}V_{current_temp}C_CompOn_100nm.png"
            os.rename(spectrometer.current_image, f"{folder}/{filename}")

        print(f"Reached {temperature}C")
        print("Waiting 5 minutes")
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 600 #wait for 10 min
        while not wait_time(now, seconds_to_wait):
            current_time = time.time()
            spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, temporal_resolution))
            file = open(filename, "a")
            file.write(f"{LFDI_TCB.get_info()}\n")
            file.close()
            current_temp = LFDI_TCB.Controllers[0].average
            current_temp = f"{float(current_temp):.2f}"
            filename = f"Hold_{str(time.time())}_{LFDI_TCB.Compensators[2].voltage}V_{current_temp}C_CompOn_100nm.png"
            os.rename(spectrometer.current_image, f"{folder}/{filename}")



def Run_Endurance_Test(spectrometer : Spectrograph.Spectrometer,LFDI_TCB: LFDI, tolerance, folder):
    
    filename = f"{folder}\\TCB_Out.tsv"
    file = open(filename, "a")
    file.write(f"{LFDI_TCB.header_format}\n")
    file.close()
    LFDI_TCB.set_compensator_auto(3)
    #Enable the Compensator        
    while True:

        #Pick a random temperature between 23 and 30
#        random_temp = np.random.randint(22.5,30)
        temperatures = np.arange(22.5,30,.5)
        #Pick a rondom Compensator
        #random_compensator = np.random.randint(0,6)
        #pick a random wavelength between 20 and 500
        random_wavelength = np.random.randint(20,415)
        #Set the Compensator to the random wavelength
        LFDI_TCB.set_compensator_wavelength(3,random_wavelength)
        #Set the temperature
        LFDI_TCB.set_controller_enable(controller_number = 1, enable = True)
        #Turn on the Auto Compensator Algo on compensator 3

        LFDI_TCB.set_compensator_enable(3,True)
        #Continuously output until we reach the set point
        for temp in temperatures:
            LFDI_TCB.set_controller_setpoint(controller_number = 1, setpoint = temp)

            while not TCB_at_temp(temp, LFDI_TCB, tolerance):
                #Get the Current time and output the spectrograph for a minute
                now = time.time()
                spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, now, 60))
                #Take a measurement
                file = open(filename, "a")
                file.write(f"{LFDI_TCB.get_info()}\n")
                file.close()
                #Get the Current Temp From LFDI
                current_temp = LFDI_TCB.Controllers[0].average
                
                #Format the Current Temp to be a string with 2 decimal places
                current_temp = f"{float(current_temp):.2f}"
                os.rename(spectrometer.current_crosssection, f"{folder}/Slew_{LFDI_TCB.Compensators[2].wave}Pos_{str(time.time())}_{str(current_temp)}C_{LFDI_TCB.Compensators[2].voltage}V.csv")
            print(f"Reached {temp}C")
            print("Waiting 5 minutes")
            #Wait For the Crystal to warm through out
            now = time.time()
            seconds_to_wait = 300 #wait for 5 min
            while not wait_time(now, seconds_to_wait):
                current_time = time.time()
                spectrometer.continuous_output(refresh_rate=1, end_trigger=partial(wait_time, current_time, 60))
                current_temp = LFDI_TCB.Controllers[0].average
                file = open(filename, "a")
                file.write(f"{LFDI_TCB.get_info()}\n")
                file.close()
                #Format the Current Temp to be a string with 2 decimal places
                current_temp = f"{float(current_temp):.2f}"
                os.rename(spectrometer.current_crosssection, f"{folder}/Hold_{LFDI_TCB.Compensators[2].wave}Pos_{str(time.time())}_{str(current_temp)}C_{LFDI_TCB.Compensators[2].voltage}V.csv")


# Sweep the temperature of the TCB and the Voltage applied from the DAC; take an image at each state
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
        LFDI_TCB.set_controller_setpoint(1, temperature)
        LFDI_TCB.set_controller_enable(1, True)
        #Continuously output until we reach the set point
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(TCB_at_temp, temperature, LFDI_TCB, tolerance))
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 300 #wait for 5 minutes
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))
        for voltage in voltages:
            #Rename the spectrometers current image, graph and Crosssection with the temperature and move them to the experiment folder
            LFDI_TCB.set_compensator_voltage(3, voltage)
            seconds_to_wait = 10
            spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))
            os.rename(spectrometer.current_image, f"{folder}/{str(temperature)}C_{voltage}V.tif")
            os.rename(spectrometer.current_graph, f"{folder}/{str(temperature)}C_{voltage}V.png")
            os.rename(spectrometer.current_crosssection, f"{folder}/{str(temperature)}C_{voltage}V.csv")
            print(f"Finished Voltage {voltage}V")
        print(f"Finished {temperature}C")
    return

# Cycle through Temperatures and take an image at each temperature
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
        LFDI_TCB.set_controller_setpoint(1,temperature)
        LFDI_TCB.set_controller_enable(1,True)
        #Continuously output until we reach the set point
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(TCB_at_temp, temperature, LFDI_TCB, tolerance))
        #Wait For the Crystal to warm through out
        now = time.time()
        seconds_to_wait = 300 #wait for 5 minutes
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(wait_time, now, seconds_to_wait))

        #Rename the spectrometers current image, graph and Crosssection with the temperature and move them to the experiment folder
       # os.rename(spectrometer.current_image, f"{folder}/{str(temperature)}C.tif")
       # os.rename(spectrometer.current_graph, f"{folder}/{str(temperature)}C.png")
       #Take the Current CSV from the Spectrometer
        os.rename(spectrometer.current_crosssection, f"{folder}/{str(temperature)}C.csv")
        print(f"Finished {temperature}C")
    return

# wait for a certain time from the input time
def wait_time(start, wait_time):
    #Get the current time
    current_time = time.time()
    #Check if the current time is greater than the input time plus the wait time
    if current_time > (start + wait_time):
        return True
    else:
        return False



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



# Make an Experiment folder with date Time stamp
def make_experiment_folder():
    #Create the folder name
    now = datetime.datetime.now()
    folder_name = 'Experiment_' + now.strftime("%Y-%m-%d_%H-%M-%S")
    #Create the folder
    os.mkdir(folder_name)
    #Return the folder name
    return folder_name



# This Function will set the camera gain and exposure
def calibrate_camera(spectrometer):
    print("Adjust the Camera settings until the image is in focus\r\nClose the Graph to adjust")

    #Set the camera exposure
    camera_exposure_good = False
    while not camera_exposure_good:
        camera_exposure = input("Enter the Camera Exposure in seconds (default .3 sec): ")
        try:
            #Make sure the entered value is a positive float
            camera_exposure = float(camera_exposure)
            if camera_exposure < 0:
                raise ValueError("Camera Exposure must be a positive number")
        except ValueError as e:
            print(f"Value Error {e} Please enter a positive number")

        spectrometer.camera.set_exposure(camera_exposure)
        # Show the Spectrograph output for the User to adjust the camera exposure
        spectrometer.single_output(show = True)
        # Ask the user if the camera exposure is good
        response = input("Is the Camera Exposure Good? (y/n): ")
        if response == "y":
            camera_exposure_good = True

    return
    

# Calibrate the Spectrometer to the H-Alph line
def calibrate_spectrometer(spectrometer, folder):
    print("Adjust the Spectrometer until the H-Alph line is centered\r\nClose the Graph when adjusted")
    spectrometer.continuous_output()
    os.mkdir(f"{folder}/H-Alpha Calibration")
    os.rename(spectrometer.current_image, f"{folder}/H-Alpha Calibration/Calibration.tif")
    os.rename(spectrometer.current_graph, f"{folder}/H-Alpha Calibration/Calibration.png")
    os.rename(spectrometer.current_crosssection, f"{folder}/H-Alpha Calibration/Calibration.csv")
    return    


# Function that will guid user through the calibration process
def calibrate_LED(spectrometer, folder):
    print("Adjust the Intensity of the LED until the signal is no longer clipping\r\nClose the Graph when adjusted")
    spectrometer.continuous_output()
    #make a sub folder in the experiment folder to store the calibration images
    os.mkdir(f"{folder}/LED Calibration")
    os.rename(spectrometer.current_image, f"{folder}/LED Calibration/Calibration.tif")
    os.rename(spectrometer.current_graph, f"{folder}/LED Calibration/Calibration.png")
    os.rename(spectrometer.current_crosssection, f"{folder}/LED Calibration/Calibration.csv")
    
    return


# Launches here
if __name__ == "__main__":
    # Create the Spectrometer
    try:
        spectrometer = Spectrograph.Spectrometer()
        spectrometer.camera.auto_exposure = False

    except Exception as e:
        print(f"Could not connect to Spectrometer Camera {e}")
        exit()
    
    # Create the LFDI_TCB
    try:
        lfdi = LFDI.LFDI_TCB("COM3", 9600)
        lfdi.set_controller_kd(controller_number=1, kd=1)
        lfdi.set_controller_ki(controller_number=1, ki=0)
        lfdi.set_controller_kp(controller_number=1, kp=1)
    # Except if we can't connect to the LFDI_TCB
    except Exception as e:
        print(f"Could not connect to LFDI_TCB On Com3 {e}")
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
            ambient_temperature = lfdi.Controllers[0].average
            time.sleep(1)
            lfdi.get_info()
        print(f"Ambient Temperature: {ambient_temperature}C")
    else:
        #Ask the user to enter the ambient temperature
        ambient_temperature = float(input("Enter the ambient temperature [C]: "))
    
    

    #Create folder
    folder = make_experiment_folder()
    calibrate_camera(spectrometer)
    calibrate_LED(spectrometer, folder)
    #spectrometer.camera.set_exposure(0.005)
    
    #Cycle through the temperatures
    #SquareWave_Sweep(spectrometer, lfdi, float(ambient_temperature), 30, .5, start_voltage=0, end_voltage=10, step_voltage=.1, tolerance=0.1, folder=folder)
    #Temp_Compensation(spectrometer, lfdi, float(ambient_temperature), 30, 1, tolerance=0.5, folder=folder)
    #Run_Endurance_Test(spectrometer=spectrometer, LFDI_TCB=lfdi,tolerance=.5, folder= folder)
    Total_Data_Collection(spectrometer=spectrometer, LFDI_TCB=lfdi, start_temp=float(ambient_temperature), end_temp=30, step_temp=.5, tolerance=.25, start_voltage = 0 , end_voltage = 12, step_voltage = .1, folder=folder)