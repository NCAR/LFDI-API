#Connect to the LFDI TCB through a serial port
import serial
from time import sleep
from time import time
from time import strftime
import time
from datetime import datetime


class Controller(object):

    def __init__(self, number):
        self.number = number
        self.kp = 0
        self.ki = 0
        self.kd = 0
        self.error_p = 0
        self.error_d = 0
        self.error_i = 0
        self.effort = 0
        self.temp = 0
        self.average = 0
        self.enabled = False
        self.setpoint = 0
        self.i2c = 0
        self.history = 0
        self.frequency = 0
        self.sensor = 0
        self.header = "Cont\tkp\tkd\tki\tep\ted\tei\teffort\ttemp\taverage\ttarget\ti2c\thist\tfreq\tenabled\tsensor"
        
        return


    def __del__(self):
        return

    def update_data(self, data):
        try:
            self.kp = float(data[1].strip(' '))
            self.kd = float(data[2].strip(' '))
            self.ki = float(data[3].strip(' '))
            self.error_p = float(data[4].strip(' '))
            self.error_d = float(data[5].strip(' '))
            self.error_i = float(data[6].strip(' '))
            self.effort = float(data[7].strip(' '))
            self.temp = float(data[8].strip(' ').strip('C'))
            self.average = float(data[9].strip(' ').strip('C'))
            #bad Way of doing this but will work for now
            try:
                self.setpoint = float(data[10].strip(' ').strip('C'))
            except:
                self.setpoint = data[10]
            self.i2c = data[11].strip(' ')
            self.history = float(data[12].strip(' '))
            self.frequency = float(data[13].strip(' '))
            self.enabled = data[14].strip(' ')
            self.sensor = data[15].strip(' ')
        except:
            print("Could not parse Controller Data")
        return

    def get_kp_command(self, kp:float):
        return f"p{kp}"
    def get_ki_command(self, ki:float):
        return f"i{ki}"
    def get_kd_command(self, kd:float):
        return f"d{kd}"
    def get_setpoint_command(self, setpoint:float):
        return f"t{setpoint}"
    def get_enable_command(self, enable:bool):
        if enable:
            return "e"
        else:
            return "d"
    def get_i2c_command(self, i2c:int):
        return f"a{i2c}"
    def get_hist_command(self, history:int):
        return f"h{history}"
    def get_frequency_command(self, frequency:int):
        return f"f{frequency}"

    def get_raw_data_command(self):
        return "r"

    #get info Tab separated in the format of the header
    def get_info(self):
        info = f"Cont{self.number}\t{self.kp}\t{self.kd}\t{self.ki}\t{self.error_p}\t{self.error_d}\t{self.error_i}\t{self.effort}\t{self.temp}\t{self.average}\t{self.setpoint}\t{self.i2c}\t{self.history}\t{self.frequency}\t{self.enabled}\t{self.sensor}"
        return info
        

class Compensator(object):


    def __init__(self, number):
        self.number = number
        self.header = "Comp\tPeak2Peak\tWave\tTemp\tAvg\tAuto\tUseAverage\ti2c\tenabled\tsensor"
        self.voltage = 0
        self.wave = 0
        self.temp = 0
        self.avg = 0
        self.auto = False
        self.useAverage = False
        self.i2c = 0
        self.enabled = False
        self.sensor = 0
        return

    def __del__(self):

        return

    def update_data(self, data):
        self.voltage = data[1]
        self.wave = data[2]
        self.temp = float(data[3].strip(' ').strip("C"))
        self.avg = float(data[4].strip(" ").strip('C'))
        self.auto = data[5]
        self.useAverage = data[6]
        self.i2c = data[7]
        self.enabled = data[8]
        self.sensor = data[9]
        return

    def get_voltage_command(self, voltage):
        return f"v{voltage}"

    def get_enable_command(self, enable):
        if enable:
            return "e"
        else:
            return "d"
        
    def get_auto_command(self):
        return "comp"
        
    def get_useAverage_command(self, useAverage):
        #not implemented
        return 
    
    def get_i2c_command(self, i2c):
        return f"a{i2c}"

    def get_raw_data_command(self):
        return "r"
    
    def get_wavelength_command(self, wavelength):
        return f"w{wavelength}"
    
    #Get the info in tab separated format
    def get_info(self):
        info = f"Comp{self.number}\t{self.voltage}\t{self.wave}\t{self.temp}\t{self.avg}\t{self.auto}\t{self.useAverage}\t{self.i2c}\t{self.enabled}\t{self.sensor}"
        return info

