import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import savgol_filter
from PIL import Image
#Smooth a 1D csv and plot it
import heapq
from matplotlib import animation
import imageio

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
    
    #Create a list of the first local maxima sorted by Voltages
    first_local_maxima = []
    for scan in scans:
        first_local_maxima.append(scan.first_local_maxima)
    return first_local_maxima
    

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
        first_local_maxima = []
        for scan2 in same_temperature_scans:
            plt.plot(scan2.voltage, scan2.first_local_maxima, 'o')
            first_local_maxima.append(scan2.first_local_maxima)
        plt.xlabel('Voltage (V)')
        plt.ylabel('First Maxima (Pixel Position)')    
        plt.title('First Maxima vs Voltage at ' + str(scan.temperature) + 'C')
        np.savetxt(save_path+"\\" + 'LocalMaximasVsVoltage' + str(scan.temperature) + '.csv', first_local_maxima, delimiter=",")
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

        #Return the first local maxima of the scans sorted by voltage
        for scan in same_temperature_scans:
            first_local_maxima.append(scan.first_local_maxima)
        #Save the first local maximas as a csv file
        
        return first_local_maxima


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
    fig = plt.figure(figsize=(10.0, 10.0))
    ax = fig.add_subplot(111, projection='3d')
    x = []
    y = []
    z = []
    for scan in scans:
        x.append(scan.temperature)
        z.append(scan.first_local_maxima)
        y.append(scan.voltage)
    ax.scatter(x, y, z)
    ax.set_xlabel('Temperature (C)')
    ax.set_ylabel("Voltage (V)")
    ax.set_zlabel('First Maxima (Pixel Position)')
    if save:
        plt.savefig(save_path+"\\" + 'Voltage vs First Maxima vs Temperature.png', bbox_inches='tight')
    
    #Create a gif of the plot rotating horizontally
    for angle in range(0, 360):
        ax.view_init(30, angle)
        plt.draw()
        plt.savefig(save_path+"\\" + 'Voltage vs First Maxima vs Temperature' + str(angle) + '.png', bbox_inches='tight')
    #Combine the images into a gif
    images = []
    for angle in range(0, 360):
        images.append(imageio.imread(save_path+"\\" + 'Voltage vs First Maxima vs Temperature' + str(angle) + '.png'))
    imageio.mimsave(save_path+"\\" + 'Voltage vs First Maxima vs Temperature.gif', images)
    plt.close()
    #Delete the images
    for angle in range(0, 360):
        os.remove(save_path+"\\" + 'Voltage vs First Maxima vs Temperature' + str(angle) + '.png')
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


#Using a seed scan find the correlation of every other scan in the set of temperature scans make a correlation matrix at the end
def findCorrelation(seed_scan: Scan, temperature_scan_sets: list[TemperatueScanSet], show = False, save = False, save_path = None):
    #make a list of the correlation values
    correlation_values = []
    temperature_Correlation = []
    #for every temperature scan set
    for temperature_scan_set in temperature_scan_sets:
        #for every scan in the temperature scan set
        for scan in temperature_scan_set.scans:
            #find the correlation between the seed scan and the scan
            correlation = np.corrcoef(seed_scan.data, scan.data)[0,1]
            #add the correlation to the list of correlation values
            temperature_Correlation.append(correlation)
            correlation_values.append(correlation)

    #make a correlation matrix
    correlation_matrix = np.reshape(correlation_values, (len(temperature_scan_sets), len(temperature_scan_set.scans)))
    #Plot correlations with a value of 1 as a Green Dot

    #plot the correlation matrix
    #cLEAR ALL PREVIOUS PLOTS
    plt.clf()
    plt.imshow(correlation_matrix, cmap='hot', interpolation='nearest')
    plt.colorbar(label='Correlation')
    plt.scatter(np.where(correlation_matrix == 1)[1], np.where(correlation_matrix == 1)[0], c='g', marker='o', label='Seed')
    #Show legen
    plt.legend()
    #label the x axis
    plt.xlabel('Voltage (V)')
    #Change the Axis so that the voltage is in the correct order
    plt.xticks(np.arange(len(temperature_scan_set.scans)), [scan.voltage for scan in temperature_scan_set.scans])
    #only plot every 5th label on the x axis
    plt.xticks(np.arange(len(temperature_scan_set.scans))[::5], [scan.voltage for scan in temperature_scan_set.scans][::5])
    #label the y axis
    plt.ylabel('Temperature (C)')
    #mark the position of the Seed with a green dot
    #Change the Axis so that the temperature is in the correct order
    plt.yticks(np.arange(len(temperature_scan_sets)), [temperature_scan_set.temperature for temperature_scan_set in temperature_scan_sets])
    #label the color bar
    
    #Plot the Title
    plt.title(f'Correlation of Seed {str(seed_scan.temperature)}C and {str(seed_scan.voltage)}V')
    #Expand the size of the plot to fit the labels
    plt.gcf().set_size_inches(20, 10)    
    #save the plot
    if save:
        #File name is the temperature and voltage of the seed scan
        filename = f"{save_path}\\Correlation of Seed {str(seed_scan.temperature)}C and {str(seed_scan.voltage)}V.png"
        plt.savefig(filename , bbox_inches='tight')
    #show the plot
    if show:
        plt.show()
    #make a File to store the max correlation values
    CSV = f"{save_path}\\Correlation of Seed {str(seed_scan.temperature)}C.csv"
    with open(CSV, "a") as file:
        file.write(f"Max Correlation Voltage, Temperature, Seed Voltage\n")
    #For each row in the correlation matrix find the highest correlation value and the voltage that it corresponds to
    i = 0
    for row in correlation_matrix:
        #find the highest correlation value
        max_correlation = np.max(row[29:60])
        #find the voltage that corresponds to the highest correlation value
        max_correlation_voltage = float(np.where(row == max_correlation)[0][0]/10)
        #print the results
        with open(CSV, "a") as file:
            file.write(f"{max_correlation_voltage}V, {temperature_scan_sets[i].temperature}C, {seed_scan.voltage}V\n")
        i += 1
    return correlation_matrix, filename 



