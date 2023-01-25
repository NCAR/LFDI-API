from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
#import a savgol filter to smooth the data
from scipy.signal import savgol_filter


def Open_Image(filename):
    image = Image.open(filename)
    image = np.array(image)
    return image


def Get_Image_Crosssection(filename, crosssection_position, crosssection_width):
    image = Open_Image(filename)
    if crosssection_position == 'middle':
        crosssection = np.mean(image[int(image.shape[0]/2)-int(crosssection_width/2):int(image.shape[0]/2)+int(crosssection_width/2), :], axis=0)
    else:
        crosssection = np.mean(image[int(crosssection_position)-int(crosssection_width/2):int(crosssection_position)+int(crosssection_width/2), :], axis=0)
    return crosssection

def Plot_Image(filename, axis, crosssection_position, crosssection_width):
    axis.set_ylabel('Pixel Y')
    image = Open_Image(filename)
    axis.imshow(image)
    if crosssection_position == 'middle':
        axis.axhline(int(image.shape[0]/2), color='r', linestyle='-')
    else:
        axis.axhline(int(crosssection_position), color='r', linestyle='-')
    return

def Plot_Image_Crosssection(filename, axis, crosssection_position, crosssection_width):
    axis.set_xlabel('Pixel X')
    axis.set_ylabel('Intensity')
    

    crosssection = Get_Image_Crosssection(filename, crosssection_position, crosssection_width)
    #Find the Peak Pixel Position
    peak_pixel = np.argmax(crosssection)
    #If multiple values in a row are at the peak pixel take the center one
    if len(np.where(crosssection == crosssection[peak_pixel])[0]) > 1:
        peak_pixel = np.where(crosssection == crosssection[peak_pixel])[0][int(len(np.where(crosssection == crosssection[peak_pixel])[0])/2)]
    #Plot the Peak Pixel Position
    axis.plot(crosssection, linestyle='-', label='Raw Data')
    #Apply a savgol filter to smooth the data
    smoothed = savgol_filter(crosssection, 51, 3)
    axis.plot(smoothed, linestyle='-', label='Smoothed Data')

    peak_pixel = np.argmax(smoothed)
    #If multiple values in a row are at the peak pixel take the center one
    if len(np.where(smoothed == smoothed[peak_pixel])[0]) > 1:
        peak_pixel = np.where(smoothed == smoothed[peak_pixel])[0][int(len(np.where(smoothed == smoothed[peak_pixel])[0])/2)]

    
    axis.axvline(peak_pixel, color='r', linestyle='-')
    #Print the Peak Pixel Position in the Top Corner of the Plot
    axis.text(0.95, 0.95, f'Peak Pixel: {peak_pixel}', horizontalalignment='right', verticalalignment='top', transform=axis.transAxes)
    return


if __name__ == '__main__':
    
   
    crosssection_position = 'middle'
    crosssection_width = 4
    folder = "C:\\Users\\mjeffers\\Desktop\\Calibration\\"
    Bromine_image = f'{folder}Bromine-656pt0.tif'
    H_Alpha_image = f'{folder}H-Alpha.tif'
    D_Alpha_image = f'{folder}D-Alpha.tif'
    fig, axes = plt.subplots(3, 2)
    #Create a Title on the First Row
    axes[0, 0].set_title('Bromine')
    Plot_Image(Bromine_image, axes[0, 0], crosssection_position, crosssection_width)
    Plot_Image_Crosssection(Bromine_image, axes[0, 1], crosssection_position, crosssection_width)
    axes[1, 0].set_title('H-Alpha')
    Plot_Image(H_Alpha_image, axes[1, 0], crosssection_position, crosssection_width)
    Plot_Image_Crosssection(H_Alpha_image, axes[1, 1], crosssection_position, crosssection_width)
    

    axes[2, 0].set_title('D-Alpha')
    Plot_Image(D_Alpha_image, axes[2, 0], crosssection_position, crosssection_width)
    Plot_Image_Crosssection(D_Alpha_image, axes[2, 1], crosssection_position, crosssection_width)
    #make it so that all images in Column 2 Share ann x axis
    axes[0, 1].get_shared_x_axes().join(axes[0, 1], axes[1, 1], axes[2, 1])
    plt.show()
    
    
    print('Done')