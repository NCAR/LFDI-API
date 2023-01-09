import matplotlib.pyplot as plt
import numpy as np
import time
from PIL import Image
import matplotlib
import ZWO
import datetime
import os

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
def Deuterium_Lamp_Calibration(camera = None, calibration_folder= None):
    print("Please ensure the Deuterium bulb is in the lamp.\r\nPress Enter when ready")
    input()
    
    print("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input()
    
    print("A window will open with the spectrometer output. Please adjust the lamp and slit until the emission line is captured.\r\nClose the Spectrometer window when ready\r\nPress Enter to continue")
    input()
    #Show the Spectrometer output
    show_spectrometer_output(camera)
    if camera == None:
        #open the Tiff image
        pixel_value = find_peak_position('Test1.tif')
    else:
        pixel_value = find_peak_position('Calibration_Image.tif')
        os.rename('Calibration_Image.tif', calibration_folder + '/Deuterium_Calibration_Image.tif')
        
    
    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {deuterium_wavelength} nm\r\nImage saved to {calibration_folder}/Deuterium_Calibration_Image.tif")
    return pixel_value


def Hydrogen_Lamp_Calibration(camera = None, calibration_folder= None):
    print("Please ensure the hydrogen bulb is in the lamp.\r\nPress Enter when ready")
    input()
    print("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input()
    print("A window will open with the spectrometer output. Please adjust the lamp ONLY until the emission line is captured.\r\nClose the Spectrometer window when ready\r\nPress Enter to continue")
    input()
    #Show the Spectrometer output
    show_spectrometer_output(camera)
    if camera == None:
        #open the Tiff image
        pixel_value = find_peak_position('Test1.tif')
    else:
        pixel_value = find_peak_position('Calibration_Image.tif')
        os.rename('Calibration_Image.tif', calibration_folder + '/Hydrogen_Calibration_Image.tif')
        
    
    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {hydrogen_wavelength} nm\r\nImage saved to {calibration_folder}/Hydrogen_Calibration_Image.tif")
    return pixel_value
    
    

#Will open up an image and find the pixel with the peak intensity
def find_peak_position(filename):
    #open the Tiff image
    image = Image.open(filename)
    #Convert the image to a numpy array
    image = np.array(image)
    #Get a 1d array from the values in the middle of the image
    crosssection = image[int(image.shape[0]/2), :]
    #Find the Position  of Peak of the emission line
    peak_position = np.argmax(crosssection)
    return peak_position


#A function to open a window with the spectrometer output from the ZWO Camera. The window should be updated every 2 seconds
def show_spectrometer_output(camera = None):
    plt.ion()
    fig = plt.figure()
    #Create 2 Subplots in the figure with 1 row and 2 columns and white space inbetween
    ax = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    ax.set_title('Spectrometer Output')

    ax.set_xlabel('Pixel X')
    ax.set_ylabel('Pixel Y')
    #Try to connect to the camera
    

    #While the user has the window open keep updating the image. The user should have the ability to increase or decrease the exposure time
    while True:
        if camera is not None:
            image_name = 'Calibration_Image.tif'
            camera.capture(image_name)
        else:
            image_name = 'Test1.tif'
        
        #open the Tif image
        image = Image.open(image_name)
        #Convert the image to a numpy array
        image = np.array(image)
        #Get a 1d array from the values in the middle of the image
        crosssection = image[int(image.shape[0]/2), :]
        #clear axis 1
        ax.clear()
        #clear axis 2
        ax2.clear()
        #plot the image
        ax.imshow(image)
        #plot the cross section on the image
        ax.axhline(int(image.shape[0]/2), color='r')

        #Update the plot
        ax2.plot(crosssection)
        #plot the peak intensity in the Cross section
        ax2.axvline(np.argmax(crosssection), color='r')
        #Make axis 1 and axis 2 share the same x axis
        #ax2.get_shared_x_axes().join(ax, ax2)
        ax2.set_title('Cross Section')
        ax.set_title('Spectrometer Output')
        ax2.set_xlabel('Pixel X')
        ax2.set_ylabel('Intensity')
        #makesure the canvas is cleared
        

        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(0.5)
        #Exit the loop if the user closes the plot
        if not plt.fignum_exists(fig.number):
            break
        
    return 




    



if __name__ == "__main__":
    
    
    #Make a calibration folder
    calibration_folder = make_calibration_folder()
    #the function to turn on interactive mode
    
    print("Please remove any components between the spectrometer and the Lamp except for the Columnating Lense.\r\nPress Enter when ready")
    #ask if user would like to use Auto Exposure
    response = input("Would you like to use auto exposure for calibration, Once Exposure is set for the Deuterium Lamp it will be used for the Hydrogen Lamp. Press Enter to continue [y/n]")
    if response.lower() == 'y':
        auto_exposure = True
    else:
        auto_exposure = False
    try: 
        camera = ZWO.ZWO_Camera()
        if auto_exposure:
            camera.set_auto_exposure(True)
        else:
            camera.set_exposure(0.1)
        camera.set_binning(1)
        camera.set_image_type('RAW16')
        camera.set_roi('max', 'max')    
    except:
        print("Error: Could not capture image from ZWO Camera. Please check that the camera is connected and the driver is installed")
        camera = None
    #Calibrate the spectrometer
    d_pixel_Position = Deuterium_Lamp_Calibration(camera, calibration_folder=calibration_folder)
    #Get the exposure of the camera
    if camera is not None:
        exposure = camera.get_camera_exposure()
        print(f"Exposure Used for Deuterium Lamp: {exposure} seconds")
        camera.set_auto_exposure(False)
        camera.set_exposure(exposure)
    h_pixel_Position = Hydrogen_Lamp_Calibration(camera, calibration_folder=calibration_folder)

    #Make a File With Calibration information
    #Open the file
    file = open('Calibration.txt', 'w')
    #Write the Calibration date
    file.write(f"Calibration Date: {datetime.datetime.now()}")
    #print the ZWO Camera Settings
    file.write(f"ZWO Camera Settings:")
    if camera is not None:
            #Need to implement a function to get the camera settings
            file.write(f"{camera}")
    #Write the Calibration information to the file
    file.write(f"Deuterium Wavelength: {deuterium_wavelength} nm")
    file.write(f"Deuterium Pixel Position: {d_pixel_Position}")
    file.write(f"Hydrogen Wavelength: {hydrogen_wavelength} nm")
    file.write(f"Hydrogen Pixel Position: {h_pixel_Position}")

    #Close the file
    file.close()
    #move the File to the Calibration Folder
    os.rename('Calibration.txt', calibration_folder + '/Calibration.txt')
