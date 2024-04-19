from Scan import Scan


# @Brief: This function will go through a list of scans and process each of them
# @Param: scans - list of scans to process
def process_scans(scans: list, l2_path: str, generate_graph=True):
    # Allocate an empty list to store the cross sections
    crosssections = []
    processed_scans = []
    for temp in scans:
        # if temp is a list then there are multiple scans at that temperature
        try:
            print(f"Temperature: {temp[0].temperature}")
            # only process one scan at that temperature
            scan = temp[0]
        except:
            print(f"Temperature: {temp.temperature}")
            scan = temp
        
        print(f"Scan: {scan}")
        filename = f"{l2_path}\\CrossSection{scan.temperature}C.png"
        if generate_graph:
            if not scan.processed:
                scan.process()
            scan.save_cross_section(filename,  smooth=True, plot_raw=True, scale = True, Limit_Y = True)
        crosssections.append(filename)
        processed_scans.append(scan)
    
    return crosssections, processed_scans
