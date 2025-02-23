# A compliment to AAPM v1.0 - AAPM - v1p
# Alex's Amazing Phantom Maker - v1.0-priyash
import numpy as np
import gzip
import vtk
import os
import datetime
from vtk.util import numpy_support

#right now, the phantom is a simple semicircle extended in the z direction


#defining parameters for the phantom
voxel_size = 0.01 #int(input("Enter the voxel size: "))   #voxel size
#mediolateral_distance = int(input("Enter the mediolateral distance: "))   #mediolateral distance
#craniocaual_distance = int(input("Enter the craniocaual distance: "))   #craniocaual distance
phantom_radius = 9 #int(input("Enter the phantom radius: "))   #phantom radius in cm
breast_thickness = 5 #int(input("Enter the breast thickness: ")) #breast thickness in cm
background = 0   #background material voxel value
#adipose_tissue = 1   #adipose tissue voxel value
glandular_tissue = 180   #glandular tissue voxel value




#saving the phantom as a vti file
def save_vti_file(phantom, filename, voxel_size):
    print("VTI file saved as ", filename)
    length, width, depth = phantom.shape
    image_data = vtk.vtkImageData()
    image_data.SetDimensions(width, length, depth)
    image_data.SetSpacing(voxel_size, voxel_size, voxel_size)

    vtk_array = numpy_support.numpy_to_vtk(num_array=phantom.ravel(), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
    image_data.GetPointData().SetScalars(vtk_array)

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(image_data)
    writer.Write()
    print("VTI file saved as ", filename)


# using gzip to compress the raw file
def save_raw_gz_file(phantom, filename):
    print(f"save_as_raw_gz: Saving raw phantom to {filename}")
    phantom = phantom.astype(np.uint8)
    with gzip.open(filename, 'wb') as f_out:
        f_out.write(phantom.tobytes())
    print(f"Saved raw phantom to {filename}")


# function to generate the phantom array using the parameters
# switch this function to change what kind of phantom is generated
def create_phantom(phantom_radius, breast_thickness, voxel_size, background, adipose_tissue, glandular_tissue):
    print(f"create_phantom: Creating phantom with phantom_radius={phantom_radius}, breast_thickness={breast_thickness}, voxel_size={voxel_size}")

    # Compute the size of the phantom
    lateral_length = int(2 * phantom_radius / voxel_size)
    craniocaudal_length = int(breast_thickness / voxel_size)

    # Initialize the phantom array for numpy
    phantom = np.full((craniocaudal_length, lateral_length, int(lateral_length / 2)), background, dtype=np.uint8)

    # For loop to populate the phantom array
    for z in range(craniocaudal_length):
        for y in range(lateral_length):
            for x in range(breast_thickness):
                phantom[z, y, x] = glandular_tissue

    print(f"3D block created with shape {phantom.shape}")
    return phantom


def main():
    print("starting main function")

    #generate the phantom
    phantom = create_phantom(phantom_radius, breast_thickness, voxel_size, background, 1, glandular_tissue)

    # Generate unique identifier for filenames
    unique_id = datetime.datetime.now().strftime("%Y%m%d")

    # Save the phantom in various formats
    base_filename = f"p_{unique_id}"

    # VTK image format
    vti_filename = f"{base_filename}.vti"
    save_vti_file(phantom, vti_filename, voxel_size)

    # Compressed RAW format
    raw_gz_filename = f"{base_filename}.raw.gz"
    save_raw_gz_file(phantom, raw_gz_filename)

    print("main: Finished main function")

if __name__ == "__main__":
    main()
