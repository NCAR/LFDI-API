import os
import pickle
from datetime import datetime
import Scan


def get_all_scans(scans_path, stage_size):
        #Get all the scans in the scans_path
        Files = [scan for scan in os.listdir(scans_path) if scan.endswith(".png")]
        scans = []
        for File in Files:
            #Check if a pickle file exists for the scan
            if os.path.exists(f"{scans_path}\\{File[:-4]}.pkl"):
                #Load the pickle file
                with open(f"{scans_path}\\{File[:-4]}.pkl", 'rb') as f:
                    scans.append(pickle.load(f))
            else:
                scans.append(Scan.Scan(File, scans_path, stage_size))
        return scans


# make a level 2 folder for the data
def makeLevel2Folder(path):
    #get the current time
    now = datetime.now()
    #format the time
    dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    #make the folder
    os.mkdir(path + "Level2_" + dt_string)
    return path + "Level2_" + dt_string
