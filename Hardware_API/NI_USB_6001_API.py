import nidaqmx
import numpy as np
import time
import datetime

class NI_USB_6001:
    def __init__(self):
        #Connnect to the NI USB 6001
        self.com = 'Dev1/ai0'
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(self.com)
        #self.sampling_frequency = 1000
        #self.task.timing.cfg_samp_clk_timing(1000)
        return
    
    def set_sampling_frequency(self, frequency):
        #max is 1000Hz min is 1Hz
        if frequency <= 1000 and frequency >= 1:
            self.sampling_frequency = frequency
            self.task.timing.cfg_samp_clk_timing(frequency, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=8000)
        else:
            print("Sampling frequency must be between 1 and 1000Hz")


    def get_voltage(self):
        return self.task.read()
    
    def close(self):
        self.task.stop()
        self.task.close()
        return
    
    def get_voltage_array(self, duration):
        #duration must not collect more than 1000 points at current sampling frequency
        if duration*self.sampling_frequency > 1000:
            print(f"Duration must be less than {1000/self.sampling_frequency}")
            return
        self.task.start()
        data = self.task.read(duration*self.sampling_frequency)
        self.task.stop()
        return np.array(data)
    
    def get_voltage_array_continuous(self):
        self.task.start()
        return time.time()
       
    def stop_continuous(self, timer_handle):
        
        self.task.stop()
        #return the duration
        end = time.time()
        return end - timer_handle
        
    
    # read the Data collected by the get_voltage_array_continuous
    def read_continuous(self, duration):
        #Data collected only goes to 1000 points.
        #Round the number of samples to the nearest whole number
        samples = round(duration*self.sampling_frequency)
        data = self.task.read(samples)
        return np.array(data)
    
    # match an array of data with timestamps
    def match_timestamps(self, duration, begining_timestamp):
        # Data collected only goes to 1000 points.
        # Round the number of samples to the nearest whole number
        print(self.sampling_frequency)
        samples = round(duration*self.sampling_frequency)
        print(samples)
        timestamps = np.linspace(begining_timestamp, begining_timestamp + duration, samples)
        # only use the last 1000 points
        timestamps = timestamps[-1000:]
        #get the Date and Time from all the timestamps
        timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in timestamps]
        return timestamps


# run this to test the NI_USB_6001
if __name__ == '__main__':
    
    # print("Testing NI_USB_6001")
    # ni = NI_USB_6001()
    # ni.set_sampling_frequency(500)
    # data1 = ni.get_voltage_array(1)
    # print(data1)
    # print("Length of data1: ", len(data1))
    # ni.close()
    # print("Test Complete")
    # print("Testing Continuous")
    # ni = NI_USB_6001()
    # ni.set_sampling_frequency(500)
    # timer_handle = ni.get_voltage_array_continuous()
    # time.sleep(2)
    # duration = ni.stop_continuous(timer_handle)
    # print(f"Duration: {duration}")
    # #round
    # data2 = ni.read_continuous(duration)
    # print("Length of data2: ", len(data2))
    # ni.close()

    # match_timestamps = ni.match_timestamps(duration, timer_handle)
    # for t in match_timestamps:
    #     print(t)
    # #plot the data from data2
    # import matplotlib.pyplot as plt
    # plt.plot(match_timestamps, data2)

    # plt.show()
    # print("Test Complete")

    #make a live output of the data
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import time
    import datetime
    import numpy as np
    ni = NI_USB_6001()
    ni.set_sampling_frequency(500)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs = []
    ys = []

    def animate(i, xs, ys):
        # Read Voltage from NI_USB_6001
        data = ni.get_voltage()
        # Add x and y to lists
        xs.append(datetime.datetime.now().strftime('%H:%M:%S.%f'))
        ys.append(data)

        # Limit x and y lists to 20 items
        xs = xs[-20:]
        ys = ys[-20:]

        # Draw x and y lists
        ax.clear()
        ax.plot(xs, ys)

        # Format plot
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('Live Voltage over Time')
        plt.ylabel('Voltage (V)')
        plt.xlabel('Time')
        plt.tight_layout()

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
    plt.show()
    ni.close()
