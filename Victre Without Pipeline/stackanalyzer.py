# import numpy as np
import cupy as np   # Now you dont have to change anything but this comment
from scipy import ndimage
import pandas as pd
from pathlib import Path
import argparse


################################################################
###################### EXAMPLE USAGE  ##########################
# python3 /pathtoscript/stackanalyzer.py /path/to/stack --output '/path/to/output/Mag_5x5_1p9cm.csv'


class SignalROIAnalyzer:
    def __init__(self, roi_size=(20, 20)): # ROI is 1cm x 1cm
        self.roi_size = roi_size

    # So we know the image is centered in x because we did so in the in file
    # Find where the signal is max for scatter only and min for Primary and Primary + Scatter
    # Remember an image is formed by absorbed X-rays so where the image is clear
    # it means those x-rays were absorbed and vice versa
    def find_signal_region(self, image, filename):
        """Find the center of the signal region based on slice height and stack type"""
        x_center = 1795  # Fixed center in X

        # Debug section 1: Image stats
        print(f"\n=== Processing {filename} ===")
        print(f"Image shape: {image.shape}")
        print(f"Image value range: {np.min(image):.2f} to {np.max(image):.2f}")

        # Get slice number from slice info in filename or data
        # Slice height mapping: 1=5cm, 2=10cm, 3=15cm, 4=20cm, 5=25cm, 6=30cm

        # Use intensity profile to center in Y direction
        window_size = 10  # Might need to adjust based on spread
        y_profile = image[:, x_center-window_size:x_center+window_size].mean(axis=1)

        print(f"\nProfile Analysis:")
        print(f"Y profile length: {len(y_profile)}")
        print(f"Y profile range: {np.min(y_profile):.2f} to {np.max(y_profile):.2f}")

        if filename == "Scatter_Stack.raw":
            # Scatter maintains its peak characteristic across heights
            y_center = np.argmax(y_profile)
            print(f"Scatter stack: finding maximum signal at y={y_center}")
        else:
            # For Primary and Primary+Scatter:
            min_val = np.min(y_profile)
            max_val = np.max(y_profile)
            value_range = max_val - min_val

            print(f"\nSignal Detection Values:")
            print(f"Min value: {min_val:.2f}")
            print(f"Max value: {max_val:.2f}")
            print(f"Value range: {value_range:.2f}")

            # More lenient threshold for higher slices
            if "slice" in locals():  # If we got slice info
                print(f"Processing slice at height: {slice_height}cm")
                if slice_height > 20:  # Slices 5-6
                    threshold = min_val + (value_range * 0.8)
                    print("Using lenient threshold (80% of range)")
                else:  # Slices 1-4
                    threshold = min_val + (value_range * 0.4)
                    print("Using strict threshold (40% of range)")
            else:
                # Default if we don't have slice info
                threshold = min_val + (value_range * 0.6)
                print("Using default threshold (60% of range)")

            print(f"Threshold value: {threshold:.2f}")

            low_signal_region = y_profile < threshold
            low_signal_indices = np.where(low_signal_region)[0]

            if len(low_signal_indices) == 0:
                print("No signal region found!")
                return None

            y_start = low_signal_indices[0]
            y_end = low_signal_indices[-1]
            y_center = (y_start + y_end) // 2

            print(f"\nSignal Region Found:")
            print(f"Y range: {y_start} to {y_end}")
            print(f"Y center: {y_center}")
            print(f"Region size: {y_end - y_start} pixels")

        return (y_center, x_center)

    def place_roi_at_center(self, center, image_shape):
        """Create ROI coordinates centered at given point"""
        if center is None:
            return None

        y, x = center
        half_height, half_width = np.array(self.roi_size) // 2

        # Calculate ROI boundaries
        roi_bounds = {
            'top': max(0, int(y - half_height)),
            'bottom': min(image_shape[0], int(y + half_height)),
            'left': max(0, int(x - half_width)),
            'right': min(image_shape[1], int(x + half_width))
        }

        return roi_bounds

    def measure_roi(self, image, roi_bounds):
        """Measure statistics within ROI"""
        if roi_bounds is None:
            return {
                'Mean': np.nan,
                'StdDev': np.nan,
                'Min': np.nan,
                'Max': np.nan,
                'Signal_Found': False
            }

        roi_region = image[
            roi_bounds['top']:roi_bounds['bottom'],
            roi_bounds['left']:roi_bounds['right']
        ]

        return {
            'Mean': np.mean(roi_region),
            'StdDev': np.std(roi_region),
            'Min': np.min(roi_region),
            'Max': np.max(roi_region),
            'Signal_Found': True,
            'ROI_Top': roi_bounds['top'],
            'ROI_Bottom': roi_bounds['bottom'],
            'ROI_Left': roi_bounds['left'],
            'ROI_Right': roi_bounds['right']
        }

    def process_stack(self, stack_path):
        """Process a single stack"""
        try:
            # Read raw file with your specific dimensions
            raw_data = np.fromfile(str(stack_path), dtype=np.float32)

            # Add diagnostic info about raw data
            total_pixels = len(raw_data)
            num_pixels_per_slice = 3584 * 2816
            num_slices = total_pixels // num_pixels_per_slice

            print(f"\nStack Diagnostics for {Path(stack_path).name}:")
            print(f"Total pixels in file: {total_pixels}")
            print(f"Pixels per slice: {num_pixels_per_slice}")
            print(f"Number of complete slices: {num_slices}")
            print(f"Remainder pixels: {total_pixels % num_pixels_per_slice}")

            if total_pixels % num_pixels_per_slice != 0:
                print("WARNING: Raw data size is not an exact multiple of slice size!")

            # Reshape the stack to (slices, height, width)
            stack = raw_data.reshape(num_slices, 2816, 3584)

            results = []
            filename = Path(stack_path).name

            for i in range(num_slices):
                slice_data = stack[i]

                # Add per-slice diagnostic info
                print(f"\nSlice {i+1} shape: {slice_data.shape}")
                print(f"Slice {i+1} value range: {np.min(slice_data):.2f} to {np.max(slice_data):.2f}")

                center = self.find_signal_region(slice_data, filename)
                roi_bounds = self.place_roi_at_center(center, slice_data.shape)
                measurements = self.measure_roi(slice_data, roi_bounds)

                results.append({
                                    'Stack': filename,
                                    'Height_Above_Detector_cm': i * 5,  # Each slice is 5cm increment
                                    'Slice': i + 1,
                                    'Center_Y': center[0] if center is not None else np.nan,
                                    'Center_X': center[1] if center is not None else np.nan,
                                    **measurements
                                })

            return pd.DataFrame(results)
        except Exception as e:
            print(f"Error processing {stack_path}: {str(e)}")
            return pd.DataFrame()

