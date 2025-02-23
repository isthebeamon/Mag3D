import os
import json
import datetime
import sys
from jinja2 import Template
import re

global name_for_bash
global bash_variable
bash_variable = []

# function to define each mode
def mode_selection():
    # request user input
    global mode
    mode = input("Single or batch Mode? ")
    #different modes
    if mode == 'single':
        return(mode)
    elif mode == 'batch':
        global parameter
        parameter = input("What parameter will you be varying? ")
        global step_size
        step_size = int(input("What step size will the parameter be varying by? "))
        global initial_val
        initial_val = int(input("What is the minimum value for the parameter? "))
        global end_val
        end_val = int(input("What is the maximum value of the parameter? "))
        return(mode, parameter, step_size, initial_val, end_val)
    else:
        raise ValueError(f"This mode is not defined yet...")


# function to generate the in file
def GenerateInFiles(simulator, mode):
    print("Generating in File")
    global Simulation_date
    Simulation_date = datetime.datetime.now().strftime("%Y-%m-%d")
    global particle_histories
    particle_histories = input("Enter the number of particle histories ( e.g. 5.51e10 )  ")
    # For my use case this is really just directing where the approriate result directory
    global material_selection
    material_selection = input("Enter the Directory to store the images (named by material) ")
    # Use this dimension to change magnification
    global z_offset_distance
    z_offset_distance = float(input("Enter the z-offset of the phantom from the detector "))
    if z_offset_distance > 0:
        material_selection = material_selection + "/Mag"
    print(material_selection)
    # Again my use case involved a square phantom and so I can describe it with 1 dimension
    # I use this 1 dimension to locate the approriate result directory
    global phantom_size
    phantom_size = float(input("Enter the side ML distance of the phantom ")) # this distance will lated be used to find zvoxels later
    # Craniocaudal length of the phantom
    global cc_length
    cc_length = float(input("Enter the Cranio Caudal distance of the phantom "))
    if abs(cc_length - 1.9) < 0.01:
        global t
        t = "1p9cm"
    else:
        t = f"{int(cc_length)}cm"
    print(t)

    global phantom_name
    phantom_name = input("Copy paste the name of the phantom you generated ")
    global source_center
    source_center = phantom_size / 2 # in cm
    global number_of_voxels_xy
    number_of_voxels_xy = int(phantom_size / 0.05) #cm/0.05[cm/voxel]
    global number_of_voxels_z
    number_of_voxels_z = int(cc_length / 0.05)  #cm/0.05[cm/voxel]
    
    # Change behavior depending on mode
    if mode == 'single':
        create_json_and_in_file()
    elif mode == 'batch':
        if parameter == 'z':
            for i in range(int(initial_val), int(end_val), int(step_size)):
                z_offset_distance = float(i)
                create_json_and_in_file()
                bash_variable.append(name_for_bash)
        else:
            raise ValueError(f"Unsupported Parameter Value")
    else:
        raise ValueError(f"This Mode Has Not Been Programmed Yet...")
                
    
    print("Generated Simulation_Title.in successfully!")


def create_json_and_in_file():
    #create the json input file
    data = {
        "Simulator": "#                          ["+ Simulating_indv + ",  " + Simulation_date + "]",
        "Histories": f"{particle_histories}",
        "Material": f"{material_selection}",
        "Size": f"{int(phantom_size)}x{int(phantom_size)}",
        "Thickness": f"{t}",
        "Phantom": f"{phantom_name}",
        "Source": source_center,
        "voxels": number_of_voxels_xy,
        "zvoxels": number_of_voxels_z,
        "ZDistance": z_offset_distance
    }

    # Writing to the input.json
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)


    #Load the template
    with open('MC_GPU_in_File.tmpl') as f:
        template = Template(f.read())

    #Render the template with data
    output = template.render(data)

    # Save to output file
    if z_offset_distance > 0:
        # If we are in Mag Mode Rename accordingly
        with open( f"InFiles/{phantom_name}_bit[32R]_size[3584x2816]_Histories[{particle_histories}]_kVp[28W]_Filter[Al700um]_projections[2]_Z[{z_offset_distance}].in", 'w') as f:
            f.write(output)
            global name_for_bash
            name_for_bash = f"{phantom_name}_bit[32R]_size[3584x2816]_Histories[{particle_histories}]_kVp[28W]_Filter[Al700um]_projections[2]_Z[{z_offset_distance}]"
    else:
        with open( f"InFiles/{phantom_name}_bit[32R]_size[3584x2816]_Histories[{particle_histories}]_kVp[28W]_Filter[Al700um]_projections[2].in", 'w') as f:
            f.write(output)
            name_for_bash = f"{phantom_name}_bit[32R]_size[3584x2816]_Histories[{particle_histories}]_kVp[28W]_Filter[Al700um]_projections[2]_Z[{z_offset_distance}]"
        
def Generate_Bash_Script():
    # Generate the Bash Script
    bash_script = "#!/bin/bash\n\n"
    
    # iterate over the in files created and amake an executable bash command
    for filename in bash_variable:
        bash_script += f"#{phantom_size}x{phantom_size}cm {cc_length}cm thick\n./MC-GPU_1.5b.x {filename}.in | tee {filename}.out\n\n"

    # save the bash script as a .sh file
    bash_script += f"\n\n\n\n\necho 'Simulations Completed!'"
    script_name = f"{phantom_name}_thickness[{cc_length}cm]_Z[{initial_val}cm_to{end_val}_cm].sh"
    with open(script_name, 'w') as f:
        f.write(bash_script)
        
    return bash_script


def main():
    print("Starting main function...")
    # User input to start the process
    global Simulating_indv
    Simulating_indv = input("First Name, Last Name ")
    # Mode selection
    mode_selection()
    # Generate the in File
    GenerateInFiles(Simulating_indv, mode)
    # Generate bash script
    Generate_Bash_Script()
  

if __name__ == "__main__":
    print("Script is running...")
    main()