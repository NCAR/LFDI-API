
import numpy as np
import LFDI_API as LFDI
import time
import Spectrograph
import os
import datetime
from functiools import partial
#Cycle through Temperatures and take an image at each temperature
def temperature_cycle(spectrometer,LFDI_TCB, start_temp, end_temp, step, tolerance, folder):
    #Create a list of temperatures to cycle through
    temperatures = np.arange(start_temp, end_temp, step)
    #Create a list to store the filenames of the images
    
    #Cycle through the temperatures
    for temperature in temperatures:
        #Set the temperature
        LFDI_TCB.set_temperature(temperature)
        LFDI_TCB.set_enable(True)
        #Continuously output until we reach the set point
        spectrometer.continuous_output(refresh_rate=0.5, end_trigger=partial(TCB_at_temp, temperature, LFDI_TCB, tolerance))
        #Rename the spectrometers current image, graph and Crosssection with the temperature and move them to the experiment folder
        os.rename(spectrometer.current_image, f"{folder}/{str(temperature)}C.tif")
        os.rename(spectrometer.current_graph, f"{folder}/{str(temperature)}C.png")
        os.rename(spectrometer.current_crosssection, f"{folder}/{str(temperature)}C.csv")
        print(f"Finished {temperature}C")
    return
        
#Check to see if the TCB temp is at the set point
def TCB_at_temp(temp, TCB, tolerance):
    #Get the current temperature
    current_temp = float(TCB.get_average_temperature())
    #Check if the current temperature is within the tolerance of the set point
    if (current_temp > (temp - tolerance)) and (current_temp < (temp + tolerance)):
        return True
    else:
        return False

#Make an Experiment folder with date Time stamp
def make_experiment_folder():
    #Create the folder name
    folder_name = 'Experiment_' + str(datetime.datetime.now())
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


if __name__ == "__main__":
    #Create the Spectrometer
    try:
        spectrometer = Spectrograph.Spectrometer()
    except:
        print("Could not connect to Spectrometer")
        exit()
    tolerance = .05
    #Create the LFDI_TCB
    try: 
        lfdi = LFDI.LFDI_TCB("COM3", 9600)
    except:
        print("Could not connect to LFDI_TCB")
        exit()
    
    
    #ask the user if they want to sample for ambient temperature or enter it manually
    response = input("Would you like to sample the ambient temperature? [y/n]")
    if response.lower() == 'y':
        #Sample the ambient temperature
        ambient_temperature = lfdi.get_average_temperature()
        print(f"Ambient Temperature: {str(ambient_temperature)}C")
    else:
        #Ask the user to enter the ambient temperature
        ambient_temperature = float(input("Enter the ambient temperature [C]: "))
    #Create folder
    folder = make_experiment_folder()
    #Cycle through the temperatures
    temperature_cycle(spectrometer, lfdi, ambient_temperature, 30, 1, tolerance, folder)
    