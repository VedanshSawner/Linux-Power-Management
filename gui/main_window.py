import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import os
import re
from typing import List, Dict, Any


# --- APPLICATION GUI CLASS ---
class ApplicationGUI:
    """
    Tkinter-based Graphical User Interface for the Linux Power Manager.
    It relies on an external AppLogic instance for all system interactions.
    """
    def __init__(self, root, app_logic):
        self.root = root
        self.logic = app_logic
        self.root.title("Linux Power Manager")
        self.root.geometry("450x800")
        self.root.resizable(True, True)

        # Set up a modern look and feel
        style = ttk.Style(self.root)
        style.theme_use('clam')

        # --- Create Top-Level Frames ---
        hw_frame = ttk.LabelFrame(self.root, text="Hardware Controls", padding=(20, 10))
        conn_frame = ttk.LabelFrame(self.root, text="Connectivity", padding=(20, 10))
        usb_frame = ttk.LabelFrame(self.root, text="USB Device Power", padding=(20, 10))
        upower_frame = ttk.LabelFrame(self.root, text="UPower Shutdown Config", padding=(20, 10)) # NEW FRAME
        profile_frame = ttk.LabelFrame(self.root, text="Settings Profiles", padding=(20, 10))

        # --- Pack Frames ---
        hw_frame.pack(padx=10, pady=10, fill="x")
        conn_frame.pack(padx=10, pady=10, fill="x")
        usb_frame.pack(padx=10, pady=10, fill="x")
        upower_frame.pack(padx=10, pady=10, fill="x") # PACK NEW FRAME
        profile_frame.pack(padx=10, pady=10, fill="x")

        # --- Populate Frames ---
        self._create_hardware_controls(hw_frame)
        self._create_connectivity_controls(conn_frame)
        self._create_usb_controls(usb_frame)
        self._create_upower_controls(upower_frame) # POPULATE NEW FRAME
        self._create_profile_controls(profile_frame)

        # Placeholder for save_profile compatibility
        self.keyboard_slider = ttk.Scale(self.root, from_=0, to=100, orient="horizontal")

        # --- Start Power Status Polling ---
        self.last_power_status = self.logic.get_power_status()
        self._check_power_loop()

    def _create_hardware_controls(self, parent_frame):
        """Creates controls for brightness, CPU governor, and fan speed (placeholder)."""
        
        # Screen Brightness Slider
        ttk.Label(parent_frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        self.brightness_slider.set(self.logic.get_brightness() or 80)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)

        # CPU Governor Dropdown
        ttk.Label(parent_frame, text="CPU Profile:").grid(row=2, column=0, sticky="w", pady=5)
        self.governor_options = ["powersave", "schedutil", "performance"]
        self.governor_var = tk.StringVar(value=self.logic.get_cpu_governor())
        gov_menu = ttk.OptionMenu(parent_frame, self.governor_var, self.governor_var.get(), 
                                 *self.governor_options, command=self._on_governor_change)
        gov_menu.grid(row=2, column=1, sticky="ew", padx=5)
            
        # Fan Speed (Placeholder)
        ttk.Label(parent_frame, text="Fan Speed (N/A):").grid(row=3, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal")
        self.fan_slider.set(50)
        self.fan_slider.state(['disabled']) # Disable fan slider as it's not implemented
        self.fan_slider.grid(row=3, column=1, sticky="ew", padx=5)

        parent_frame.columnconfigure(1, weight=1)

    def _create_connectivity_controls(self, parent_frame):
        """Creates checkbuttons for Wi-Fi and Bluetooth toggles."""
        
        # Wi-Fi Checkbutton
        self.wifi_var = tk.BooleanVar(value=self.logic.get_wifi_status())
        wifi_check = ttk.Checkbutton(parent_frame, text="Enable Wi-Fi", 
                                     variable=self.wifi_var, command=self._toggle_wifi)
        wifi_check.pack(side="left", padx=10, expand=True)

        # Bluetooth Checkbutton
        self.bt_var = tk.BooleanVar(value=self.logic.get_bluetooth_status())
        bt_check = ttk.Checkbutton(parent_frame, text="Enable Bluetooth", 
                                     variable=self.bt_var, command=self._toggle_bluetooth)
        bt_check.pack(side="left", padx=10, expand=True)

    def _create_usb_controls(self, parent_frame):
        """
        Creates controls for the primary USB device power control.
        NOTE: This GUI only shows and controls the first device (DEFAULT_DEVICE_PATH).
        """
        # Fetch the status of all target devices (list contains status of all TARGET_DEVICES)
        self.usb_devices = self.logic.get_usb_devices()
        
        # Check if the primary target device path exists in /sys/bus/usb/devices
        if not self.usb_devices or not os.path.exists(f"/sys/bus/usb/devices/{self.logic.DEFAULT_DEVICE_PATH}"):
            ttk.Label(parent_frame, text=f"Target device {self.logic.DEFAULT_DEVICE_PATH} not found or not controllable.").pack()
            return
            
        # Use the first device's status for the display
        device = self.usb_devices[0]
        
        # Display the device name, path, and current status
        label_text = f"Device: {device['name']}\nPath: {device['path']} | Status: {device['control']}"
        ttk.Label(parent_frame, text=label_text).pack(anchor="w", padx=10, pady=5)

        # Store the device path for button callbacks
        self.usb_vars = [(tk.BooleanVar(), device['path'])] 
        
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.pack(pady=10, fill="x")
        
        # Button to set power/control to 'auto' (Autosuspend ENABLED/Power Saving)
        sus_btn = ttk.Button(btn_frame, text="✅ Enable Autosuspend (Auto)", command=self._enable_autosuspend_selected)
        sus_btn.pack(side="left", expand=True, padx=5)
        
        # Button to set power/control to 'on' (Autosuspend DISABLED/Full Power)
        res_btn = ttk.Button(btn_frame, text="❌ Disable Autosuspend (On)", command=self._disable_autosuspend_selected)
        res_btn.pack(side="left", expand=True, padx=5)
        
        # Refresh button to update the status text
        ttk.Button(parent_frame, text="Refresh Status", command=self._refresh_usb_status).pack(pady=5)


    def _refresh_usb_status(self):
        """Clears and redraws the USB control frame to show the new status after an action."""
        for widget in self.root.winfo_children():
            # Find the USB LabelFrame
            if widget.winfo_class() == 'Labelframe' and widget.cget('text') == 'USB Device Power':
                usb_frame = widget
                # Destroy all children in the frame
                for child in usb_frame.winfo_children():
                    child.destroy()
                # Recreate the controls to show the updated status
                self._create_usb_controls(usb_frame)
                return

    def _create_upower_controls(self, parent_frame):
        """Creates controls for UPower configuration."""
        
        config = self.logic.get_upower_config()
        self.upower_vars = {} # Store tk.StringVar for each setting

        keys = ['PercentageLow', 'PercentageCritical', 'PercentageAction', 'CriticalPowerAction']
        action_options = ["HybridSleep", "Hibernate", "PowerOff", "Suspend", "None"] # Standard UPower actions
        
        # Helper to create label and input field
        def create_control(parent, row, key, is_percentage, options=None):
            ttk.Label(parent, text=f"{key}:").grid(row=row, column=0, sticky="w", pady=5)
            
            current_value = config.get(key, "N/A")
            var = tk.StringVar(value=current_value)
            self.upower_vars[key] = var
            
            if not is_percentage:
                # Use OptionMenu for the action
                menu = ttk.OptionMenu(parent, var, current_value, *options)
                menu.grid(row=row, column=1, sticky="ew", padx=5)
            else:
                # Use Entry for percentage values
                entry = ttk.Entry(parent, textvariable=var)
                entry.grid(row=row, column=1, sticky="ew", padx=5)

        # Create controls for the four settings
        create_control(parent_frame, 0, 'PercentageLow', True)
        create_control(parent_frame, 1, 'PercentageCritical', True)
        create_control(parent_frame, 2, 'PercentageAction', True)
        create_control(parent_frame, 3, 'CriticalPowerAction', False, action_options)
        
        # Apply button
        save_btn = ttk.Button(parent_frame, text="Apply UPower Settings (Requires Sudo)", 
                              command=self._apply_upower_settings)
        save_btn.grid(row=len(keys), column=0, columnspan=2, pady=10, sticky="ew")
        
        parent_frame.columnconfigure(1, weight=1)

    def _apply_upower_settings(self):
        """Callback to apply all modified UPower settings using the C tool."""
        try:
            # 1. Get values and perform basic validation
            low = self.upower_vars['PercentageLow'].get()
            critical = self.upower_vars['PercentageCritical'].get()
            action_pct = self.upower_vars['PercentageAction'].get()
            action_type = self.upower_vars['CriticalPowerAction'].get()

            # Input validation
            if not (low.isdigit() and critical.isdigit() and action_pct.isdigit()):
                messagebox.showwarning("Input Error", "Percentage values must be positive integers.")
                return

            low = int(low)
            critical = int(critical)
            action_pct = int(action_pct)

            if not (0 <= low <= 100 and 0 <= critical <= 100 and 0 <= action_pct <= 100):
                messagebox.showwarning("Input Error", "Percentage values must be between 0 and 100.")
                return
            
            # 2. Call AppLogic to execute the C tool
            success = self.logic.set_upower_config(low, critical, action_pct, action_type)
            
            if success:
                # Refresh status displayed by re-populating the frame
                # (A simple status refresh is not implemented, but the success message confirms execution)
                messagebox.showinfo("Success", "UPower configuration applied. Service restarted.")
            else:
                messagebox.showerror("Error", "Failed to apply UPower settings. Check console for details.")
            
        except Exception as e:
            messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}")


    def _create_profile_controls(self, parent_frame):
        """Creates controls for saving and loading power profiles."""
        
        # Save Profile controls
        ttk.Label(parent_frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.profile_name_entry = ttk.Entry(parent_frame)
        self.profile_name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        save_btn = ttk.Button(parent_frame, text="Save Current", command=self._save_profile)
        save_btn.grid(row=0, column=2, padx=5)
            
        # Load Profile controls
        ttk.Label(parent_frame, text="Load Profile:").grid(row=1, column=0, sticky="w", pady=15)
        self.profiles = self.logic.get_all_profiles()
        profile_names = list(self.profiles.keys())
        if not profile_names: profile_names = ["No profiles"]
            
        self.selected_profile = tk.StringVar(value=profile_names[0])
        self.profile_dropdown = ttk.OptionMenu(parent_frame, self.selected_profile, 
                                               profile_names[0], *profile_names)
        self.profile_dropdown.grid(row=1, column=1, sticky="ew", padx=5)
        load_btn = ttk.Button(parent_frame, text="Load Selected", command=self._load_profile_button)
        load_btn.grid(row=1, column=2, padx=5)

        parent_frame.columnconfigure(1, weight=1)

    # --- Hardware Callbacks ---
    def _on_brightness_change(self, value):
        """Called when the brightness slider is moved."""
        self.logic.set_brightness(int(float(value)))

    def _on_governor_change(self, governor):
        """Called when the CPU governor is changed in the dropdown."""
        self.logic.set_cpu_governor(governor)

    # --- Connectivity Callbacks ---
    def _toggle_wifi(self):
        """Called when the Wi-Fi checkbox is toggled."""
        self.logic.set_wifi_status(self.wifi_var.get())

    def _toggle_bluetooth(self):
        """Called when the Bluetooth checkbox is toggled."""
        self.logic.set_bluetooth_status(self.bt_var.get())

    # --- USB Autosuspend Callbacks ---
    def _enable_autosuspend_selected(self):
        """Calls the logic to set all target USB devices to 'auto'."""
        for _, device_path in self.usb_vars:
            # Note: logic.enable_autosuspend is a wrapper that calls enable_autosuspend_all
            self.logic.enable_autosuspend(device_path)
        self._refresh_usb_status() 

    def _disable_autosuspend_selected(self):
        """Calls the logic to set all target USB devices to 'on'."""
        for _, device_path in self.usb_vars:
            # Note: logic.disable_autosuspend is a wrapper that calls disable_autosuspend_all
            self.logic.disable_autosuspend(device_path)
        self._refresh_usb_status() 

    # --- Profile Callbacks ---
    def _save_profile(self):
        """Gathers current UI settings and saves them using the AppLogic."""
        profile_name = self.profile_name_entry.get()
        if not profile_name:
            messagebox.showwarning("Input Error", "Please enter a name for the profile.")
            return

        settings = [
            int(self.brightness_slider.get()),
            int(self.fan_slider.get()),
            int(self.keyboard_slider.get()), # Placeholder value
            self.governor_var.get()
        ]
        self.logic.save_settings_to_profile(profile_name, settings)
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")
        # Reload profiles list after saving
        self.profiles = self.logic.get_all_profiles()
            
    def _load_profile_button(self):
        """Initiates the process to load the selected profile."""
        self.apply_profile(self.selected_profile.get())

    def apply_profile(self, profile_name):
        """Applies the settings from a specified profile to the UI and hardware."""
        settings = self.profiles.get(profile_name)
        if not settings:
            messagebox.showerror("Error", f"Could not load settings for '{profile_name}'.")
            return

        try:
            # Unpack settings (brightness, fan_speed, kbd_brightness, governor)
            brightness, fan_speed, kbd_brightness, governor = settings
                
            # Apply to GUI (Sliders/Dropdowns)
            self.brightness_slider.set(brightness)
            self.fan_slider.set(fan_speed) 
            self.keyboard_slider.set(kbd_brightness) # Placeholder
            self.governor_var.set(governor)

            # Apply to Hardware using AppLogic
            self.logic.set_brightness(brightness)
            # self.logic.set_keyboard_brightness(kbd_brightness) # Not implemented in logic
            self.logic.set_cpu_governor(governor)
                
            messagebox.showinfo("Success", f"Profile '{profile_name}' loaded.")
        except Exception as e:
            messagebox.showerror("Profile Error", f"Error applying profile: {e}\nProfile may be outdated.")

    # --- Automatic Power Check Loop ---
    def _check_power_loop(self):
        """Polls the power status every 10 seconds and automatically loads profiles."""
        try:
            current_status = self.logic.get_power_status()
            if current_status != self.last_power_status:
                self.last_power_status = current_status
                
                # Automatically switch profiles based on power status change
                if current_status == "online":
                    self.logic.send_notification("AC Power", "Plugged in, applying 'Balanced' profile.")
                    self.apply_profile("Balanced")
                else:
                    self.logic.send_notification("On Battery", "Unplugged, applying 'Power Saver' profile.")
                    self.apply_profile("Power Saver")
        except Exception as e:
            print(f"Error in power check loop: {e}")
            
        # Schedule next check
        self.root.after(10000, self._check_power_loop) # Check every 10 seconds

    def run(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()