class LFDI_TCB(object):


    def __init__(self, com_port, baud_rate):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.OpenConnection()
        self.ser.timeout = 1
        self.ser.write_timeout = 1
        
        self.Controllers = [Controller(1)]
        self.Compensators = [Compensator(1), Compensator(2), Compensator(3), Compensator(4), Compensator(5), Compensator(6)]
        self.current_context = "main"
        self.valid_contexts = ["main", "controller", "compensator"]
        
        self.header_format = f"Date\tTime\t"
        #add controller headers
        for controller in self.Controllers:
            self.header_format += f"{controller.header}\t"
        #add compensator headers
        for compensator in self.Compensators:
            self.header_format += f"{compensator.header}\t"

    def OpenConnection(self):
        self.ser = serial.Serial(self.com_port, self.baud_rate, timeout = 2)
        self.ser.flushInput()
        self.ser.flushOutput()
        return
    def __del__(self):
        #Disable all controllers
        for controller in self.Controllers:
            self.set_controller_enable(controller.number, False)
        #Disable all compensators
        for compensator in self.Compensators:
            self.set_compensator_enable(compensator.number, False)
        self.ser.close()
        print("LFDI_TCB closed")


    #Switches the Context Menu of the TCB
    def change_context(self, context:str):
        context = context.lower()
        if context not in self.valid_contexts:
            print(f"Context {context} is not valid")
            return
        if self.current_context != "main":
            #Go back to main
            self.send_command("m")

        #if we are going to main we are there
        if context == "main":
            self.current_context = context
            return
        
        #Go to the context
        self.send_command(context)
        self.current_context = context
        return

    #Sends Command to the Controller
    def send_command(self, command, print_command = True):
        self.ser.flushInput()
        self.ser.flushOutput()
        if print_command:
            print(f"{command}")
        self.ser.write(f"{command}\r".encode('utf-8'))
        sleep(.25)
        try:
            return self.ser.read_all().decode('utf-8', errors = 'ignore')
        except:
            print(f"Lost Connection With port")
            self.ser.close()
            self.OpenConnection()

    #Set the Compensator Voltage
    def set_compensator_voltage(self, compensator_number:int, voltage:float):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_voltage_command(voltage)))
        self.change_context("main")
        return

    #Set the Compensator compensate
    def toggle_compensator_auto(self, compensator_number):
        self.change_context("compensator")
        print(self.send_command(f"c{compensator_number}"))
        print(self.send_command(self.Compensators[compensator_number-1].get_auto_command()))
        self.change_context("main")
        return

    def set_compensator_useAverage(self, compensator_number, useAverage):
        print("Not Implemented")
        return

    #Set the Compensator i2c address
    def set_compensator_i2c(self, compensator_number, i2c):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_i2c_command(i2c)))
        self.change_context("main")
        return
    
    #Set the Compensator enable
    def set_compensator_enable(self, compensator_number, enable):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_enable_command(enable)))
        self.change_context("main")
        return
    
    #Set the Controller enable
    def set_controller_enable(self, controller_number, enable):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_enable_command(enable)))
        self.change_context("main")
        return
    
    #Set the Controller i2c address
    def set_controller_i2c(self, controller_number, i2c):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_i2c_command(i2c)))
        self.change_context("main")
        return
    
    #Set the Controller Kp
    def set_controller_kp(self, controller_number, kp):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_kp_command(kp)))
        self.change_context("main")
        return
    
    #Set the Controller Ki
    def set_controller_ki(self, controller_number, ki):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_ki_command(ki)))
        self.change_context("main")
        return
    
    #Set the Controller Kd
    def set_controller_kd(self, controller_number, kd):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_kd_command(kd)))
        self.change_context("main")
        return

    #Set the Controller hist
    def set_controller_hist(self, controller_number, hist):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_hist_command(hist)))
        self.change_context("main")
        return
    
    #set the Conteller frequency
    def set_controller_frequency(self, controller_number, frequency):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_frequency_command(frequency)))
        self.change_context("main")
        return

    #set the Controller kp
    def set_controller_kp(self, controller_number, kp):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_kp_command(kp)))
        self.change_context("main")
        return
    
    #set the Controller ki
    def set_controller_ki(self, controller_number, ki):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_ki_command(ki)))
        self.change_context("main")
        return

    #set the Controller kd
    def set_controller_kd(self, controller_number, kd):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_kd_command(kd)))
        self.change_context("main")
        return
    
    #set the Controller hist
    def set_controller_hist(self, controller_number, hist):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_hist_command(hist)))
        self.change_context("main")
        return

    #set the Controller frequency
    def set_controller_frequency(self, controller_number, frequency):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_frequency_command(frequency)))
        self.change_context("main")
        return

    #set the Controller setpoint
    def set_controller_setpoint(self, controller_number, setpoint):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_setpoint_command(setpoint)))
        self.change_context("main")
        return
        
    #set the Controller i2c address
    def set_controller_i2c(self, controller_number, i2c):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_i2c_command(i2c)))
        self.change_context("main")
        return

    #Set the Controller enable
    def set_controller_enable(self, controller_number, enable:bool):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        print(self.send_command(self.Controllers[controller_number-1].get_enable_command(enable)))
        self.change_context("main")
        return

    #set the Compensator Auto
    def set_compensator_auto(self, compensator_number):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_auto_command()))
        self.change_context("main")
        return

    #set the Compensator Voltage
    def set_compensator_voltage(self, compensator_number, voltage):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_voltage_command(voltage)))
        self.change_context("main")
        return

    #set the Compensator Wavelength
    def set_compensator_wavelength(self, compensator_number, wavelength):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_wavelength_command(wavelength)))
        self.change_context("main")
        return

    #set the Compensator i2c address
    def set_compensator_i2c(self, compensator_number, i2c):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_i2c_command(i2c)))
        self.change_context("main")
        return
    
    #set the Compensator enable
    def set_compensator_enable(self, compensator_number, enable:bool):
        if not enable:
            self.set_compensator_voltage(compensator_number=compensator_number, voltage=0)
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        print(self.send_command(self.Compensators[compensator_number-1].get_enable_command(enable)))
        self.change_context("main")
        return
    
    #reset the TCB
    def reset(self):
        self.send_command("bounce")
        sleep(10)
        return

    
    #Request the Raw Data from the TCB
    def read_raw_data(self):
        return self.send_command("r")


    #parse the Controller data and update the Controller
    def parse_controller_data(self, raw_data:list[str]):
        #For each line in the data find the Controller and update the data

        for line in raw_data:
            terms = line.split("\t")
            
            #Go through each Controller and check if the line is for that Controller
            for controller in self.Controllers:
                if str(controller.number) in terms[0]:
                    controller.update_data(terms)
                    break
        return

    #parse the Compensator data and update the Compensator
    def parse_compensator_data(self, raw_data:list[str]):
        #For each line in the data find the Compensator and update the data
        for line in raw_data:
            terms = line.split("\t")
            #Go through each Compensator and check if the line is for that Compensator
            
            for compensator in self.Compensators:
                if str(compensator.number) in terms[0]:
                    compensator.update_data(terms)
                    break
        return

    #Parse the Raw Data. 
    def parse_raw_data(self, raw_data:str):
        try:
            #remove the first row which is the header
            
            raw_data = raw_data.split("\n")
            
            #Find the line that contains the header of the Controller
            for i in range(len(raw_data)):
                if self.Controllers[0].header in raw_data[i]:
                    break
            ControllerHeaderLine = i
            #Find the line that contains the header of the Compensator
            for i in range(len(raw_data)):
                if self.Compensators[0].header in raw_data[i]:
                    break
            CompensatorHeaderLine = i
            
            #Get all the lines between the Controller and Compensator Header
            controller_raw_data = raw_data[ControllerHeaderLine+1:CompensatorHeaderLine]
            self.parse_controller_data(controller_raw_data)

            #Get all the lines between the Compensator and the end of the file
            compensator_raw_data = raw_data[CompensatorHeaderLine+1:]
            self.parse_compensator_data(compensator_raw_data)

            return 0

        except IndexError as e:
            print(f"possible Desync Error with TCB output {e}")
            return(-1)

    #get the data from the TCB
    def update_data(self):
        #Get the Raw Data
        raw_data = self.read_raw_data()
        #Parse the Raw Data
        self.parse_raw_data(raw_data)
        return
    
    #return a crap ton of info in string format    
    def get_info(self):
        #Update all the Data
        self.change_context("main")
        self.update_data()
        #make a string wilth all the info
        #Get the Current Date Time in tab seperated format
        info = datetime.now().strftime("%m/%d/%Y\t%H:%M:%S")
        info = info + '\t'
        #Get the info from all the controllers
        for controller in self.Controllers:
            info += controller.get_info() + '\t'
        #Get the info from all the compensators
        for compensator in self.Compensators:
            info += compensator.get_info() + '\t'
        return info




