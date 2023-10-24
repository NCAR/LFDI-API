from Hardware_API import NI_USB_6001_API as NI
from Hardware_API import LFDI_API
import numpy as np
import time
import os
import datetime
import matplotlib.pyplot as plt

#This file will run a test moving through multiple voltage with the LFDI Compensator 4 and recording the voltages on the NI_USB_6001
#after each voltage change.  The data will be saved to a file with the name of the current time.
#The data will be saved in a csv file with the following columns:
#   Time, NI_Voltage, LFDI Voltage, LFDI Temperature
#The data will be saved in a file with the following name:



def Transistion_Time_Experiment(lfdi: LFDI_API.LFDI_TCB,ni: NI.NI_USB_6001, transistions: list, output_folder, compensator: int):
    #
    lfdi.set_compensator_enable(compensator, True)  # Enable the compensator
        
    for transistion in transistions:
        # Go to the First Position
        lfdi.set_compensator_voltage(compensator, transistion[0]) #Set the voltage peak to peak of the compensator
        file = open(f'{output_folder}/LFDI_Data.tsv', "a")  # Open the file
        file.write(f"{lfdi.get_info()}\n")  # Write the data to the file
        file.close() # Close the file
        
        # Start an NI Voltage Measurement
        print("Starting Voltage Measurement")
        timer_handle = ni.get_voltage_array_continuous()
        lfdi.set_compensator_voltage(compensator, transistion[1])
        duration = ni.stop_continuous(timer_handle)
        data = ni.read_continuous(duration)
        
        print(f"Duration: {duration}")
        # Append the LFDI Data to the File
        file = open(f'{output_folder}/LFDI_Data.tsv', "a")
        file.write(f"{lfdi.get_info()}\n")
        file.close()
        
        # Read the Data
        
        # Match the Data with Timestamps
        timestamps = ni.match_timestamps(duration, timer_handle)
        # Save the Data
        # Save it to a TSV File with the Transistion Voltages as the Name
        file = open(f"{output_folder}/{transistion[0]}-{transistion[1]}.tsv", "w")
        file.write("Time\tNI_Voltage\n")
        print(f"Length of data: {len(data)}")
        print(f"Length of timestamps: {len(timestamps)}")
        for i in range(len(data)):
            file.write(f"{timestamps[i]}\t{data[i]}\n")
        file.close()
        
        time.sleep(1)

    return


if __name__ == '__main__':
    # create the output folder
    output_folder = f"Transistion_Time_Experiment_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
    os.mkdir(output_folder)
    # Create the LFDI Object
    lfdi = LFDI_API.LFDI_TCB("COM4", 9600, silent=True)

    lfdi.set_compensator_enable(4, True)  # Enable the compensator
    # Change the lfdi voltage
    while(True):
        lfdi.set_compensator_voltage(4, 0)
        time.sleep(5)
        lfdi.set_compensator_voltage(4, 12)


    # Create the NI Object
    ni = NI.NI_USB_6001()
    # Set the Sampling Frequency
    ni.set_sampling_frequency(500)
    # Create the Transistion List
    transistions = [[12, 0], [12, 0]]
    # Run the Experiment
    Transistion_Time_Experiment(lfdi, ni, transistions, output_folder, 4)
    # Close the NI Object
    ni.close()
    #plot the collected transistion data
    #read the data
    # The first column is the datetime in the format of %Y-%m-%d %H:%M:%S.%f 
    # The second column is the voltage
    dtype = [('datetime', 'U26'), ('voltage', float)]
    data = np.loadtxt(f"{output_folder}/{transistions[0][0]}-{transistions[0][1]}.tsv", dtype=dtype, delimiter='\t',skiprows=1)
    #get the timestamps
    timestamps = [datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f') for timestamp in data['datetime']]
    #get the voltages
    voltages = data['voltage']
    #plot the data
    plt.plot(timestamps, voltages)
    plt.xlabel("Time")
    plt.ylabel("Voltage")
    plt.title(f"Transistion Time {transistions[0][0]}-{transistions[0][1]}V")
    plt.savefig(f"{output_folder}/{transistions[0][0]}-{transistions[0][1]}.png")
    plt.show()


