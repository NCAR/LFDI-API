import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import savgol_filter
from PIL import Image
#Smooth a 1D csv and plot it


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
        #if the second maxima value is biger than the first, then the first maxima is the second maxima
        if self.smoothed_data[self.maxima[1]] > self.smoothed_data[self.maxima[0]]:
            self.first_local_maxima = self.maxima[1]
        else:
            self.first_local_maxima = self.maxima[0]
        #Get the temperature from the filename by getting the filename without the extension and converting it to a float
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
    def plot(self,plot_smoothed = True,calibration_data = None,convert_to_nm = False, save = False, save_path = None):
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
        plt.ylabel('Intensity')
        plt.title('Scan at ' + str(self.temperature) + 'C')
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

#plot local maximas vs Voltage
def plotLocalMaximasVsVoltage(scans, calibration, convert_to_nm = False,fit_a_line = False, save = False, save_path = None):
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
    plt.show()
    return

#plot all the local maximas of the scans in the format nm offset vs the temperature
def plotLocalMaximasVTemperature(scans, calibration, convert_to_nm = False,fit_a_line = False, save = False, save_path = None):
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
    plt.show()
    return


#Plot for every Scan that has the same Temperature plot the local maximas vs Voltage
#go through all the scans and find the ones with the same temperature and plot them and add a line of best fit
def plotLocalMaximasVsVoltageSameTemperature(scans,fit_a_line = False, save = False, save_path = None):
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

        if fit_a_line:
            #fit a line to the data
            x = []
            y = []
            for scan2 in same_temperature_scans:
                x.append(scan2.voltage)
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
            plt.savefig(save_path+"\\" + 'LocalMaximasVsVoltage' + str(scan.temperature) + '.png', bbox_inches='tight')
        plt.show()




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
        # scan.plot(plot_smoothed = False, convert_to_nm=False, save=True, save_path=l2_path)
        scans.append(scan)
        
    #3d plot
    plot3DLocalMaximas(scans, save=True, save_path=l2_path)
    #2d plot
    plotLocalMaximasVsVoltageSameTemperature(scans, fit_a_line=True, save=True, save_path=l2_path)

    print('Done')