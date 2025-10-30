import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
# DO NOT import AppLogic here. It's given to __init__ by main.py

class ApplicationGUI:
    """The main graphical user interface for the Battery Manager."""

    def __init__(self, root, app_logic):
        self.root = root
        self.logic = app_logic # The logic object is passed in
        self.root.title("Linux Battery Manager")
        self.root.geometry("800x500") # Increased height for USB list
        self.root.resizable(True, True)

        style = ttk.Style(self.root)
        style.theme_use('clam')

        # --- Create Frames ---
        # We create all frames first
        hardware_frame = ttk.LabelFrame(self.root, text="Hardware Controls", padding=(20, 10))
        usb_frame = ttk.LabelFrame(self.root, text="USB Device Power Management", padding=(20, 10))
        # usb_frame = ttk.LabelFrame(self.root, text="USB Device Power Management", padding=(20, 10))
        profile_frame = ttk.LabelFrame(self.root, text="Settings Profiles", padding=(20, 10))

        # --- Pack Frames in Order ---
        hardware_frame.pack(padx=10, pady=10, fill="x")
        usb_frame.pack(padx=10, pady=10, fill="x")
        profile_frame.pack(padx=10, pady=10, fill="x")

        # --- Populate Frames ---
        self.usb_devices = []
        self.usb_vars = []
        self._create_hardware_controls(hardware_frame)
        self._create_usb_controls(usb_frame)
        self._create_profile_controls(profile_frame)
    
    def _create_profile_controls(self, parent_frame):
        # ... (This function is unchanged) ...
        """Creates and populates the widgets for saving and loading profiles."""
        ttk.Label(parent_frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.profile_name_entry = ttk.Entry(parent_frame)
        self.profile_name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        save_button = ttk.Button(parent_frame, text="Save Current Settings", command=self._save_profile)
        save_button.grid(row=0, column=2, padx=5)
        
        ttk.Label(parent_frame, text="Load Profile:").grid(row=1, column=0, sticky="w", pady=15)
        
        self.profiles = self.logic.get_all_profiles()
        profile_names = list(self.profiles.keys())
        if not profile_names:
            profile_names = ["No profiles found"]

        self.selected_profile = tk.StringVar(value=profile_names[0])
        
        self.profile_dropdown = ttk.OptionMenu(parent_frame, self.selected_profile, profile_names[0], *profile_names)
        self.profile_dropdown.grid(row=1, column=1, sticky="ew", padx=5)

        load_button = ttk.Button(parent_frame, text="Load Selected", command=self._load_profile)
        load_button.grid(row=1, column=2, padx=5)

        parent_frame.columnconfigure(1, weight=1)
    
    def _save_profile(self):
        """Saves the current slider values to a profile and updates the profile dropdown."""
        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            messagebox.showwarning("Input Error", "Please enter a name for the profile.")
            return

        current_brightness = int(self.brightness_slider.get())
        current_fan_speed = int(self.fan_slider.get())
        settings = [current_brightness, current_fan_speed]

        self.logic.save_settings_to_profile(profile_name, settings)

        # Refresh the profiles list from logic
        self.profiles = self.logic.get_all_profiles()
        profile_names = list(self.profiles.keys())
        if not profile_names:
            profile_names = ["No profiles found"]

        # Update the OptionMenu's menu
        menu = self.profile_dropdown["menu"]
        menu.delete(0, "end")
        for name in profile_names:
            menu.add_command(label=name, command=tk._setit(self.selected_profile, name))

        # Select the newly saved profile in the dropdown
        self.selected_profile.set(profile_name)

        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")

    def _load_profile(self):
        # ... (This function is unchanged) ...
        """Loads a profile and applies its settings to the GUI and hardware."""
        profile_name = self.selected_profile.get()
        settings = self.profiles.get(profile_name)

        if not settings:
            messagebox.showerror("Error", f"Could not load settings for profile '{profile_name}'.")
            return

        brightness, fan_speed = settings

        self.brightness_slider.set(brightness)
        self.fan_slider.set(fan_speed)
        self.logic.set_brightness(brightness)
        
        messagebox.showinfo("Success", f"Profile '{profile_name}' loaded and applied.")

    def _create_hardware_controls(self, parent_frame):
        """Creates the sliders and buttons for hardware control."""
        ttk.Label(parent_frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        
        # --- THIS IS THE KEY CHANGE ---
        # Get the current brightness from the logic and set the slider
        try:
            current_brightness = self.logic.get_brightness()
            if current_brightness is not None:
                self.brightness_slider.set(current_brightness)
            else:
                self.brightness_slider.set(80) # Fallback
        except Exception as e:
            print(f"GUI Error: Could not get brightness: {e}")
            self.brightness_slider.set(80) # Fallback
        
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(parent_frame, text="Fan Speed:").grid(row=1, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_fan_change)
        self.fan_slider.set(50)
        self.fan_slider.grid(row=1, column=1, sticky="ew", padx=5)

        parent_frame.columnconfigure(1, weight=1)

    def _on_brightness_change(self, value):
        # ... (This function is unchanged) ...
        brightness_value = int(float(value))
        self.logic.set_brightness(brightness_value)

    def _on_fan_change(self, value):
        # ... (This function is unchanged) ...
        print(f"UI Event: Fan speed slider changed to {float(value):.0f}%")
    
    def _create_usb_controls(self, parent_frame):
        # ... (This function is unchanged) ...
        """Creates checkboxes for each connected USB device."""
        self.usb_devices = self.logic.get_usb_devices()

        if not self.usb_devices:
            ttk.Label(parent_frame, text="No controllable USB devices found.").pack()
            return

        for i, device in enumerate(self.usb_devices):
            var = tk.BooleanVar()
            label = f"{device['name']} (Hub {device['location']}, Port {device['port']})"
            cb = ttk.Checkbutton(parent_frame, text=label, variable=var)
            cb.pack(anchor="w", padx=10)
            self.usb_vars.append((var, device))

        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(pady=10, fill="x", expand=True)
        
        suspend_button = ttk.Button(button_frame, text="Suspend Selected", command=self._suspend_selected_usb)
        suspend_button.pack(side="left", expand=True, padx=5)
        
        resume_button = ttk.Button(button_frame, text="Resume Selected", command=self._resume_selected_usb)
        resume_button.pack(side="left", expand=True, padx=5)
    
    def _suspend_selected_usb(self):
        # ... (This function is unchanged) ...
        suspended_count = 0
        for var, device in self.usb_vars:
            if var.get(): # If checkbox is ticked
                self.logic.suspend_usb_device(device['location'], device['port'])
                suspended_count += 1
        
        if suspended_count > 0:
            self.logic.send_notification("USB Devices Suspended", f"{suspended_count} device(s) were suspended.")
        else:
            messagebox.showinfo("No Selection", "No USB devices were selected.")
    
    def _resume_selected_usb(self):
        # ... (This function is unchanged) ...
        resumed_count = 0
        for var, device in self.usb_vars:
            if var.get():
                self.logic.resume__usb_device(device['location'], device['port'])
                resumed_count += 1
        
        if resumed_count > 0:
            self.logic.send_notification("USB Devices Resumed", f"{resumed_count} device(s) were resumed.")
        else:
            messagebox.showinfo("No Selection", "No USB devices were selected.")

    def run(self):
        """Starts the Tkinter event loop."""
        self.root.mainloop()

# This if __name__ == "__main__": block is removed
# This file should only be imported by main.py