import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import savgol_filter
from PIL import Image
#Smooth a 1D csv and plot it


#Create a class to store the data for each temperature
class TemperatueScanSet:
    def __init__(self, temperature, scans):
        self.temperature = temperature
        self.scans = scans
        #Sort the scans by voltages
        self.scans.sort(key=lambda x: x.voltage)
        self.average_distance_between_maximas = self.findAverageDistanceBetweenMaximas()
        self.retardances = []
        self.getFirstLocalMaximas()
        self.fixDiscontinuity()
        
        
        return

    #Go through all the scans and find where the the previous first maxima is lower than the current first maxima of scans and add the average distance between the maxima to the list
    def fixDiscontinuity(self):
        for i in range(len(self.scans) - 1):
            #Check if there is a discontinuity
            if self.scans[i].first_local_maxima +100 < self.scans[i + 1].first_local_maxima:
                print(f"Discontinuity found between {self.scans[i].voltage}V and {self.scans[i+1].voltage}V at {self.temperature}C")
                #for scan from i to 0 add the average distance between maximas to the index
                for j in range(i+1, -1, -1):
                    print(f"{j}")
                    print(f"Adding {self.average_distance_between_maximas} to {self.scans[j].first_local_maxima} in scan {self.scans[j].voltage}V {self.scans[j].temperature}C")
                    self.retardances[j] = self.scans[j].first_local_maxima + self.average_distance_between_maximas                
        return 

    #Copy the first local maximas to a list
    def getFirstLocalMaximas(self):
        for scan in self.scans:
            self.retardances.append(scan.first_local_maxima)
        
    #plot all the first local maximas vs the voltage
    def plotFirstLocalMaximas(self, save = False, folder = None):
        #Clear all plots
        plt.clf()
        plt.figure()
        plt.title(f"First Local Maximas vs Voltage for {self.temperature}C Fixed Discontinuities")
        plt.xlabel("Voltage (V)")
        plt.ylabel("First Local Maxima")
        #Go through each scan and plot the voltage vs the retardance
        for i in range(len(self.scans)):
            plt.plot(self.scans[i].voltage, self.retardances[i], 'o')

        if save:
            plt.savefig(f"{folder}/{self.temperature}C.png")

        #plt.show()

    #Find the Average of all the average distances between maximas
    def findAverageDistanceBetweenMaximas(self):
        distances = []
        for scan in self.scans:
            distances.append(scan.average_distance_between_maximas)
        return np.mean(distances)



