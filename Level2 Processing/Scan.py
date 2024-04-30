#This File Contains the Scan Class implementation
#This class will hold information on a Spectra Cross section Scan

#Create a class for a scan
#This stores all of the data for a single scan

import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import numpy as np
from PIL import Image
import os
from scipy import signal
import pickle


px_per_nm_at_4656 = 924
halpha_px_position_at_4656 = 2128
halpha_nm_position = 656.28

class Stage:
    def __init__(self, stage_size = 2.7):
        self.stage_size = stage_size
        if stage_size == 2.7:
            self.fsr = .44
        elif stage_size == 5.4:
            self.fsr = .22
        elif stage_size == 10.8:
            self.fsr = .11


############################################################################################################
# Scan Class
############################################################################################################

# Convert an X pixel value to a wavelength based on the ASI 1600 Camera
def ConversionEquation(x, image_xaxis_size):
    # 0.001 nm/px + 653.377 nm @ max resolution
    y_intercept = halpha_nm_position - (1/px_per_nm_at_4656)*halpha_px_position_at_4656
    return (1/px_per_nm_at_4656)*x*(4656/image_xaxis_size) + y_intercept

# The Expected name format is for images is
scanformat = "[PREFIX]_[TimeStamp]_[Voltage]V_[Temperature]C_Comp[Status]_[Wavelength]nm.png"

# This is the General Scan Class that will be used to Read in all of the CSVs
# The Expected name format is "PREFIX_TimeStamp_TemperatureC_VoltageV.csv"
# Prefix can be whatever the User Wants. Normally Experiment Based ie "Slew" "Hold"
# TimeStamp should the raw output of time.time()
# Temperature should be the Temperature that Scans are taken at
# Voltage should be the Voltage applied to the optic at the Time


