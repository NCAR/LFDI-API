from Data_Gathering import get_all_scans
from Scan_Processing import process_scans
import matplotlib.pyplot as plt
import numpy as np
from Scan import filter_scans, ConversionEquation, Scan

# Mark Regions of Delta Wavelength over Delta Voltage and find the linear equation that best matches that region
# @Brief: This function will plot the nearest maxima vs voltage and Create a Graphical box around different regions of the plot
#   The user will then be able to select the region that they want to find the linear equation for and the program will find the best fit line for that region
# @Param scans_path: The path to the scans
# @Param l2_path: The path to the level 2 folder
# @Param stage_size: The stage size of the scans
# @Param temperatures: The temperatures to filter by
# @Param filename: The name of the file to save the plot as
# @Param fix_discontinue: If true then the program will fix any discontinuities in the data
# @Param Voltage_Regions: A list of tuples that represent the regions to find the linear equation for
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
        if len(scans) == 0:
            continue
        
        print("Temperature: ", scans)
    # Get the nearest maxima for each scan
        for scan in scans:
            print(scan.nearest_maxima)
        nearest_maxima = [ConversionEquation(scan.nearest_maxima,scan.image_xaxis) for scan in scans]
        #Get the voltages for each scan
        voltages = [scan.voltage for scan in scans]
        corrected_Wavelengths = []
        # Create the plot
        # go through the nearest maximas and look for a discontinuity in the data
        # if there is a discontinuity, then add .45nm to all the previous data
        print("Length of nearest maxima: ", len(nearest_maxima))
        for i in range(len(nearest_maxima)):
            if i == 0:
                continue

            # The 10.8 Stage is inverted so the discontinuity is the opposite
            if stage_size == 10.8:
                if nearest_maxima[i] < nearest_maxima[i-1] - (scan.stage.fsr*.25):
                    print("Discontinuity found")
                    for j in range(i):
                        nearest_maxima[j] -= scan.stage.fsr
            else:
                if nearest_maxima[i] < nearest_maxima[i-1] - (scan.stage.fsr*.25):
                    for j in range(i):
                        nearest_maxima[j] -= scan.stage.fsr +.01215
                        print("adjusting")
            
        middle_plot = [maxima - scan.stage.fsr for maxima in nearest_maxima]

        ax.plot(voltages, middle_plot, 'o', color= colors[c])
        ax.set(xlabel='2kHz LCVR Control Voltage Amplitude [Vpp]', ylabel='Tuning Range (nm)',
            title=f'Wavelength Vs Voltage Relationship for Tuning Regions\nfor the {scans[0].stage.stage_size}mm LFDI Wide-Fielded Stage at {round(scan.temperature*2)/2}C')
        ax.grid()
        # Draw Boxes around the voltage regions make each region a different color
        n=0
        # linestiles list
        linestyles = ["+", "--", "*", "-.", ":", "-"]
        for region in Voltage_Regions:
            
            # Get a uniq Color for the region
            color = np.random.rand(3,)
            ax.axvspan(region[0], region[1], alpha=0.5, color=color)
            # Find the Deta Voltage and Delta Wavelength for the region
            # Find the index of the start and end voltage
            start_index = (np.abs(np.array(voltages) - region[0])).argmin()
            end_index = (np.abs(np.array(voltages) - region[1])).argmin()
            # Get the voltages and nearest maximas for the region
            region_voltages = voltages[start_index:end_index]
            region_nearest_maxima = middle_plot[start_index:end_index]
            # Fit a line to the data
            z = np.polyfit(region_voltages, region_nearest_maxima, 1)
            print(f"Region {n}: y={z[0]}x+{z[1]}")
            p = np.poly1d(z)
            ax.plot(region_voltages,p(region_voltages),f"r{linestyles[n]}", linewidth = 3, label = f"Region {n}: y={z[0]:.5f}x+{z[1]:.2f}")
            corrected_Wavelengths.extend(region_nearest_maxima)
            n= n+1

            
        c=+1
        # Show the Plot

        plt.legend()
        plt.show()

        # Save the plot
        fig.savefig(l2_path + "\\" + filename)
        # retrun the maximas vs Voltage data
        return corrected_Wavelengths, voltages


# Create 2 figure plot 
# One figure is the crosssection
# The other figure is the nearest maxima vs voltage with the Current Voltage highlighted in orange
def TwoplotVoltageVsCurve(scan, voltage_wavelength_data, save_path, filename = "2PlotVoltageVsWavelength.png"):
    # Create a 2 figure plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    fig.suptitle(f'Voltage vs Wavelength for LFDI Single Wide-Fielded Stage ({scan.stage_size}) at {round(scan.temperature)}C')
    ax1.plot(scan.smoothed_cross_section/16, linewidth = 3, label = "Smoothed Data")
    
    # Set the Ticks for Axis 1
    ax1.set_xticks(np.linspace(0, len(scan.cross_section), 10), np.round(np.linspace(Scan.ConversionEquation(0, scan.image_xaxis), Scan.ConversionEquation(len(scan.cross_section), scan.image_xaxis), 10), 2))
    ax1.axvline(x=2128, color='r', linewidth = 3,linestyle='--', label = "H-Alpha")
    ax1.set(xlabel='Wavelength (nm)', ylabel='Intensity (adu)')
    # Plot a line through the nearest maxima
    ax1.axvline(x = scan.nearest_maxima, color = "red", linestyle = ":", linewidth = 3,label = "Nearest transmission peak to H-alpha")
    # Keep the legen in the top right
    ax1.legend(loc='upper right')
    ax1.grid()
    # Make Axis static
    ax1.set_ylim([0, 1000])
    ax2.plot(voltage_wavelength_data[0], voltage_wavelength_data[1], 'o', markersize = 10)
    
    # Plot the current voltage in orange
    # Find the Point in the voltage_wavelength_data that is closest to the current voltage
    # Find the index of the closest point
    index = (np.abs(np.array(voltage_wavelength_data[0]) - scan.voltage)).argmin()
    # Plot the point
    ax2.plot(voltage_wavelength_data[0][index], voltage_wavelength_data[1][index], 'o', color = "orange", markersize = 10)
    # Set the Axis voltage should be V with the subscript pp and the wavelength should be nm 
    ax2.set(xlabel="$Voltage (V_{pp})$", ylabel='Wavelength (nm)')
    ax2.grid()
    # Set y Limit
    ax2.set_ylim([656.1, 657.1])
    
    # Save the plot
    # Increase the Size of the plot to avoid overlapping text
    fig.set_size_inches(16, 12)
    fig.savefig(save_path + "\\" + filename)
    plt.close(fig)
    
    return