class Scan:
    def __init__(self, filename):
        #File name will have the format "XX.XXXC_V.VV.csv"
        self.temperature = float(filename[0:5])
        self.voltage = float(filename[8:11])
        print(f"Scan {self.temperature}C {self.voltage}V")
        self.filename = filename
        
        self.data = np.loadtxt(filename, delimiter=',')
        self.smoothed_data = savgol_filter(self.data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 100, 3)
        self.maxima, self.minima = self.findLocalMaximaMinima(len(self.smoothed_data), self.smoothed_data)
        #Check to see if there is a minima before the first maxima and if there is not the second maxima is the first maxima
        if self.minima[0] + 25 < self.maxima[0]:
            self.first_local_maxima = self.maxima[0]
            self.first_local_maxima_index = 0
        else:
            self.first_local_maxima = self.maxima[1]
            self.first_local_maxima_index = 1
        
        
        self.average_distance_between_maximas = self.findAverageDistanceBetweenMaximas()

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

    #find the average distance between local maximas starting at self.first_local_maxima_index
    def findAverageDistanceBetweenMaximas(self):
        #create a list of the distances between the maximas
        distances = []
        for i in range(self.first_local_maxima_index, len(self.maxima)-1):
            distances.append(self.maxima[i+1] - self.maxima[i])
        #return the average distance between maximas
        return np.mean(distances)

    #plot the Scan data. If the calibration data is provided, plot the mercury and hydrogen position on the graph as well, if convert_to_nm is true, convert the x axis to nm
    def plot(self,plot_smoothed = True,calibration_data = None,convert_to_nm = False, save = True, save_path = None, show = False):
        plt.figure(figsize=(30.0, 10.0))
        plt.plot(self.data, label = 'Raw Data')
        if plot_smoothed:
            plt.plot(self.smoothed_data, label = 'Smoothed Data')
            plt.plot(self.maxima, self.smoothed_data[self.maxima], 'o', label = 'Maxima')
            plt.plot(self.minima, self.smoothed_data[self.minima], 'o', label = 'Minima')
            #plot the fist local maxima with a red verical line
            plt.axvline(x = self.first_local_maxima, color = 'r', label = 'First Local Maxima')
        if calibration_data is not None:
            #Create a Vertical Line with a label at the Hydrogen, deuterium and Mercury Position
            plt.axvline(x = calibration_data.Hydrogen_Pixel_Position, color = 'y', label = 'Hydrogen')
            plt.axvline(x = calibration_data.Bromine_Pixel_Position, color = 'g', label = 'Bromine')
            plt.axvline(x = calibration_data.Deuterium_Pixel_Position, color = 'b', label = 'Deuterium')

        if convert_to_nm:
            plt.xlabel('Wavelength (nm)')
            #Convert the x axis to nm using Pixel Scaling and Pixel Offset            
            plt.xticks(np.arange(0, len(self.smoothed_data), 1), np.arange(calibration_data.Pixel_Offset, len(self.smoothed_data)*calibration_data.Pixel_Scaling + calibration_data.Pixel_Offset, calibration_data.Pixel_Scaling)[:-1])

            #only show 10 ticks
            plt.locator_params(axis='x', nbins=10)

        else:
            plt.xlabel('Pixel Position')
            #Xtick every 500 pixels
            plt.xticks(np.arange(0, len(self.smoothed_data), 500))
            #grid
            plt.grid()
        #include the distance between maximas in the top left corner
        plt.text(0.01, 0.99, f'Average Distance Between Maximas: {str(self.findAverageDistanceBetweenMaximas())}', horizontalalignment='left', verticalalignment='top', transform=plt.gca().transAxes)
       
        plt.ylabel('Intensity')
        plt.title(f'Scan at {str(self.temperature)}C {str(self.voltage)}V')
        plt.legend()

        #Plot first local maxima
        plt.annotate(str(self.first_local_maxima), xy=(self.first_local_maxima, self.smoothed_data[self.first_local_maxima]), xytext=(self.first_local_maxima, self.smoothed_data[self.first_local_maxima]), arrowprops=dict(facecolor='black', shrink=0.05),)

        if save:
            #Save as full screen png
            plt.savefig(f"{save_path}\\{str(self.temperature)}C_{str(self.voltage)}V.png", bbox_inches='tight')
        if show:  
            plt.show()
        return

#Go through all the Scans and find the local maxima that is furthest to the right
def findMaxima(scans):
    maxima = 0
    for scan in scans:
        if scan.first_local_maxima > maxima:
            maxima = scan.first_local_maxima
    return maxima

#plot local maximas vs Voltage
def plotLocalMaximasVsVoltage(scans, calibration, convert_to_nm = False,fit_a_line = False, save = False, save_path = None, show = False):
    plt.figure(figsize=(30.0, 10.0))
    for scan in scans:
        plt.plot(scan.voltage, scan.first_local_maxima, 'o')
    plt.xlabel('Voltage (V)')
    plt.ylabel('First Maxima (Pixel Position)')    
    plt.title('First Maxima vs Voltage')
    Furthest_Maxima = findMaxima(scans)
    #Convert the y axis to nm using Pixel Scaling and Pixel Offset with 2 decimal places
    if convert_to_nm:
        plt.ylabel('First Maxima (nm)')
        plt.yticks(np.arange(0, Furthest_Maxima*calibration.Pixel_Scaling + calibration.Pixel_Offset, 1), np.arange(0, Furthest_Maxima*calibration.Pixel_Scaling + calibration.Pixel_Offset, 1).round(2))
        plt.title('First Maxima vs Voltage (nm)')
    if fit_a_line:
        #fit a line to the data
        z = np.polyfit(scans[0].voltage, scans[0].first_local_maxima, 1)
        p = np.poly1d(z)
        plt.plot(scans[0].voltage, p(scans[0].voltage), "r--", label = 'Fit')
        plt.legend()
    if save:
        #Save as full screen png
        plt.savefig(save_path+"\\" + 'LocalMaximasVsVoltage.png', bbox_inches='tight')
    if show:
        plt.show()
    return

