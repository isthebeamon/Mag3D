# Import packages
import numpy as np
import os
import time
import sys
import shutil
import gzip

# Parameters
voxel_size = %VOXEL_SIZE%  # cm
a_cm_max = %A_CM_MAX%  # cm, PA extent
b_cm_max = %B_CM_MAX%  # cm, ML extent
t_cm = %T_CM%  # cm, CC extent
frequency = %FREQUENCY%  # in um^-1
vox_option = %VOX_OPTION%
compress_option = %COMPRESS_OPTION%
material = %MATERIAL%
material2 = %MATERIAL2%

# Dimensions
dimX = int(b_cm_max / voxel_size)
dimY = int(a_cm_max / voxel_size)
dimZ = int(t_cm / voxel_size)
print("This script creates the Defrise-style phantom.")
print(f"The voxel size is {voxel_size} cm")

# Parameters - MCGPU voxelIds and materials
intensity_air = 0  # Air, Material 0
intensity_adip = 1  # Adipose tissue (fat), Material 1
intensity_skin = 2  # Skin, Material 2
intensity_glan = 29  # Glandular tissue, Material 3
intensity_nipp = 33  # Skin (nipple), Material 4
intensity_musc = 40  # Muscle, Material 6
intensity_C = 45  # Amorphous Carbon (aC), Material 28
intensity_PS = 50  # Polystyrene (MCGPU compression paddle / breast support), Material 10
intensity_PMMA = 55  # PMMA, Material 19
intensity_PE = 57  # Polyethylene, Material 22
intensity_PVC = 58  # PVC, Material 23
intensity_PC = 60 # Polycarbonate, Material 20
intensity_W = 65  # Tungsten (W), Material 13
intensity_Se = 66  # Selenium (Se), Material 14
intensity_stee = 67  # Steel, Material 17
intensity_Al = 68  # Aluminum (Al), Material 18
intensity_Ti = 69  # Titanium (Ti), Material 29
intensity_Pb = 70  # Lead (Pb), Material 16
intensity_I = 75  # Iodine (I), Material 15
intensity_CsI = 77  # Cesium Iodide (CsI), Material 27
intensity_Au = 80  # Gold (Au), Material 24
intensity_Cu = 85  # Copper (Cu), Material 25
intensity_liga = 88  # Connective Woodard tissue (ligament), Material 5
intensity_TDLU = 95  # Muscle (TDLU), Material 9
intensity_H2O = 100  # Water, Material 21
intensity_duct = 125  # Muscle (duct), Material 7
intensity_arte = 150  # Blood (artery), Material 8
intensity_9010 = 175  # Blood 90% Iodine 10%, Material 26
intensity_mass = 200  # Glandular tissue (cancerous mass), Material 11
intensity_vein = 225  # Blood (vein), Material 8
intensity_CO = 250  # Calcium Oxalate (calcification), Material 12

# Parameters - MCGPU material number and density
density_air = (0, 0.00120)  # Air, Material 0
density_adip = (1, 0.920)  # Adipose tissue (fat), Material 1
density_skin = (2, 1.090)  # Skin, Material 2
density_glan = (3, 1.035)  # Glandular tissue, Material 3
density_nipp = (4, 1.090)  # Skin (nipple), Material 4
density_musc = (6, 1.050)  # Muscle, Material 6
density_C = (28, 2.000)  # Amorphous Carbon (aC), Material 28
density_PS = (10, 1.060)  # Polystyrene (MCGPU compression paddle / breast support), Material 10
density_PMMA = (19, 1.190)  # PMMA, Material 19
density_PE = (22, 0.950)  # Polyethylene, Material 22
density_PVC = (23, 1.400)  # PVC, Material 23
density_PC = (20, 1.200) # Polycarbonate, Material 20
density_W = (13, 19.30)  # Tungsten (W), Material 13
density_Se = (14, 4.50)  # Selenium (Se), Material 14
density_stee = (17, 8.000)  # Steel, Material 17
density_Al = (18, 2.6989)  # Aluminum (Al), Material 18
density_Ti = (29, 4.540)  # Titanium (Ti), Material 29
density_Pb = (16, 11.350)  # Lead (Pb), Material 16
density_I = (15, 4.930)  # Iodine (I), Material 15
density_CsI = (27, 4.510)  # Cesium Iodide (CsI), Material 27
density_Au = (24, 19.320)  # Gold (Au), Material 24
density_Cu = (25, 8.960)  # Copper (Cu), Material 25
density_liga = (5, 1.120)  # Connective Woodard tissue (ligament), Material 5
density_TDLU = (9, 1.050)  # Muscle (TDLU), Material 9
density_H2O = (21, 1.000)  # Water, Material 21
density_duct = (7, 1.050)  # Muscle (duct), Material 7
density_arte = (8, 1.000)  # Blood (artery), Material 8
density_9010 = (26, 1.447)  # Blood 90% Iodine 10%, Material 26
density_mass = (11, 1.060)  # Glandular tissue (cancerous mass), Material 11
density_vein = (8, 1.000)  # Blood (vein), Material 8
density_CO = (12, 1.781)  # Calcium Oxalate (calcification), Material 12

