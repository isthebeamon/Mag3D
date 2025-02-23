# Alex's Amazing Phantom Maker (AAPM) v1.0
# A GUI to simplify the process of creating voxelized breast phantom anatomies for use in VICTRE-MCGPU
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import subprocess
import os
import tempfile
import threading


class ThemeManager:
    def __init__(self):
        self.themes = {
            "Light": {
                "bg": "#FFFFFF", "fg": "#000000", "button": "#E0E0E0", "font": ("Helvetica", 10),
                "ttk_theme": "vista"  # Adjust based on available themes
            },
            "Dark": {
                "bg": "#333333", "fg": "#CCCCCC", "button": "#555555", "font": ("Helvetica", 10, "bold"),
                "ttk_theme": "clam"  # Adjust based on available themes
            },
        }
        self.current_theme = "Light"
        self.style = ttk.Style()

    def apply_theme(self, theme_name, widget):
        theme = self.themes.get(theme_name, self.themes["Light"])
        self.current_theme = theme_name
        self.style.theme_use(theme["ttk_theme"])  # Set the ttk theme

        # Configure default styles for all ttk widgets
        self.style.configure('.', background=theme["bg"], foreground=theme["fg"], font=theme["font"])

        # If needed, configure specific ttk widgets more granularly here
        # Example: self.style.configure('TButton', background=theme["button_bg"])

        def apply(awidget):
            # Apply theme configurations to tkinter widgets
            if hasattr(awidget, 'config'):
                try:
                    awidget.config(background=theme["bg"])
                except tk.TclError:
                    pass  # Ignore widgets that do not support the 'background' option

                try:
                    awidget.config(foreground=theme["fg"])
                except tk.TclError:
                    pass  # Ignore widgets that do not support the 'foreground' option

                try:
                    if awidget.winfo_class() not in ['TScale', 'Scale']:
                        awidget.config(font=theme["font"])
                except tk.TclError:
                    pass  # Ignore widgets that do not support the 'font' option

            # Recursively apply theme to child widgets
            for child in awidget.winfo_children():
                apply(child)

        apply(widget)  # Start the recursive application of the theme


