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

scanformat = f"PREFIX_TimeStamp_TemperatureC_VoltageV.csv"
#This is the General Scan Class that will be used to Read in all of the CSVs
#The Expected name format is "PREFIX_TimeStamp_TemperatureC_VoltageV.csv"
#Prefix can be whatever the User Wants. Normally Experiment Based ie "Slew" "Hold"
#TimeStamp should the raw output of time.time()
#Temperature should be the Temperature that Scans are taken at
#Voltage should be the Voltage applied to the optic at the Time
class Scan:
    def __init__(self, filename):
        try:
            self.temperature = float(filename.split("_")[-2].strip("C"))
            self.voltage = filename.split('_')[-1].split('V.csv')[0]
            if self.voltage != "Auto":
                self.voltage = float(filename.split('_')[-1].split('V.csv')[0])
            self.voltage = float()
            self.timestamp = filename.split('_')[-3]
            self.prefix = filename.split('_')[-4]
            self.filename = filename
        except:    
            print(f"File Name {filename} is not in the Correct Format {scanformat}")
            return


        self.data = np.loadtxt(filename, delimiter=',')
        
        #Smoothing the Crap out of the Data. This is a cheesy way to do it but subjectivly it works for now
        self.smoothed_data = savgol_filter(self.data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 50, 3)
        self.smoothed_data = savgol_filter(self.smoothed_data, 100, 3)

        #Find the Local Maxima and Minima
        self.maxima, self.minima = self.findLocalMaximaMinima(len(self.smoothed_data), self.smoothed_data)
        
        
        #Check to see if there is a minima before the first maxima and if there is not the second maxima is the first maxima. 
        # This is because we dont want to use our uphill slope as a maxima
        if self.minima[0] + 25 < self.maxima[0]:
            self.first_local_maxima = self.maxima[0]
            self.first_local_maxima_index = 0
        else:
            self.first_local_maxima = self.maxima[1]
            self.first_local_maxima_index = 1
        
        #Find the average distance between maximas This will tell us 1 FSR theoretically
        self.average_distance_between_maximas = self.findAverageDistanceBetweenMaximas()
        print(f"Read in Scan with Temperature {self.temperature}C, Voltage {self.voltage}V, Timestamp {self.timestamp}, and Prefix {self.prefix}")
        return

    # Function to find local maxima and minimas. 
    # This Code could use some tolerance Points so that it doesnt pick up bumps in the tail of the signal
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
        
        return mx, mn


    #find the average distance between local maximas starting at self.first_local_maxima_index
    def findAverageDistanceBetweenMaximas(self):
        #create a list of the distances between the maximas
        distances = []
        #Exlude the last maxima because it can be a false reading. Also exclude any maxima that is less than 50 pixels away from a minima
        for i in range(self.first_local_maxima_index, len(self.maxima)-2):
            if self.maxima[i] - self.minima[i] > 50:
                distances.append(self.maxima[i+1] - self.maxima[i])
        #return the average distance between maximas
        return np.mean(distances)

    #plot the Scan data. If the calibration data is provided, plot the mercury and hydrogen position on the graph as well, if convert_to_nm is true, convert the x axis to nm
    def plot(self,plot_smoothed = True,calibration_data = None,convert_to_nm = False, save = True, save_path = None, show = False):
        #Make image large
        plt.figure(figsize=(30.0, 10.0))
        #First plot the data Directly From the File
        plt.plot(self.data, label = 'Raw Data')
        #If plot_smoothed is true, plot the smoothed data
        if plot_smoothed:
            plt.plot(self.smoothed_data, label = 'Smoothed Data')
            plt.plot(self.maxima, self.smoothed_data[self.maxima], 'o', label = 'Maxima')
            plt.plot(self.minima, self.smoothed_data[self.minima], 'o', label = 'Minima')
            #plot the fist local maxima with a red verical line to indicate the first local maxima
            plt.axvline(x = self.first_local_maxima, color = 'r', label = 'First Local Maxima')
        
        #This is Currently Not used but this would plot the Calibration lines if they were provided
        if calibration_data is not None:
            #Create a Vertical Line with a label at the Hydrogen, deuterium and Mercury Position
            plt.axvline(x = calibration_data.Hydrogen_Pixel_Position, color = 'y', label = 'Hydrogen')
            plt.axvline(x = calibration_data.Bromine_Pixel_Position, color = 'g', label = 'Bromine')
            plt.axvline(x = calibration_data.Deuterium_Pixel_Position, color = 'b', label = 'Deuterium')

        #This is Currently Not used but Would Scale the Graph to the Calibration Data if it was provided
        if convert_to_nm:
            plt.xlabel('Wavelength (nm)')
            #Convert the x axis to nm using Pixel Scaling and Pixel Offset            
            plt.xticks(np.arange(0, len(self.smoothed_data), 1), np.arange(calibration_data.Pixel_Offset, len(self.smoothed_data)*calibration_data.Pixel_Scaling + calibration_data.Pixel_Offset, calibration_data.Pixel_Scaling)[:-1])
            #only show 10 ticks
            plt.locator_params(axis='x', nbins=10)
        
        #If we are not Converting to nm, just plot the pixel position
        else:
            plt.xlabel('Pixel Position')
            #Xtick every 500 pixels
            plt.xticks(np.arange(0, len(self.smoothed_data), 500))
            #grid
            plt.grid()

        
        #include the distance between maximas in the top left corner
        plt.text(0.01, 0.99, f'Average Distance Between Maximas: {str(self.findAverageDistanceBetweenMaximas())}', horizontalalignment='left', verticalalignment='top', transform=plt.gca().transAxes)
        #Keep the limits the Same so that we can make a gif later on
        plt.ylim(0,50000)
        plt.ylabel('Intensity')
        plt.title(f'Scan at {str(self.temperature)}C {str(self.voltage)}V')
        plt.legend()

        #Plot first local maxima and write the pixel position
        plt.annotate(str(self.first_local_maxima), xy=(self.first_local_maxima, self.smoothed_data[self.first_local_maxima]), xytext=(self.first_local_maxima, self.smoothed_data[self.first_local_maxima]), arrowprops=dict(facecolor='black', shrink=0.05),)

        if save:
            #Save as full screen png
            plt.savefig(f"{save_path}\\{str(self.temperature)}C_{str(self.voltage)}V.png", bbox_inches='tight')
        if show:  
            plt.show()
        #Close the plot to conserve memory
        plt.close()
        return

    def __str__(self):
        #Format the self.timestamp to be more readable
        return f"{self.prefix} Scan at {str(self.temperature)}C {str(self.voltage)}V {self.timestamp}"



