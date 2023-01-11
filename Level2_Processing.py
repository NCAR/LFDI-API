import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import savgol_filter
#Smooth a 1D csv and plot it


class Scan:
    def __init__(self, filename):
        self.filename = filename
        self.data = np.loadtxt(filename, delimiter=',')
        self.smoothed_data = savgol_filter(self.data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 100, 3)
        self.maxima, self.minima = self.findLocalMaximaMinima(len(self.smoothed_data), self.smoothed_data)
        #if the second maxima value is biger than the first, then the first maxima is the second maxima
        if self.smoothed_data[self.maxima[1]] > self.smoothed_data[self.maxima[0]]:
            self.first_local_maxima = self.maxima[1]
        else:
            self.first_local_maxima = self.maxima[0]
        #Get the temperature from the filename by getting the filename without the extension and converting it to a float
        self.temperature = float(filename[:-5])
        return

    def findLocalMaximaMinima(self, n, arr):

        # Empty lists to store points of
        # local maxima and minima
        mx = []
        mn = []
    
        # Checking whether the first point is
        # local maxima or minima or neither
        if(arr[0] > arr[1]):
            mx.append(0)
        elif(arr[0] < arr[1]):
            mn.append(0)
    
        # Iterating over all points to check
        # local maxima and local minima
        for i in range(1, n-1):
    
            # Condition for local minima
            if(arr[i-1] > arr[i] < arr[i + 1]):
                mn.append(i)
    
            # Condition for local maxima
            elif(arr[i-1] < arr[i] > arr[i + 1]):
                mx.append(i)
    
        # Checking whether the last point is
        # local maxima or minima or neither
        if(arr[-1] > arr[-2]):
            mx.append(n-1)
        elif(arr[-1] < arr[-2]):
            mn.append(n-1)
    
            # Print all the local maxima and
            # local minima indexes stored
        
        return mx, mn

    #plot the Scan data. If the calibration data is provided, plot the mercury and hydrogen position on the graph as well, if convert_to_nm is true, convert the x axis to nm
    def plot(self, calibration_data = None,convert_to_nm = False, save = False, save_path = None):
        plt.figure(figsize=(30.0, 10.0))
        plt.plot(self.data, label = 'Raw Data')
        plt.plot(self.smoothed_data, label = 'Smoothed Data')
        plt.plot(self.maxima, self.smoothed_data[self.maxima], 'o', label = 'Maxima')
        plt.plot(self.minima, self.smoothed_data[self.minima], 'o', label = 'Minima')
        if calibration_data is not None:
            #Create a Vertical Line with a label at the Hydrogen, deuterium and Mercury Position
            plt.axvline(x = calibration_data.Hydrogen_Pixel_Position, color = 'r', label = 'Hydrogen')
            plt.axvline(x = calibration_data.Mercury_Pixel_Position, color = 'g', label = 'Mercury')
            plt.axvline(x = calibration_data.Deuterium_Pixel_Position, color = 'b', label = 'Deuterium')

        if convert_to_nm:
            plt.xlabel('Wavelength (nm)')
            #Convert the x axis to nm using Pixel Scaling and Pixel Offset            
            plt.xticks(np.arange(0, len(self.smoothed_data), 1), np.arange(calibration_data.Pixel_Offset, len(self.smoothed_data)*calibration_data.Pixel_Scaling + calibration_data.Pixel_Offset, calibration_data.Pixel_Scaling)[:-1])

            #only show 10 ticks
            plt.locator_params(axis='x', nbins=10)

            
        else:
            plt.xlabel('Pixel Position')
        plt.ylabel('Intensity')
        plt.legend()
        if save:
            #Save as full screen png
            plt.savefig(save_path+"\\" + str(self.temperature) + '.png', bbox_inches='tight')
            
        plt.show()
        return

#Go through all the Scans and find the local maxima that is furthest to the right
def findMaxima(scans):
    maxima = 0
    for scan in scans:
        if scan.first_local_maxima > maxima:
            maxima = scan.first_local_maxima
    return maxima

