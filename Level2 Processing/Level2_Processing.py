
from datetime import datetime
from scipy.signal import savgol_filter
import imageio
from Scan import Scan, TemperatueScanSet, VoltageScanSet, ExperimentSet
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#import maxnlocators
from matplotlib.ticker import MaxNLocator

#make a level 2 folder for the data
def makeLevel2Folder(path):
    #get the current time
    now = datetime.now()
    #format the time
    dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    #make the folder
    os.mkdir(path + "Level2_" + dt_string)
    return path + "Level2_" + dt_string



#Fix Discontinuities in the data 
# TODO This is Completly Hands on Needs to Be more Automated Its difficult to look for True Discontinuities in messy data
def fixDiscontinuities(temperature_scan_set: TemperatueScanSet, threshold = 10):
    FixedLocalMaximas = []
    #Find the Scan with the Highest First Local Maxima
    highest_first_local_maxima = 0
    highest_first_local_maxima_scan = None
    for scan in temperature_scan_set.scans:
        if scan.first_local_maxima > highest_first_local_maxima:
            highest_first_local_maxima = scan.first_local_maxima
            highest_first_local_maxima_scan = scan
    #Copy over all the data points from the highest first local maxima scan
    for i in range(0, len(temperature_scan_set.scans)):
        FixedLocalMaximas.append(temperature_scan_set.scans[i].first_local_maxima)
    
    #For all Data points between 0 and 2.3V add the highest first local maxima to the data point + 25
    for i in range(0, 230):
        FixedLocalMaximas[i] += highest_first_local_maxima
    #For all Data points between 0 and 4.16V and add the highest first local maxima to the data point + 25
    for i in range(0, 416):
        FixedLocalMaximas[i] += highest_first_local_maxima 
    #Anypoints that are over 1060 Subtract highest first local maxima
    for i in range(0, len(FixedLocalMaximas)):
        if FixedLocalMaximas[i] > 1060:
            FixedLocalMaximas[i] -= highest_first_local_maxima
        if FixedLocalMaximas[i] < 120:
            FixedLocalMaximas[i] += highest_first_local_maxima
    #if a point between 2.1 and 2.3V is less than 734 add the highest first local maxima to the data point
    for i in range(210, 260):
        if FixedLocalMaximas[i] < 734:
            FixedLocalMaximas[i] += highest_first_local_maxima
    #Remove the outliers points if they are too far away from their neighbours
    for i in range(0, len(FixedLocalMaximas)):
        if i > 0 and i < len(FixedLocalMaximas) - 1:
            if (abs(FixedLocalMaximas[i] - FixedLocalMaximas[i-1]) > threshold or abs(FixedLocalMaximas[i] - FixedLocalMaximas[i+1]) > threshold):
                FixedLocalMaximas[i] = (FixedLocalMaximas[i-1] + FixedLocalMaximas[i+1])/2
    #Smooth the data
    SmoothedLocalMaximas = savgol_filter(FixedLocalMaximas, 51, 3)
    SmoothedLocalMaximas = savgol_filter(SmoothedLocalMaximas, 51, 3)
    SmoothedLocalMaximas = savgol_filter(SmoothedLocalMaximas, 100, 3)
    return FixedLocalMaximas, SmoothedLocalMaximas
    




#Create a gif out of a list of Files
def createGif(file_list, save_path, filename = "CorrelationsAt23.1C.gif", delete_files = False):
    #make a list of images
    images = []
    for file in file_list:
        images.append(imageio.imread(file))
    #save the gif
    imageio.mimsave(save_path+"\\" + f'{filename}.gif', images)

    #Delete the files
    if delete_files:

        for file in file_list:
            #Check if file exists or if it's a directory
            if os.path.exists(file) and os.path.isfile(file):
                # Delete it
                os.remove(file)
    return