class ScriptRunnerApp:
    def __init__(self, master):
        self.master = master
        master.title("Alex's Amazing Phantom Maker v1.0")
        self.theme_manager = ThemeManager()

        # Initialize output_directory to None
        self.output_directory = None

        # Main frame
        self.main_frame = tk.Frame(master)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # self.main_frame.pack()

        # Script selection
        self.label = tk.Label(self.main_frame, text="Choose which phantom you want to make:")
        self.label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        # self.label.pack()

        self.script_var = tk.StringVar(master)
        self.script_var.set("Dance_phantom")  # Default script selection
        self.script_options = ["Dance_phantom", "Dance_phantom_ellipse", "MLO_phantom", "Defrise_generator",
                               "StarPattern_generator"]
        self.script_dropdown = tk.OptionMenu(self.main_frame, self.script_var, *self.script_options,
                                             command=lambda _: self.update_parameters())
        self.script_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        # Output directory selection
        self.directory_label = tk.Label(self.main_frame, text="Select a directory to save the output file:")
        self.directory_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.directory_button = tk.Button(self.main_frame, text="Browse", command=self.browse_directory)
        self.directory_button.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        # Define phantom uniformity selection dropdowns before calling update_parameters()
        self.uniformity_var = tk.StringVar(master)
        self.uniformity_var.set("Homogeneous")
        self.uniformity_options = {
            "Homogeneous": "'homogeneous'",
            "Heterogeneous": "'heterogeneous'"
        }
        self.uniformity_label = tk.Label(self.main_frame, text="Choose if phantom creates interior adipose/glandular "
                                                               "mix region homogeneously or heterogeneously:")
        self.uniformity_dropdown = tk.OptionMenu(self.main_frame, self.uniformity_var, *self.uniformity_options.keys())
        self.uniformity_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.uniformity_dropdown.grid(row=3, column=1, padx=10, pady=10, sticky="e")

        # Define material selection dropdowns before calling update_parameters()
        self.material_var = tk.StringVar(master)
        self.material_var.set("Adipose")
        self.material_options = {
            "Air": "intensity_air",
            "Adipose": "intensity_adip",
            "Glandular": "intensity_glan",
            "PMMA": "intensity_PMMA"
        }
        self.material_label = tk.Label(self.main_frame, text="Choose first material for Defrise generator:")
        self.material_dropdown = tk.OptionMenu(self.main_frame, self.material_var, *self.material_options.keys())

        self.material_var2 = tk.StringVar(master)
        self.material_var2.set("Glandular")
        self.material_label2 = tk.Label(self.main_frame, text="Choose second material for Defrise generator:")
        self.material_dropdown2 = tk.OptionMenu(self.main_frame, self.material_var2, *self.material_options.keys())

        # Material dropdown setup complete, now safe to invoke update_parameters
        self.material_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.material_dropdown.grid(row=4, column=1, padx=10, pady=10, sticky="e")
        self.material_label2.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.material_dropdown2.grid(row=5, column=1, padx=10, pady=10, sticky="e")

        # Parameters frame
        self.parameters_frame = tk.Frame(self.main_frame)
        self.parameters_frame.grid(row=6, column=0, padx=10, pady=10, columnspan=2)

        # Mapping of display names to script parameter names
        self.parameter_mapping = {
            "Voxel Size (cm)": "voxel_size",
            "Adipose Shield Thickness (cm)": "shield_cm",
            "PA Extent (cm)": "a_cm_max",
            "ML Extent (cm)": "b_cm_max",
            "Compressed Breast Thickness (cm)": "d_cm",
            "Thickness (cm)": "t_cm",
            "Compression Paddle Thickness (cm)": "paddle_thickness_cm",
            "Breast Support Thickness (cm)": "breast_support_cm",
            "Glandularity (%)": "glandularity",
            "Frequency (um^-1)": "frequency",
            "Major Radius (cm)": "r_maj_cm",
            "Minor Radius (cm)": "r_min_cm",
            "Angle of Individual Sector (deg)": "sector_angle",
            "Total Number of Sectors": "num_sectors"
        }

        # Script-specific parameters including their default values and mappings
        self.script_parameters = {
            "Dance_phantom": {
                "Voxel Size (cm)": "0.02",
                "Adipose Shield Thickness (cm)": "0.5",
                "PA Extent (cm)": "8.0",
                "ML Extent (cm)": "16.0",
                "Compressed Breast Thickness (cm)": "5.0",
                "Compression Paddle Thickness (cm)": "0.2",
                "Breast Support Thickness (cm)": "0.2",
                "Glandularity (%)": "50.0"
            },
            "Dance_phantom_ellipse": {
                "Voxel Size (cm)": "0.02",
                "Adipose Shield Thickness (cm)": "0.5",
                "PA Extent (cm)": "16.0",
                "ML Extent (cm)": "16.0",
                "Compressed Breast Thickness (cm)": "5.0",
                "Compression Paddle Thickness (cm)": "0.2",
                "Breast Support Thickness (cm)": "0.2",
                "Glandularity (%)": "50.0"
            },
            "MLO_phantom": {
                "Voxel Size (cm)": "0.02",
                "Adipose Shield Thickness (cm)": "0.5",
                "PA Extent (cm)": "8.0",
                "ML Extent (cm)": "16.0",
                "Compressed Breast Thickness (cm)": "5.0",
                "Compression Paddle Thickness (cm)": "0.2",
                "Breast Support Thickness (cm)": "0.2",
                "Glandularity (%)": "50.0"
            },
            "Defrise_generator": {
                "Voxel Size (cm)": "0.02",
                "PA Extent (cm)": "15.0",
                "ML Extent (cm)": "15.0",
                "Thickness (cm)": "8.0",
                "Frequency (um^-1)": "125"
            },
            "StarPattern_generator": {
                "Voxel Size (cm)": "0.02",
                "Major Radius (cm)": "5.0",
                "Minor Radius (cm)": "1.0",
                "Thickness (cm)": "0.1",
                "Angle of Individual Sector (deg)": "6",
                "Total Number of Sectors": "60"
            }
        }

        self.current_parameter_widgets = {}
        self.update_parameters()  # Initialize parameters for the default script

        # Theme selection
        self.theme_var = tk.StringVar(master)
        self.theme_var.set("Light")  # Default theme selection
        self.theme_options = ["Light", "Dark"]
        self.theme_label = tk.Label(self.main_frame, text="Theme:")
        self.theme_dropdown = tk.OptionMenu(self.main_frame, self.theme_var, *self.theme_options, command=self.apply_theme)
        self.theme_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.theme_dropdown.grid(row=7, column=1, padx=10, pady=10, sticky="e")

        # Checkbox for compression option
        self.compress_var = tk.StringVar()
        self.compress_checkbox = ttk.Checkbutton(self.main_frame, text="GZip file",
                                                 variable=self.compress_var, onvalue="'yes'", offvalue="'no'")
        self.compress_checkbox.grid(row=8, column=0, padx=10, pady=10, columnspan=2)

        # Checkbox for .vox file creation
        self.vox_var = tk.StringVar()
        self.vox_checkbox = ttk.Checkbutton(self.main_frame, text="Vox file",
                                            variable=self.vox_var, onvalue="'yes'", offvalue="'no'")
        self.vox_checkbox.grid(row=8, column=1, padx=10, pady=10, columnspan=2)

        # Run script button
        self.run_button = tk.Button(self.main_frame, text="Run Script", command=self.run_script)
        self.run_button.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    def apply_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name, self.master)  # Apply theme to the entire application

    def update_parameters(self):
        # Remember the previous visibility state of the uniformity dropdown
        previous_uniformity_visibility = self.uniformity_label.winfo_ismapped()

        # Clear existing parameters
        for widget in self.parameters_frame.winfo_children():
            widget.destroy()
        self.current_parameter_widgets.clear()

        # Dynamically create parameter entries based on the selected script
        selected_script = self.script_var.get()
        script_params = self.script_parameters.get(selected_script, {})
        for param, value in script_params.items():
            label = tk.Label(self.parameters_frame, text=f"{param}:")
            label.pack()
            entry_var = tk.StringVar(value=value)  # Use StringVar for easier data handling
            entry = tk.Entry(self.parameters_frame, textvariable=entry_var)
            entry.pack()
            # Store the variable associated with this entry for later use
            self.current_parameter_widgets[self.parameter_mapping[param]] = entry_var

        # Toggle material selection visibility
        self.toggle_material_selection_visibility()

        # Toggle uniformity selection visibility only for applicable scripts
        if selected_script in ["Dance_phantom", "Dance_phantom_ellipse", "MLO_phantom"]:
            self.uniformity_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            self.uniformity_dropdown.grid(row=3, column=1, padx=10, pady=10, sticky="e")
        else:
            self.uniformity_label.grid_forget()
            self.uniformity_dropdown.grid_forget()

        # Restore the previous visibility state of the uniformity dropdown if it was visible before
        if previous_uniformity_visibility and selected_script in ["Dance_phantom", "Dance_phantom_ellipse",
                                                                  "MLO_phantom"]:
            self.uniformity_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            self.uniformity_dropdown.grid(row=3, column=1, padx=10, pady=10, sticky="e")

    def toggle_material_selection_visibility(self):
        selected_script = self.script_var.get()
        if selected_script == "Defrise_generator":
            self.material_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
            self.material_dropdown.grid(row=4, column=1, padx=10, pady=10, sticky="e")
            self.material_label2.grid(row=5, column=0, padx=10, pady=10, sticky="w")
            self.material_dropdown2.grid(row=5, column=1, padx=10, pady=10, sticky="e")
        else:
            self.material_label.grid_forget()
            self.material_dropdown.grid_forget()
            self.material_label2.grid_forget()
            self.material_dropdown2.grid_forget()

    def browse_directory(self):
        self.output_directory = filedialog.askdirectory()
        # Update the directory label to reflect the selected directory
        self.directory_label.config(text="Output directory: " + self.output_directory)

    def run_script(self):
        # Disable the Run Script button to prevent multiple clicks
        self.run_button.config(state=tk.DISABLED)

        # Create a new thread to run the script in the background
        script_thread = threading.Thread(target=self.execute_script)
        script_thread.start()

    def execute_script(self):
        selected_script = self.script_var.get()
        script_path = f"./scripts/{selected_script}.py"

        if not os.path.isfile(script_path):
            print("Script file does not exist:", script_path)
            return

        with open(script_path, 'r') as file:
            script_content = file.read()

        if selected_script == "Defrise_generator":
            selected_material = self.material_var.get()
            selected_material2 = self.material_var2.get()
            script_content = script_content.replace("%MATERIAL%", self.material_options[selected_material])
            script_content = script_content.replace("%MATERIAL2%", self.material_options[selected_material2])
        if selected_script in ["Dance_phantom", "Dance_phantom_ellipse", "MLO_phantom"]:
            selected_uniformity = self.uniformity_var.get()
            script_content = script_content.replace("%UNIFORMITY%", self.uniformity_options[selected_uniformity])
        else:
            pass

        # Replace placeholders with parameter values
        for internal_param_name, entry_var in self.current_parameter_widgets.items():
            placeholder = f"%{internal_param_name.upper()}%"
            script_content = script_content.replace(placeholder, entry_var.get())

        compress_option = "'yes'" if self.compress_var.get() == "'yes'" else "'no'"
        script_content = script_content.replace("%COMPRESS_OPTION%", compress_option)

        vox_option = "'yes'" if self.vox_var.get() == "'yes'" else "'no'"
        script_content = script_content.replace("%VOX_OPTION%", vox_option)

        temp_script_path = tempfile.mktemp(suffix='.py')
        with open(temp_script_path, 'w') as temp_file:
            temp_file.write(script_content)

        output_directory = self.output_directory if self.output_directory else "."

        try:
            command = ["python", temp_script_path, output_directory]
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            # Open a new window to show script output
            output_window = tk.Toplevel(self.master)
            output_window.title("Script Output")

            # Use scrolled text widget to display output
            output_text = scrolledtext.ScrolledText(output_window, wrap=tk.WORD, width=80, height=20)
            output_text.pack()

            # Read output from the subprocess and insert it into the text widget
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                output_text.insert(tk.END, line)
                output_text.see(tk.END)  # Auto-scroll
                output_window.update_idletasks()  # Update the GUI to reflect changes

        except Exception as e:
            print(f"Error executing script: {e}")
        finally:
            os.remove(temp_script_path)
            # Schedule re-enabling of the Run Script button on the GUI thread
            self.master.after(0, lambda: self.run_button.config(state=tk.NORMAL))


# Create the main window
root = tk.Tk()
app = ScriptRunnerApp(root)

# Configure grid to fill entire window
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.mainloop()
