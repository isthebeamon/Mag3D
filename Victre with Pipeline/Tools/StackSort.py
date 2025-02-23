import os
import argparse
import re
import sys
from pathlib import Path
from tqdm import tqdm
import cupy as np  # Use CuPy for GPU acceleration
from fnmatch import fnmatch

# (Optional, original import of numpy commented out)
# import numpy as np  # Uncomment if you prefer CPU computation

def extract_file_info(filename):
    """
    Extract key values ML, CC and Z from the filename.
    Assumes files are named like:
      BlockPhantom_PA[20]cm_ML[20]cm_CC[3]cm_PA[400]vx_ML[400]vx_CC[60]vx_VxlRes[5.0]mm_Material[5]_Z[20]_0002.raw
    This function uses regex to look for:
       _ML[<num>]
       _CC[<num>]
       _Z[<num>]
    Returns a tuple (ml_val, cc_val, z_val) as integers or None if any token is missing.
    """
    ml_match = re.search(r'_ML\[(\d+)\]', filename)
    cc_match = re.search(r'_CC\[(\d+)\]', filename)
    z_match = re.search(r'_Z\[(\d+)\]', filename)
    if ml_match and cc_match and z_match:
        try:
            return int(ml_match.group(1)), int(cc_match.group(1)), int(z_match.group(1))
        except ValueError:
            return None
    else:
        return None