#plot all the local maximas of the scans in the format nm offset vs the temperature
def plotLocalMaximasVTemperature(scans, calibration, convert_to_nm = False,fit_a_line = False, save = False, save_path = None, show = False):
    plt.figure(figsize=(30.0, 10.0))
    for scan in scans:
        plt.plot(scan.temperature, scan.first_local_maxima, 'o')
    plt.xlabel('Temperature (C)')
    plt.ylabel('First Maxima (Pixel Position)')    
    plt.title('First Maxima vs Temperature')
    Furthest_Maxima = findMaxima(scans)
    #Convert the y axis to nm using Pixel Scaling and Pixel Offset with 2 decimal places
    if convert_to_nm:
        plt.ylabel('First Maxima (nm)')
        plt.yticks(np.arange(0, Furthest_Maxima, 1), np.around(np.arange(calibration.Pixel_Offset, Furthest_Maxima*calibration.Pixel_Scaling + calibration.Pixel_Offset, calibration.Pixel_Scaling), 2))

    if fit_a_line:
        #Fit a line to the data
        x = []
        y = []
        for scan in scans:
            x.append(scan.temperature)
            y.append(scan.first_local_maxima)
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        plt.plot(x,p(x),"r--")
        #display the equation of the line
        plt.text(0.05, 0.95, 'y=%.6fx+(%.6f)'%(z[0],z[1]), ha='left', va='top', transform=plt.gca().transAxes)

    #only plot 10 ticks
    plt.locator_params(axis='y', nbins=10)
    #add grid lines
    plt.grid()
    if save:
        plt.savefig(save_path+"\\" + 'First Maxima vs Temperature.png', bbox_inches='tight')
    if show:
        plt.show()
    return


#Plot for every Scan that has the same Temperature plot the local maximas vs Voltage
#go through all the scans and find the ones with the same temperature and plot them and add a line of best fit
def plotLocalMaximasVsVoltageSameTemperature(scans,fit_a_line = False, save = False, save_path = None, show = False):
    plt.figure(figsize=(30.0, 10.0))
    #go through all the scans and find the ones with the same temperature
    for scan in scans:
        #find the scans with the same temperature
        same_temperature_scans = []
        for scan2 in scans:
            if scan.temperature == scan2.temperature:
                same_temperature_scans.append(scan2)
        #plot the local maximas vs voltage for the scans with the same temperature
        for scan2 in same_temperature_scans:
            plt.plot(scan2.voltage, scan2.first_local_maxima, 'o')
        plt.xlabel('Voltage (V)')
        plt.ylabel('First Maxima (Pixel Position)')    
        plt.title('First Maxima vs Voltage at ' + str(scan.temperature) + 'C')
        Furthest_Maxima = findMaxima(same_temperature_scans)

        #only plot 10 ticks
        plt.locator_params(axis='y', nbins=10)
        #add grid lines
        plt.grid()
        if save:
            plt.savefig(save_path+"\\" + 'LocalMaximasVsVoltage' + str(scan.temperature) + '.png', bbox_inches='tight')
            
        if show:
            plt.show()
        #clear the plot
        plt.clf()


#plot the local maximas vs temperature for all the scans with the same voltage
def plotLocalMaximasVsTemperatureSameVoltage(scans,fit_a_line = False, save = False, save_path = None, show = False):
    plt.figure(figsize=(30.0, 10.0))
    #go through all the scans and find the ones with the same voltage
    for scan in scans:
        #find the scans with the same voltage
        same_voltage_scans = []
        for scan2 in scans:
            if scan.voltage == scan2.voltage:
                same_voltage_scans.append(scan2)
        #plot the local maximas vs temperature for the scans with the same voltage
        for scan2 in same_voltage_scans:
            plt.plot(scan2.temperature, scan2.first_local_maxima, 'o')
        plt.xlabel('Temperature (C)')
        plt.ylabel('First Maxima (Pixel Position)')    
        plt.title('First Maxima vs Temperature at ' + str(scan.voltage) + 'V')
        Furthest_Maxima = findMaxima(same_voltage_scans)
        #Convert the y axis to nm using Pixel Scaling and Pixel Offset with 2 decimal places
        if fit_a_line:
            #Fit a line to the data
            x = []
            y = []
            for scan2 in same_voltage_scans:
                x.append(scan2.temperature)
                y.append(scan2.first_local_maxima)
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            plt.plot(x,p(x),"r--")
            #display the equation of the line
            plt.text(0.05, 0.95, 'y=%.6fx+(%.6f)'%(z[0],z[1]), ha='left', va='top', transform=plt.gca().transAxes)

        #only plot 10 ticks
        plt.locator_params(axis='y', nbins=10)
        #add grid lines
        plt.grid()
        if save:
            plt.savefig(save_path+"\\" + 'LocalMaximasVsTemperature' + str(scan.voltage) + '.png', bbox_inches='tight')
        if show:
            plt.show()
        #clear the plot
        plt.clf()



