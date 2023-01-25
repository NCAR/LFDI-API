import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import Hardware_API.Spectrograph as Spectrograph

#This script will help the user with Calibrating the Spectrometer so that output and Scaling is known for Collection

class lamp:
    def __init__(self, name, wavelength):
        self.name = name
        self.wavelength = wavelength
        self.pixel_value = None
        return


H_Alpha_Wavelength = 656.28
deuterium_wavelength = 656.11
bromine_wavelength = 656.0

#Set up the calibration lamps
calibration_lamps = [lamp('Hydrogen', hydrogen_wavelength), lamp('Deuterium', deuterium_wavelength), lamp('Bromine', bromine_wavelength)]

#Make a Calibration folder
def make_calibration_folder():
    #Get the current date and time
    now = datetime.datetime.now()
    #Create a folder with the current date and time
    folder = 'Calibration_' + now.strftime("%Y-%m-%d_%H-%M-%S")
    #Create the folder
    os.mkdir(folder)
    return folder


def calibration_routine(spectrometer:Spectrograph.Spectrometer, folder, lamp:lamp):
    input(f"Please ensure the {lamp.name} bulb is in the lamp.\r\nPress Enter when ready")
    input("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input("A window will open with the spectrometer output. Please adjust the lamp and slit until the emission line is captured.\r\nClose the Spectrometer window when ready")
        #Show the Spectrometer output
    spectrometer.continuous_output()
    
    lamp.pixel_value = spectrometer.get_peak_position(spectrometer.get_image_crosssection(spectrometer.current_image))
    os.rename(spectrometer.current_image, f"{folder}/{lamp.name}_Calibration_Image.tif")
    os.rename(spectrometer.current_graph, f"{folder}/{lamp.name}_Calibration_Graph.png")
    os.rename(spectrometer.current_crosssection, f"{folder}/{lamp.name}_Calibration_CrossSection.csv")
    


#Plot the 2 calibration cross sections together
def plot_calibration_cross_sections(calibration_folder = None):
    #open the 2 CSVs of the Calibration Cross sections
    hydrogen_cross_section = np.genfromtxt(calibration_folder + '/Hydrogen_Calibration_CrossSection.csv', delimiter=',')
    deuterium_cross_section = np.genfromtxt(calibration_folder + '/Deuterium_Calibration_CrossSection.csv', delimiter=',')
    #Plot the 2 Cross sections
    plt.plot(hydrogen_cross_section, label='Hydrogen')
    plt.plot(deuterium_cross_section, label='Deuterium')
    #Open the Calibration.txt file and get the nm/px conversion for the X axis
    with open(calibration_folder + '/Calibration.txt', 'r') as f:
        #Find the line that begins with Pixel Scaling
        for line in f:
            if line.startswith('Pixel Scaling'):
                #Get the nm/px conversion
                nm_per_px = float(line.split(' ')[2])
                break
    #Set the X axis to be the wavelength in nm
    plt.xticks(np.arange(0, len(hydrogen_cross_section), 100), np.arange(0, len(hydrogen_cross_section)*nm_per_px, 100*nm_per_px))
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity')
    plt.title('Calibration of Hydrogen and Deuterium Emission Lines')
    plt.legend()
    plt.show()
    #Save the plot to the Calibration Folder
    plt.savefig(calibration_folder + '/Calibration_Graph.png')
    return




if __name__ == "__main__":
    #Set up the calibration lamps
    calibration_lamps = [lamp('Hydrogen', hydrogen_wavelength), lamp('Deuterium', deuterium_wavelength), lamp('Bromine', bromine_wavelength)]
    #Make a calibration folder
    calibration_folder = make_calibration_folder()
    #the function to turn on interactive mode
    print("Initalizing Spectrometer")
    spectrometer = Spectrograph.Spectrometer()
    input("Please remove any components between the spectrometer and the Lamp except for the Columnating Lense.\r\nPress Enter when ready")
    #ask if user would like to use Auto Exposure
    response = input("Would you like to use auto exposure for calibration. Press Enter to continue [y/n]")
    if response.lower() == 'y':
        auto_exposure = True
        spectrometer.camera.set_auto_exposure(True)
    elif response.lower() == 'n':
        auto_exposure = False
        spectrometer.camera.set_auto_exposure(False)
        input("Please set the exposure time in Seconds and press Enter")
        spectrometer.camera.set_exposure(float(input()))

    #Calibrate the spectrometer
    for lamps in calibration_lamps:
        calibration_routine(spectrometer, folder=calibration_folder, lamp=lamps)
    
    file = open('Calibration.txt', 'w')
    #Write the Calibration date
    file.write(f"Calibration Date: {datetime.datetime.now()}\r\n")
    #print the ZWO Camera Settings
    file.write(f"ZWO Camera Settings:\r\n")
    #Need to implement a function to get the camera settings
    file.write(f"{spectrometer.camera}\r\n")
    #write the cross section position of the spectrometer
    file.write(f"Spectrometer Cross Section Position: {spectrometer.crosssection_position}\r\n")
    #write the cross section width
    file.write(f"Spectrometer Cross Section Width averaged over: {spectrometer.crosssection_width}\r\n")
    #Write the Calibration information to the file
    for lamps in calibration_lamps:
        file.write(f"{lamps.name} Wavelength: {lamps.wavelength} nm\r\n")
        file.write(f"{lamps.name} Pixel Position: {lamps.pixel_value}\r\n")
            
    file.write(f"Pixel Scaling: {(calibration_lamps[2].wavelength - calibration_lamps[0].wavelength)/(calibration_lamps[2].pixel_value - calibration_lamps[0].pixel_value)} nm/px\r\n")
    #Close the file
    file.close()
    #move the File to the Calibration Folder
    os.rename('Calibration.txt', calibration_folder + '/Calibration.txt')
    #Plot the Calibration Cross Sections
    plot_calibration_cross_sections(calibration_folder=calibration_folder)