def process_raw_file(file_path, slice_size, np_dtype, width, height):
    """
    Processes a single .raw file, splitting it into two slices and computing the subtraction.
    Returns a tuple of 3 arrays (primary, secondary, scatter) or (None, None, None) on failure.
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        if len(data) != slice_size * 2:
            print(f"Warning: File {file_path} has size {len(data)} bytes vs expected {slice_size*2} bytes")
            return None, None, None

        data_slice1 = data[:slice_size]
        data_slice2 = data[slice_size:]
        arr_slice1 = np.frombuffer(data_slice1, dtype=np_dtype).reshape((height, width))
        arr_slice2 = np.frombuffer(data_slice2, dtype=np_dtype).reshape((height, width))
        arr_scatter = (arr_slice1 - arr_slice2).astype(np_dtype)
        return arr_slice1, arr_slice2, arr_scatter

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None, None, None

def find_files_in_directory(root_dir, patterns):
    """
    Recursively search root_dir (and all its subdirectories) for files matching any
    of the patterns (e.g., ['*_0002.raw']). Returns a list of full file paths.
    """
    matches = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            for pattern in patterns:
                if fnmatch(filename, pattern):
                    matches.append(os.path.join(dirpath, filename))
                    break
    return matches

def main():
    parser = argparse.ArgumentParser(description='Process and stack raw images by ML and CC distance (and sort by Z).')
    parser.add_argument('input_root', help='Input root folder (e.g., /results/Lucite/Homogenous_Lucite/Mag)')
    parser.add_argument('output_root', help='Output folder')
    parser.add_argument('--width', type=int, required=True, help='Width of image slice')
    parser.add_argument('--height', type=int, required=True, help='Height of image slice')
    parser.add_argument('--dtype', default='float32', choices=['uint8', 'uint16', 'float32'],
                        help='Pixel data type')
    # The pattern lets you activate files ending in _0002.raw.
    parser.add_argument('--patterns', nargs='+', default=['*_0002.raw'],
                        help='Filename patterns to search for (e.g., *_0002.raw)')
    args = parser.parse_args()

    input_root = args.input_root
    output_root = args.output_root
    width = args.width
    height = args.height
    dtype = args.dtype
    patterns = args.patterns

    if not os.path.isdir(input_root):
        print(f"Error: Input root does not exist: {input_root}")
        sys.exit(1)

    # Data type mapping
    dtype_info = {'uint8': (1, np.uint8),
                  'uint16': (2, np.uint16),
                  'float32': (4, np.float32)}
    if dtype not in dtype_info:
        print(f"Error: Unsupported data type: {dtype}")
        sys.exit(1)
    bytes_per_pixel, np_dtype = dtype_info[dtype]
    slice_size = width * height * bytes_per_pixel

    os.makedirs(output_root, exist_ok=True)

    # Find ML_distance directories (e.g., "20cm", "40cm", etc.) in the input root.
    ml_distances = [d for d in os.listdir(input_root)
                    if os.path.isdir(os.path.join(input_root, d)) and 'cm' in d.lower()]
    if not ml_distances:
        print("Error: No ML_distance directories found in the input root.")
        sys.exit(1)

    print(f"Found ML_distance directories: {ml_distances}\n")

    # Process each ML folder separately.
    for ml_distance in ml_distances:
        ml_dir = os.path.join(input_root, ml_distance)
        print(f"Processing ML directory: {ml_distance}")

        # Instead of a single list we now group based on the CC distance.
        # The dictionary key is the CC value, and each value is a list of tuples (z_value, file_path).
        stacks_dict = {}

        # Use the new recursive file search function to find all files matching the patterns.
        found_files = find_files_in_directory(ml_dir, patterns)
        for file_path in found_files:
            # Only process files ending with '_0002.raw'
            if not file_path.endswith('_0002.raw'):
                continue
            info = extract_file_info(file_path)
            if info is None:
                print(f"Skipping file (could not extract ML/CC/Z): {file_path}")
                continue
            ml_val, cc_val, z_val = info
            # Optionally you might verify that ml_val matches ml_distance, if desired.
            if cc_val not in stacks_dict:
                stacks_dict[cc_val] = []
            stacks_dict[cc_val].append((z_val, file_path))

        if not stacks_dict:
            print(f"Warning: No valid files found in ML folder: {ml_distance}")
            continue

        # Process each CC group within the current ML folder.
        for cc_val, file_list in stacks_dict.items():
            # Sort files by the Z value.
            file_list.sort(key=lambda x: x[0])
            print(f"\nBuilding stack for ML[{ml_distance}] and CC[{cc_val}] with {len(file_list)} slices (sorted by Z)")

            stack_primary_and_scatter = []
            stack_primary = []
            stack_scatter = []

            for idx, (z_val, file_path) in enumerate(tqdm(file_list, desc=f"ML[{ml_distance}]_CC[{cc_val}]")):
                arr_slice1, arr_slice2, arr_scatter = process_raw_file(file_path, slice_size, np_dtype, width, height)
                if arr_slice1 is not None:
                    stack_primary_and_scatter.append(arr_slice1)
                    stack_primary.append(arr_slice2)
                    stack_scatter.append(arr_scatter)
                    print(f"Processed slice {idx+1}/{len(file_list)} (Z={z_val}) from: {file_path}")
                else:
                    print(f"Failed to process: {file_path}")

            if stack_primary_and_scatter:
                stack_ps = np.stack(stack_primary_and_scatter)
                stack_p  = np.stack(stack_primary)
                stack_sc = np.stack(stack_scatter)

                # Output filenames include ML and CC information.
                out_prefix = f"ML[{ml_distance}]_CC[{cc_val}]"
                out_file_ps = os.path.join(output_root, f"{out_prefix}_Primary_plus_Scatter_Stack.raw")
                out_file_p  = os.path.join(output_root, f"{out_prefix}_Primary_Stack.raw")
                out_file_sc = os.path.join(output_root, f"{out_prefix}_Scatter_Stack.raw")

                try:
                    stack_ps.tofile(out_file_ps)
                    stack_p.tofile(out_file_p)
                    stack_sc.tofile(out_file_sc)
                    print(f"Saved stacks for ML[{ml_distance}] CC[{cc_val}]:")
                    print(f"  Primary+Scatter: {stack_ps.shape}")
                    print(f"  Primary:         {stack_p.shape}")
                    print(f"  Scatter:         {stack_sc.shape}")
                except Exception as e:
                    print(f"Error saving stacks for ML[{ml_distance}] CC[{cc_val}]: {str(e)}")
            else:
                print(f"No valid slices for ML[{ml_distance}] CC[{cc_val}]")

        print(f"\nCompleted processing for ML folder: {ml_distance}\n{'-'*60}")

    print("All ML and CC distances have been processed successfully.")


if __name__ == "__main__":
    main()
