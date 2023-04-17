#This File Contains the Scan Class implementation
#This class will hold information on a Spectra Cross section Scan

#Create a class for a scan
#This stores all of the data for a single scan

import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import numpy as np
from PIL import Image
import imageio
import os
from scipy import signal
import pickle



def ConversionEquation(x):
    #0.001 nm/px + 653.377 nm
    return .001*x + 654.377

scanformat = f"[PREFIX]_[TimeStamp]_[Voltage]V_[Temperature]C_Comp[Status]_[Wavelength]nm.png"
#This is the General Scan Class that will be used to Read in all of the CSVs
#The Expected name format is "PREFIX_TimeStamp_TemperatureC_VoltageV.csv"
#Prefix can be whatever the User Wants. Normally Experiment Based ie "Slew" "Hold"
#TimeStamp should the raw output of time.time()
#Temperature should be the Temperature that Scans are taken at
#Voltage should be the Voltage applied to the optic at the Time
class Scan:
    def __init__(self, filename, parentFolder):
        #Set the filename
        
        #Information Pulled from File name
        self.parentFolder = parentFolder
        self.filename = filename #set filename to the filename
        self.prefix = filename.split("_")[0] #set prefix to the first value in the filename, split by the "_"
        self.timestamp = filename.split("_")[1] #set timestamp to the second value in the filename, split by the "_"
        self.temperature = float(filename.split("_")[3].replace("C", "")) #set temperature to the third value in the filename, split by the "_"
        #remove the "V" from the voltage and the space from the voltage
        self.voltage = float(filename.split("_")[2].replace("V", "").replace(" ", "")) #set voltage to the fourth value in the filename, split by the "_" [remove the "V" from the voltage and the space from the voltage
        self.wavelength = float(filename.split("_")[5].split("nm")[0]) #set wavelength to the fifth value in the filename, split by the "_"
        self.compensated = filename.split("_")[4] == "CompOn" #set compensated to the sixth value in the filename, split by the "_"
        
        
        #Possible data asets
        self.cross_section = None
        self.smoothed_cross_section = None
        self.cross_section_location = 2000
        self.span = 20
        self.nearest_maxima = None
        self.processed = False
        #Git the scan a pickle name based on the scan format
        self.processed_pickle =  self.filename.replace(".png", ".pkl")




    def process(self):        
        self.cross_section = self.get_CrossSection(self.parentFolder, self.cross_section_location, self.span)
        self.smoothed_cross_section = self.smooth(self.cross_section)
        self.nearest_maxima = self.find_maxima(self.parentFolder, self.smoothed_cross_section, self.span)
        self.processed = True
        #Save the Scan as a pickle use the parent folder and the processed pickle name
        with open(os.path.join(self.parentFolder, self.processed_pickle), 'wb') as f:
            pickle.dump(self, f)
        return


    def get_CrossSection(self, parentFolder, crosssection, span):
        # Get the Image
        image = Image.open(os.path.join(parentFolder, self.filename))
        # Get the Cross Section
        # If Span is greater than 1 then we need to coaverage the Cross Section
        if span > 1:
            pixelValues_to_mean= []
            # Loop through the Cross Section
            r = round(span/2)
            for i in range(r):
                # Get the pixel values
                pixelValues_to_mean.append(np.array(image)[crosssection-(i), :])
                pixelValues_to_mean.append(np.array(image)[crosssection+(i), :])
            crosssection = np.mean(pixelValues_to_mean, axis=0)

        # Coaverage the Cross Section
        # Return the Cross Section
        return crosssection
        
    def smooth(self, crosssection):
        smoothed = savgol_filter(crosssection, 203, 2)
        #Use a butter worth filter to smooth the data the 4th order filter with a cutoff of 2/418
        b, a = signal.butter(4, 2/418, 'low', analog=False)
        smoothed = signal.filtfilt(b, a, smoothed)
        return smoothed
    
    #Find the Maxima closest to 1903 pixels
    def find_maxima(self, parentFolder, smoothed, span):
        #Find all the local maximas
        maxima = np.r_[True, smoothed[1:] > smoothed[:-1]] & np.r_[smoothed[:-1] > smoothed[1:], True]
        
        #Find the maxima closest to 1903 pixels
        maxima = np.where(maxima)[0]
        maxima = maxima[np.abs(maxima-1903).argmin()]
        
        #return the maxima
        return maxima



    def plot_cross_section(self, parentFolder, crosssection, span):
        crosssection = self.get_CrossSection(parentFolder, crosssection, span)
        plt.figure()
        plt.plot(crosssection)
        plt.show()

    def save_cross_section(self, filename, smooth=True, plot_raw=False, scale = True):
        plt.close()
        plt.figure()
        plt.title(f"{self.prefix} {self.temperature}C {self.voltage}V Compensator {self.compensated} {self.wavelength}nm")
        plt.ylabel("Intensity (ADU)")
        #Convert the x axis to nm
        plt.xlabel("Wavelength (nm)")
        #Camera is actually 12 bit, but the camera driver is set to 16 bit; should we scle back to 12 bit?
        
        if scale:
            plt.ylim(0, 30000/16)
            cross_section = self.cross_section/16
            cross_section_smooth = self.smoothed_cross_section/16
        else:
            cross_section_smooth = self.smoothed_cross_section
            cross_section = self.cross_section
            plt.ylim(0, 30000)
        if plot_raw:
            plt.plot(cross_section, label = "Raw Data")
        if smooth:
            #Plot the smooithed data with a thick line
            plt.plot(cross_section_smooth , label = "Smoothed Data", linewidth=3)
            print(f"Holding Position {ConversionEquation(self.nearest_maxima)}nm")
            
            #Plot the maxima with a vertical line
            plt.axvline(x=self.nearest_maxima, color='r', linestyle=':', label = "Nearest transmission peak to H-alpha")
            
        
        #plot a vertical line at 1093 pixels
        plt.axvline(x=1903, color='r', linestyle='--', label = "H-Alpha")
        plt.legend()
        #Change the x axis to be in nm only plot 10 ticks only plot to 2 signifigant figures
        
        plt.xticks(np.linspace(0, len(cross_section), 10), np.round(np.linspace(ConversionEquation(0), ConversionEquation(len(cross_section)), 10), 2))
        #make the plot look nice
        plt.tight_layout()
        #make the plot font larger
        plt.rcParams.update({'font.size': 22})
        #make the plot 16:9
        plt.rcParams['figure.figsize'] = [16, 9]
        #Keep y axis the same for all scans
        
        plt.savefig(filename)
        plt.close()

    def __str__(self):
        return f"{self.prefix} {self.temperature}C {self.voltage}V Compensator {self.compensated} {self.wavelength}nm"


