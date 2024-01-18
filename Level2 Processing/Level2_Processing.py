
from datetime import datetime
from scipy.signal import savgol_filter
import imageio
import Scan
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#import maxnlocators
from matplotlib.ticker import MaxNLocator
import pickle

#Generate a LUT from the wavelength calibration data. 
#This should be an array of Voltages with the index being the wavelength with the following formula applied 
#   wavelength = index/1000 + 656.28
#   @param wavelength_calibration_data: The data to use to generate the LUT
#   @param stage_size: The stage size of the data
#   @param save_path: The path to save the LUT to
def generate_LUT(wavelength_calibration_data, stage_size, save_path):
    #Create the LUT
    LUT = [0 for i in range(1000)]
    #Go through the wavelength calibration data and add the voltage to the LUT
    for data in wavelength_calibration_data:
        LUT[int(round((data[0] - 656.28)*1000))] = data[1]
    #Save the LUT
    with open(save_path + "\\" + f"LUT_{stage_size}mm.pkl", "wb") as f:
        pickle.dump(LUT, f)
    return LUT

def Multi_FSR_Plot(scans_path, save_path, stage_size):
    scans = get_all_scans(scans_path, stage_size)
    #Filter Scans to only get scans at 3.0V
    scans = filter_scans(scans, temperature = [23.4, 23.6], prefix = "Hold", sort = "Voltage")
    process_scans(scans, save_path, generate_graph = True)
    #Get the nearest maxima for each scan
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    
    #Get the voltages for each scan
    voltages = [scan.voltage for scan in scans]
    voltages.extend([scan.voltage for scan in scans])
    voltages.extend([scan.voltage for scan in scans])
    #Create the plot
    #go through the nearest maximas and look for a discontinuity in the data
    #if there is a discontinuity, then add .45nm to all the previous data
    for i in range(len(nearest_maxima)):
        if i == 0:
            continue
        if nearest_maxima[i] > .30 + nearest_maxima[i-1]:
            for j in range(i):
                nearest_maxima[j] += .43

    Upper_FSR = [nearest_maxima[i] + .43 for i in range(len(nearest_maxima))]
    Lower_FSR = [nearest_maxima[i] - .43 for i in range(len(nearest_maxima))]
    nearest_maxima.extend(Upper_FSR)
    nearest_maxima.extend(Lower_FSR)

    #Go through make all the data relative to the lowest point
    zeroout = False
    if zeroout:
        lowest = min(nearest_maxima)
        for i in range(len(nearest_maxima)):
            nearest_maxima[i] -= lowest
        fig, ax = plt.subplots()
        ax.plot(voltages, nearest_maxima, 'o')
        ax.set(xlabel='Voltage (V)', ylabel='Wavelength Offset (nm)',
        title=f'Wavelength Offset (nm) vs LCVR Drive Voltage\n for LFDI Single Wide-Fielded Stage ({scans[0].stage_size}) at {scans[0].temperature}C')
    else:
        fig, ax = plt.subplots()
        ax.plot(voltages, nearest_maxima, 'o')
        ax.set(xlabel='Voltage (V)', ylabel='Tuning Range (nm)',
        title=f'Tuning Range (nm) vs LCVR Drive Voltage\n for LFDI Single Wide-Fielded Stage ({scans[0].stage_size}) at {scans[0].temperature}C')    
    ax.grid()

    #Save the plot
    fig.savefig(save_path + "\\" + "Multi_FSR_Plot.png")




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
def createGif(file_list, save_path, filename = "CorrelationsAt23.1C.gif", delete_files = False, setFPS = 2):
    #make a list of images
    images = []
    for file in file_list:
        images.append(imageio.imread(file))
    #save the gif
    
    #One image for every 1 second
    
    imageio.mimsave(save_path+"\\" + f'{filename}.gif', images, fps = setFPS)

    #Delete the files
    if delete_files:

        for file in file_list:
            #Check if file exists or if it's a directory
            if os.path.exists(file) and os.path.isfile(file):
                # Delete it
                os.remove(file)
    return

