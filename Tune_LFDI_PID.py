#This will use the LFDI PID controller to tune the PID controller for the LFDI

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import sys
import Hardware_API.LFDI_API as LFDI_API
import Hardware_API.Spectrograph as Spectrograph

# Create a Graph and Continually Update it
def create_graph():
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Temp (C)')
    ax.set_title('Temp vs. Time')
    fig.show()
    fig.canvas.draw()
    return fig, ax

# Update the Graph
def update_graph(fig, ax, x, y):
    ax.plot(x, y, color='b')
    fig.canvas.draw()
    fig.canvas.flush_events()


def get_temp():
    LFDI.get_info()
    return LFDI.Controllers[0].temp

from DataCollection.LFDI_Experiment import make_experiment_folder
# Create an instance of the LFDI Controller and set the PID values
if __name__ == "__main__":
    #Set up the Spectrometer
    Spectrograph = Spectrograph.Spectrometer()
    Spectrograph.camera.set_exposure(.05)
    Spectrograph.camera.set_binning(4)
    Spectrograph.camera.set_gain(300)
    LFDI = LFDI_API.LFDI_TCB("COM6", 9600)
    LFDI.set_controller_kd(1, .75)
    LFDI.set_controller_ki(1, 0)
    LFDI.set_controller_kp(1, 5)
    LFDI.set_controller_setpoint(1, 25)
    LFDI.set_compensator_voltage(3, 0)
    LFDI.set_compensator_enable(3, True)
    LFDI.set_controller_enable(1, True)
    Temps = [25, 30, 25]
    # Create a Graph
    fig, ax = create_graph()
    x = []
    y = []
    start_time = time.time()
    folder = make_experiment_folder()
    # Go through all temps
    for temp in Temps:
        LFDI.set_compensator_voltage(4, 5.0)
        LFDI.set_controller_setpoint(1, temp)
        #image takes about 4 sec
        for i in range(0,900):# Go for about 1 hr
            try:
                temp = get_temp()
                x.append(time.time() - start_time)
                y.append(temp)
                update_graph(fig, ax, x, y)
                current_temp = f"{float(temp):.2f}"
                Spectrograph.single_output()
                filename = f"{folder}/Slew_{str(time.time())}_{LFDI.Compensators[5].voltage}V_{current_temp}C_CompOff_0nm.png"
                os.rename(Spectrograph.current_image, f"{filename}")
                time.sleep(4)
            #only keep the last 1000 points
                if len(x) > 1000:
                    x = x[1:]
                    y = y[1:]
            except KeyboardInterrupt:
                break