class Scan:
    def __init__(self, filename, parentFolder, stage_size):
        # Set the filename
        # Information pulled from file name
        self.parentFolder = parentFolder
        self.filename = filename  # set filename to the filename
        self.prefix = filename.split("_")[0]  # set prefix to the first value in the filename, split by the "_"
        self.timestamp = filename.split("_")[1]  #set timestamp to the second value in the filename, split by the "_"
        self.temperature = float(filename.split("_")[3].replace("C", ""))  # set temperature to the third value in the filename, split by the "_"
        # remove the "V" from the voltage and the space from the voltage
        self.voltage = float(filename.split("_")[2].replace("V", "").replace(" ", ""))  # set voltage to the fourth value in the filename, split by the "_" [remove the "V" from the voltage and the space from the voltage
        self.wavelength = float(filename.split("_")[5].split("nm")[0])  # set wavelength to the fifth value in the filename, split by the "_"
        self.compensated = filename.split("_")[4] == "CompOn"  # set compensated to the sixth value in the filename, split by the "_"
        
        # Possible data asets
        self.stage = Stage(stage_size)
        
        self.peak_distance = None  # 203*(2.7/stage_size)*(image_size/4656) (Found Peak Distance of the 2.7mm Stage)*(Calcite thickness)
        self.Filter_Frequncy = None  # Cutoff Frequency for the Butterworth Filter used to smooth the data
        self.cross_section = None
        self.smoothed_cross_section = None
        self.cross_section_location = float(1/2)  # Get From the Middle
        self.span = 0.01  # Percent Coverage of the Final Image. Cover all rows would be 100
        self.halpha_CrossSection = 0.457045  # position of Halpha Line. 1 is all the way to the right 0 is all the other way to the left
        
        self.image_xaxis = None
        self.nearest_maxima = None
        self.processed = False
        # Get the scan a pickle name based on the scan format
        self.processed_pickle = self.filename.replace(".png", ".pkl")



    # This will process the scan by doing the following
    # 1. Get the Cross Section of the image at the location with the specified span
    # 2. Smooth the Cross Section
    # 3. Find the Nearest Maxima to the Halpha Line
    # 4. Save the Scan as a pickle for quicker access
    def process(self):
        print("Gettting Cross Section")        
        self.cross_section = self.get_CrossSection(self.parentFolder, self.cross_section_location, self.span)
        print("Smoothing")
        self.peak_distance = round((px_per_nm_at_4656*self.stage.fsr)*(self.image_xaxis/4656))
        self.smoothed_cross_section = self.smooth(self.cross_section, peak_distance=self.peak_distance)
        self.nearest_maxima = self.find_maxima(self.parentFolder, self.smoothed_cross_section, self.span)
        self.processed = True
        # Save the Scan as a pickle use the parent folder and the processed pickle name
        with open(os.path.join(self.parentFolder, self.processed_pickle), 'wb') as f:
            pickle.dump(self, f)
        return

    # This Function will find the Cross section of the image at 
    # a specific location and average across the specified span
    def get_CrossSection(self, parentFolder, crosssection, span):
        
        # Get the Image
        image = Image.open(os.path.join(parentFolder, self.filename))
        # Get the Cross Section
        self.image_xaxis = np.array(image).shape[1]
        print(f"Xaxis {self.image_xaxis}")
        crossSectionPixels = round(np.array(image).shape[0]*crosssection) 
        
        # Get the Y Dimension of the image and multiply by the span to get the 
        # number of rows to average
        bounds = round(np.array(image).shape[1]*span)
        PixelValuesToMean = []
        
        # Loop through the Cross Section
        r = round(bounds/2)
        print(f"Meaning {r} rows")
        for i in range(r):
            # Get the pixel values to average
            PixelValuesToMean.append(np.array(image)[crossSectionPixels-(i), :])
            PixelValuesToMean.append(np.array(image)[crossSectionPixels+(i), :])
        # Average the pixel values
        crosssection = np.mean(PixelValuesToMean, axis=0)

        # Coaverage the Cross Section
        # Return the Cross Section
        return crosssection
    
    # This Function will smooth the cross section using a Savitzky-Golay Filter
    # The assumed peak Distance is the FSR
    # The assumed frequency is 0.75
    # TODO These are BAD assumptions
    def smooth(self, crosssection, peak_distance, frequency = .75):
        smoothed = savgol_filter(crosssection, peak_distance, 2)
        #Use a butter worth filter to smooth the data the 4th order filter with a cutoff of 2/418
        #b, a = signal.butter(4, frequency, 'low', analog=False)
       # smoothed = signal.filtfilt(b, a, smoothed)
        return smoothed
    
    #Find the Maxima closest to 1903 pixels
    # TODO This is a bad Assumption based on the halpha Cross section
    def find_maxima(self, parentFolder, smoothed, span):
        #Find all the local maximas
        maxima = np.r_[True, smoothed[1:] > smoothed[:-1]] & np.r_[smoothed[:-1] > smoothed[1:], True]
        print(f"Maximas {maxima}")
        #Find the maxima closest to Halpha pixels
        maxima = np.where(maxima)[0]
        print(f"Maximas {maxima}")
        halphaPixel = round(len(smoothed)*self.halpha_CrossSection)
        print(f"Halpha Pixel {halphaPixel}")
        
        maxima = maxima[np.abs(maxima-halphaPixel).argmin()]
        print(f"Maxima {maxima}")
        #return the maxima
        return maxima


    # This will show the Cross Section of the image at the location with the specified span
    def plot_cross_section(self, parentFolder, crosssection, span):
        crosssection = self.get_CrossSection(parentFolder, crosssection, span)
        plt.figure()
        plt.plot(crosssection)
        plt.show()
        return
    
    # This will svae the smoothed Cross Section of the image at the location with the specified span
    def save_cross_section(self, filename, smooth=True, plot_raw=False, scale = True, Limit_Y = True):
        plt.close()
        plt.figure()
        plt.title(f"{self.prefix} {self.temperature}C {self.voltage}V Compensator {self.compensated} {self.wavelength}nm")
        plt.ylabel("Intensity (ADU)")
        #Convert the x axis to nm
        plt.xlabel("Wavelength (nm)")
        #Camera is actually 12 bit, but the camera driver is set to 16 bit; should we scle back to 12 bit?
        
        if scale:
            if Limit_Y:
                plt.ylim(0, 3)
            cross_section = self.cross_section/16
            cross_section_smooth = self.smoothed_cross_section/16
        else:
            cross_section_smooth = self.smoothed_cross_section
            cross_section = self.cross_section
            if Limit_Y:
                plt.ylim(0, 30000)
        if plot_raw:
            plt.plot(cross_section, label = "Raw Data")
        if smooth:
            # Plot the smooithed data with a thick line
            plt.plot(cross_section_smooth , label = "Smoothed Data", linewidth=3, color = "orange")
            print(f"Holding Position {ConversionEquation(self.nearest_maxima, self.image_xaxis)}nm")
            
            # Plot the maxima with a vertical line
            plt.axvline(x=self.nearest_maxima, color='r', linestyle=':', label = "Nearest transmission peak to H-alpha")
            
        
        # plot a vertical line at the H-Alpha line
        plt.axvline(x=round(self.halpha_CrossSection*len(cross_section_smooth)), color='r', linestyle='--', label = "H-Alpha")
        plt.legend()
        plt.xticks(np.linspace(0, len(cross_section), 10), 
                   np.round(np.linspace(ConversionEquation(
                       0, self.image_xaxis), ConversionEquation(
                           len(cross_section), self.image_xaxis), 10), 2))
        plt.tight_layout()
        plt.rcParams.update({'font.size': 22})
        plt.rcParams['figure.figsize'] = [16, 9]
        plt.savefig(filename)
        plt.close()

    def __str__(self):
        return f"{self.prefix} {self.temperature}C {self.voltage}V Compensator {self.compensated} {self.wavelength}nm"




