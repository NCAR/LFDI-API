import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import Spectrograph

#This script will help the user with Calibrating the Spectrometer so that output and Scaling is known for Collection


H_Alpha_Wavelength = 656.28
deuterium_wavelength = 656.11
hydrogen_wavelength = 656.27

#Make a Calibration folder
def make_calibration_folder():
    #Get the current date and time
    now = datetime.datetime.now()
    #Create a folder with the current date and time
    folder = 'Calibration_' + now.strftime("%Y-%m-%d_%H-%M-%S")
    #Create the folder
    os.mkdir(folder)
    return folder

#Deuterium Lamp Calibration
def Deuterium_Lamp_Calibration(spectrometer = None, calibration_folder= None):
    input("Please ensure the Deuterium bulb is in the lamp.\r\nPress Enter when ready")
    input("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input("A window will open with the spectrometer output. Please adjust the lamp and slit until the emission line is captured.\r\nClose the Spectrometer window when ready")
    
    #Show the Spectrometer output
    spectrometer.continuous_output()
    
    pixel_value = spectrometer.get_peak_position(spectrometer.get_image_crosssection(spectrometer.current_image))
    os.rename(spectrometer.current_image, calibration_folder + '/Deuterium_Calibration_Image.tif')
    os.rename(spectrometer.current_graph, calibration_folder + '/Deuterium_Calibration_Graph.png')
    os.rename(spectrometer.current_crosssection, calibration_folder + '/Deuterium_Calibration_CrossSection.csv')

    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {deuterium_wavelength} nm\r\nImage saved to {calibration_folder}/Deuterium_Calibration_Image.tif")
    return pixel_value


def Hydrogen_Lamp_Calibration(spectrometer = None, calibration_folder= None):
    input("Please ensure the hydrogen bulb is in the lamp.\r\nPress Enter when ready")
    input("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input("A window will open with the spectrometer output. Please adjust the lamp and the columnating lense ONLY until the emission line is captured.\r\nClose the Spectrometer window when ready")
    
    #Show the Spectrometer output
    spectrometer.continuous_output()
    
    pixel_value = spectrometer.get_peak_position(spectrometer.get_image_crosssection(spectrometer.current_image))
    os.rename(spectrometer.current_image, calibration_folder + '/Hydrogen_Calibration_Image.tif')
    os.rename(spectrometer.current_graph, calibration_folder + '/Hydrogen_Calibration_Graph.png')
    os.rename(spectrometer.current_crosssection, calibration_folder + '/Hydrogen_Calibration_CrossSection.csv')

    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {hydrogen_wavelength} nm\r\nImage saved to {calibration_folder}/Hydrogen_Calibration_Image.tif")
    return pixel_value
    
    

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
    h_pixel_Position = Hydrogen_Lamp_Calibration(spectrometer, calibration_folder=calibration_folder)
    #Get the exposure of the camera

    d_pixel_Position = Deuterium_Lamp_Calibration(spectrometer, calibration_folder=calibration_folder)

    #Make a File With Calibration information
    #Open the file
    file = open('Calibration.txt', 'w')
    #Write the Calibration date
    file.write(f"Calibration Date: {datetime.datetime.now()}")
    #print the ZWO Camera Settings
    file.write(f"ZWO Camera Settings:")
    #Need to implement a function to get the camera settings
    file.write(f"{spectrometer.camera}")
    #Write the Calibration information to the file
    file.write(f"Deuterium Wavelength: {deuterium_wavelength} nm\n")
    file.write(f"Deuterium Pixel Position: {d_pixel_Position}\n")
    file.write(f"Hydrogen Wavelength: {hydrogen_wavelength} nm\n")
    file.write(f"Hydrogen Pixel Position: {h_pixel_Position}\n")
    file.write(f"Pixel Scaling: {(hydrogen_wavelength-deuterium_wavelength)/(h_pixel_Position-d_pixel_Position)} nm/px")
    #Close the file
    file.close()
    #move the File to the Calibration Folder
    os.rename('Calibration.txt', calibration_folder + '/Calibration.txt')
    #Plot the Calibration Cross Sections
    plot_calibration_cross_sections(calibration_folder=calibration_folder)