# Fill the phantom with materials
start_timer1 = time.time()
phantom_shape = (dimZ, dimY, dimX)
phantom = np.zeros(phantom_shape, dtype=np.uint8)
thickness_Defrise_bar = 100 / frequency  # in cm
thickness_voxels = int(thickness_Defrise_bar / voxel_size)
for x in range(dimX):
    for y in range(dimY):
        for z in range(dimZ):
            if x // thickness_voxels % 2 == 0:
                phantom[z, y, x] = material
            else:
                phantom[z, y, x] = material2
end_timer1 = time.time()
elapsed_time1 = '%.2f' % (end_timer1 - start_timer1)
print(f"The time elapsed to generate the phantom was {elapsed_time1} seconds")

# Create output files and folders
start_timer2 = time.time()
phantom_shape = phantom.shape
output_file1 = f"Defrise_barThickness{int(thickness_Defrise_bar * 10)}mm_freq{int(frequency)}perum.raw"

# Pointer to folder
output_folder1 = sys.argv[1]
if not os.path.exists(output_folder1):
    os.makedirs(output_folder1)
output_path1 = os.path.join(output_folder1, output_file1)

# Save regular output volume as .raw
phantom.tofile(output_path1)
end_timer2 = time.time()
elapsed_time2 = '%.3f' % (end_timer2 - start_timer2)
print(f"The time elapsed to save the uncompressed phantom was {elapsed_time2}"
      f" seconds")
print(f"Saved uncompressed raw phantom to {output_file1} in"
      f" the {output_folder1} folder")
print("The volume can be read in ImageJ with the following parameters:"
      f" Image type: 8-bit, Width: {phantom_shape[2]}, Height:"
      f" {phantom_shape[1]}, Number of Images: {phantom_shape[0]},"
      " Little-endian byte order")

