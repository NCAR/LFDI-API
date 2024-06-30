import matplotlib.pyplot as plt

#Generate a LUT from the wavelength calibration data. 
#This should be an array of Voltages with the index being the wavelength with the following formula applied 
#   wavelength = index/1000 + 656.28
#   @param wavelength_calibration_data: The data to use to generate the LUT
#   @param stage_size: The stage size of the data
#   @param save_path: The path to save the LUT to
def generate_LUT(wavelength, voltage, fsr):
    print("Generating LUT")
    #Create the LUT
    LUT = [0 for i in range(1000)]
    print(f"Voltages: {len(voltage)}")
    print(f"Wavelengths: {len(wavelength)}")
    print(f"Wavelengths: {wavelength}")
    
    wavelength = fix_wavelength(wavelength, fsr)
    print(f"Wavelengths: {wavelength}")
    input()
    LUT = fill_known_values(wavelength, voltage, LUT)
    print(f"LUT: {LUT}")
    input()
    LUT = linear_interpolation(LUT)
    print(f"LUT: {LUT}")
    LUT = fsr_fill(LUT, fsr)
    print(f"LUT: {LUT}")
    input()
    


    
    # Convert to mV
    for i in range(len(LUT)):
        LUT[i] = int(LUT[i]*1000)

    #Plot the LUT to make sure it looks good
    plt.plot([i/1000 + 656.28 for i in range(1000)], LUT)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Voltage (mV)")
    plt.title("Look Up Table")
    plt.show()
    print(LUT)
    return LUT


def fix_wavelength(wavelength, fsr):
    #if the highest wavelength is less than 656 then we need to add the FSR to the wavelength then
    #add the FSR to the rest of the wavelengths
    #Find the max wavelength
    max_wavelength = max(wavelength)
    # If the max wavelength is less than 656 then we need to add the FSR to the wavelength
    while max(wavelength) < 656:
        #Add the FSR to the wavelength
        for i in range(len(wavelength)):
            wavelength[i] += fsr
    while min(wavelength) > 657:
        #Subtract the FSR from the wavelength
        for i in range(len(wavelength)):
            wavelength[i] -= fsr
    return wavelength

# @Brief this will go through the wavelength and Volatages and fill in the known values in the LUT
# @Param wavelength: The wavelength calibration data
# @Param voltage: The voltage calibration data
# @Param LUT: The LUT to fill
def fill_known_values(wavelength, voltage, LUT):
    LUT = [0 for i in range(1000)]
    # Go through the wavelength calibration data and add the voltage to the LUT
    for i in range(len(wavelength)):
        print(f"Data {wavelength[i]} {voltage[i]}")
        try:
            LUT[int(round((wavelength[i] - 656)*1000))] = voltage[i]
        # Create Exception for LUT out of bounds
        except IndexError:
            continue

    return LUT
              

# @Brief this will go through the LUT 
# and fill in any remaining zeros between 2 known points using linear interpolation
# @Param LUT: The LUT to fill
def linear_interpolation(LUT):
    first_non_zero = 0
    for i in range(len(LUT)):
        try:
            #Find the First Non zero, if there are no non zeros then break
            first_non_zero = LUT.index(next((x for x in LUT[first_non_zero:] if x != 0), 0),first_non_zero)
            # Find the Next Non Zero, if there are no non zeros then break
            next_non_zero = LUT.index(next((x for x in LUT[first_non_zero+1:] if x != 0), 0), first_non_zero+1)
        except ValueError:
            break
        if next_non_zero == LUT.index(0):
            break
      
        
        difference = next_non_zero - first_non_zero
        voltage_difference = LUT[next_non_zero] - LUT[first_non_zero]
        #Find the slope of the line
        slope = voltage_difference/difference
        #Find the y intercept
        y_intercept = LUT[first_non_zero] - slope*first_non_zero
        #Go through the LUT and fill in the missing values between the first and next non zero values
        for i in range(first_non_zero, next_non_zero):
            LUT[i] = round(slope*i + y_intercept,3)
        first_non_zero = next_non_zero

    return LUT

# @Brief fill in any remaining zeros using the FSR of the stage
# ie if we have a 0 at position 100 then we can fill it with the value found at 100+FSR
# @Param LUT: The LUT to fill
def fsr_fill(LUT, fsr):
    #Go through the LUT and fill in any remaining zeros using the FSR of the stage
    fsr = int(fsr*1000)
    for i in range(len(LUT)):
        if LUT[i] == 0:
            try:
                LUT[i] = LUT[i+fsr]
            except IndexError:
                try:
                    LUT[i] = LUT[i-fsr]
                except IndexError:
                    continue

    return LUT