#Convert all files with extension .csv and the format of 25.602C_9.200000000000001V.csv to have the correct format of 25.602C_9.2V.csv
def convertCSVFileNames(path):
    #for every file in the directory
    for file in os.listdir(path):
        #if the file is a csv file
        if file.endswith(".csv"):
            #split the file name into the temperature and voltage
            temperature, voltage = file.split("_")
            #remove the C from the temperature
            temperature = temperature[:-1]
            #remove the V from the voltage
            voltage = voltage[:-1]
            #remove the .csv from the voltage
            voltage = voltage[:-4]
            #convert the voltage to a float
            voltage = float(voltage)
            #round the voltage to 1 decimal place
            voltage = round(voltage, 1)
            #add the V back to the voltage
            voltage = str(voltage) + "V"
            #rename the file
            try:
                os.rename(path + file, path + temperature + "C_" + voltage + ".csv")
            except:
                print(f"Failed to rename {file}")
    return

#Create a gif out of a list of Files
def createGif(file_list, save_path, duration = 0.5):
    #make a list of images
    images = []
    for file in file_list:
        images.append(imageio.imread(file))
    imageio.mimsave(save_path+"\\" + 'CorrelationsAt23.1C.gif', images)
    return

if __name__ == '__main__':
    path = "C:\\Users\\mjeffers\\Desktop\\"
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"


    # print(calibration)
    scan_path = f"{path}Experiment_2023-01-19_11-40-31\\"
    #find all CSV files in the directory
    import glob
    import os
    os.chdir(scan_path)
    convertCSVFileNames(scan_path)
    files = glob.glob("*.csv")
    #Create a list of Scan objects
    scans = []
    l2_path = makeLevel2Folder(path)
    for file in files:
        scan = Scan(file)
        #scan.plot(plot_smoothed = True, convert_to_nm=False, save=True, save_path=l2_path)
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
    print("Creating 3D Plots")
    plot3DLocalMaximas(scans, save=True, save_path=l2_path)
    #2d plot
    print("Creating 2D Plots")
    plotLocalMaximasVsVoltageSameTemperature(scans, fit_a_line=True, save=True, save_path=l2_path)
    # #2d plot
    #plotLocalMaximasVsTemperatureSameVoltage(scans, fit_a_line=True, save=True, save_path=l2_path)

    #find the correlation of every other scan in the set of temperature scans
    #Find the Scan that is closest to 23C and 3.0V
    seed_scan = None
    files = []
    for scan in scans:
        if scan.temperature == 23.1:
            seed_scan = scan
            print("Creating Correlation Plots")
            correlation_matrix, filename = findCorrelation(seed_scan, temperature_scan_sets, save=True, save_path=l2_path)
            files.append(filename)
    #Create a Gif out of the correlation plots
    createGif(files, save_path=l2_path)
    
    print('Done')