#plot all the local maximas of the scans in the format nm offset vs the temperature
def plotLocalMaximas(scans, calibration, save = False, save_path = None):
    plt.figure(figsize=(30.0, 10.0))
    for scan in scans:
        plt.plot(scan.temperature, scan.first_local_maxima, 'o')
    plt.xlabel('Temperature (C)')
    plt.ylabel('First Maxima (nm)')
    plt.title('First Maxima vs Temperature')
    Furthest_Maxima = findMaxima(scans)
    #Convert the y axis to nm using Pixel Scaling and Pixel Offset with 2 decimal places
    plt.yticks(np.arange(0, Furthest_Maxima, 1), np.around(np.arange(calibration.Pixel_Offset, Furthest_Maxima*calibration.Pixel_Scaling + calibration.Pixel_Offset, calibration.Pixel_Scaling), 2))

    #only plot 10 ticks
    plt.locator_params(axis='y', nbins=10)
    #add grid lines
    plt.grid()
    if save:
        plt.savefig(save_path+"\\" + 'First Maxima vs Temperature.png', bbox_inches='tight')
    plt.show()
    return


#open the Hydrogen Calibration csv and find the max value
def findHydrogenMax(filename):
    data = np.loadtxt(filename, delimiter=',')
    return np.argmax(data)

#Find every entry that has the same value as the max value and return the average of the pixel position
def findHydrogenPixelPosition(filename):
    data = np.loadtxt(filename, delimiter=',')
    max_value = np.max(data)
    max_value_positions = np.where(data == max_value)
    return np.average(max_value_positions)

