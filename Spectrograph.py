#
# Description: This is a class that will control the Spectrograph as well as the Camera attached to it
# Author: Mitchell Jeffers
# Date: 1/20/2022 





import ZWO
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import time
from functools import partial




#This Class is to Control the Peripherials attached to the Spectrometer
class Spectrometer:
    def __init__(self):
        self.camera = ZWO.ZWO_Camera()
        self.camera.set_exposure(0.1)
        self.camera.set_binning(1)
        self.camera.set_image_type('RAW16')
        self.camera.set_roi('max', 'max')
        self.crosssection_position = 'middle'
        self.crosssection_width = 20
        self.current_image = '_temp_image.tif'
        self.current_graph = '_temp_graph.png'
        self.current_crosssection = '_temp_crosssection.csv'

        return
    
    #Takes an Image with the ZWO camera and saves it to the filename
    def take_image(self, filename):
        self.camera.capture(filename)
        return
    
    def plot_image(self, filename, axis, include_crosssection=True):
        axis.set_title('Spectrometer Output')
        axis.set_xlabel('Pixel X')
        axis.set_ylabel('Pixel Y')
        image = Image.open(filename)
        image = np.array(image)
        axis.imshow(image)
        if include_crosssection:
            if self.crosssection_position == 'middle':
                axis.axhline(int(image.shape[0]/2), color='r', linestyle='-')
            else:
                axis.axhline(int(self.crosssection_position), color='r', linestyle='-')
        return
    

    #This will get a 1D array of the intensity profile of the image across the horizontal access
    def get_image_crosssection(self, filename):
        image = Image.open(filename)
        image = np.array(image)
        if self.crosssection_position == 'middle':
            crosssection = np.mean(image[int(image.shape[0]/2)-int(self.crosssection_width/2):int(image.shape[0]/2)+int(self.crosssection_width/2), :], axis=0)
        else:
            crosssection = np.mean(image[int(self.crosssection_position)-int(self.crosssection_width/2):int(self.crosssection_position)+int(self.crosssection_width/2), :], axis=0)
        return crosssection

        
    #This will plot the cross section of the image
    def plot_crosssection(self, crosssection, axis, include_peak_marker=True):
        axis.plot(crosssection)
        if include_peak_marker:
            axis.axvline(self.get_peak_position(crosssection), color='r')
        axis.set_title('Cross Section')
        axis.set_xlabel('Pixel X')
        axis.set_ylabel('Intensity')
        return

    #This will get the position of the peak in the cross section
    def get_peak_position(self, crosssection):
        peak_position = np.argmax(crosssection)
        return peak_position

    #Run Continuous Output of the Plot all images will be saved to the Temp Files names the refresh rate is in seconds and the end trigger is a function that returns a boolean 
    def continuous_output(self, refresh_rate=1, end_trigger=None):
        print('Starting Continuous Output')
        print('Close the plot to Continue')
        if end_trigger is not None:
            print(f'Or End will be Trigger When {end_trigger.__name__} Returns True')
        plt.ion()
        fig = plt.figure()
        #Create 2 Subplots in the figure with 1 row and 2 columns and white space inbetween
        ax = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)

        #While the user has the window open keep updating the image. The user should have the ability to increase or decrease the exposure time
        while True:
            if self.camera is not None:
                image_name = self.current_image
                self.take_image(self.current_image)
            else:
                image_name = 'Test1.tif'
            #clear axis 1
            ax.clear()
            #clear axis 2
            ax2.clear()
           
            #Update the plot
            self.plot_image(image_name, ax)
            crosssection = self.get_image_crosssection(image_name)
            self.plot_crosssection(crosssection, ax2)
            
            #Update the Canvas
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(refresh_rate)

            #Save the Plot
            fig.savefig(self.current_graph)
            #Save the one dimensional cross section
            np.savetxt(self.current_crosssection, crosssection, delimiter=',')
            #Exit the loop if the user closes the plot or if lthe end trigger is met
            if end_trigger is not None:
                if end_trigger():
                    print("End Triggered")
                    plt.close()
                    break
            if not plt.fignum_exists(fig.number):
                print("Figure Closed")
                break
        return


    #Get a Single Output and save the image, graph, and cross section
    def single_output(self, image_name_prefix = 'Test'):
        image_fn = image_name_prefix + '.tif'
        graph_fn = image_name_prefix + '.png'
        crosssection_fn = image_name_prefix + '.csv'
        self.take_image(image_fn)

        fig = plt.figure()
        ax = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        self.plot_image(image_fn, ax)
        crosssection = self.get_image_crosssection(image_fn)
        self.plot_crosssection(crosssection, ax2)
        fig.savefig(graph_fn)
        np.savetxt(crosssection_fn, crosssection, delimiter=',')
        plt.show()
        return

    #Enable auto exposure for the ZWO Camera
    def enable_auto_exposure(self, enable):
        self.camera.auto_exposure = enable
        return

#A function that will return true 25 seconds after the entered time Just to test Functionality
def end_trigger(start):
    if  time.time()> start + 25:
        return True
    else:
        return False

if __name__ == '__main__':
    spec = Spectrometer()
    print("Output With out auto Exposure")
    spec.single_output('Test1')
    spec.continuous_output()
    print("Output With auto Exposure")
    spec.enable_auto_exposure(True)
    spec.single_output('Test1')
    start = time.time()
    spec.continuous_output(end_trigger=partial(end_trigger, start))