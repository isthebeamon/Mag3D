import glob
import os
import re
from Victre import Pipeline
from Victre import Constants
from Victre.Constants import PHANTOM_MATERIALS
from Victre import Lesions
from Victre.Victre_Tools import read_raw_file, extract_phantom_value, random_number_generator
import subprocess

def run_stack_sort():
    # Define the parameters
    input_root = "./results/Lucite/Mag_W_Lesions/Main"  # Adjust this path to match your results directory
    output_root = "./results/Lucite/Mag_W_Lesions/Stacks"  # Where you want the stacked images to be saved
    width = 3584  # Match your image_pixels[0] from MC-GPU settings
    height = 2816  # Match your image_pixels[1] from MC-GPU settings
    dtype = "float32"  # The data type of your raw files
    # Pattern matching specific filename format
    pattern = "BlockPhantom_PA*cm_ML*cm_CC*cm_PA*vx_ML*vx_CC*vx_VxlRes*mm_Material*_Z*_0002.raw"

    # Construct the command
    cmd = [
        "python",
        "./Tools/StackSort2.py",
        input_root,
        output_root,
        "--width", str(width),
        "--height", str(height),
        "--dtype", dtype,
        "--patterns", pattern
    ]

    try:
        print("Starting stack sorting...")
        result = subprocess.run(cmd, check=True)
        print("Stack sorting completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running StackSort2.py: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":

    max_z = int(input("Enter the maximum Z value for the simulations: "))
    z_interval = int(input("Enter the Z interval for the simulations: "))
    # Get the absolute path of the current working directory
    base_dir = os.getcwd()

    # Check how many size phantoms we have by counting the number of directories in the phantom folder
    ML_sizes = os.listdir("./phantoms/Lucite/Lesions")
    print(ML_sizes)
    for ML in ML_sizes:
        raw_files = glob.glob(os.path.join("./phantoms/Lucite/Lesions", ML, "*.raw.gz"))
        print(f"Found {len(raw_files)} raw files in {ML}")

        if len(raw_files) == 0:
            print("No raw files found! Check the path and file pattern.")
            continue

        phantom_files = []
        for raw_file in raw_files:
            cc, ml, pa = extract_phantom_value(raw_file)
            phantom_files.append((cc, ml, pa, raw_file))

        phantom_files.sort(key=lambda x: x[0])

        for cc, ml, pa, raw_file in phantom_files:
            for z in range(5, max_z+1, z_interval):
                filename = os.path.basename(raw_file)
                try:
                    new_seed = random_number_generator()
                except Exception as seed_e:
                    print(f"Skipping phantom {filename} due to seed generation error: {seed_e}")
                    continue
                try:
                    # Reset working directory at start of each phantom
                    os.chdir(base_dir)

                    print(f"Processing phantom: {filename} as ML[{ML}] x CC[{cc}] at Z = {z}")

                    results_dir = f"./results/Lucite/Mag_W_Lesions/Main/{ML}/{int(cc)}"
                    os.makedirs(results_dir, exist_ok=True)
                    os.makedirs(f"{results_dir}/{new_seed}", exist_ok=True)

                    new_output_file = os.path.basename(raw_file)
                    z_suffix = f"_Z[{z}]"  # creates "_Z[0]"
                    new_output_file = new_output_file.replace(".raw.gz", z_suffix)
                    new_output_file = f"{results_dir}/{new_seed}/{new_output_file}"

                    n_voxels_pa = int(pa / 0.05)
                    n_voxels_ml = int(ml / 0.05)
                    n_voxels_cc = int(cc / 0.05)

                    # Create pipeline directly in the loop
                    pline = Pipeline(
                        seed=new_seed,
                        results_folder=results_dir,
                        phantom_file=f"./phantoms/Lucite/Lesions/{ML}/{filename}",
                        lesion_file=None,
                        arguments_mcgpu={
                            "number_histories": int((5.51e10) * (2.718281828459045 ** (0.4758 * (cc - 2)))),
                            "selected_gpu": 0,
                            "number_gpus": 1,
                            "gpu_threads": 128,
                            "histories_per_thread": 20433,
                            "source_position": [0.00001, ml / 2, 73.80141],
                            "source_direction": [0.0, 0.0, -1.0],
                            "fam_beam_aperture": [-15.0, 11.203],
                            "euler_angles": [90.0, -90.0, 180.0],
                            "focal_spot": 0.0300,
                            "angular_blur": 0.18,
                            "collimate_beam": "YES",
                            "output_file": new_output_file,
                            "image_pixels": [3584, 2816],
                            "image_size": [30.464, 23.936],
                            "distance_source": 76.24441,
                            "image_offset": [0, 0],
                            "detector_thickness": 0.02,
                            "mean_free_path": 0.004027,
                            "k_edge_energy": [12658.0, 11223.0, 0.596, 0.00593],
                            "detector_gain": [50.0, 0.99],
                            "additive_noise": 5200.0,
                            "cover_thickness": [0.10, 1.9616],
                            "antiscatter_grid_ratio": [0, 0, 0],
                            "antiscatter_strips": [0.00089945, 1.9616],
                            "antiscatter_grid_lines": 0,
                            "number_projections": 2,
                            "rotation_axis_distance": 73.80141,
                            "projections_angle": 5.0,
                            "angular_rotation_first": -5.0,
                            "rotation_axis": [1.0, 0.0, 0.0],
                            "axis_translation": 0,
                            "detector_fixed": "YES",
                            "simulate_both": "NO",
                            "tally_material_dose": "YES",
                            "tally_voxel_dose": "NO",
                            "output_dose_filename": "mc-gpu_dose.dat",
                            "voxel_geometry_offset": [0, 0, z],
                            "number_voxels": [n_voxels_pa, n_voxels_ml, n_voxels_cc],
                            "voxel_size": [0.05, 0.05, 0.05],
                            "low_resolution_voxel_size": [0, 0, 0]
                        },
                        materials = [
                            {"material": "./Victre/projection/material/Air_dry_near_s__5-120keV.mcgpu.gz",
                            "density": 0.0012,
                            "voxel_id": [PHANTOM_MATERIALS["air"]]
                            },
                            {"material": "./Victre/projection/material/adipose__5-120keV.mcgpu.gz",
                            "density": 0.92,
                            "voxel_id": [PHANTOM_MATERIALS["adipose"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.1543,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite_lower_density"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": 1.190,
                            "voxel_id": [PHANTOM_MATERIALS["Lucite"]]
                            },
                            {"material": "./Victre/projection/material/Polymethyl_met__5-120keV.mcgpu.gz",
                            "density": (0.95 * 1.190),
                            "voxel_id": [PHANTOM_MATERIALS["Lucite_lower_density"]]
                            }
                        ]
                    )

                    print("MC-GPU arguments:")
                    for param, value in pline.arguments_mcgpu.items():
                        print(f"  {param}: {value}")

                    try:
                        pline.project()
                        pline.reconstruct()
                        pline.save_DICOM("dbt")
                        pline.save_DICOM("DM")
                    except Exception as e:
                        print(f"Error during pipeline execution: {str(e)}")
                        print(f"Continuing with next phantom...")
                        continue
                # Catch any exceptions that occur during the processing of the phantom
                except Exception as e:
                    print(f"Error processing phantom {filename}: {str(e)}")
                    continue
            print(f"Completed all Z values for ML[{ML}] CC[{cc}]")  # After Z loop
        print(f"Completed all simulations for ML group: {ML}")  # After CC loop
    print("All phantoms completed successfully.")

    # Run the stack sorting
    run_stack_sort()
