#Connect to the LFDI TCB through a serial port
import serial
from time import sleep
from time import time
from time import strftime
import time



class LFDI_TCB(object):


    def __init__(self, com_port, baud_rate):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.com_port, self.baud_rate)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.timeout = 1
        self.ser.write_timeout = 1
        self.send_command("c1")
        
    def __del__(self):
        print(self.set_enable(False))
        self.ser.close()
        print("LFDI_TCB closed")

    def send_command(self, command):
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.write(f"{command}\r".encode('utf-8'))
        sleep(.5)
        return self.ser.read_all().decode('utf-8')

    def get_temperature(self):
        return self.send_command("raw")
    
    def set_temperature(self, temperature):
        return self.send_command("t" + str(temperature))

    def get_help(self):
        return self.send_command("help")

    def set_enable(self, enable):
        if enable:
            return self.send_command("e")
        else:
            return self.send_command("d")
    def set_kp(self, kp):
        return self.send_command("p" + str(kp))
    def set_ki(self, ki):
        return self.send_command("i" + str(ki))
    def set_kd(self, kd):
        return self.send_command("d" + str(kd))
    def set_setI2C_Add(self, add):
        return self.send_command("a" + str(add))
    def set_frequency(self, frequency):
        return self.send_command("f" + str(frequency))
    def read_raw_data(self):
        return self.send_command("r")
    #Parse the Raw Data. Data Comes in as a string that is tab seperated into 16 columns the Header is the first row
    def parse_raw_data(self, raw_data):
        raw_data = self.read_raw_data()
        #remove the first row which is the header
        raw_data = raw_data.split("\n")
        raw_data = raw_data[1].split("\t")
        return(raw_data)

if __name__ == "__main__":

    #Prompt the user to set a temperature
    temp = input("Enter a set point temperature: ")
    #Prompt the user to select an output file
    file_name = input("Enter a file name to output data to: ")
    #Prompt the user to select a sample rate
    sample_rate = int(input("How many Seconds between Samples: "))
    #Ask the user if they want to use a configuration file for the PID
    use_config = input("Set the values for PID? (y/n) (if \"n\" the Default values of the kp =1  kd = 0 and ki = 0 will be used): ")
    if use_config == "y":
        kp = input("Enter a value for kp: ")
        ki = input("Enter a value for ki: ")
        kd = input("Enter a value for kd: ")
    if use_config == "n":
        kp = 1
        ki = 0
        kd = 0
    try: 
        lfdi = LFDI_TCB("COM4", 9600)
    except:
        print("Could not connect to LFDI_TCB")
        exit()
    #Set the temperature
    print(lfdi.set_temperature(temp))
    #Set the PID values
    print(lfdi.set_kp(kp))
    print(lfdi.set_ki(ki))
    print(lfdi.set_kd(kd))
    

    #Open the file
    file = open(file_name, "w")
    #Write the header
    header = "Date\tTime\tChan\tkp\tkd\tki\tep\ted\tei\teffort\ttemp\taverage\ttarget\ti2c\thist\tfreq\tenabled\tsensor\r"
    file.write(header)
    file.close()
    print("Starting Data Collection")
    print("Press Ctrl+C to stop")
    print(lfdi.set_enable(True))
    #Start the data collection
    while True:
        #Open the file
        file = open(file_name, "a")
        #Parse the raw data
        raw_data = lfdi.read_raw_data()
        print(raw_data)
        raw_data = lfdi.parse_raw_data(raw_data)
        
        #Convert list to a tsv string
        raw_data = "\t".join(raw_data)
        #Get Current Time formatted to be Month/day/Year\tHour:Minute:Sec
        raw_data = time.strftime("%m/%d/%Y\t%H:%M:%S\t") + raw_data

        
        #Write the tsv data to the file
        file.write(f"{raw_data}\r")
        #Close the file
        file.close()
        #Sleep for the sample rate
        sleep(sample_rate)

    #print("Done")