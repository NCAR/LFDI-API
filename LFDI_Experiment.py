from ZWO import ZWO_Camera
import numpy as np
import matplotlib.pyplot as plt
import LFDI_API as LFDI
from PIL import Image
import time


#Set the camera to use
camera = ZWO_Camera()
camera.set_exposure(0.1)
camera.set_binning(1)
camera.set_image_type('RAW16')
camera.set_roi('max', 'max')
camera.capture('test1.tiff')

#Open the tiff image and find a horizontal cross section intensity profile
def plot_image(filename, filename_1d=None):
    image = Image.open(filename)
    image = np.array(image)
    #Get a 1d array from the values in the middle of the image
    crosssection = image[int(image.shape[0]/2), :]
    if filename_1d != None:
        #save the numpy array as a tsv file
        np.savetxt(filename_1d, crosssection, delimiter='\t')
    #Make a plat with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2)
    #Plot the intensity profile on the left subplot
    ax1.plot(crosssection)

    #Show the image with a line where the cross section is
    ax2.imshow(image)
    ax2.axhline(y=int(image.shape[0]/2), color='y', linestyle='-')
    return plt


#Cycle through Temperatures and take an image at each temperature
def temperature_cycle(camera,LFDI_TCB, start_temp, end_temp, step, exposure, filename):
    #Create a list of temperatures to cycle through
    temperatures = np.arange(start_temp, end_temp, step)
    #Create a list to store the filenames of the images
    filenames = []
    #Cycle through the temperatures
    for temperature in temperatures:
        #Set the temperature
        LFDI_TCB.set_temperature(temperature)
        LFDI_TCB.set_enable(True)
        
        #Wait for the temperature to stabilize
        time.sleep(10)
        #Take the image
        filename = filename + '_' + str(temperature) + '.tiff'
        camera.capture(filename)
        plot = plot_image(filename)
        plot.show()
        
    return filenames