# Save output volume as .vox text file
def save_as_vox(array, filename, compress=False):
    """
    Save a 3D numpy array in the .vox format, replacing intensity values with corresponding material ID and density.

    :param array: 3D numpy array with voxel intensity values.
    :param filename: Name of the file to save the .vox data.
    """
    z_dim, y_dim, x_dim = array.shape

    # Dictionary mapping intensity values to their (material ID, density) pairs
    intensity_to_material_density = {
        intensity_air: density_air,
        intensity_adip: density_adip,
        intensity_skin: density_skin,
        intensity_glan: density_glan,
        intensity_nipp: density_nipp,
        intensity_musc: density_musc,
        intensity_C: density_C,
        intensity_PS: density_PS,
        intensity_PMMA: density_PMMA,
        intensity_PE: density_PE,
        intensity_PVC: density_PVC,
        intensity_PC: density_PC,
        intensity_W: density_W,
        intensity_Se: density_Se,
        intensity_stee: density_stee,
        intensity_Al: density_Al,
        intensity_Ti: density_Ti,
        intensity_Pb: density_Pb,
        intensity_I: density_I,
        intensity_CsI: density_CsI,
        intensity_Au: density_Au,
        intensity_Cu: density_Cu,
        intensity_liga: density_liga,
        intensity_TDLU: density_TDLU,
        intensity_H2O: density_H2O,
        intensity_duct: density_duct,
        intensity_arte: density_arte,
        intensity_9010: density_9010,
        intensity_mass: density_mass,
        intensity_vein: density_vein,
        intensity_CO: density_CO
    }

    open_func = gzip.open if compress else open
    mode = 'wt' if compress else 'w'

    with open_func(filename, mode) as file:
        # Writing the header section
        file.write("[SECTION VOXELS HEADER v.2008-04-13]\n")
        file.write(f"{x_dim}  {y_dim}  {z_dim}              No. OF VOXELS IN X,Y,Z\n")
        file.write(f"{voxel_size}  {voxel_size}  {voxel_size}        VOXEL SIZE (cm) ALONG X,Y,Z\n")
        file.write("1                    COLUMN NUMBER WHERE MATERIAL ID IS LOCATED\n")
        file.write("2                    COLUMN NUMBER WHERE THE MASS DENSITY [g/cm3] IS LOCATED\n")
        file.write("1                    BLANK LINES AT END OF X,Y-CYCLES (1=YES,0=NO)\n")
        file.write("[END OF VXH SECTION]\n")

        # Writing voxel data
        for z in range(z_dim):
            for y in range(y_dim):
                for x in range(x_dim):
                    voxel_value = array[z, y, x]
                    if voxel_value in intensity_to_material_density:
                        material_id, density = intensity_to_material_density[voxel_value]
                        file.write(f"{material_id}  {density:.4f}\n")
                    else:
                        # Handling for undefined voxel values
                        file.write("0  0.0000\n")  # Assuming 0 is the material ID for undefined/air
                if y < y_dim - 1 or z < z_dim - 1:  # To prevent extra blank lines at the end of the file
                    file.write('\n')  # Blank line at the end of each y-cycle
            if z < z_dim - 1:  # To prevent extra blank lines at the end of the file
                file.write('\n')  # Blank line at the end of each z-cycle

        file.write("# >>>> END OF FILE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")

        if compress:
            print(f"Compressed .vox file saved to {filename}")
        else:
            print(f".vox file saved to {filename}")

if vox_option == 'yes' and compress_option == 'yes':
    start_timer4 = time.time()
    vox_filename = f"Defrise_barThickness{int(thickness_Defrise_bar * 10)}mm_freq{int(frequency)}perum.vox.gz"
    vox_file_path = os.path.join(output_folder1, vox_filename)
    save_as_vox(phantom, vox_file_path, compress=True)
    end_timer4 = time.time()
    elapsed_time4 = '%.3f' % (end_timer4 - start_timer4)
    print(f"The time elapsed to create the vox file was {elapsed_time4} seconds.")
    print(f"Saved vox file to {vox_filename} in the {output_folder1} folder.")
elif vox_option == 'yes' and compress_option == 'no':
    start_timer4 = time.time()
    vox_filename = f"Defrise_barThickness{int(thickness_Defrise_bar * 10)}mm_freq{int(frequency)}perum.vox"
    vox_file_path = os.path.join(output_folder1, vox_filename)
    save_as_vox(phantom, vox_file_path, compress=False)
    end_timer4 = time.time()
    elapsed_time4 = '%.3f' % (end_timer4 - start_timer4)
    print(f"The time elapsed to create the vox file was {elapsed_time4} seconds.")
    print(f"Saved vox file to {vox_filename} in the {output_folder1} folder.")
else:
    print("No .vox file created.")

# Compress .raw file with gzip
if compress_option == 'yes':
    start_timer3 = time.time()
    output_file2 = f"Defrise_barThickness{int(thickness_Defrise_bar * 10)}mm_freq{int(frequency)}perum.raw.gz"
    output_path2 = os.path.join(output_folder1, output_file2)
    with open(output_path1, 'rb') as f_in, gzip.open(output_path2, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    end_timer3 = time.time()
    elapsed_time3 = '%.3f' % (end_timer3 - start_timer3)
    print(f"The time elapsed to save and compress the phantom was {elapsed_time3} seconds.")
    print(f"Saved compressed phantom volume to {output_file2} in the {output_folder1} folder")
else:
    print("Compression option declined.")
