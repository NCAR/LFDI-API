import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import sys

def load_data(file):
    df = pd.read_csv(file, sep='\t', header=0)
    #Format the Time column to be used as an index the current format is HH:MM:SS
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S')
    #Use the First time point as 0 then convert to seconds
    df['Time'] = (df['Time'] - df['Time'][0]).dt.total_seconds() / 60
    
    #Format the Temperature column to remove the 'C' and then to be used as a float
    df['average'] = df['average'].str.replace('C', '')
    df['average'] = df['average'].astype(float)
    #Format the target data to remove the 'C' and then to be used as a float
    df['target'] = df['target'].str.replace('C', '')
    df['target'] = df['target'].astype(float) 
    return df

p = load_data('kp1-kd0-ki0.tsv')
pi = load_data('kp1-kd0-ki1.tsv')
pid = load_data('kp1-kd1-ki1.tsv')

#Find the Shortest dataset and truncate the others to match
min_len = min(len(p), len(pi), len(pid))
p = p[:min_len]
pi = pi[:min_len]
pid = pid[:min_len]

#make a figure for each of the datasets
fig, ax = plt.subplots(3, 1, sharex=True)
#for each figure plot the Temperature and the taget data
ax[0].plot(p['Time'], p['average'], 'b-', linewidth=2)
ax[0].plot(p['Time'], p['target'], 'g-', linewidth=2)
ax[1].plot(pi['Time'], pi['average'], 'b-', linewidth=2)
ax[1].plot(pi['Time'], pi['target'], 'g-', linewidth=2)
ax[2].plot(pid['Time'], pid['average'], 'b-', linewidth=2)
ax[2].plot(pid['Time'], pid['target'], 'g-', linewidth=2)
#Use the Same Plot But with different axis to plot the effort
ax0t = ax[0].twinx()
ax1t = ax[1].twinx()
ax2t = ax[2].twinx()
ax0t.plot(p['Time'], p['effort'], 'r-', linewidth=2)
ax1t.plot(pi['Time'], pi['effort'], 'r-', linewidth=2)
ax2t.plot(pid['Time'], pid['effort'], 'r-', linewidth=2)

#Set the title for each figure
ax[0].set_title('kP=1 kD=0 kI=0')
ax[1].set_title('kP=1 kD=0 kI=1')
ax[2].set_title('kP=1 kD=1 kI=1')
#Set the Y axis label for each figure
ax[0].set_ylabel('Temperature (C)')
ax[1].set_ylabel('Temperature (C)')
ax[2].set_ylabel('Temperature (C)')
#Set the Y axis label for the effort
ax0t.set_ylabel('Heater Duty Cycle (%)')
ax1t.set_ylabel('Heater Duty Cycle (%)')
ax2t.set_ylabel('Heater Duty Cycle (%)')
#Set the X axis label for the last figure
ax[2].set_xlabel('Time (Minutes)')
#Set the Y axis ticks for the Temperature
ax[0].set_yticks(np.arange(25, 31, 1))
ax[1].set_yticks(np.arange(25, 31, 1))
ax[2].set_yticks(np.arange(25, 31, 1))
#Set the Y axis ticks for the effort
ax0t.set_yticks(np.arange(0, 101, 20))
ax1t.set_yticks(np.arange(0, 101, 20))
ax2t.set_yticks(np.arange(0, 101, 20))
#Create a legend for each
ax[0].legend(['Current Temp', 'Target Temp'], loc='upper left')
ax[1].legend(['Current Temp', 'Target Temp'], loc='upper left')
ax[2].legend(['Current Temp', 'Target Temp'], loc='upper left')
ax0t.legend(['Heater Duty Cycle'], loc='upper right')
ax1t.legend(['Heater Duty Cycle'], loc='upper right')
ax2t.legend(['Heater Duty Cycle'], loc='upper right')
#Increase the line thickness for each axis
# ax[0].tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
# ax[1].tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
# ax[2].tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
# ax0t.tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
# ax1t.tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
# ax2t.tick_params(axis='both', which='major', labelsize=8, width=2, length=4)
#Use a tight layout
fig.tight_layout()
#Title The Figure
fig.suptitle('PID Controller Tuning - Temperature Vs Time and Duty Cycle Vs Time')
#show the plot
plt.show()