#Plot the nearest maxima vs voltage
def plotNearestMaximaVsVoltage(scans_path, save_path, stage_size, filename = "NearestMaximaVsVoltage.png"):
    scans = get_all_scans(scans_path, stage_size)
    #Filter Scans to only get scans at 3.0V
    scans = filter_scans(scans, temperature = [23.4, 23.6], prefix = "Hold", sort = "Voltage")
    print(f"Number of Scans Found: {len(scans)}")
    process_scans(scans, save_path, generate_graph = True)
    #Get the nearest maxima for each scan
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    #Get the voltages for each scan
    voltages = [scan.voltage for scan in scans]
    #Create the plot
    #go through the nearest maximas and look for a discontinuity in the data
    #if there is a discontinuity, then add .45nm to all the previous data
    for i in range(len(nearest_maxima)):
        if i == 0:
            continue
        if nearest_maxima[i] > .30 + nearest_maxima[i-1]:
            for j in range(i):
                nearest_maxima[j] += .43

    #Go through make all the data relative to the lowest point
    zeroout = True
    if zeroout:
        lowest = min(nearest_maxima)
        for i in range(len(nearest_maxima)):
            nearest_maxima[i] -= lowest
        fig, ax = plt.subplots()
        ax.plot(voltages, nearest_maxima, 'o')
        ax.set(xlabel='Voltage (V)', ylabel='Wavelength Offset (nm)',
        title=f'Wavelength Offset (nm) vs LCVR Drive Voltage\n for LFDI Single Wide-Fielded Stage ({scans[0].stage_size}) at {scans[0].temperature}C')
    else:
        fig, ax = plt.subplots()
        ax.plot(voltages, nearest_maxima, 'o')
        ax.set(xlabel='Voltage (V)', ylabel='Tuning Range (nm)',
        title=f'Tuning Range (nm) vs LCVR Drive Voltage\n for LFDI Single Wide-Fielded Stage ({scans[0].stage_size}) at {scans[0].temperature}C')    
    ax.grid()

    #Save the plot
    fig.savefig(save_path + "\\" + filename)
    two_plot = True
    if two_plot:
        filenames = []
        for scan in scans:
            filename = f"2PlotVoltageVsWavelength_{scan.voltage}.png"
            TwoplotVoltageVsCurve(scan, [voltages, nearest_maxima], save_path, filename = filename)
            filenames.append(save_path + "\\" + filename)
    
    #Make a gif of the 2 plot
    
    
    createGif(filenames, save_path, filename = "2PlotVoltageVsWavelength.gif", delete_files = True, setFPS = 5)
    return



#Make a diagrom showing the nearest maxima vs voltage for multiple temperatures
def plotNearestMaximaVsVoltage_Diagram(scans_path, l2_path, stage_size, temperatures, filename = "NearestMaximaVsVoltageMultiTemp.png", fix_discontinue= True):
        
    scans = get_all_scans(scans_path, stage_size)
    temperature_sets = []
    for temp in temperatures:
        filtered_scans = filter_scans(scans,compensated = False, temperature = [temp - .2, temp + .2], prefix = "Hold", sort = "Voltage")
        cross_section,processed_scans  = process_scans(filtered_scans, l2_path, generate_graph = True)
        print(f"Length of Filtered Scans {len(filtered_scans)}")
        temperature_sets.append(processed_scans)
        
    print("Done Sorting")
    print("Saving Cross Sections")
    


    print(len(temperature_sets))
    fig, ax = plt.subplots()
    colors = ["tab:blue", "tab:orange", "tab:brown", "tab:red"]
    c = 0
    for scans in temperature_sets:
    
        
        print("Temperature: ", scans)
    #Get the nearest maxima for each scan
        for scan in scans:
            print(scan.nearest_maxima)
        nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
        #Get the voltages for each scan
        voltages = [scan.voltage for scan in scans]
        if stage_size  == 2.7:
            fsr = .42
        if stage_size == 5.4:
            fsr = .205
        #Create the plot
        #go through the nearest maximas and look for a discontinuity in the data
        #if there is a discontinuity, then add .45nm to all the previous data
        print("Length of nearest maxima: ", len(nearest_maxima))
        for i in range(len(nearest_maxima)):
            if i == 0:
                continue
            if nearest_maxima[i] > (fsr-.1) + nearest_maxima[i-1]:
                for j in range(i):
                    nearest_maxima[j] += fsr
        
        middle_plot = [maxima - fsr for maxima in nearest_maxima]
        lower_plot = [maxima - fsr for maxima in middle_plot]
        
        ax.plot(voltages, nearest_maxima, 'o', color= colors[c])
        ax.plot(voltages, middle_plot,  'o',color= colors[c])
        ax.plot(voltages, lower_plot,  'o',color=colors[c], label = f"{round(scan.temperature*2)/2}C")
        c=+1
        ax.set(xlabel='2kHz LCVR Control Voltage Amplitude [Vpp]', ylabel='Tuning Range (nm)',
            title=f'Verification of the Achievable Tuning Range\nfor the {scans[0].stage_size}mm LFDI Wide-Fielded Stage at {round(scan.temperature*2)/2}C')
        ax.grid()
        #Add a line at the following points
        #656.28nm
        #656.08nm
        #656.48nm
        ax.axhline(656.28, color = 'violet',linewidth = 3, label = "H-alpha at 656.28")
        ax.axhline(656.08, color = 'b', linewidth = 2,label = "656.08nm FSR Requirement (Blueward)")
        ax.axhline(656.48, color = 'r', linewidth = 2,label = "656.48 nm FSR Requirement (Redward)")
        ax.legend()
        #Save the plot
        fig.savefig(l2_path + "\\" + filename)
        plt.show()


