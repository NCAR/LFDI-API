#Connect to the LFDI TCB through a serial port
#Creates Commands and executes in the following manner
#User wants to set controller 1's set point to 25C:
#lfdi.set_controller_setpoint(1, 25)
# serial Send commands
#'controller' -- go to the controller context menu
#'c1' -- select controller 1
#'t25' -- set the controller to 25
#'m' -- return to the main menu


#This software is currently still a WIP its not uncommon for the system to desync or send bad commands
#I think this is due to a number of reasons. The host machine for this software is scanning com ports which can intercept some data and cause desync issues
import serial
from time import sleep
from time import time
from time import strftime
import time
from datetime import datetime


#This is the Controller Class Mostly used as a data class
# All data for the Controllers are stored here and will be polled for LFDI's get info class
# This will also compose commands for the TCB 
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

    def get_kp_response(self):
        return f"kp set to"
    def get_ki_response(self):
        return f"ki set to"
    def get_kd_response(self):
        return f"kd set to"
    def get_setpoint_response(self):
        return f"Target temperature set to"
    def get_enable_response(self, enable:bool):
        if(enable):
            return f"Controller enabled."
        else:
            return f"Controller disabled."
    def get_i2c_response(self):
        return f"Sensor Address Set to"
    def get_hist_response(self):
        return f"History set to"
    def get_frequency_response(self):
        return f"Frequency set to"



    #get info Tab separated in the format of the header
    def get_info(self):
        info = f"Cont{self.number}\t{self.kp}\t{self.kd}\t{self.ki}\t{self.error_p}\t{self.error_d}\t{self.error_i}\t{self.effort}\t{self.temp}\t{self.average}\t{self.setpoint}\t{self.i2c}\t{self.history}\t{self.frequency}\t{self.enabled}\t{self.sensor}"
        return info
        

# This Works as a data class for the Compensators #Controlling the Peak to Peak Voltage applied to the Optic
#         
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

    #This is the expected Responses from the various commands
    def get_voltage_response(self):
        return f" Voltage Set to"

    def get_enable_response(self, enable:bool):
        if(enable):
            return f"Compensator {self.number} Enabled."
        else:
            return f"Compensator {self.number} Disabled."

    def get_auto_response(self):
        return f"Compensator {self.number} Auto Compensating"
    
    def get_useAverage_response(self):
        return None
    
    def get_i2c_response(self):
        return f"Sensor Address Set"
    
    def get_wavelength_response(self):
        return f"Wavelength Set"
    

    
    # Data Class for the GPIOs
class GPIO(object):

    def __init__(self, number):
        self.number = number
        self.header = "GPIO\tEnabled"
        self.state = False
        return

    def __del__(self):
        return

    def update_data(self, data):
        self.state = data[1]
        return

    def get_info(self):
        info = f"GPIO{self.number}\t{self.state}"
        return info

    def get_raw_data_command(self):
        return "r"

    def get_state_command(self):
        return "e"

    def get_state_response(self):
        return f"GPIO{self.number} set to"


class Bipolar(object):

    def __init__(self, number):
        self.number = number
        self.header = "Bipolar\tfrequency\tpulses\tPeak2Peak\tEnabled"
        self.frequency = 0
        self.pulses = 0
        self.voltage = 0
        self.enabled = False

        return

    def __del__(self):
        return

    def update_data(self, data):
        self.frequency = data[1]
        self.pulses = data[2]
        self.voltage = data[3]
        self.enabled = data[4]
        return
    
    def get_info(self):
        info = f"Bipolar{self.number}\t{self.frequency}\t{self.pulses}\t{self.voltage}\t{self.enabled}"
        return info
    
    def get_raw_data_command(self):
        return "r"
    
    def get_frequency_command(self, frequency):
        return f"f{frequency}"
    