#Create a class to store all of the Classes with the Same Voltage
#and plot Groupl level Data
class VoltageScanSet:
    def __init__(self, voltage, scans: list[Scan]):
        self.voltage = voltage
        self.scans = scans
        #Sort the scans by temperatures
        self.scans.sort(key=lambda x: x.temperature)
        return

    #Create a plot of the first local maximas vs the temperature
    def plotFirstLocalMaximasVsTemperature(self, save = False, folder = None):
        #Clear all plots
        plt.clf()
        plt.figure()
        #Set the title and axis labels
        plt.title(f"First Local Maximas vs Temperature for {self.voltage}V")
        plt.xlabel("Temperature (C)")
        plt.ylabel("First Local Maxima")
        plt.ylim
        #Go through each scan and plot the temperature vs the retardance
        for i in range(len(self.scans)):
            plt.plot(self.scans[i].temperature, self.scans[i].first_local_maxima, 'o')

        #Fit a line to the data
        z = np.polyfit([scan.temperature for scan in self.scans], [scan.first_local_maxima for scan in self.scans], 1)
        p = np.poly1d(z)
        plt.plot([scan.temperature for scan in self.scans], p([scan.temperature for scan in self.scans]), 'r--')
        
        #Save the plot if save is true
        #Plot the equation of the line on the plot
        plt.text(0.01, 0.99, f'Equation: {str(p)}', horizontalalignment='left', verticalalignment='top', transform=plt.gca().transAxes)
        plt.legend()
        if save:
            filename = f"{folder}/{self.voltage}V.png"
            plt.savefig(filename, bbox_inches='tight')
        plt.close()
        return filename

        #What to Print out when we print the class
    def __str__(self):
        return f"Voltage Scan Set of {self.voltage}V length {len(self.scans)}"