def process_stacks(stack_paths, roi_size=(50, 50)):
    """Process stacks sequentially"""
    analyzer = SignalROIAnalyzer(roi_size)
    all_results = []

    for stack_path in stack_paths:
        print(f"Processing {stack_path}")
        results = analyzer.process_stack(stack_path)
        if not results.empty:
            all_results.append(results)
        else:
            print(f"Failed to process {stack_path}")

    if not all_results:
        print("No results were generated")
        return pd.DataFrame()

    try:
        combined_results = pd.concat(all_results, ignore_index=True)
        print(f"Successfully combined results from all stacks")
        return combined_results
    except Exception as e:
        print(f"Error combining results {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Take arguments
    parser = argparse.ArgumentParser(description='Process raw image stacks')
    parser.add_argument('input_directory', type=str, help='Directory containing raw stack files')
    parser.add_argument('--pattern', type=str, default='*.raw',
                       help='Pattern to match stack files (default: *.raw)')
    parser.add_argument('--output', type=str, default='analysis_results.csv',
                       help='Output CSV file name (default: analysis_results.csv)')
    parser.add_argument('--roi-size', type=int, nargs=2, default=[20, 20],
                       help='ROI size as height width (default: 20 20)')  # 1cm x 1cm

    # parse them
    args = parser.parse_args()

    # check for the output directories
    data_dir = Path(args.input_directory)
    if not data_dir.exists():
        print(f"Directory {data_dir} does not exist")
        exit(1)

    stack_paths = list(data_dir.glob(args.pattern))
    if not stack_paths:
        print(f"No files matching {args.pattern} found in {data_dir}")
        exit(1)

    print(f"Found {len(stack_paths)} stack files")
    print(f"Files to process: {[p.name for p in stack_paths]}")

    try:
        results = process_stacks(stack_paths, tuple(args.roi_size))
        if results.empty:
            print("No results were generated")
        else:
            print(f"Processed {len(results)} total slices")
            results.to_csv(args.output, index=False)
            print(f"Results saved to {args.output}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
