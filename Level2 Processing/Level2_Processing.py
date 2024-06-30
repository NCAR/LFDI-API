
import os
from Generate_LUT import generate_LUT
from Generate_Gif import createGif
import pickle
from Scan_Processing import process_scans
from Data_Gathering import get_all_scans, makeLevel2Folder 
from TemperaturePlots import plotNearestMaximaVsTemperature
from VoltagePlots import plotNearestMaximaVsVoltage_Diagram2



# Main Function
if __name__ == '__main__':
    gen_compensated = True
    gen_uncompensated = False
    gen_nearest_maxima_v_Temp = False
    gen_nearest_maxima_v_Voltage = True
    path = "C:\\Users\\mjeffers\\Desktop\\TempSweep\\"
    #path = "C:\\Users\\iguser\\Documents\\GitHub\\LFDI_API\\"
    
    #path = ".\\"
    print("Path: ", path)
    scans_path = f"{path}Experiment_2023-03-25_01-50-48\\"
    scans_path = f"{path}Experiment_2023-03-26_01-05-23\\"
    scans_path = f"{path}Experiment_2023-03-26_04-07-04\\"
    scans_path = f"{path}Experiment_2023-10-27_02-05-39\\"
    scans_path = f"{path}Experiment_2023-10-30_13-10-56\\"
    scans_path = f"{path}Experiment_2023-11-10_13-28-07\\"
    scans_path = f"{path}Experiment_2023-11-14_00-50-06\\"
    
    scans_path = f"{path}Experiment_2023-11-20_11-46-57\\" # 5.4mm Look up table data Set
    #scans_path = f"{path}Experiment_2023-11-17_16-20-49\\" #5.4 mm Temperature Cycle
    scans_path = f"{path}Experiment_2023-12-04_19-07-10\\" # new Look up table
    stage_size = 5.4
    scans_path = f"{path}Experiment_2023-12-17_18-08-49\\" #2.7 mm LUT Epoxy New Tuning Control Board Complete
    stage_size = 2.7
    # scans_path = f"{path}Exp\\" #10.8 mm LUT Epoxy New Tuning Control Board Complete
    # stage_size = 2.7
    # scans_path = f"C:\\Users\\mjeffers\\Desktop\\TempSweep\\Experiment_2024-01-11_12-46-57\\" #10.8 mm LUT Epoxy New Tuning Control Board Complete
    # stage_size = 10.8
    if stage_size == 2.7:
        fsr = .44
    
    print("Making Level 2 Folder")
    l2_path = makeLevel2Folder(path)

    #Generate the Nearest Maxima vs Temperature plot
    if gen_nearest_maxima_v_Temp:
        
        plotNearestMaximaVsTemperature(scans_path, l2_path, stage_size=stage_size, voltage = 0.0)
            
    #Generate a plot of nearest maxima vs Voltage for all temperatures
    if gen_nearest_maxima_v_Voltage:

        temperatures = [25.5, 29.5]
        wave, voltage = plotNearestMaximaVsVoltage_Diagram2(scans_path, l2_path, stage_size=stage_size,temperatures=temperatures)
       
        #Generatere the Lookup Table
        LUT_Data = generate_LUT(wave, voltage, fsr)
        print(f"To Tune To 656.28 Use one of the Following Voltages {LUT_Data[17]}, {LUT_Data[18]}, {LUT_Data[19]}, {LUT_Data[20]}, {LUT_Data[21]}")
        input()
       # plotNearestMaximaVsVoltage_Diagram(scans_path, l2_path, stage_size=stage_size,temperatures=temperatures)

    scans = get_all_scans(scans_path, stage_size)
    #Check to see if scans have been previously processed in a pickle file
    #If they have been processed then load the pickle file
    #If they have not been processed then process them and save them to a pickle file
    if os.path.exists(f"{scans_path}\\Processed.pkl"):
        #Load the pickle file
        with open(f"{scans_path}\\Processed.pkl", 'rb') as f:
            scans = pickle.load(f)
        
    else:
        crosssections, scans = process_scans(scans, l2_path, generate_graph = True)
        #Save the scans to a pickle file
        with open(f"{scans_path}\\Processed.pkl", 'wb') as f:
            pickle.dump(scans, f)
        #Save Crosssections:
        with open(f"{scans_path}\\Crosssections.pkl", 'wb') as f:
            pickle.dump(crosssections, f)
    print(len(scans))