#Create a class to store all of the Classes with the Same Temperature
#and plot Groupl level Data
class TemperatueScanSet:
    def __init__(self, temperature, scans: list[Scan]):
        self.temperature = temperature
        self.scans = scans
        #Sort the scans by voltages
        self.scans.sort(key=lambda x: x.voltage)
        self.average_distance_between_maximas = self.findAverageDistanceBetweenMaximas()
        self.retardances = []
        self.getFirstLocalMaximas()
        #self.fixDiscontinuity()
        
        
        return

    #Go through all the scans and find where the the previous first maxima is lower than the current first maxima of scans and add the average distance between the maxima to the list
    #This Works Poorly Currently
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
        plt.title(f"First Local Maximas vs Voltage for {self.temperature}C")
        plt.xlabel("Voltage (V)")
        plt.ylabel("First Local Maxima")
        #Go through each scan and plot the voltage vs the retardance
        for i in range(len(self.scans)):
            plt.plot(self.scans[i].voltage, self.retardances[i], 'o')

        if save:
            plt.savefig(f"{folder}/{self.temperature}C.png")
        plt.close()
        return

        #plt.show()

    #Find the Average of all the average distances between maximas
    def findAverageDistanceBetweenMaximas(self):
        distances = []
        for scan in self.scans:
            distances.append(scan.average_distance_between_maximas)
        return np.mean(distances)



    #Create a CSV where the index is the first local maxima and the Value is the Voltage
    #Thsi Requires a lot of baby sitting Needs to be updated
    def createCSVOfVoltageSortedByPosition(self, save_path = None, FixedData = None ):
        #Create a list of Tuples of the voltage values and the Maximas
        if FixedData is None:
            labels = [(scan.voltage, scan.first_local_maxima) for scan in self.scans]
        else:
            labels = [(scan.voltage, FixedData[i]) for i, scan in enumerate(self.scans)]
        #Sort the list by local maxima value
        labels.sort(key=lambda x: x[1])
        print(labels)
        #Create a CSV where the index is the first local maxima and the value is the voltage if a fist local maxima value is missing then interpolate between the two adjacent values. There should be a value for every position between zero and the highest value local maxima
        #File name is the temperature of the temperature scan set
        filename = f"{save_path}\\Voltage Sorted by Position of {self.temperature}C.csv"
        with open(filename, "a") as file:
            file.write(f"Position, Voltage\n")
            #for every position between zero and the highest value local maxima
            Positions = "Position,"
            Voltages = "Voltages,"
            for i in range(int(labels[-1][1])):
                print(i)
                #if the position is in the list of first local maxima
                if i in [label[1] for label in labels]:
                    #write the position and the voltage to the CSV
                    Positions += f"{i},"
                    Voltages += f"{round(labels[i][0], 3)},"
                    #file.write(f"{i}, {round(labels[i][0], 3)}\n")
                else:
                    #find the first position that is greater than the current position
                    for label in labels:
                        if label[1] > i:
                            #find the first position that is less than the current position
                            for label2 in reversed(labels):
                                if label2[1] < i:
                                    #interpolate between the two positions
                                    voltage = label2[0] + (label[0] - label2[0]) * (i - label2[1]) / (label[1] - label2[1])
                                    #Format Voltage to 3 decimal places
                                    Voltages += f"{round(voltage, 3)},"
                                    Positions += f"{i},"
                                    #write the position and the voltage to the CSV
                                    #file.write(f"{i}, {voltage}\n")
                                    break
                            break
            file.write(f"{Positions}\n{Voltages}\n")
        return filename