#Example Code
if __name__ == "__main__":
    #Test Functionality
    lfdi = LFDI_TCB("COM3", 9600)

    #Test Header
    file = open('Test.tsv', "w")
    file.write(f"{lfdi.header_format}\n")
    file.write(f"{lfdi.get_info()}\n")
    file.close()

    #Test the Controller
    # lfdi.set_controller_kp(1, 1)
    # lfdi.set_controller_ki(1, 1)
    # lfdi.set_controller_kd(1, 1)
    # lfdi.set_controller_setpoint(1, 25)
    # lfdi.set_controller_frequency(1,200)
    # lfdi.set_controller_hist(1,26)
    # lfdi.set_controller_i2c(1,0)
    # lfdi.set_controller_enable(1,True)
    # file = open('Test.tsv', "a")
    # file.write(f"{lfdi.get_info()}\n")
    # file.close()

    for compensator in lfdi.Compensators:
        lfdi.set_compensator_i2c(compensator.number,00)
        lfdi.set_compensator_voltage(compensator.number,10)
        lfdi.set_compensator_wavelength(compensator.number,100)
        lfdi.set_compensator_enable(compensator.number, True)
        file = open('Test.tsv', "a")
        file.write(f"{lfdi.get_info()}\n")
        file.close()

    exit()
    





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
        lfdi = LFDI_TCB("COM3", 9600)
    except:
        print("Could not connect to LFDI_TCB")
        exit()
    #Set the temperature
    print(lfdi.set_controller_setpoint(1,temp))
    #Set the PID values
    print(lfdi.set_controller_kp(1,kp))
    print(lfdi.set_controller_ki(1,ki))
    print(lfdi.set_controller_kd(1,kd))
    

    #Open the file
    file = open(file_name, "w")
    #Write the header
    file.write(lfdi.header_format)
    file.close()
    #Print Information to the User
    print("Starting Data Collection")
    print("Press Ctrl+C to stop")
    print(lfdi.set_controller_enable(1, True))
    #Start the data collection
    while True:
        
        
        #Open the file
        file = open(file_name, "a")
        #Parse the raw data
        data = lfdi.get_info()
        print(data)
        print("LFDI Compensator will now sweep voltage from 0 to 10")
        lfdi.set_compensator_enable(3, True)
        for i in range(10):
            print(lfdi.set_compensator_voltage(3, i))
            file.write(f"{lfdi.get_info}\r\n")
            sleep(2)
        
        
        
        #Write the tsv data to the file
        file.write(f"{lfdi.get_info}\r\n")
        #Close the file
        file.close()
        #Sleep for the sample rate
        sleep(sample_rate)

    #print("Done")