#Mark Regions of Delta Wavelength over Delta Voltage and find the linear equation that best matches that region
##@Brief: This function will plot the nearest maxima vs voltage and Create a Graphical box around different regions of the plot
#   The user will then be able to select the region that they want to find the linear equation for and the program will find the best fit line for that region
#@Param scans_path: The path to the scans
#@Param l2_path: The path to the level 2 folder
#@Param stage_size: The stage size of the scans
#@Param temperatures: The temperatures to filter by
#@Param filename: The name of the file to save the plot as
#@Param fix_discontinue: If true then the program will fix any discontinuities in the data
#@Param Voltage_Regions: A list of tuples that represent the regions to find the linear equation for
#   The tuple should be in the form (start_voltage, end_voltage)
def plotNearestMaximaVsVoltage_Diagram2(scans_path, l2_path, stage_size, temperatures, filename = "NearestMaximaVsVoltageMultiTemp.png", fix_discontinue= True, Voltage_Regions = [(0, 1.7), (1.7, 5.0), (5.0, 8.0), (8.0, 17)]):
    #Get all the scans in the scans_path
    scans = get_all_scans(scans_path, stage_size)
    #Filter the scans
    temperature_sets = []
    for temp in temperatures:
        filtered_scans = filter_scans(scans,compensated = False, temperature = [temp - .2, temp + .2], prefix = "Hold", sort = "Voltage")
        cross_section,processed_scans  = process_scans(filtered_scans, l2_path, generate_graph = True)
        print(f"Length of Filtered Scans {len(filtered_scans)}")
        temperature_sets.append(processed_scans)
        
    print("Done Sorting")
    print("Saving Cross Sections")
    


    print(len(temperature_sets))
    fig, ax = plt.subplots()
    colors = ["tab:blue", "tab:orange", "tab:brown", "tab:red"]
    c = 0
    for scans in temperature_sets:
    
        
        print("Temperature: ", scans)
    #Get the nearest maxima for each scan
        for scan in scans:
            print(scan.nearest_maxima)
        nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
        #Get the voltages for each scan
        voltages = [scan.voltage for scan in scans]
        if stage_size  == 2.7:
            fsr = .42
        if stage_size == 5.4:
            fsr = .205
        if stage_size == 10.8:
            fsr = .09
        #Create the plot
        #go through the nearest maximas and look for a discontinuity in the data
        #if there is a discontinuity, then add .45nm to all the previous data
        print("Length of nearest maxima: ", len(nearest_maxima))
        for i in range(len(nearest_maxima)):
            if i == 0:
                continue

            #The 10.8 Stage is inverted so the discontinuity is the opposite
            if stage_size == 10.8:
                if nearest_maxima[i] < nearest_maxima[i-1] - (fsr*.25):
                    print("Discontinuity found")
                    for j in range(i):
                        nearest_maxima[j] -= fsr
            else:
                if nearest_maxima[i] > (fsr*.25) + nearest_maxima[i-1]:
                    for j in range(i):
                        nearest_maxima[j] += fsr
            
        middle_plot = [maxima - fsr for maxima in nearest_maxima]

        ax.plot(voltages, middle_plot, 'o', color= colors[c])
        ax.set(xlabel='2kHz LCVR Control Voltage Amplitude [Vpp]', ylabel='Tuning Range (nm)',
            title=f'Wavelength Vs Voltage Relationship for Tuning Regions\nfor the {scans[0].stage_size}mm LFDI Wide-Fielded Stage at {round(scan.temperature*2)/2}C')
        ax.grid()
        #Draw Boxes around the voltage regions make each region a different color
        n=0
        #linestiles list
        linestyles = ["+", "--", "*", "-.", ":", "-"]
        for region in Voltage_Regions:
            
            #Get a uniq Color for the region
            color = np.random.rand(3,)
            ax.axvspan(region[0], region[1], alpha=0.5, color=color)
            #Find the Deta Voltage and Delta Wavelength for the region
            #Find the index of the start and end voltage
            start_index = (np.abs(np.array(voltages) - region[0])).argmin()
            end_index = (np.abs(np.array(voltages) - region[1])).argmin()
            #Get the voltages and nearest maximas for the region
            region_voltages = voltages[start_index:end_index]
            region_nearest_maxima = middle_plot[start_index:end_index]
            #Fit a line to the data
            z = np.polyfit(region_voltages, region_nearest_maxima, 1)
            p = np.poly1d(z)
            ax.plot(region_voltages,p(region_voltages),f"r{linestyles[n]}", linewidth = 3, label = f"Region {n}: y={z[0]:.3f}x+{z[1]:.2f}")
            n= n+1

            
        c=+1
        #Show the Plot
        plt.legend()
        plt.show()

        #Save the plot
        fig.savefig(l2_path + "\\" + filename)
        #retrun the maximas vs Voltage data
        return (voltages, middle_plot)