class LFDI_TCB(object):


    def __init__(self, com_port, baud_rate = 9600):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.OpenConnection()
        self.ser.timeout = 1
        self.ser.write_timeout = 1
        
        self.Controllers = [Controller(1), Controller(2), Controller(3)] # Create the Controllers
        self.Compensators = [Compensator(1), Compensator(2), Compensator(3), Compensator(4), Compensator(5), Compensator(6)] #Create the Compensators
        self.GPIOs = [GPIO(1), GPIO(2), GPIO(3), GPIO(4), GPIO(5)]
        self.Bipolars = [Bipolar(1), Bipolar(2)]
        self.current_context = "main"
        self.valid_contexts = ["main", "controller", "compensator"]
        
        self.header_format = f"Date\tTime\t"
        #add controller headers
        for controller in self.Controllers:
            self.header_format += f"{controller.header}\t"
        #add compensator headers
        for compensator in self.Compensators:
            self.header_format += f"{compensator.header}\t"
        #add gpio headers
        for gpio in self.GPIOs:
            self.header_format += f"{gpio.header}\t"
        #add bipolar headers
        for bipolar in self.Bipolars:
            self.header_format += f"{bipolar.header}\t"
            

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
    def send_command(self, command, print_command = True, expected_response = None, attempts = 0):
        if attempts > 3:
            print(f"Too many attempts to send command {command}\nRestarting Connection")
            self.ser.close()
            self.OpenConnection()
            return
         #try to send command   
        self.ser.flushInput()
        self.ser.flushOutput()
        
        if print_command:
            print(f"{command}")
        self.ser.write(f"{command}\r".encode('utf-8'))
        sleep(.5)
        try:
            val = self.ser.read_all().decode('utf-8', errors = 'ignore')
        except:
            print(f"Lost Connection With port")
            self.ser.close()
            self.OpenConnection()
        #Check to see we got the right stuff back
        if expected_response is None:
            return val
        #If our response doesnot contain the expected response we are out of sync
        if expected_response not in val:
            print(f"Expected response: {expected_response} not Response: {val}")        
            val = self.send_command(command, print_command, expected_response, attempts=attempts+1)
            return val
        return val
             
        



    #Set the Compensator Voltage
    def set_compensator_voltage(self, compensator_number:int, voltage:float):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_voltage_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_voltage_command(voltage), expected_response = expected_response))
        self.change_context("main")
        return

    #Set the Compensator compensate
    def toggle_compensator_auto(self, compensator_number):
        self.change_context("compensator")
        print(self.send_command(f"c{compensator_number}"))
        expected_response = self.Compensators[compensator_number-1].get_auto_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_auto_command(), expected_response = expected_response))
        self.change_context("main")
        return

    def set_compensator_useAverage(self, compensator_number, useAverage):
        print("Not Implemented")
        return

    #Set the Compensator i2c address
    def set_compensator_i2c(self, compensator_number, i2c):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_i2c_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_i2c_command(i2c), expected_response = expected_response))
        self.change_context("main")
        return
    
    #Set the Compensator enable
    def set_compensator_enable(self, compensator_number, enable):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_enable_response(enable)
        print(self.send_command(self.Compensators[compensator_number-1].get_enable_command(enable), expected_response=expected_response))
        self.change_context("main")
        return
    
    #Set the Controller enable
    def set_controller_enable(self, controller_number, enable):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_enable_response(enable)
        print(self.send_command(self.Controllers[controller_number-1].get_enable_command(enable), expected_response=expected_response))
        self.change_context("main")
        return
    
    #Set the Controller i2c address
    def set_controller_i2c(self, controller_number, i2c):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_i2c_response()
        print(self.send_command(self.Controllers[controller_number-1].get_i2c_command(i2c), expected_response = expected_response))
        self.change_context("main")
        return
    
    #Set the Controller Kp
    def set_controller_kp(self, controller_number, kp):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_kp_response()
        print(self.send_command(self.Controllers[controller_number-1].get_kp_command(kp), expected_response = expected_response))
        self.change_context("main")
        return
    
    #Set the Controller Ki
    def set_controller_ki(self, controller_number, ki):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_ki_response()
        print(self.send_command(self.Controllers[controller_number-1].get_ki_command(ki), expected_response=expected_response))
        self.change_context("main")
        return
    
    #Set the Controller Kd
    def set_controller_kd(self, controller_number, kd):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_kd_response()
        print(self.send_command(self.Controllers[controller_number-1].get_kd_command(kd), expected_response=expected_response))
        self.change_context("main")
        return

    #Set the Controller hist
    def set_controller_hist(self, controller_number, hist):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_hist_response()
        print(self.send_command(self.Controllers[controller_number-1].get_hist_command(hist), expected_response=expected_response))
        self.change_context("main")
        return
    
    #set the Conteller frequency
    def set_controller_frequency(self, controller_number, frequency):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_frequency_response()
        print(self.send_command(self.Controllers[controller_number-1].get_frequency_command(frequency), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Controller kp
    def set_controller_kp(self, controller_number, kp):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_kp_response()
        print(self.send_command(self.Controllers[controller_number-1].get_kp_command(kp), expected_response=expected_response))
        self.change_context("main")
        return
    
    #set the Controller ki
    def set_controller_ki(self, controller_number, ki):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_ki_response()
        print(self.send_command(self.Controllers[controller_number-1].get_ki_command(ki), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Controller kd
    def set_controller_kd(self, controller_number, kd):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_kd_response()
        print(self.send_command(self.Controllers[controller_number-1].get_kd_command(kd), expected_response=expected_response))
        self.change_context("main")
        return
    
    #set the Controller hist
    def set_controller_hist(self, controller_number, hist):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_hist_response()
        print(self.send_command(self.Controllers[controller_number-1].get_hist_command(hist), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Controller frequency
    def set_controller_frequency(self, controller_number, frequency):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_frequency_response()
        print(self.send_command(self.Controllers[controller_number-1].get_frequency_command(frequency), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Controller setpoint
    def set_controller_setpoint(self, controller_number, setpoint):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_setpoint_response()
        print(self.send_command(self.Controllers[controller_number-1].get_setpoint_command(setpoint), expected_response=expected_response))
        self.change_context("main")
        return
        
    #set the Controller i2c address
    def set_controller_i2c(self, controller_number, i2c):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_i2c_response()
        print(self.send_command(self.Controllers[controller_number-1].get_i2c_command(i2c), expected_response=expected_response))
        self.change_context("main")
        return

    #Set the Controller enable
    def set_controller_enable(self, controller_number, enable:bool):
        self.change_context("controller")
        self.send_command(f"c{controller_number}")
        expected_response = self.Controllers[controller_number-1].get_enable_response(enable)
        print(self.send_command(self.Controllers[controller_number-1].get_enable_command(enable), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Compensator Auto
    def set_compensator_auto(self, compensator_number):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_auto_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_auto_command(), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Compensator Voltage
    def set_compensator_voltage(self, compensator_number, voltage):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_voltage_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_voltage_command(voltage), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Compensator Wavelength
    def set_compensator_wavelength(self, compensator_number, wavelength):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_wavelength_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_wavelength_command(wavelength), expected_response=expected_response))
        self.change_context("main")
        return

    #set the Compensator i2c address
    def set_compensator_i2c(self, compensator_number, i2c):
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_i2c_response()
        print(self.send_command(self.Compensators[compensator_number-1].get_i2c_command(i2c), expected_response=expected_response))
        self.change_context("main")
        return
    
    #set the Compensator enable
    def set_compensator_enable(self, compensator_number, enable:bool):
        if not enable:
            self.set_compensator_voltage(compensator_number=compensator_number, voltage=0)
        self.change_context("compensator")
        self.send_command(f"c{compensator_number}")
        expected_response = self.Compensators[compensator_number-1].get_enable_response(enable)
        print(self.send_command(self.Compensators[compensator_number-1].get_enable_command(enable), expected_response=expected_response))
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

    def parse_gpio_data(self, raw_data:list[str]):
        #For each line in the data find the GPIO and update the data
        for line in raw_data:
            terms = line.split(" ")
            #Go through each GPIO and check if the line is for that GPIO
            for gpio in self.GPIOs:
                if str(gpio.number) in terms[0]:
                    gpio.update_data(terms)
                    break
        return
    
    def parse_bipolar_data(self, raw_data:list[str]):
        #For each line in the data find the Bipolar and update the data
        for line in raw_data:
            terms = line.split(" ")
            #Go through each Bipolar and check if the line is for that Bipolar
            for bipolar in self.Bipolars:
                if str(bipolar.number) in terms[0]:
                    bipolar.update_data(terms)
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
            #find the line that contains the header of the GPIO 
            for i in range(len(raw_data)):
                print(raw_data[i])
                if "GPIO" in raw_data[i]:
                    break
            GPIOHeaderLine = i
            #find the line that contains the header of the Bipolar
            for i in range(len(raw_data)):
                if "Bipolar" in raw_data[i]:
                    break
            BipolarHeaderLine = i

            #Get all the lines between the Controller and Compensator Header
            controller_raw_data = raw_data[ControllerHeaderLine+1:CompensatorHeaderLine]
            self.parse_controller_data(controller_raw_data)
            #Get all the lines between the Compensator and the end of the file
            compensator_raw_data = raw_data[CompensatorHeaderLine+1:GPIOHeaderLine]
            self.parse_compensator_data(compensator_raw_data)
            #Get all the lines between the GPIO and the end of the file
            gpio_raw_data = raw_data[GPIOHeaderLine+1:BipolarHeaderLine]
            self.parse_gpio_data(gpio_raw_data)
            #Get all the lines between the Bipolar and the end of the file
            bipolar_raw_data = raw_data[BipolarHeaderLine+1:]
            self.parse_bipolar_data(bipolar_raw_data)
            
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
        for gpio in self.GPIOs:
            info += gpio.get_info() + '\t'
        for bipolar in self.Bipolars:
            info += bipolar.get_info() + '\t'
        return info




# Example Code
if __name__ == "__main__":
    #See if User Wants an Automated Test or a Manual Test
    test = input("Automated Test? (y/n): ")
    if test == "y":
        #Test Functionality
        lfdi = LFDI_TCB("COM6", 9600)
        #print(lfdi.get_info())
        #time.sleep(10000)
        #Test Header
        file = open('Test.tsv', "w")
        file.write(f"{lfdi.header_format}\n")#Writes the Header to the First line of the File
        file.write(f"{lfdi.get_info()}\n") #Writes the Data to the Second line of the File
        file.close() #Closes the File

        #Test the Controller
        for controller in lfdi.Controllers:
            print(f"Testing Controller {controller.number}")
            print(f"Setting Controller {controller.number} PID to 1,1,1")
            lfdi.set_controller_kp(controller.number, 1)
            lfdi.set_controller_ki(controller.number, 1)
            lfdi.set_controller_kd(controller.number, 1)
            print(f"Setting Controller {controller.number} Setpoint to 30 (light on)")
            lfdi.set_controller_setpoint(controller.number, 30)
            print(f"Setting Controller {controller.number} Frequency to 200")
            lfdi.set_controller_frequency(controller.number,200)
            print(f"Setting Controller {controller.number} History to 26")
            lfdi.set_controller_hist(controller.number,26)
            print(f"Setting Controller {controller.number} i2c to 0")
            lfdi.set_controller_i2c(controller.number,0)
            print(f"Enabling Controller {controller.number} Heater Light Should be on")
            lfdi.set_controller_enable(controller.number,True)
            print(f"Getting Controller {controller.number} Info and Writing to File Test.tsv")
            file = open('Test.tsv', "a")
            file.write(f"{lfdi.get_info()}\n")
            file.close()
            print(f"Sleeping for 10 Seconds")
            sleep(5)
            print(f"Setting Controller {controller.number} Setpoint to 20 (light off)")
            lfdi.set_controller_setpoint(controller.number, 20)
            print(f"Getting Controller {controller.number} Info and Writing to File Test.tsv")
            file = open('Test.tsv', "a")
            file.write(f"{lfdi.get_info()}\n")
            file.close()
            print(f"Sleeping for 10 Seconds")
            sleep(5)
            print(f"Disabling Controller {controller.number} Heater Light Should be off")
            lfdi.set_controller_enable(controller.number,False)
            print(f"Getting Controller {controller.number} Info and Writing to File Test.tsv")
            file = open('Test.tsv', "a")
            file.write(f"{lfdi.get_info()}\n")
            file.close()



        for compensator in lfdi.Compensators:
            print(f"Testing Compensator {compensator.number}")
            print(f"Setting Compensator {compensator.number} I2C to 00")
            lfdi.set_compensator_i2c(compensator.number,00) #Set the i2c address of the sensor
            print(f"Setting Compensator {compensator.number} Voltage to 10")
            lfdi.set_compensator_voltage(compensator.number,10) #Set the voltage peak to peak of the compensator
            print(f"Setting Compensator {compensator.number} Wavelength to 100")
            lfdi.set_compensator_wavelength(compensator.number,100) #Set the wavelength of the compensator
            print(f"Enabling Compensator {compensator.number}")
            lfdi.set_compensator_enable(compensator.number, True) #Enable the compensator
            file = open('Test.tsv', "a") #Open the file
            file.write(f"{lfdi.get_info()}\n") #Write the data to the file
            file.close() #Close the file

        exit()
        
    else:




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
            lfdi = LFDI_TCB("COM6", 9600)
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