############################################################################################################
# Helper Functions
############################################################################################################

# @Brief: This function will filter out the scans based on the filters provided
# @param kwargs: The filters to use when generating the gif
#   @param compensated: The compensated state of the scans to use (True or False)
#   @param prefix: The prefix of the scans to use (ex: "LFDI", "Hold", "Slew")
#   @param temperature: The Range of temperatures of the scans to use (ex: [25, 30], [20, 35])
#   @param voltage: The voltage of the scans to use (ex: 0.0, 3.3)
#   @param wavelength: The wavelength of the scans to use (ex: 656.28, 0.0)
#   @param sort: The sort of the scans to use (ex: "Voltage", "Temperature")
def filter_scans(scans, **kwargs):
        #Filter the scans
        if "compensated" in kwargs:
            print("Filtering by compensated")
            scans = get_scans_with_compensator_state(scans, kwargs["compensated"])
        if "prefix" in kwargs:
            print("Filtering by prefix")
            scans = get_scans_with_prefix(scans, kwargs["prefix"])
        if "temperature" in kwargs:
            print("Filtering by temperature")
            scans = get_scans_at_temperature(scans, kwargs["temperature"])
        if "voltage" in kwargs:
            print("Filtering by voltage")
            scans = get_scans_at_voltage(scans, kwargs["voltage"])
        if "wavelength" in kwargs:
            print("Filtering by wavelength")
            if "converted" in kwargs:
                converted = kwargs["converted"]
            else:
                converted = True
            scans = get_scans_at_wavelength(scans, kwargs["wavelength"], converted)
        if "sort" in kwargs:
            print("Sorting by attribute")
            if "only_unique" in kwargs:
                unique = kwargs["only_unique"]
                print(f"Using only Unique State: {unique}")
                scans = sort_scans_by_attribute(scans, attribute = kwargs["sort"], only_unique=kwargs["only_unique"])
            else:
                scans = sort_scans_by_attribute(scans, attribute = kwargs["sort"])
        
        return scans

# Filter the Scans by Prefix
# @param scans: List of Scans
# @param prefix: Prefix to filter by
# @return: List of Scans with the specified prefix
def get_scans_with_prefix(scans: list, prefix: str):
    scans_with_prefix = []
    for scan in scans:
        if scan.prefix == prefix:
            scans_with_prefix.append(scan)
    return scans_with_prefix

# Get all scans at the same Voltage
# @param scans: List of Scans
# @param voltage: Voltage to filter by
# @return: List of Scans with the specified voltage
def get_scans_at_voltage(scans, voltage):
    scans_at_voltage = []
    for scan in scans:
        if scan.voltage == voltage:
            scans_at_voltage.append(scan)
    return scans_at_voltage


# Get all scans at the same Temperature range
# @param scans: List of Scans
# @param range: Temperature range to filter by [min, max]
# @return: List of Scans with the specified temperature
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