#Create a plot of The nearest_maxima vs Temperature
def plotNearestMaximaVsTemperature(scans_path, save_path,stage_size, filename = "NearestMaximaVsTemperature.png", voltage = 5.0):
    scans = get_all_scans(scans_path, stage_size)

    #Filter Scans to only get scans at 3.0V
    scans = filter_scans(scans, voltage = voltage, prefix = "Hold", sort = "Temperature")

    crosssections, scans = process_scans(scans, l2_path, generate_graph = True)

    #Get the nearest maxima for each scan
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
    
    #Subtract the lowest point from all the data
    # lowest = min(nearest_maxima)
    # for i in range(len(nearest_maxima)):
    #     nearest_maxima[i] -= lowest
    
    #Go through all nearest maximas and fix any discontinuities. ie if the current data point is less than.2nm add .43nm th the data point
    for i in range(len(nearest_maxima)):
        if i == 0:
            continue
        #TODO Bad Assumption Here Need to fix discontiniuty detection
        if nearest_maxima[i] < nearest_maxima[i-1]-.2:
            print("Discontinuity found")
            nearest_maxima[i] += .41
            
                
    #Get the temperatures for each scan
    temperatures = [scan.temperature for scan in scans]
    #Create the plot
    fig, ax = plt.subplots()
    
    
    
    ax.plot(temperatures, nearest_maxima, 'o')
    ax.set(xlabel='Temperature (C)', ylabel='Wavelength Offset (nm)',
        title=f'Wavelength Offset (nm) vs Temperature at LCVR Drive Voltage {scans[0].voltage}V')
    ax.grid()
    #Fit a line to the data
    z = np.polyfit(temperatures, nearest_maxima, 1)
    p = np.poly1d(z)
    ax.plot(temperatures,p(temperatures),"r--")
    #Show the linear equation as well as the R^2 value
    ax.text(0.05, 0.95, f"y={z[0]:.2f}x+{z[1]:.2f}", transform=ax.transAxes, fontsize=14, verticalalignment='top')
    #Save the plot
    fig.savefig(save_path + "\\" + f"NearestMaximaVsTemperature_{voltage}V.png")
    two_plot = True
    if two_plot:
        filenames = []
        for scan in scans:
            filename = f"2PlotTemperatureVsWavelength_{scan.temperature}_{voltage}V.png"
            TwoPlotTemperatureVsWavelength(scan, [temperatures, nearest_maxima], save_path, filename = filename)
            filenames.append(save_path + "\\" + filename)
        
        #Make a gif of the 2 plot
        createGif(filenames, save_path, filename = "2PlotTemperatureVsWavelength.gif", delete_files = True, setFPS = 5)
    return

#Create a plot with two figures one on top is the crosssection with the neaeast maxima marked and the bottom is the nearest maxima vs temperature
def TwoPlotTemperatureVsWavelength(scan, data, save_path, filename = "2PlotTemperatureVsWavelength.png"):
    #Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=False, sharey=False, figsize=(16, 12))
    
    fig.suptitle(f"Temperature vs Wavelength Offset of LFDI Wide-Fielded Stage ({scans[0].stage_size}) at {scan.temperature}V")
    #Plot the cross section
    ax1.plot(scan.smoothed_cross_section/16, linewidth = 3, color = "blue", label = "Smoothed data")

    #Set the Ticks for Axis 1
    ax1.set_xticks(np.linspace(0, len(scan.cross_section), 10), np.round(np.linspace(Scan.ConversionEquation(0,scan.image_xaxis), Scan.ConversionEquation(len(scan.cross_section),scan.image_xaxis), 10), 2))
    ax1.axvline(x = 1903, color = "red", linestyle = "--",linewidth = 3,label = "H-Alpha")
    ax1.set(xlabel='Wavelength (nm)', ylabel='Intensity (adu)')
    #Plot a line through the nearest maxima
    ax1.axvline(x = scan.nearest_maxima, linestyle = ":",linewidth = 3,color = "red", label = "Nearest transmission peak to H-alpha")
    #Keep legend in the top right Corner
    ax1.legend(loc = "upper right")
    ax1.grid()
    #Make Axis static
    ax1.set_ylim([0, 1000])


    ax2.plot(data[0], data[1], 'o', markersize = 10)
    ax2.set(xlabel='Temperature (C)', ylabel='Wavelength Offset (nm)')

    ax2.grid()
    #Fit a line to the data
    z = np.polyfit(data[0], data[1], 1)
    p = np.poly1d(z)
    ax2.plot(data[0],p(data[0]),"r--")
    #Show the linear equation as well as the R^2 value
    ax2.text(0.05, 0.95, f"y={z[0]:.2f}x+{z[1]:.2f}", transform=ax2.transAxes, fontsize=14, verticalalignment='top')
    #Plot an orange dot on the current temperature
    index = (np.abs(np.array(data[0]) - scan.temperature)).argmin()
    #Plot the point
    ax2.plot(data[0][index], data[1][index], 'o', color = "orange", markersize = 10)
    #Save the plot
    fig.savefig(save_path + "\\" + filename)

    return