#Holds all of the Data for a Controller
class Controller():
    def __init__(self, number: int, dataframe: pd.DataFrame):
        self.data = dataframe
        self.number = number
        self.kp = self.getColumn('kp')
        self.kd = self.getColumn('kd')
        self.ep = self.getColumn('ep')
        self.ki = self.getColumn('ki')
        self.ed = self.getColumn('ed')
        self.ei = self.getColumn('ei')
        self.effort = self.getColumn('effort')
        self.temp = self.getColumn('temp', duplicate = 0)
        self.average = self.getColumn('average', duplicate = 0)
        self.target = self.getColumn('target')
        self.i2c = self.getColumn('i2c', duplicate = 0)
        self.hist = self.getColumn('hist')
        self.freq = self.getColumn('freq')
        self.enabled = self.getColumn('enabled', duplicate = 0)
        self.sensor = self.getColumn('sensor', duplicate = 0)

    def getColumn(self, column_name, duplicate = None):
        if duplicate == None:
            return self.data[column_name].values
        else:
            return self.data.filter(like=column_name).iloc[:,duplicate]


#Make a child class of the TCB_TSV class
class Compensator():
    def __init__(self, number, dataframe):
        self.data = dataframe
        self.Peak2Peak = self.getColumn('Peak2Peak', duplicate = number-1)
        self.Wave = self.getColumn('Wave', duplicate = number-1)
        self.Temp = self.getColumn('Temp', duplicate = number)
        self.Avg = self.getColumn('Avg', duplicate = number)
        self.Auto = self.getColumn('Auto', duplicate = number-1)
        self.UseAverage = self.getColumn('UseAverage', duplicate = number-1)
        self.i2c = self.getColumn('i2c', duplicate = number)
        self.enabled = self.getColumn('enabled', duplicate = number)
        self.sensor = self.getColumn('sensor', duplicate = number)
    
    def getColumn(self, column_name, duplicate = None):
        if duplicate == None:
            return self.data[column_name].values
        else:
            return self.data.filter(like=column_name).iloc[:,duplicate]


#This class will contain the data for a tsv file
#all data will be read in and stored in a numpy array
#The data has the header of 
class TCB_TSV:

    def __init__(self, filename):
        self.filename = filename
        self.header = "Date\tTime\tCont\tkp\tkd\tki\tep\ted\tei\teffort\ttemp\taverage\ttarget\ti2c\thist\tfreq\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\tComp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor\t"
        self.data = []
        self.readData()
        self.Controller = Controller(1, self.data)
        self.Compensators = [Compensator(1, self.data), Compensator(2, self.data),Compensator(3, self.data)]
        self.date = self.getColumn('Date')
        self.time = self.getColumn('Time')
        
    #Read the data from the file into a pandas dataframe
    def readData(self):
        self.data = pd.read_csv(self.filename, sep='\t', header=0)
        self.data.columns = self.header.split('\t')
        return

    def getColumn(self, column_name, duplicate = None):
        if duplicate == None:
            return self.data[column_name].values
        else:
            return self.data.filter(like=column_name).iloc[:,duplicate]


    #Plot the Target and Temperature data of the Controller against the date and time
    def plot(self, show = False):
        #Create a figure
        fig = plt.figure()
        ax = fig.add_subplot(111)

        #Plot the data
        ax.plot(self.time, self.Controller.target, label = "Target")
        ax.plot(self.time, self.Controller.temp, label = "Temperature")

        #Set the axis labels
        ax.set_xlabel("Time")
        ax.set_ylabel("Temperature (C)")

        #Set the title
        ax.set_title(f"Target and Temperature vs Time")

        #Set the legend
        ax.legend()

        #only show 5 xticks
        ax.xaxis.set_major_locator(MaxNLocator(5))
        
        

        #Show the plot
        if show:
            plt.show()
        return
    


