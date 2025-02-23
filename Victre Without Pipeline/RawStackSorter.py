import os
import argparse
#import numpy as np
import cupy as np   #If you want to use CUPY instead of NUMPY
import re

################################################################
###################### EXAMPLE USAGE  ##########################
# python3 RawStackSorterV2.py /path/to/input /path/to/output/stack1 /path/to/output/stack2 /path/to/output/stack3 --width=3584 --height=2816 --dtype=float32


def extract_sort_value(filename):
    """
    Extract either Z value or Block number for sorting.
    Returns a tuple of (sort_type, value) where:
    - sort_type is 0 for Z-values and 1 for Block numbers (to ensure Z sorts come before Block)
    - value is the floating point or integer value to sort by
    """

    # Try to find Block number
    block_match = re.search(r'(\d+)Block', filename)
    if block_match:
        return (1, int(block_match.group(1)))

    # Try to find Z value first
    z_match = re.search(r'Z\[(\d+\.?\d*)]', filename)
    if z_match:
        return (0, float(z_match.group(1)))

    # If neither found, return a tuple that will sort after both
    return (2, 0)

def custom_sort_key(filename):
    """
    Custom sorting key that sorts by Z value or Block number
    """
    return extract_sort_value(filename)



def main():
    parser = argparse.ArgumentParser(description='Process raw image files: split into slices and compute subtraction, saving each stack as a single file.')
    parser.add_argument('input_folder', help='Path to the input folder containing raw image files.')
    parser.add_argument('output_folder1', help='Path to the output folder for Stack 1 (Slice 1 images).')
    parser.add_argument('output_folder2', help='Path to the output folder for Stack 2 (Slice 2 images).')
    parser.add_argument('output_folder3', help='Path to the output folder for Stack 3 (Slice 1 - Slice 2 images).')
    parser.add_argument('--width', type=int, required=True, help='Width of each image slice.')
    parser.add_argument('--height', type=int, required=True, help='Height of each image slice.')
    parser.add_argument('--dtype', default='float32', choices=['uint8', 'uint16', 'float32'], help='Data type of the pixel data.')

    args = parser.parse_args()

    # Create output directories if they don't exist
    os.makedirs(args.output_folder1, exist_ok=True)
    os.makedirs(args.output_folder2, exist_ok=True)
    os.makedirs(args.output_folder3, exist_ok=True)

    # Prepare data type information
    dtype_info = {
        'uint8': (1, np.uint8),
        'uint16': (2, np.uint16),
        'float32': (4, np.float32)
    }

    if args.dtype not in dtype_info:
        print(f"Unsupported data type: {args.dtype}")
        return

    bytes_per_pixel, np_dtype = dtype_info[args.dtype]
    slice_size = args.width * args.height * bytes_per_pixel
    expected_length = slice_size * 2  # two slices

    # Initialize lists to hold all slices for each stack
    stack1_slices = []  # Primary+Scatter
    stack2_slices = []  # Primary
    stack3_slices = []  # Scatter (difference)

    # Get list of raw image files
    file_list = [f for f in os.listdir(args.input_folder)
                 if f.endswith('_0002.raw')]
    file_list.sort(key=custom_sort_key)

    # Print the sorted order with the sorting values for verification
    print("\nSorted files to process:")
    for f in file_list:
        sort_type, value = extract_sort_value(f)
        type_str = "Z" if sort_type == 0 else "Block" if sort_type == 1 else "Other"
        print(f"{type_str}[{value}] - {f}")
    print(f"\nTotal files found: {len(file_list)}")

    for idx, filename in enumerate(file_list):
        filepath = os.path.join(args.input_folder, filename)

        try:
            with open(filepath, 'rb') as f:
                data = f.read()

            if len(data) != expected_length:
                print(f"File {filename} has unexpected size: {len(data)} bytes vs expected {expected_length} bytes")
                continue

            # Split the data into two slices
            data_slice1 = data[:slice_size]
            data_slice2 = data[slice_size:]

            # Convert data to numpy arrays for processing
            arr_slice1 = np.frombuffer(data_slice1, dtype=np_dtype).reshape((args.height, args.width))
            arr_slice2 = np.frombuffer(data_slice2, dtype=np_dtype).reshape((args.height, args.width))

            # Compute subtraction while maintaining the original data type
            arr_result = np.subtract(arr_slice1, arr_slice2, dtype=np_dtype)

            # Append each slice to its respective stack
            stack1_slices.append(arr_slice1)
            stack2_slices.append(arr_slice2)
            stack3_slices.append(arr_result)

            print(f"Processed file {idx + 1}/{len(file_list)}: {filename}")

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    # Convert lists of arrays into 3D arrays (stack_size × height × width)
    stack1 = np.stack(stack1_slices)
    stack2 = np.stack(stack2_slices)
    stack3 = np.stack(stack3_slices)

    # Save each stack as a single file
    stack1_path = os.path.join(args.output_folder1, 'Primary+Scatter_Stack.raw')
    stack2_path = os.path.join(args.output_folder2, 'Primary_Stack.raw')
    stack3_path = os.path.join(args.output_folder3, 'Scatter_Stack.raw')

    try:
        stack1.tofile(stack1_path)
        stack2.tofile(stack2_path)
        stack3.tofile(stack3_path)

        print("\nStack sizes:")
        print(f"Primary+Scatter Stack: {stack1.shape}")
        print(f"Primary Stack: {stack2.shape}")
        print(f"Scatter Stack: {stack3.shape}")
        print(f"\nStacks have been saved successfully")

    except Exception as e:
        print(f"Error saving stacks: {str(e)}")

if __name__ == "__main__":
    main()