#Create 2 figure plot 
# One figure is the crosssection
#The other figure is the nearest maxima vs voltage with the Current Voltage highlighted in orange
def TwoplotVoltageVsCurve(scan, voltage_wavelength_data, save_path, filename = "2PlotVoltageVsWavelength.png"):
    #Create a 2 figure plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    #Super title
    fig.suptitle(f'Voltage vs Wavelength for LFDI Single Wide-Fielded Stage ({scan.stage_size}) at {round(scan.temperature)}C')
    #Plot the cross section
    ax1.plot(scan.smoothed_cross_section/16, linewidth = 3, label = "Smoothed Data")
    
    #Set the Ticks for Axis 1
    ax1.set_xticks(np.linspace(0, len(scan.cross_section), 10), np.round(np.linspace(Scan.ConversionEquation(0, scan.image_xaxis), Scan.ConversionEquation(len(scan.cross_section), scan.image_xaxis), 10), 2))
    ax1.axvline(x=1903, color='r', linewidth = 3,linestyle='--', label = "H-Alpha")
    ax1.set(xlabel='Wavelength (nm)', ylabel='Intensity (adu)')
    #Plot a line through the nearest maxima
    ax1.axvline(x = scan.nearest_maxima, color = "red", linestyle = ":", linewidth = 3,label = "Nearest transmission peak to H-alpha")
    #Keep the legen in the top right
    ax1.legend(loc='upper right')
    ax1.grid()
    #Make Axis static
    ax1.set_ylim([0, 1000])
    ax2.plot(voltage_wavelength_data[0], voltage_wavelength_data[1], 'o', markersize = 10)
    
    #Plot the current voltage in orange
    #Find the Point in the voltage_wavelength_data that is closest to the current voltage
    #Find the index of the closest point
    index = (np.abs(np.array(voltage_wavelength_data[0]) - scan.voltage)).argmin()
    #Plot the point
    ax2.plot(voltage_wavelength_data[0][index], voltage_wavelength_data[1][index], 'o', color = "orange", markersize = 10)
    #Set the Axis voltage should be V with the subscript pp and the wavelength should be nm 
    ax2.set(xlabel="$Voltage (V_{pp})$", ylabel='Wavelength (nm)')
    ax2.grid()
    #Set y Limit
    ax2.set_ylim([656.1, 657.1])
    
    #Save the plot
    #Increase the Size of the plot to avoid overlapping text
    fig.set_size_inches(16, 12)
    fig.savefig(save_path + "\\" + filename)
    plt.close(fig)
    
    return


#@param kwargs: The filters to use when generating the gif
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
            scans = Scan.get_scans_with_compensator_state(scans, kwargs["compensated"])
        if "prefix" in kwargs:
            print("Filtering by prefix")
            scans = Scan.get_scans_with_prefix(scans, kwargs["prefix"])
        if "temperature" in kwargs:
            print("Filtering by temperature")
            scans = Scan.get_scans_at_temperature(scans, kwargs["temperature"])
        if "voltage" in kwargs:
            print("Filtering by voltage")
            scans = Scan.get_scans_at_voltage(scans, kwargs["voltage"])
        if "wavelength" in kwargs:
            print("Filtering by wavelength")
            if "converted" in kwargs:
                converted = kwargs["converted"]
            else:
                converted = True
            scans = Scan.get_scans_at_wavelength(scans, kwargs["wavelength"], converted)
        if "sort" in kwargs:
            print("Sorting by attribute")
            if "only_unique" in kwargs:
                unique = kwargs["only_unique"]
                print(f"Using only Unique State: {unique}")
                scans = Scan.sort_scans_by_attribute(scans, attribute = kwargs["sort"], only_unique=kwargs["only_unique"])
            else:
                scans = Scan.sort_scans_by_attribute(scans, attribute = kwargs["sort"])
        
        
        return scans


#Filter the scans by temperature get only the scans at the given temperatures
#@param scans: The scans to filter
#@param temperatures: The temperatures to filter by [start, end, step](ex: 23.5, 30, 0.5)
def filter_Temperatures(scans, start, end, step):
        NewTemperatures = []
        import numpy as np
        for i in np.arange(start, end, step):
            #Find the Temperature that is closest to the current temperature
            closest = min(scans, key=lambda x:abs(x.temperature-i))
            NewTemperatures.append(closest)

        return NewTemperatures

############################################################################################################
#Create a gif out of multiple Cross sections of the Spectra Output
#@param scans_path: The path to the scans
#@param l2_path: The path to the L2 files
#@param filename: The name of the file to save the gif as
#@param kwargs: The filters to use when generating the gif
#   @param compensated: The compensated state of the scans to use (True or False)
#   @param prefix: The prefix of the scans to use (ex: "LFDI", "Hold", "Slew")
#   @param temperature: The Range of temperatures of the scans to use (ex: [25, 30], [20, 35])
#   @param voltage: The voltage of the scans to use (ex: 0.0, 3.3)
#   @param wavelength: The wavelength of the scans to use (ex: 656.28, 0.0)
#   @param sort: The sort of the scans to use (ex: "Voltage", "Temperature")
def generate_gif_plot(scans_path, l2_path, stage_size, filename = "Gif.gif", **kwargs):
        #kwargs will be used to Filter the scans
        #Get all the scans in the scans_path
        scans = get_all_scans(scans_path, stage_size=stage_size)

        #Filter the scans
        scans = filter_scans(scans, **kwargs)
        print("Done Sorting")
        crosssections = []
        print("Saving Cross Sections")
        processed_scans = []
        
        #go through all the Uniq temperatures and store all the temperatures that are closes to .5C intervals in a new list
        #This is done to reduce the number of scans that are used to generate the compensated plot
        scans = filter_Temperatures(scans, 23.5, 30, 0.5)
        print("Done Finding Closest Temperatures")

        crosssections, processed_scans = process_scans(scans, l2_path)


        #Find the mean nearest maxima for all of the scans
        nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in processed_scans]
        mean_nearest_maxima = np.mean(nearest_maxima)
        print(f"Mean Nearest Maxima: {mean_nearest_maxima}")
        #Find the maximum Variance from the mean
        max_variance = max([abs(mean_nearest_maxima - nearest_maxima[i]) for i in range(len(nearest_maxima))])
        print(f"Max Variance: {max_variance}")
        #Find the standard deviation
        std = np.std(nearest_maxima)
        print(f"Standard Deviation: {std}")
        #Calculate the RMS
        #Sum the squares of the differences from the mean
        square_diff = 0
        for i in range(len(nearest_maxima)):
            square_diff += (nearest_maxima[i] - mean_nearest_maxima)**2
        #Divide by the number of scans
        nearest_maxima = square_diff/len(nearest_maxima)
        #Take the square root

        rms = np.sqrt(nearest_maxima)
        print(f"RMS: {rms}")


        print("Making Gif")

        #Remove the first Filename for some reason its messed up
        crosssections = crosssections[1:]
        createGif(crosssections, l2_path, filename, delete_files=True)
        return