def get_scans_with_prefix(scans, prefix):
    scans_with_prefix = []
    for scan in scans:
        if scan.prefix == prefix:
            scans_with_prefix.append(scan)
    return scans_with_prefix


def get_scans_at_voltage(scans, voltage):
    scans_at_voltage = []
    for scan in scans:
        if scan.voltage == voltage:
            scans_at_voltage.append(scan)
    return scans_at_voltage


#Get all scans at the same Temperature range
def get_scans_at_temperature(scans, range: list):
    #Create a list to hold the scans
    scans_at_temperature = []
    #Loop through all of the scans
    for scan in scans:
        #Check if the scan is at the right temperature
        if scan.temperature >= range[0] and scan.temperature <= range[1]:
            #Add the scan to the list
            scans_at_temperature.append(scan)
    #Return the list
    return scans_at_temperature


#Get all scans at the same Wavelength
def get_scans_at_wavelength(scans, wavelength):
    #Create a list to hold the scans
    scans_at_wavelength = []
    #Loop through all of the scans
    for scan in scans:
        #Check if the scan is at the right wavelength
        if scan.wavelength == wavelength:
            #Add the scan to the list
            scans_at_wavelength.append(scan)
    #Return the list
    return scans_at_wavelength

#Get all scans with CompensatorOn
def get_scans_with_compensator_state(scans, compensated = True):
    #Create a list to hold the scans
    scans_with_compensator_on = []
    #Loop through all of the scans
    for scan in scans:
        #Check if the scan has the compensator on
        if scan.compensated == compensated:
            #Add the scan to the list
            scans_with_compensator_on.append(scan)
    #Return the list
    return scans_with_compensator_on


#Sort Scans by attribute (Voltage, Temperature, Wavelength)
#return a list of scans sorted by the attribute
def sort_scans_by_attribute(scans, attribute = "Voltage"):
    #Create a list to hold the scans
    sorted_scans = []
    #Check the attribute
    if attribute == "Voltage":
        #Get all of the unique voltages
        unique_voltages = set([float(scan.voltage) for scan in scans])
        #Sort the voltages
        unique_voltages = sorted(unique_voltages)
        
        #Loop through all of the unique voltages
        for voltage in unique_voltages:
            #Get all of the scans at the voltage
            scans_at_voltage = get_scans_at_voltage(scans, voltage)
            #Add the scans to the list
            sorted_scans.append(scans_at_voltage[0])
    elif attribute == "Temperature":
        #Get all of the unique temperatures
        unique_temperatures = set([float(scan.temperature) for scan in scans])
        
        #Sort the temperatures
        unique_temperatures = sorted(unique_temperatures)
        #Loop through all of the unique temperatures
        for temperature in unique_temperatures:
            #Get all of the scans at the temperature
            scans_at_temperature = get_scans_at_temperature(scans, [temperature, temperature])
            #Add the scans to the list
            sorted_scans.append(scans_at_temperature[0])
    elif attribute == "Wavelength":
        #Get all of the unique wavelengths
        unique_wavelengths = set([float(scan.wavelength) for scan in scans])
        #Loop through all of the unique wavelengths
        for wavelength in unique_wavelengths:
            #Get all of the scans at the wavelength
            scans_at_wavelength = get_scans_at_wavelength(scans, wavelength)
            #Add the scans to the list
            sorted_scans.append(scans_at_wavelength[0])
    #Return the list
    return sorted_scans


if __name__ == "__main__":

    #load data from file
    scans_path = "C:/Users/mjeffers/Desktop/LFDI Entire Data Set"
    Files = [scan for scan in os.listdir(scans_path) if scan.endswith(".png")]
    print(Files)
    scans = []
    for File in Files:
        scans.append(Scan(File))

    
    #Get all of the scans with the prefix "Slew"
    SlewScans = get_scans_with_prefix(scans, "Slew")
    #Get all of the scans with the prefix "Hold"
    HoldScans = get_scans_with_prefix(scans, "Hold")
    print("Slew Scans: ", len(SlewScans))
    print("Hold Scans: ", len(HoldScans))


    #Sort the Slew Scans by Voltage
    SlewScans = sort_scans_by_attribute(SlewScans, "Voltage")
    #Sort the Hold Scans by Voltage
    HoldScans = sort_scans_by_attribute(HoldScans, "Voltage")
    for scans in HoldScans:
        print("Voltage: ", scans[0].voltage)
        print("Number of Scans: ", len(scans))
        for scan in scans:
            scan.plot_cross_section(scans_path, 2000, 50)

        