#Main Function
if __name__ == '__main__':
    path = "C:\\Users\\mjeffers\\Desktop\\"
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"

    TCB_TSV_file = f"{path}TCB_Out.tsv"
    tcb = TCB_TSV(TCB_TSV_file)
    tcb.plot(show=True)

    scan_path = f"{path}Experiment_2023-01-20_15-19-55\\"
    scan_path = f"{path}Experiment_2023-01-23_14-48-31\\"


    l2_path = makeLevel2Folder(path)
    
    #find all CSV files in the directory
    os.chdir(scan_path)
    files = glob.glob("*.csv")

    #Create a list of Scan objects
    scans = []
    for file in files:
        scan = Scan(file)
        #scan.plot(plot_smoothed = True, convert_to_nm=False,show=True, save=True, save_path=l2_path)
        scans.append(scan)
    
    #Create a Gif of the scan plots
    #Get all scans With 3.0 V
    #scans = [scan for scan in scans if scan.voltage == 3.0]
    #Sort the scans by temperature
    scans.sort(key=lambda x: x.temperature)
    
    #Create a list of the file names of the plots
    plot_list = []
    print(f"Plotting all the Scans")
    for scan in scans:
        scan.plot(plot_smoothed = True, convert_to_nm=False,show=False, save=True, save_path=l2_path)
        plot_list.append(f"{l2_path}\\{str(scan.temperature)}C_{str(scan.voltage)}V.png")

    print("Making Gif")
    createGif(plot_list, l2_path, "UnCompensatedTemperatureSweep", delete_files=True)
    #Go through all the Scans and find the average distance between the local maxima

    #find all the scans that have the same temperature
    print("Grouping the scans by temperature and Voltage")
    temperature_scan_sets = []
    temperatureList = []
    voltageList = []
    voltage_scan_sets = []
    for scan in scans:
        TemperatureScans = []
        #Find if we already have a scan set with this temperature
        if scan.temperature not in temperatureList:
            temperatureList.append(scan.temperature)
            #Find all the scans that match this temperature
            for scan2 in scans:
                if scan.temperature == scan2.temperature:
                    TemperatureScans.append(scan2)
            #Make a new scan set with the matching scans
            temperature_scan_sets.append(TemperatueScanSet(scan.temperature, TemperatureScans))
        
        voltageScans = []
        #If the Voltage is not in the list of voltages add it to the list
        if scan.voltage not in voltageList:
            voltageList.append(scan.voltage)
            #Find all the scans that match this voltage
            for scan2 in scans:
                if scan.voltage == scan2.voltage:
                    voltageScans.append(scan2)
            #Make a new scan set with the matching scans
            voltage_scan_sets.append(VoltageScanSet(scan.voltage, voltageScans))

    #plot  the scans that have the same voltage
    filenames = []
    for voltage_scan_set in voltage_scan_sets:        
        filenames.append(voltage_scan_set.plotFirstLocalMaximasVsTemperature(save=True, folder=l2_path))

    createGif(filenames, l2_path, filename="TemperatrueSweep")

    #plot the scans that have the same temperature
    for temperature_scan_set in temperature_scan_sets:
        temperature_scan_set.plotFirstLocalMaximas(save=True, folder=l2_path)
    

    #make an Experiment Set
    experiment_set = ExperimentSet(scans, l2_path)
    #3d plot
    print("Creating 3D Plots")
    experiment_set.plot3DLocalMaximas(scans, save=True, save_path=l2_path)
    #Run a Correlation based on a seed
    seed_scan = None
    for scan in scans:
        if scan.temperature == 23.1:
            seed_scan = scan
    experiment_set.correlateAllScans(seed_scan, save=True, save_path=l2_path)

    print("Creating a CSV of the Data Collected at Temperature: {CSVTemp}") 
    for tempSet in temperature_scan_sets:
        plot, Smoothed = tempSet.plotFirstLocalMaxima(show = True, save=True, save_path=l2_path, FixDiscontinuities=True)
        tempSet.createCSVOfVoltageSortedByPosition(save_path=l2_path, FixedData=Smoothed)
    
    
    
    # # plotLocalMaximasVsVoltageSameTemperature(scans, fit_a_line=True, save=True, save_path=l2_path)
    # # #2d plot
    #plotLocalMaximasVsTemperatureSameVoltage(scans, fit_a_line=True, save=True, save_path=l2_path)

    #find the correlation of every other scan in the set of temperature scans
    #Find the Scan that is closest to 23C and 3.0V
    # seed_scan = None
    # files = []
    # for scan in scans:
    #     if scan.temperature == 23.1:
    #         seed_scan = scan
    #         print("Creating Correlation Plots")
    #         correlation_matrix, filename = findCorrelation(seed_scan, temperature_scan_sets, save=True, save_path=l2_path)
    #         files.append(filename)
    # #Create a Gif out of the correlation plots
    # createGif(files, save_path=l2_path)
    
    print('Done')