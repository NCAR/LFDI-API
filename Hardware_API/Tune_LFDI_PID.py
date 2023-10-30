#This will use the LFDI PID controller to tune the PID controller for the LFDI

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import sys
import LFDI_API

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


# Create an instance of the LFDI Controller and set the PID values
if __name__ == "__main__":
    LFDI = LFDI_API.LFDI_TCB()
    LFDI.set_controller_kd(1)
    LFDI.set_controller_ki(0)
    LFDI.set_controller_kp(1)
    LFDI.set_controller_setpoint(30)
    LFDI.set_controller_enable(1, True)

    # Create a Graph
    fig, ax = create_graph()
    x = []
    y = []
    start_time = time.time()
    while True:
        try:
            temp = get_temp()
            x.append(time.time() - start_time)
            y.append(temp)
            update_graph(fig, ax, x, y)
            time.sleep(0.1)
        #only keep the last 1000 points
            if len(x) > 1000:
                x = x[1:]
                y = y[1:]
        except KeyboardInterrupt:
            break