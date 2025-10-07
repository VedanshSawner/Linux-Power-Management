import tkinter as tk
from tkinter import ttk # For a modern look and feel
from tkinter import messagebox

class ApplicationGUI:
    """The main graphical user interface for the Battery Manager."""

    def __init__(self, root, app_logic):
        """Initializes the GUI components."""
        self.root = root
        self.logic = app_logic # Store the logic controller
        self.root.title("Linux Battery Manager")
        self.root.geometry("400x450")
        self.root.resizable(False, False)

        # Use a modern theme
        style = ttk.Style(self.root)
        style.theme_use('clam')

        # --- Main Frames ---
        hardware_frame = ttk.LabelFrame(self.root, text="Hardware Controls", padding=(20, 10))
        hardware_frame.pack(padx=10, pady=10, fill="x", expand=True)
        profile_frame = ttk.LabelFrame(self.root, text="Settings Profiles", padding=(20, 10))
        profile_frame.pack(padx=10, pady=10, fill="x", expand=True)

        # --- Create Widgets ---
        self._create_hardware_controls(hardware_frame)
        self._create_profile_controls(profile_frame)

    def _create_hardware_controls(self, parent_frame):
        """Creates the sliders and buttons for hardware control."""
        ttk.Label(parent_frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        self.brightness_slider.set(50)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(parent_frame, text="Fan Speed:").grid(row=1, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_fan_change)
        self.fan_slider.set(50)
        self.fan_slider.grid(row=1, column=1, sticky="ew", padx=5)

        parent_frame.columnconfigure(1, weight=1)

        self.webcam_button = ttk.Button(parent_frame, text="Disable Webcam", command=self._toggle_webcam)
        self.webcam_button.grid(row=2, column=0, columnspan=2, pady=15)
        
    def _create_profile_controls(self, parent_frame):
        """Creates the widgets for saving and loading profiles."""
        ttk.Label(parent_frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.profile_name_entry = ttk.Entry(parent_frame)
        self.profile_name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        save_button = ttk.Button(parent_frame, text="Save Current Settings", command=self._save_profile)
        save_button.grid(row=0, column=2, padx=5)
        
        ttk.Label(parent_frame, text="Load Profile:").grid(row=1, column=0, sticky="w", pady=15)
        profile_options = ["Power Saver", "Balanced", "Performance"]
        self.selected_profile = tk.StringVar(value=profile_options[1])
        self.profile_dropdown = ttk.OptionMenu(parent_frame, self.selected_profile, *profile_options)
        self.profile_dropdown.grid(row=1, column=1, sticky="ew", padx=5)
        load_button = ttk.Button(parent_frame, text="Load Selected", command=self._load_profile)
        load_button.grid(row=1, column=2, padx=5)

        parent_frame.columnconfigure(1, weight=1)

    def _on_brightness_change(self, value):

        # Convert the string value from the slider to an integer
        brightness_value = int(float(value))
        
        # Call the method on the logic object
        self.logic.set_brightness(brightness_value)

    def _on_fan_change(self, value):
        print(f"UI Event: Fan speed slider changed to {float(value):.0f}%")

    def _toggle_webcam(self):
        """
        This function is called when the webcam button is clicked.
        It calls the toggle_webcam method in the core logic.
        """
        current_text = self.webcam_button.cget("text")
        print(f"GUI: Webcam button clicked. Current state is '{current_text}'")

        # Call the logic controller to perform the action
        self.logic.toggle_webcam(current_text)

        # Update the button's text to reflect the new state
        new_text = "Enable Webcam" if "Disable" in current_text else "Disable Webcam"
        self.webcam_button.config(text=new_text)
        
    def _save_profile(self):
        profile_name = self.profile_name_entry.get()
        if not profile_name:
            messagebox.showwarning("Input Error", "Please enter a name for the profile.")
            return
        print(f"UI Event: Saving settings to profile '{profile_name}'")
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")

    def _load_profile(self):
        profile_name = self.selected_profile.get()
        print(f"UI Event: Loading settings from profile '{profile_name}'")
        messagebox.showinfo("Success", f"Profile '{profile_name}' loaded.")

    def run(self):
        """Starts the Tkinter event loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root_window = tk.Tk()
    app = ApplicationGUI(root_window)
    app.run()
