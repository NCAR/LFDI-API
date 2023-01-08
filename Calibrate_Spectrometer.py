import matplotlib.pyplot as plt
import numpy as np
import time
from PIL import Image
import matplotlib
import ZWO
import datetime

#This script will help the user with Calibrating the Spectrometer so that output and Scaling is known for Collection


H_Alpha_Wavelength = 656.28
deuterium_wavelength = 589.3
Chloride_Wavelength = 546.07
#Deuterium Lamp Calibration
def Deuterium_Lamp_Calibration(camera = None):
    print("Please ensure the Deuterium bulb is in the lamp.\r\nPress Enter when ready")
    input()
    
    print("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input()
    
    print("A window will open with the spectrometer output. Please adjust the lamp and slit until the emission line is captured.\r\nClose the Spectrometer window when ready\r\nPress Enter to continue")
    input()
    #Show the Spectrometer output
    show_spectrometer_output(camera)
    
    pixel_value = find_peak_position('Test1.tif')
    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {deuterium_wavelength} nm\r\nImage saved to deuterium_calibration.tiff")
    return pixel_value


def Chloride_Lamp_Calibration(camera = None):
    print("Please ensure the Chloride bulb is in the lamp.\r\nPress Enter when ready")
    input()
    print("Turn On the lamp and attempt to align the the emission line with the spectrometer slit.\r\nPress Enter when ready")
    input()
    print("A window will open with the spectrometer output. Please adjust the lamp ONLY until the emission line is captured.\r\nClose the Spectrometer window when ready\r\nPress Enter to continue")
    #open a Windo with the spectrometer output from the ZWO Camera. The window should be updated every 2 seconds
    #Show window with the spectrometer output
    #save the last image from the ZWO Camera output
    #Show the Spectrometer output
    show_spectrometer_output(camera)
    #open the Tiff image
    pixel_value = find_peak_position('Test1.tif')
    print(f"The peak position is {pixel_value} pixels from the left of the image which represents a wavelength of {Chloride_Wavelength} nm\r\nImage saved to Chloride_calibration.tiff")
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
    ax, ax2 = fig.add_subplot(2,1,1), fig.add_subplot(2,1,2)
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
        ax2.get_shared_x_axes().join(ax, ax2)
        ax2.set_title('Cross Section')
        ax2.set_xlabel('Pixel X')
        ax2.set_ylabel('Intensity')
        #makesure the canvas is cleared
        

        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(2)
        #Exit the loop if the user closes the plot
        if not plt.fignum_exists(fig.number):
            break
    return




    



if __name__ == "__main__":
    #the function to turn on interactive mode
    print("Please remove any components between the spectrometer and the Lamp.\r\nPress Enter when ready")
    input()
    try: 
        camera = ZWO.Camera()
        camera.set_exposure(0.1)
        camera.set_exposure(0.1)
        camera.set_binning(1)
        camera.set_image_type('RAW16')
        camera.set_roi('max', 'max')    
    except:
        print("Error: Could not capture image from ZWO Camera. Please check that the camera is connected and the driver is installed")
        camera = None
    #Calibrate the spectrometer
    d_pixel_Position = Deuterium_Lamp_Calibration(camera)
    c_pixel_Position = Chloride_Lamp_Calibration(camera)

    #Make a File With Calibration information
    #Open the file
    file = open('Calibration.txt', 'w')
    #Write the Calibration date
    file.write(f"Calibration Date: {datetime.datetime.now()}\r\n")
    #print the ZWO Camera Settings
    file.write(f"ZWO Camera Settings:\r\n")
    #Write the Calibration information to the file
    file.write(f"Deuterium Wavelength: {deuterium_wavelength} nm\r\n")
    file.write(f"Deuterium Pixel Position: {d_pixel_Position}\r\n")
    file.write(f"Chloride Wavelength: {Chloride_Wavelength} nm\r\n")
    file.write(f"Chloride Pixel Position: {c_pixel_Position}\r\n")
    #Close the file