# Get all scans at the same Wavelength
# @param scans: List of Scans
# @param wavelength_range: Wavelength range to filter by [min, max]
# @return: List of Scans with the specified wavelength
def get_scans_at_wavelength(scans, wavelength_range:list, converted=True):
    print(f"Original leng of scans {len(scans)}")
    #Create a list to hold the scans
    scans_at_wavelength = []
    #Loop through all of the scans
    for scan in scans:
        #Check if the scan is at the right wavelength
        print(f"{wavelength_range[0]}, {wavelength_range[1]}")
        if (ConversionEquation(scan.nearest_maxima, scan.image_xaxis) >= wavelength_range[0]) and (ConversionEquation(scan.nearest_maxima, scan.image_xaxis) <= wavelength_range[1]):
            print(ConversionEquation(scan.nearest_maxima, scan.image_xaxis))
            #Add the scan to the list
            scans_at_wavelength.append(scan)
    #Return the list
    return scans_at_wavelength

# Get all scans with CompensatorOn
# @param scans: List of Scans
# @param compensated: Compensator State to filter by
# @return: List of Scans with the specified compensator state
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
def sort_scans_by_attribute(scans, attribute = "Voltage", only_unique = True):
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
            if only_unique:
                sorted_scans.append(scans_at_voltage[0])
            #Else sort the results by time
            else:
                sorted_scans.append(sorted(scans_at_voltage, key=lambda scan: scan.timestamp))
    elif attribute == "Temperature":
        #Get all of the unique temperatures
        unique_temperatures = set([float(scan.temperature) for scan in scans])
        
        #Sort the temperatures
        unique_temperatures = sorted(unique_temperatures)
        #Loop through all of the unique temperatures
        for temperature in unique_temperatures:
            #Get all of the scans at the temperature
            scans_at_temperature = get_scans_at_temperature(scans, [temperature, temperature])
            print(f"Scans at {temperature}: {len(scans_at_temperature)}")
            #Add the scans to the list
            if only_unique:
                sorted_scans.append(scans_at_temperature[0])
            #Else sort the results by time
            else:
                print("Using All of the Scans")
                sorted_scans.extend(sorted(scans_at_temperature, key=lambda scan: scan.timestamp))
            
    elif attribute == "Wavelength":
        #Get all of the unique wavelengths
        unique_wavelengths = set([float(scan.wavelength) for scan in scans])
        #Loop through all of the unique wavelengths
        for wavelength in unique_wavelengths:
            #Get all of the scans at the wavelength
            scans_at_wavelength = get_scans_at_wavelength(scans, wavelength)
            
            #Add the scans to the list
            if only_unique:
                sorted_scans.append(scans_at_wavelength[0])
            #Else sort the results by time
            else:
                sorted_scans.append(sorted(scans_at_wavelength, key=lambda scan: scan.timestamp))
            
    #Return the list
    return sorted_scans



if __name__ == "__main__":

    #load data from file
    scans_path = "C:/Users/mjeffers/Desktop/TempSweep/Experiment_2023-03-26_04-07-04"
    Files = [scan for scan in os.listdir(scans_path) if scan.endswith(".png")]
    print(Files)
    scans = []
    for File in Files:
        scans.append(Scan(File,scans_path))

    
    #Get all of the scans with the prefix "Slew"
    SlewScans = get_scans_with_prefix(scans, "Slew")
    #Get all of the scans with the prefix "Hold"
    HoldScans = get_scans_with_prefix(scans, "Hold")
    print("Slew Scans: ", len(SlewScans))
    print("Hold Scans: ", len(HoldScans))


    #Get All of the Scans with the Compensator On
    SlewScans = get_scans_with_compensator_state(SlewScans, True)
    HoldScans = get_scans_with_compensator_state(HoldScans, True)
    print("Slew Scans: ", len(SlewScans))
    print("Hold Scans: ", len(HoldScans))

    for scans in HoldScans:
        for scan in scans:
            scan.plot_cross_section(scans_path, 2000,50)

    # #Sort the Slew Scans by Voltage
    # SlewScans = sort_scans_by_attribute(SlewScans, "Voltage")
    # #Sort the Hold Scans by Voltage
    # HoldScans = sort_scans_by_attribute(HoldScans, "Voltage")
    # for scans in HoldScans:
    #     print("Voltage: ", scans[0].voltage)
    #     print("Number of Scans: ", len(scans))
    #     for scan in scans:
    #         scan.plot_cross_section(scans_path, 2000, 50)

        