#make a 3d plot of the first local maxima vs temperature and voltage
def plot3DLocalMaximas(scans, save = False, save_path = None):
    fig = plt.figure(figsize=(30.0, 10.0))
    ax = fig.add_subplot(111, projection='3d')
    x = []
    y = []
    z = []
    for scan in scans:
        x.append(scan.temperature)
        y.append(scan.first_local_maxima)
        z.append(scan.voltage)
    ax.scatter(x, y, z)
    ax.set_xlabel('Temperature (C)')
    ax.set_ylabel('First Maxima (Pixel Position)')
    ax.set_zlabel('Voltage (V)')
    if save:
        plt.savefig(save_path+"\\" + 'Voltage vs First Maxima vs Temperature.png', bbox_inches='tight')
    #plt.show()
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

#open the Bromine_Calibration_Image.tif and find the max value using the cross section through the middle of the image.
#Plot the cross section and the max value
def find_Max(calibration, filename):
    image = Image.open(filename)
    image = np.array(image)
    #Find the cross section through the middle of the image
    cross_section = image[int(len(image)/2)]
    smoothed_data = savgol_filter(cross_section, 50, 3)
    smoothed_data = savgol_filter(smoothed_data, 50, 3)
    
    #Find the max value in the cross section
    max_value = np.max(smoothed_data)
    #Find the pixel position of the max value
    max_value_position = np.argmax(smoothed_data)
    #Plot the cross section and the max value
    plt.figure(figsize=(30.0, 10.0))
    plt.plot(cross_section)
    plt.plot(smoothed_data)
    plt.plot(max_value_position, max_value, 'o')
    plt.xlabel('Pixel Position')
    #Print the pixel position of the max value on the graph with a label 
    plt.text(max_value_position, max_value, 'Max Value Pixel Position: ' + str(max_value_position), ha='left', va='top')
    plt.ylabel('Intensity')
    plt.title('Bromine Calibration')
    plt.show()
    return max_value_position



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
    path = "C:\\Users\\mjeffers\\Desktop\\"
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"
    #Load in the calibration data
    # calibration = Calibration(f"{path}Calibration_2023-01-11_18-33-13\\")
    # hydrogen_pixel_position = findHydrogenPixelPosition(f'{path}Calibration_2023-01-11_18-33-13\\Hydrogen_Calibration_CrossSection.csv')
    # findBromineMax(f'{path}Calibration_2023-01-11_18-33-13\\Bromine_Calibration_Image.tif')
    # calibration.Hydrogen_Pixel_Position = hydrogen_pixel_position
    # calibration.Pixel_Scaling = calibration.get_Pixel_Scaling()
    # calibration.Pixel_Offset = calibration.get_Pixel_Offset()

    # print(calibration)
    scan_path = f"{path}Experiment_2023-01-17_14-04-09\\"
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
        scan.plot(plot_smoothed = True, convert_to_nm=False, save=True, save_path=l2_path)
        scans.append(scan)

    #find all the scans that have the same temperature
    temperature_scan_sets = []
    temperatureList = []
    for scan in scans:
        TemperatureScans = []
        if scan.temperature not in temperatureList:
            temperatureList.append(scan.temperature)
            for scan2 in scans:
                if scan.temperature == scan2.temperature:
                    TemperatureScans.append(scan2)
            temperature_scan_sets.append(TemperatueScanSet(scan.temperature, TemperatureScans))
    #plot the scans that have the same temperature
    for temperature_scan_set in temperature_scan_sets:
        temperature_scan_set.plotFirstLocalMaximas(save=True, folder=l2_path)
        
    #3d plot
    plot3DLocalMaximas(scans, save=True, save_path=l2_path)
    #2d plot
    plotLocalMaximasVsVoltageSameTemperature(scans, fit_a_line=True, save=True, save_path=l2_path)
    #2d plot
    plotLocalMaximasVsTemperatureSameVoltage(scans, fit_a_line=True, save=True, save_path=l2_path)

    print('Done')