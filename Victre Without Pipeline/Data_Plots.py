import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import cupy as np

##########################################################################
################# EXAMPLE USAGE ###########################################
# python3 path/to/script.py /path/to/csv/files --output /path/to/output

# Global plot parameters
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 24,
    'axes.titlesize': 32,
    'axes.labelsize': 28,
    'xtick.labelsize': 24,
    'ytick.labelsize': 24,
    'legend.fontsize': 24,
    'figure.titlesize': 34,
    'lines.markersize': 20,
    'figure.subplot.right': 0.95,
    'figure.subplot.left': 0.15,
    'figure.subplot.top': 0.95,
    'figure.subplot.bottom': 0.15,
})

def ensure_directory(path):
    """Ensure directory exists, creating it and all parent directories if necessary"""
    Path(path).mkdir(parents=True, exist_ok=True)

def plot_ml_sp_ratios(df, output_dir):
    """Create separate S/P ratio plots for each ML distance"""
    ensure_directory(output_dir)

    # For each ML distance
    for ml_size in sorted(df['PhantomSize'].unique()):
        plt.figure(figsize=(15, 10))
        ml_data = df[df['PhantomSize'] == ml_size]

        # For each phantom thickness at this ML distance
        for thickness in sorted(ml_data['Thickness'].unique()):
            thick_data = ml_data[ml_data['Thickness'] == thickness]

            # Get primary and scatter data
            primary_data = thick_data[thick_data['Stack'] == 'Primary_Stack.raw']
            scatter_data = thick_data[thick_data['Stack'] == 'Scatter_Stack.raw']

            # Calculate S/P ratio
            ratio_data = pd.merge(
                primary_data[['Height_Above_Detector_cm', 'Mean']],
                scatter_data[['Height_Above_Detector_cm', 'Mean']],
                on='Height_Above_Detector_cm', suffixes=('_primary', '_scatter')
            )
            ratio_data['ratio'] = ratio_data['Mean_scatter'] / ratio_data['Mean_primary']

            # Plot this thickness's S/P ratio
            plt.plot(ratio_data['Height_Above_Detector_cm'],
                    ratio_data['ratio'],
                    'o-',
                    label=f'Thickness {thickness}cm',
                    markersize=12)

        plt.title(f'Scatter to Primary Ratio - ML Distance {ml_size}cm')
        plt.xlabel('Height Above Detector (cm)')
        plt.ylabel(r"$\frac{S}{P}$", fontsize=40)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=20, title="Phantom Thickness")

        plt.tight_layout()
        plt.savefig(Path(output_dir) / f'sp_ratio_ML{ml_size}cm.png', bbox_inches='tight', dpi=300)
        plt.close()

def plot_single_csv(df, output_dir, title_prefix=""):
    """Create individual plots for each dataset"""
    # Create separate folder for different plot types
    primary_scatter_dir = Path(output_dir) / "primary_scatter_plots"
    sp_ratio_dir = Path(output_dir) / "sp_ratio_plots"
    ensure_directory(primary_scatter_dir)
    ensure_directory(sp_ratio_dir)

    # Plot primary and scatter signals
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(25, 30))

    primary_data = df[df['Stack'] == 'Primary_Stack.raw']
    scatter_data = df[df['Stack'] == 'Scatter_Stack.raw']

    ax1.plot(primary_data['Height_Above_Detector_cm'], primary_data['Mean'], 'o-', label='Primary')
    ax1.set_title('Primary')
    ax1.set_xlabel('Height Above Detector (cm)')
    ax1.set_ylabel('Mean Signal')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(scatter_data['Height_Above_Detector_cm'], scatter_data['Mean'], 'o-', label='Scatter')
    ax2.set_title('Scatter')
    ax2.set_xlabel('Height Above Detector (cm)')
    ax2.set_ylabel('Mean Signal')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Calculate and plot S/P ratio
    ratio_data = pd.merge(
        primary_data[['Height_Above_Detector_cm', 'Mean']],
        scatter_data[['Height_Above_Detector_cm', 'Mean']],
        on='Height_Above_Detector_cm', suffixes=('_primary', '_scatter')
    )
    ratio_data['ratio'] = ratio_data['Mean_scatter'] / ratio_data['Mean_primary']

    ax3.plot(ratio_data['Height_Above_Detector_cm'], ratio_data['ratio'], 'o-', label=r"$\frac{S}{P}$")
    ax3.set_title('Scatter to Primary Ratio')
    ax3.set_xlabel('Height Above Detector (cm)')
    ax3.set_ylabel(r"$\frac{S}{P}$", fontsize=40)
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()
    plt.savefig(primary_scatter_dir / f'{title_prefix}_analysis.png')
    plt.close()

def load_and_assign_sizes(csv_dir):
    dfs = []
    csvs = list(Path(csv_dir).glob('*.csv'))

    for csv in csvs:
        df = pd.read_csv(csv)
        name_parts = csv.stem.split('_')
        ML_dist = int(name_parts[1].split('x')[0])
        cc_dist = int(name_parts[2].replace('cm',''))
        df['PhantomSize'] = ML_dist
        df['Thickness'] = cc_dist
        df['SourceFile'] = csv.stem
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def plot_all_data(df, output_dir='plots'):
    output_dir = Path(output_dir)
    ensure_directory(output_dir)

    # Create individual plots for each dataset
    for source_file in df['SourceFile'].unique():
        single_file_data = df[df['SourceFile'] == source_file]
        plot_single_csv(
            single_file_data,
            output_dir,
            title_prefix=source_file
        )

    # Create ML-specific S/P ratio plots
    plot_ml_sp_ratios(df, output_dir)

    # Save processed data
    df.to_csv(output_dir / 'all_data.csv', index=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_dir', help='Directory containing CSV files')
    parser.add_argument('--output', default='plots', help='Output directory for plots')
    args = parser.parse_args()

    # Verify input directory exists
    if not Path(args.csv_dir).exists():
        print(f"Error: Input directory '{args.csv_dir}' does not exist")
        exit(1)

    df = load_and_assign_sizes(args.csv_dir)
    plot_all_data(df, args.output)