#Calibration class to hold the calibration data
#The calibration format 
# Calibration Date: 2023-01-10 16:29:10.166252
# ZWO Camera Settings:
# Camera Info: {'Name': 'ZWO ASI1600MM', 'CameraID': 0, 'MaxHeight': 3520, 'MaxWidth': 4656, 'IsColorCam': False, 'BayerPattern': 2, 'SupportedBins': [1, 2, 3, 4], 'SupportedVideoFormat': [0, 2], 'PixelSize': 3.8, 'MechanicalShutter': False, 'ST4Port': 1, 'IsCoolerCam': False, 'IsUSB3Host': False, 'IsUSB3Camera': True, 'ElecPerADU': 0.0049600000493228436, 'BitDepth': 12, 'IsTriggerCam': 0}
# Binning: 1
# Width: 4656
# Height: 3520
# Image Type: 2
# Exposure: 3.2e-05
# Spectrometer Cross Section Position: middle
# Spectrometer Cross Section Width averaged over: 20
# Hydrogen Wavelength: 656.27 nm
# Hydrogen Pixel Position: 2122
# Deuterium Wavelength: 656.11 nm
# Deuterium Pixel Position: 2126
# Mercury Wavelength: 546.07 nm
# Mercury Pixel Position: 2184
# Pixel Scaling: -1.7774193548387085 nm/px
class Calibration:
    def __init__(self, filename):
        self.filename = filename
        #open the file and read the data
        with open(filename) as f:
            self.data = f.readlines()
        self.Hydrogen_Wavelength = self.get_Hydrogen_Wavelength()
        self.Hydrogen_Pixel_Position = self.get_Hydrogen_Pixel_Position()
        self.Mercury_Wavelength =  578.2
        self.Mercury_Pixel_Position = self.get_Mercury_Pixel_Position()
        self.Deuterium_Wavelength = 656.1
        self.Deuterium_Pixel_Position = self.get_Deuterium_Pixel_Position()
        self.Pixel_Scaling = self.get_Pixel_Scaling()
        self.Pixel_Offset = self.get_Pixel_Offset()

        return

    def get_Hydrogen_Wavelength(self):
        for line in self.data:
            #if the line contains the substring Hydrogen Wavelength, return the wavelength
            if 'Hydrogen Wavelength' in line:
                return float(line.split(' ')[2])

    def get_Hydrogen_Pixel_Position(self):
        #find the line that starts with Hydrogen Pixel Position
        for line in self.data:
            if 'Hydrogen Pixel Position' in line:
                    return int(line.split(' ')[3])
    
    def get_Mercury_Wavelength(self):
        #find the line that starts with Mercury Wavelength
        for line in self.data:
            if 'Mercury Wavelength' in line:
                return float(line.split(' ')[2])
    def get_Mercury_Pixel_Position(self):
        #find the line that starts with Mercury Pixel Position
        for line in self.data:
            if 'Mercury Pixel Position' in line:
                return int(line.split(' ')[3])

    def get_Deuterium_Wavelength(self):
        #find the line that starts with Deuterium Wavelength
        for line in self.data:
            if 'Deuterium Wavelength' in line:
                return float(line.split(' ')[2])

    def get_Deuterium_Pixel_Position(self):
        #find the line that starts with Deuterium Pixel Position
        for line in self.data:
            if 'Deuterium Pixel Position' in line:
                return int(line.split(' ')[3])

    def get_Pixel_Scaling(self):
        #Calculate the Pixel Scaling
        return (self.Deuterium_Pixel_Position - self.Hydrogen_Pixel_Position) / (self.Deuterium_Wavelength - self.Hydrogen_Pixel_Position)

    def get_Pixel_Offset(self):
        #Calculate the Pixel Offset
        return self.Deuterium_Wavelength - self.Deuterium_Pixel_Position * self.Pixel_Scaling

    def __str__(self):
        return "Hydrogen Wavelength: " + str(self.Hydrogen_Wavelength) + " nm\n" + "Hydrogen Pixel Position: " + str(self.Hydrogen_Pixel_Position) + "\n" + "Mercury Wavelength: " + str(self.Mercury_Wavelength) + " nm\n" + "Mercury Pixel Position: " + str(self.Mercury_Pixel_Position) + "\n" + "Deuterium Wavelength: " + str(self.Deuterium_Wavelength) + " nm\n" + "Deuterium Pixel Position: " + str(self.Deuterium_Pixel_Position) + "\n" + "Pixel Scaling: " + str(self.Pixel_Scaling) + " nm/px\n" + "Pixel Offset: " + str(self.Pixel_Offset) + " nm"

#Load in the Calibration file
def loadCalibration(filename):
    calibration = np.loadtxt(filename, delimiter=',')
    return calibration

#make a level 2 folder for the data
def makeLevel2Folder(path):
    #get the current time
    now = datetime.now()
    #format the time
    dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    #make the folder
    os.mkdir(path + "Level2_" + dt_string)
    return path + "Level2_" + dt_string

if __name__ == '__main__':
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\LFDI Temperature Sweep Trial Run\\"
    #Load in the calibration data
    calibration = Calibration(f"{path}Calibration_2023-01-10_16-23-35\\Calibration.txt")
    hydrogen_pixel_position = findHydrogenPixelPosition(f'{path}Calibration_2023-01-10_16-23-35\\Hydrogen_Calibration_CrossSection.csv')
    calibration.Hydrogen_Pixel_Position = hydrogen_pixel_position
    calibration.Pixel_Scaling = calibration.get_Pixel_Scaling()
    calibration.Pixel_Offset = calibration.get_Pixel_Offset()


    print(calibration)
    scan_path = f"{path}Experiment_2023-01-10_16-39-59\\"
    #find all CSV files in the directory
    import glob
    import os
    os.chdir(scan_path)
    files = glob.glob("*.csv")
    #Create a list of Scan objects
    scans = []
    l2_path = makeLevel2Folder(path)
    for file in files:
        scan = Scan(file)
        scan.plot(calibration_data=calibration, convert_to_nm=True, save=True, save_path=l2_path)
        scans.append(scan)
        
    plotLocalMaximas(scans, calibration, save=True, save_path=l2_path)
    print('Done')