def get_all_scans(scans_path, stage_size):
        #Get all the scans in the scans_path
        Files = [scan for scan in os.listdir(scans_path) if scan.endswith(".png")]
        scans = []
        for File in Files:
            #Check if a pickle file exists for the scan
            if os.path.exists(f"{scans_path}\\{File[:-4]}.pkl"):
                #Load the pickle file
                with open(f"{scans_path}\\{File[:-4]}.pkl", 'rb') as f:
                    scans.append(pickle.load(f))
            else:
                scans.append(Scan.Scan(File, scans_path, stage_size))
        return scans

#This will produce a graph of the Needed Voltage Vs given temperature for a given Wavelength 
def generate_Voltage_V_Temperature(scans:list, l2_path, wavelength:float, error = .01):
    #Find all the Scans that have a nearest maxima of "wavelength"
    scans = filter_scans(scans, wavelength=[wavelength-error, wavelength+error], converted = True)
    #Only get the First scan for each Temperature
    scans = Scan.sort_scans_by_attribute(scans=scans,attribute="Temperature", only_unique=True)

    
    #Get the temperatures for each scan
    temperatures = [scan.temperature for scan in scans]
    #get the voltages of each scan
    voltages = [scan.voltage for scan in scans]
    print(temperatures)
    fig, ax = plt.subplots()
    
    ax.plot(temperatures, voltages, 'o', label = "Temperature Vs Voltage Tuning")
    
    ax.set(xlabel='Temperature (C)', ylabel='Peak To Peak Voltage (V)',
        title=f'Voltage V Temperature to tune to {wavelength}nm with a tolerance of +/-{error}nm')
    #plot the nearest maxima vs time on the same plot
    ax.grid()
    plt.show()
    
    return


def process_scans(scans, l2_path, generate_graph = True):
    crosssections = []
    processed_scans = []
    for temp in scans:
        #if temp is a list then there are multiple scans at that temperature
        try:
            print(f"Temperature: {temp[0].temperature}")
            #only process one scan at that temperature
            scan = temp[0]
        except:
            print(f"Temperature: {temp.temperature}")
            scan = temp
        print(f"Scan: {scan}")
        filename = f"{l2_path}\\CrossSection{scan.temperature}C.png"
        if generate_graph:
            if not scan.processed:
                scan.process()
            scan.save_cross_section(filename,  smooth=True, plot_raw=False, scale = True, Limit_Y = False)
        crosssections.append(filename)
        processed_scans.append(scan)
    
    return crosssections, processed_scans