#This is the Scan for the Experiment level of the data
#Usually Will contain all the Data Collected for a single Experiment
class ExperimentSet:
    def __init__(self, scans: list[Scan], folder_path: str):
        self.folder_path = folder_path
        self.scans = scans
        return

    #make a 3d plot of the first local maxima vs temperature and voltage
    def plot3DLocalMaximas(self, save = False, save_path = None):
        fig = plt.figure(figsize=(10.0, 10.0))
        ax = fig.add_subplot(111, projection='3d')
        x = []
        y = []
        z = []
        for scan in self.scans:
            x.append(scan.temperature)
            z.append(scan.first_local_maxima)
            y.append(scan.voltage)
        ax.scatter(x, y, z)
        ax.set_xlabel('Temperature (C)')
        ax.set_ylabel("Voltage (V)")
        ax.set_zlabel('First Maxima (Pixel Position)')

        plt.show()
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

    #Plot 3 Sets of TemperatureSCanSets in the Same plot with the same x axis of Voltage the plots should be line plots
    def plotTemperatureScanSetsSamePlot(self, temps: list[float], save = False, folder = None):
        #Clear all plots
        plt.clf()
        plt.figure()
        plt.title(f"First Local Maximas vs Voltage")
        plt.xlabel("Voltage (V)")
        plt.ylabel("First Local Maxima")
        #Go through each temperature scan set and plot the voltage vs the retardance plots should be line Graphs
        dataset = []
        for scan in self.scans:
            for temp in temps:
                #Go through each scan and plot
                if scan.temperature == temp:
                    dataset.append(scan.first_local_maxima)
                    
                plt.plot(dataset, 'o', label = f"{temp}C")
                dataset.clear()

        #Change the x axis to be the voltage
        plt.xticks(np.arange(0, len(self.scans[0].voltage), 1), self.scans[0].voltage)
        #Add major gridlines to every 10th point
        plt.grid(which='major', axis='x', linestyle='-', linewidth='0.5', color='red')
        #Add minor gridlines to every 5st point
        plt.grid(which='minor', axis='x', linestyle='-', linewidth='0.5', color='black')
        #add grid lines to the y axis
        plt.grid(which='major', axis='y', linestyle='-', linewidth='0.5', color='red')
            
        plt.legend()    
        plt.show()
        

        
        #Save the plot if save is true

        if save:
            filename = f"{folder}/3TemperatureScanSetsSamePlot.png"
            plt.savefig(filename, bbox_inches='tight')
        return filename

    
    #Using a seed scan find the correlation of every other scan in the set of temperature scans make a correlation matrix at the end
    def findCorrelation(self, seed_scan: Scan, show = False, save = False, save_path = None):
        # #make a list of the correlation values
        # correlation_values = []
        # temperature_Correlation = []
        # #for every temperature scan set
        # for temperature_scan_set in temperature_scan_sets:
        #     #for every scan in the temperature scan set
        #     for scan in temperature_scan_set.scans:
        #         #find the correlation between the seed scan and the scan
        #         correlation = np.corrcoef(seed_scan.data, scan.data)[0,1]
        #         #add the correlation to the list of correlation values
        #         temperature_Correlation.append(correlation)
        #         correlation_values.append(correlation)

        # #make a correlation matrix
        # correlation_matrix = np.reshape(correlation_values, (len(temperature_scan_sets), len(temperature_scan_set.scans)))
        # #Plot correlations with a value of 1 as a Green Dot

        # #plot the correlation matrix
        # #cLEAR ALL PREVIOUS PLOTS
        # plt.clf()
        # plt.imshow(correlation_matrix, cmap='hot', interpolation='nearest')
        # plt.colorbar(label='Correlation')
        # plt.scatter(np.where(correlation_matrix == 1)[1], np.where(correlation_matrix == 1)[0], c='g', marker='o', label='Seed')
        # #Show legen
        # plt.legend()
        # #label the x axis
        # plt.xlabel('Voltage (V)')
        # #Change the Axis so that the voltage is in the correct order
        # plt.xticks(np.arange(len(temperature_scan_set.scans)), [scan.voltage for scan in temperature_scan_set.scans])
        # #only plot every 5th label on the x axis
        # plt.xticks(np.arange(len(temperature_scan_set.scans))[::5], [scan.voltage for scan in temperature_scan_set.scans][::5])
        # #label the y axis
        # plt.ylabel('Temperature (C)')
        # #mark the position of the Seed with a green dot
        # #Change the Axis so that the temperature is in the correct order
        # plt.yticks(np.arange(len(temperature_scan_sets)), [temperature_scan_set.temperature for temperature_scan_set in temperature_scan_sets])
        # #label the color bar
        
        # #Plot the Title
        # plt.title(f'Correlation of Seed {str(seed_scan.temperature)}C and {str(seed_scan.voltage)}V')
        # #Expand the size of the plot to fit the labels
        # plt.gcf().set_size_inches(20, 10)    
        # #save the plot
        # if save:
        #     #File name is the temperature and voltage of the seed scan
        #     filename = f"{save_path}\\Correlation of Seed {str(seed_scan.temperature)}C and {str(seed_scan.voltage)}V.png"
        #     plt.savefig(filename , bbox_inches='tight')
        # #show the plot
        # if show:
        #     plt.show()
        # #make a File to store the max correlation values
        # CSV = f"{save_path}\\Correlation of Seed {str(seed_scan.temperature)}C.csv"
        # with open(CSV, "a") as file:
        #     file.write(f"Max Correlation Voltage, Temperature, Seed Voltage\n")
        # #For each row in the correlation matrix find the highest correlation value and the voltage that it corresponds to
        # i = 0
        # for row in correlation_matrix:
        #     #find the highest correlation value
        #     max_correlation = np.max(row[29:60])
        #     #find the voltage that corresponds to the highest correlation value
        #     max_correlation_voltage = float(np.where(row == max_correlation)[0][0]/10)
        #     #print the results
        #     with open(CSV, "a") as file:
        #         file.write(f"{max_correlation_voltage}V, {temperature_scan_sets[i].temperature}C, {seed_scan.voltage}V\n")
        #     i += 1
        # return correlation_matrix, filename 
        return


