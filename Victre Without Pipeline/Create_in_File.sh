#!/bin/bash

# Define your variables
export Simulator="${Simulator:-"#"}"
export Histories="${Histories:-"5.5e10"}"
export Material="${Material:-"Lucite_Block"}"
export Size="${Size:-"20x20"}"
export Thickness="${Thickness:-"1p9cm"}"
export Phantom="${Phantom:-"BlockPhantom"}"
export Source="${Source:-10.0}"
export voxels=$(echo "$Source * 2 / 0.05" | bc -l)  # Dynamically calculate voxels
export voxels=${voxels%.*}  # Convert to integer
export zvoxels="${zvoxels:-37}"  # Fixed value
export ZDistance="${ZDistance:-0.0}"

# Generate JSON data with matching keys for the template
data=$(jq -n \
  --arg Simulator "$Simulator" \
  --arg Histories "$Histories" \
  --arg Material "$Material" \
  --arg Size "$Size" \
  --arg Thickness "$Thickness" \
  --arg Phantom "$Phantom" \
  --argjson Source "$Source" \
  --argjson voxels "$voxels" \
  --argjson zvoxels "$zvoxels" \
  --argjson ZDistance "$ZDistance" \
  '{Simulator: $Simulator, Histories: $Histories, Material: $Material, Size: $Size, Thickness: $Thickness, Phantom: $Phantom, Source: $Source, voxels: $voxels, zvoxels: $zvoxels, ZDistance: $ZDistance}')

# Debugging: Print the generated JSON to verify
echo "Generated JSON:"
echo "$data" | jq .

# Use tmpl to process the template and generate the output file
tmpl -data "$data" MC_GPU_in_File.tmpl > Simulation_Title.in

# Check if the file was generated successfully
if [ -s Simulation_Title.in ]; then
  echo "Generated Simulation_Title.in successfully!"
else
  echo "Output file is empty. Check template placeholders and JSON data."
fi