#Main Function
if __name__ == '__main__':
    gen_compensated = False
    gen_uncompensated = False
    gen_nearest_maxima_v_Temp = False
    gen_nearest_maxima_v_Voltage = True
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"
    path = "C:\\Users\\iguser\\Documents\\GitHub\\LFDI_API\\"

    scans_path = f"{path}Experiment_2023-03-25_01-50-48\\"
    scans_path = f"{path}Experiment_2023-03-26_01-05-23\\"
    scans_path = f"{path}Experiment_2023-03-26_04-07-04\\"
    scans_path = f"{path}Experiment_2023-10-27_02-05-39\\"
    scans_path = f"{path}Experiment_2023-10-30_13-10-56\\"
    scans_path = f"{path}Experiment_2023-11-10_13-28-07\\"
    scans_path = f"{path}Experiment_2023-11-14_00-50-06\\"
    
    scans_path = f"{path}Experiment_2023-11-20_11-46-57\\" # 5.4mm Look up table data Set
    #scans_path = f"{path}Experiment_2023-11-17_16-20-49\\" #5.4 mm Temperature Cycle
    scans_path = f"{path}Experiment_2023-12-04_19-07-10\\" # new Look up table
    stage_size = 5.4
    # scans_path = f"{path}Experiment_2023-11-09_15-53-00\\" #2.7 mm LUT Epoxy New Tuning Control Board
    # stage_size = 2.7
    # scans_path = f"{path}Experiment_2023-03-26_04-07-04\\" #2.7 mm LUT Epoxy Old Tuning Control Board
    # stage_size = 2.7
    scans_path = f"{path}Experiment_2023-12-17_18-08-49\\" #2.7 mm LUT Epoxy New Tuning Control Board Complete
    stage_size = 2.7
    scans_path = f"{path}Experiment_2024-01-11_12-46-57\\" #10.8 mm LUT Epoxy New Tuning Control Board Complete
    stage_size = 10.8




    
    

    l2_path = makeLevel2Folder(path)
    #Generate the Compensated plot
    if gen_compensated:
        print("Generating Compensated")
        generate_gif_plot(scans_path, l2_path,stage_size=stage_size, filename = "Compensated.png", compensated = True, prefix = "Hold", sort = "Temperature")

    
    if gen_uncompensated:
        print("Generating Uncompensated")
        generate_gif_plot(scans_path, l2_path,stage_size=stage_size, filename = "Uncompensated.png", compensated = False, prefix = "Hold",voltage = 3.0, sort = "Temperature")

    #Generate the Nearest Maxima vs Temperature plot
    if gen_nearest_maxima_v_Temp:
        for i in range(1, 24):
            plotNearestMaximaVsTemperature(scans_path, l2_path,stage_size=stage_size, voltage = i*.5)
            

    # if gen_nearest_maxima_v_Voltage:

    #     plotNearestMaximaVsVoltage(scans_path, l2_path,stage_size=stage_size)
    #     Multi_FSR_Plot(scans_path, l2_path,stage_size=stage_size)


    #Generate a plot of nearest maxima vs Voltage for all temperatures
    if gen_nearest_maxima_v_Voltage:

        temperatures = [25.5, 29.5]
        data = plotNearestMaximaVsVoltage_Diagram2(scans_path, l2_path, stage_size=stage_size,temperatures=temperatures)
       
        #Generatere the Lookup Table
        LUT_Data = generate_LUT(data[0], data[1], l2_path, stage_size)
        print(LUT_Data)
       # plotNearestMaximaVsVoltage_Diagram(scans_path, l2_path, stage_size=stage_size,temperatures=temperatures)

    scans = get_all_scans(scans_path, stage_size)
    #Check to see if scans have been previously processed in a pickle file
    #If they have been processed then load the pickle file
    #If they have not been processed then process them and save them to a pickle file
    if os.path.exists(f"{scans_path}\\Processed.pkl"):
        #Load the pickle file
        with open(f"{scans_path}\\Processed.pkl", 'rb') as f:
            scans = pickle.load(f)
        
    else:
        crosssections, scans = process_scans(scans, l2_path, generate_graph = True)
        #Save the scans to a pickle file
        with open(f"{scans_path}\\Processed.pkl", 'wb') as f:
            pickle.dump(scans, f)
        #Save Crosssections:
        with open(f"{scans_path}\\Crosssections.pkl", 'wb') as f:
            pickle.dump(crosssections, f)
    print(len(scans))
    #Filter Scans to only get scans at 3.0V
    
    #plotNearestMaximaVsVoltage_Diagram(scan)
    scans = filter_scans(scans, compensated = False, prefix = "Hold", only_unique = False)
    generate_Voltage_V_Temperature(scans, l2_path, wavelength=656.28, error = 0.001)
    print(len(scans))
    
    #Find how long it takes the the optic to reach thermal equilibrium by looking at the time between scans and the stability of the nearest maxima
    #Create a Gif of the Scans that take place between the Temperature range of 25.5C and 26C
    #Filter Scans to only get scans at 3.0V
    #scans = filter_scans(scans, prefix = "Slew", only_unique = False)
    print(len(scans))
    #Create a Gif of the Cross Sections

    
    #plot the nearest maxima vs Temperature only get one scan from each temp
    #  and plot the nearest maxima



    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    #Get the temperatures for each scan
    temperatures = [scan.temperature for scan in scans]
    timestamps = [scan.timestamp for scan in scans]
    #Create the plot
    fig, ax = plt.subplots()
    #do not over lap the data
    start = timestamps[0]
    for i in range(len(timestamps)):
        timestamps[i] = (float(timestamps[i])- float(start))

    line1 = ax.plot(timestamps, temperatures, 'o', label = "Temperature")
    
    #make it so that each point is marked witht the time it was taken at
    #only do this for one point per temperature maxima pair
    # maxima_temp_pairs = []
    # for i in range(len(nearest_maxima)):
    #     if (nearest_maxima[i], temperatures[i]) not in maxima_temp_pairs:
    #         maxima_temp_pairs.append((nearest_maxima[i], temperatures[i]))
    #         ax.text(temperatures[i], nearest_maxima[i], f"{scans[i].timestamp}", fontsize=14, verticalalignment='top')
     
    ax.set(xlabel='Time (s)', ylabel='Temperature (C)',
        title='Temperature and Nearest Maxima to H-Alpha (nm) vs Time')
    #plot the nearest maxima vs time on the same plot
    ax.grid()
    ax2 = ax.twinx()
    line2 = ax2.plot(timestamps, nearest_maxima, 'o', color = "red", label = "Wavelength")
    ax2.set(ylabel='Nearest Maxima to H-Alpha (nm)')
    lines = line1 + line2
    labels = [l.get_label() for l in lines]

    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    ax.legend(lines, labels, loc=0)
    # Find all the points at which a window of ten points have an RMS Less than 0.05
    #Use a Window to find the RMS of all the Scans
    window = 40
    rms = []
    for i in range(len(nearest_maxima)):
        if i < window:
            rms.append(0)
        else:
            #Find the Mean of this Window
            mean_nearest_maxima = np.mean(nearest_maxima[i-window:i])
           
            #Calculate the RMS of the window
            #Sum the squares of the differences from the mean
            square_diff = 0
            for j in range(i - window, i):
                square_diff += (nearest_maxima[j] - mean_nearest_maxima)**2
            #Divide by the number of scans
            #Take the square root
            rms.append(np.sqrt(square_diff/window))
    #Plot the RMS
    # ax3 = ax.twinx()
    # line3 = ax3.plot(timestamps, rms, 'o', color = "green", label = "RMS")
    fig, ax = plt.subplots()
    ax.plot(timestamps, nearest_maxima, 'o')
    ax.set(xlabel='Time (s)', ylabel='RMS of Nearest Maxima to H-Alpha (nm)',
        title='RMS of Nearest Maxima to H-Alpha (nm) vs Time')
    ax.grid()
    #show the plot
    plt.show()

    
    #ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    ax.grid()
    #show the plot
    plt.show()
    #Ploat the Nearest maxima vs time
    #Get the times for each scan
    times = [scan.timestamp for scan in scans]
    #Create the plot
    fig, ax = plt.subplots()
    ax.plot(times, nearest_maxima, 'o')
    ax.set(xlabel='Time', ylabel='Nearest Maxima to H-Alpha (nm)',
        title='Nearest Maxima to H-Alpha (nm) vs Time')
    ax.grid()
    #show the plot
    plt.show()
    
    
    
    #Find the RMS of the nearest maxima from all the scans
    maximas = []
    maximas = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    #Find the mean nearest maxima for all of the scans
    mean_nearest_maxima = np.mean(maximas)
    print(f"Mean Nearest Maxima: {mean_nearest_maxima}")
    #Find the RMS of the nearest maxima from all the scans
    #Sum the squares of the differences from the mean
    square_diff = 0
    for i in range(len(maximas)):
        square_diff += (maximas[i] - mean_nearest_maxima)**2
    #Divide by the number of scans
    nearest_maxima = square_diff/len(maximas)
    #Take the square root
    rms = np.sqrt(nearest_maxima)
    print(f"RMS: {rms}")
    #Convert the nearest maxima to nm
    

    #make a Gif of the cross sections
