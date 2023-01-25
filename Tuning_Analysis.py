import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.signal import savgol_filter
from PIL import Image
#Smooth a 1D csv and plot it
import heapq
from matplotlib import animation
import imageio



class Scan:

    def __init__(self, filename):
        #File name will have the format "XX.XXXC_V.VV.csv or in the format of "XX.XC_VV.VV.csv"
        #Get the temperature and voltage from the file name
        self.hold = (filename.split('_')[-4] == "Hold")
        self.time = filename.split('_')[-3]
        self.temperature = filename.split('_')[-2].split('C')[0]
        self.voltage = filename.split('_')[-1].split('V.csv')[0]

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
        #Exlude the last maxima because it can be a false reading. Also exclude any maxima that is less than 50 pixels away from a minima
        for i in range(self.first_local_maxima_index, len(self.maxima)-2):
            if self.maxima[i] - self.minima[i] > 100:
                print(f"Maxima {i} is {self.maxima[i] - self.minima[i]} pixels away from minima {i}")
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
        #keep the y axis between 0 and 50000
        plt.ylim(0,50000)
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



#make a level 2 folder for the data
def makeLevel2Folder(path):
    #get the current time
    now = datetime.now()
    #format the time
    dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    #make the folder
    os.mkdir(path + "Level2_" + dt_string)
    return path + "Level2_" + dt_string


#Create a gif out of a list of Files
def createGif(file_list, save_path, filename = "CorrelationsAt23.1C.gif"):
    #make a list of images
    images = []
    for file in file_list:
        images.append(imageio.imread(file))
    imageio.mimsave(save_path+"\\" + f'{filename}.gif', images)
    return


#Main Function
if __name__ == '__main__':
    path = "C:\\Users\\mjeffers\\Desktop\\"
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"


    # print(calibration)
    #scan_path = f"{path}Experiment_2023-01-20_15-19-55\\"
    scan_path = f"{path}Experiment_2023-01-23_14-48-31\\"
    #find all CSV files in the directory
    import glob
    import os
    os.chdir(scan_path)
    #convertCSVFileNames(scan_path)
    files = glob.glob("*.csv")
    #Create a list of Scan objects
    scans = []
    l2_path = makeLevel2Folder(path)
    for file in files:
        scan = Scan(file)
        #scan.plot(plot_smoothed = True, convert_to_nm=False,show=True, save=True, save_path=l2_path)
        scans.append(scan)

    #Find the First local maxima for each scan
    first_local_maximas = []
    for scan in scans:
        first_local_maximas.append(scan.first_local_maxima)
    #Find the average first local maxima
    average_first_local_maxima = np.mean(first_local_maximas)
    #Find the standard deviation of the first local maxima
    std_first_local_maxima = np.std(first_local_maximas)
    #Find the max and min first local maxima
    max_first_local_maxima = np.max(first_local_maximas)
    min_first_local_maxima = np.min(first_local_maximas)
    print(f'Average First Local Maxima: {str(average_first_local_maxima)}')
    print(f'Standard Deviation of First Local Maxima: {str(std_first_local_maxima)}')
    print(f'Max First Local Maxima: {str(max_first_local_maxima)}')
    print(f'Min First Local Maxima: {str(min_first_local_maxima)}')
    plot_list = []
    #Sort the Scan objects by temperature
    scans.sort(key=lambda x: float(x.temperature), reverse=False)
    for scan in scans:
        scan.plot(plot_smoothed = True, convert_to_nm=False,show=False, save=True, save_path=l2_path)
        plot_list.append(f"{l2_path}\\{str(scan.temperature)}C_{str(scan.voltage)}V.png")

    
    createGif(plot_list, l2_path, filename = "TempCompensationAlgorithm")

    print('Done')