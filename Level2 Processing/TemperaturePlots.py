from Data_Gathering import get_all_scans
import Scan
from Scan_Processing import process_scans
import matplotlib.pyplot as plt
import numpy as np
from Generate_Gif import createGif

# Go through the scans and get the nearest maxima for each scan then find the RMS value
def RMS_Calculation(scans):
    # Get the nearest maxima for each scan
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
    #Get the mean of the nearest maxima
    mean_nearest_maxima = np.mean(nearest_maxima)
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

    return rms



# Create a plot of The nearest_maxima vs Temperature
def plotNearestMaximaVsTemperature(scans_path, save_path,stage_size, filename = "NearestMaximaVsTemperature.png", voltage = 5.0):
    scans = get_all_scans(scans_path, stage_size)

    # Filter Scans to only get scans at 3.0V
    scans = Scan.filter_scans(scans, voltage = voltage, prefix = "Hold", sort = "Temperature")
    #Check to see if there are any scans if not return
    if len(scans) == 0:
        return
    crosssections, scans = process_scans(scans, save_path, generate_graph = True)
    createGif(crosssections[1:], save_path, filename = "CrossSections", delete_files = True, setFPS = 2)
    #Print the nearest maximas for each scan
    RMS_Calculation(scans)
    for scan in scans:
        #Convert to Wavelength
        print(Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis))
    input("Press Enter to Continue")
    # Get the nearest maxima for each scan
    nearest_maxima = [Scan.ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
    
    # Subtract the lowest point from all the data
    # lowest = min(nearest_maxima)
    # for i in range(len(nearest_maxima)):
    #     nearest_maxima[i] -= lowest
    
    # Go through all nearest maximas and fix any discontinuities. ie if the current data point is less than.2nm add .43nm th the data point
    for i in range(len(nearest_maxima)):
        if i == 0:
            continue
        # TODO Bad Assumption Here Need to fix discontiniuty detection
        if nearest_maxima[i] < nearest_maxima[i-1]-.2:
            print("Discontinuity found")
            nearest_maxima[i] += scan.stage.fsr
            
                
    # Get the temperatures for each scan
    temperatures = [scan.temperature for scan in scans]
    # Create the plot
    fig, ax = plt.subplots()
    
    
    
    ax.plot(temperatures, nearest_maxima, 'o')
    ax.set(xlabel='Temperature (C)', ylabel='Wavelength Offset (nm)',
        title=f'Wavelength Offset (nm) vs Temperature at LCVR Drive Voltage {scans[0].voltage}V')
    ax.grid()
    # Fit a line to the data
    z = np.polyfit(temperatures, nearest_maxima, 1)
    print(f"y={z[0]}x+{z[1]}")
    p = np.poly1d(z)
    ax.plot(temperatures,p(temperatures),"r--")
    # Show the linear equation as well as the R^2 value
    ax.text(0.05, 0.95, f"y={z[0]:.2f}x+{z[1]:.2f}", transform=ax.transAxes, fontsize=14, verticalalignment='top')
    # Save the plot
    input("Press Enter to Continue")
    fig.savefig(save_path + "\\" + f"NearestMaximaVsTemperature_{voltage}V.png")
    two_plot = False
    if two_plot:
        filenames = []
        for scan in scans:
            filename = f"2PlotTemperatureVsWavelength_{scan.temperature}_{voltage}V.png"
            TwoPlotTemperatureVsWavelength(scan, [temperatures, nearest_maxima], save_path, filename = filename)
            filenames.append(save_path + "\\" + filename)
        
        #Make a gif of the 2 plot
        createGif(filenames, save_path, filename = "2PlotTemperatureVsWavelength.gif", delete_files = True, setFPS = 5)
    return


# Create a plot with two figures one on top is the crosssection with the neaeast maxima marked and the bottom is the nearest maxima vs temperature
def TwoPlotTemperatureVsWavelength(scan, data, save_path, filename = "2PlotTemperatureVsWavelength.png"):
    #Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=False, sharey=False, figsize=(16, 12))
    
    fig.suptitle(f"Temperature vs Wavelength Offset of LFDI Wide-Fielded Stage ({scan.stage.stage_size}) at {scan.temperature}V")
    # Plot the cross section
    ax1.plot(scan.smoothed_cross_section/16, linewidth = 3, color = "blue", label = "Smoothed data")

    # Set the Ticks for Axis 1
    ax1.set_xticks(np.linspace(0, len(scan.cross_section), 10), np.round(np.linspace(Scan.ConversionEquation(0,scan.image_xaxis), Scan.ConversionEquation(len(scan.cross_section),scan.image_xaxis), 10), 2))
    ax1.axvline(x = 1903, color = "red", linestyle = "--",linewidth = 3,label = "H-Alpha")
    ax1.set(xlabel='Wavelength (nm)', ylabel='Intensity (adu)')
    # Plot a line through the nearest maxima
    ax1.axvline(x = scan.nearest_maxima, linestyle = ":",linewidth = 3,color = "red", label = "Nearest transmission peak to H-alpha")
    # Keep legend in the top right Corner
    ax1.legend(loc = "upper right")
    ax1.grid()
    # Make Axis static
    ax1.set_ylim([0, 1000])


    ax2.plot(data[0], data[1], 'o', markersize = 10)
    ax2.set(xlabel='Temperature (C)', ylabel='Wavelength Offset (nm)')

    ax2.grid()
    # Fit a line to the data
    z = np.polyfit(data[0], data[1], 1)
    p = np.poly1d(z)
    ax2.plot(data[0],p(data[0]),"r--")
    # Show the linear equation as well as the R^2 value
    ax2.text(0.05, 0.95, f"y={z[0]:.2f}x+{z[1]:.2f}", transform=ax2.transAxes, fontsize=14, verticalalignment='top')
    # Plot an orange dot on the current temperature
    index = (np.abs(np.array(data[0]) - scan.temperature)).argmin()
    # Plot the point
    ax2.plot(data[0][index], data[1][index], 'o', color = "orange", markersize = 10)
    # Save the plot
    fig.savefig(save_path + "\\" + filename)

    return