#    createGif(crosssections, l2_path, filename = "CrossSections.gif", delete_files = True)
    


    #Do the same for the uncompensated scans
    scans = get_all_scans(scans_path, stage_size)

    #Filter Scans to only get scans at 3.0V
    scans = filter_scans(scans, compensated = False, prefix = "Hold",voltage = 3.0, sort = "Temperature", only_unique = False)

    #process the Scans
    crosssections, scans = process_scans(scans, l2_path, generate_graph = True)
    crosssections, scans = process_scans(scans, l2_path, generate_graph = True)

    #Get the nearest maxima for each scan
    for scan in scans:
        print(scan.nearest_maxima)
    #plot the nearest maxima vs Temperature
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    #Get the temperatures for each scan
    temperatures = [scan.temperature for scan in scans]
    #Create the plot
    fig, ax = plt.subplots()
    ax.plot(temperatures, nearest_maxima, 'o')
    ax.set(xlabel='Temperature (C)', ylabel='Nearest Maxima to H-Alpha (nm)',
        title='Nearest Maxima to H-Alpha (nm) vs Temperature')
    ax.grid()
    #show the plot
    plt.show()
    #Find the RMS of the nearest maxima from all the scans
    maximas = []
    maximas = [Scan.ConversionEquation(scan.nearest_maxima, scan.image_xaxis) for scan in scans]
    #Find the mean nearest maxima for all of the scans
    mean_nearest_maxima = np.mean(maximas)
    print(f"Mean Nearest Maxima: {mean_nearest_maxima}")
    #Find the RMS of the nearest maxima from all the scans
    #Sum the squares of the differences from the mean
    square_diff = 0
    for i in range(len(maximas)):
        square_diff += (maximas[i] - mean_nearest_maxima)**2
    #Divide by the number of scans
    nearest_maxima = square_diff/len(maximas)
    #Take the square root
    rms = np.sqrt(nearest_maxima)
    print(f"RMS: {rms}")
    #Convert the nearest maxima to nm

    #make a Gif of the cross sections
    createGif(crosssections, l2_path, filename = "CrossSectionsUncompensated.gif", delete_files = True)

    print('Done')