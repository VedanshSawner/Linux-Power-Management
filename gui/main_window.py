import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ApplicationGUI:
    def __init__(self, root, app_logic):
        self.root = root
        self.logic = app_logic
        self.root.title("Linux Power Manager")
        self.root.geometry("450x800") # New size for all widgets
        self.root.resizable(True, True)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)


        style = ttk.Style(self.root)
        style.theme_use('clam')

        # --- Create Frames ---
        hw_frame = ttk.LabelFrame(self.root, text="Hardware Controls", padding=(20, 10))
        conn_frame = ttk.LabelFrame(self.root, text="Connectivity", padding=(20, 10))
        usb_frame = ttk.LabelFrame(self.root, text="USB Device Power", padding=(20, 10))
        profile_frame = ttk.LabelFrame(self.root, text="Settings Profiles", padding=(20, 10))

        # --- Pack Frames ---
        hw_frame.pack(padx=10, pady=10, fill="x")
        conn_frame.pack(padx=10, pady=10, fill="x")
        usb_frame.pack(padx=10, pady=10, fill="x")
        profile_frame.pack(padx=10, pady=10, fill="x")

        # --- Populate Frames ---
        self._create_hardware_controls(hw_frame)
        self._create_connectivity_controls(conn_frame)
        self._create_usb_controls(usb_frame)
        self._create_profile_controls(profile_frame)

        # --- Start Power Status Polling ---
        self.last_power_status = self.logic.get_power_status()
        self._check_power_loop()

    def _create_hardware_controls(self, parent_frame):
        # --- Screen Brightness ---
        ttk.Label(parent_frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        self.brightness_slider.set(self.logic.get_brightness() or 80)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)

        # --- CPU Governor ---
        ttk.Label(parent_frame, text="CPU Profile:").grid(row=2, column=0, sticky="w", pady=5)
        self.governor_options = ["powersave", "schedutil", "performance"]
        self.governor_var = tk.StringVar(value=self.logic.get_cpu_governor())
        gov_menu = ttk.OptionMenu(parent_frame, self.governor_var, self.governor_var.get(), *self.governor_options, command=self._on_governor_change)
        gov_menu.grid(row=2, column=1, sticky="ew", padx=5)
        
        # --- Fan Speed (Placeholder) ---
        ttk.Label(parent_frame, text="Fan Speed (N/A):").grid(row=3, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal")
        self.fan_slider.set(50)
        self.fan_slider.state(['disabled']) # Disable fan slider
        self.fan_slider.grid(row=3, column=1, sticky="ew", padx=5)

        parent_frame.columnconfigure(1, weight=1)

    def _create_connectivity_controls(self, parent_frame):
        self.wifi_var = tk.BooleanVar(value=self.logic.get_wifi_status())
        wifi_check = ttk.Checkbutton(parent_frame, text="Enable Wi-Fi", variable=self.wifi_var, command=self._toggle_wifi)
        wifi_check.pack(side="left", padx=10, expand=True)

        self.bt_var = tk.BooleanVar(value=self.logic.get_bluetooth_status())
        bt_check = ttk.Checkbutton(parent_frame, text="Enable Bluetooth", variable=self.bt_var, command=self._toggle_bluetooth)
        bt_check.pack(side="left", padx=10, expand=True)

    def _create_usb_controls(self, parent_frame):
        self.usb_devices = self.logic.get_usb_devices()
        if not self.usb_devices:
            ttk.Label(parent_frame, text="No controllable USB devices found.").pack()
            return
        
        self.usb_vars = []
        for i, device in enumerate(self.usb_devices):
            var = tk.BooleanVar()
            label = f"{device['name']} (Hub {device['location']}, Port {device['port']})"
            cb = ttk.Checkbutton(parent_frame, text=label, variable=var)
            cb.pack(anchor="w", padx=10)
            self.usb_vars.append((var, device))

        btn_frame = ttk.Frame(parent_frame)
        btn_frame.pack(pady=10, fill="x")
        sus_btn = ttk.Button(btn_frame, text="Suspend Selected", command=self._suspend_selected_usb)
        sus_btn.pack(side="left", expand=True, padx=5)
        res_btn = ttk.Button(btn_frame, text="Resume Selected", command=self._resume_selected_usb)
        res_btn.pack(side="left", expand=True, padx=5)

    def _create_profile_controls(self, parent_frame):
        ttk.Label(parent_frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.profile_name_entry = ttk.Entry(parent_frame)
        self.profile_name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        save_btn = ttk.Button(parent_frame, text="Save Current", command=self._save_profile)
        save_btn.grid(row=0, column=2, padx=5)
        
        ttk.Label(parent_frame, text="Load Profile:").grid(row=1, column=0, sticky="w", pady=15)
        self.profiles = self.logic.get_all_profiles()
        profile_names = list(self.profiles.keys())
        if not profile_names: profile_names = ["No profiles"]
        
        self.selected_profile = tk.StringVar(value=profile_names[0])
        self.profile_dropdown = ttk.OptionMenu(parent_frame, self.selected_profile, profile_names[0], *profile_names)
        self.profile_dropdown.grid(row=1, column=1, sticky="ew", padx=5)
        load_btn = ttk.Button(parent_frame, text="Load Selected", command=self._load_profile_button)
        load_btn.grid(row=1, column=2, padx=5)

        parent_frame.columnconfigure(1, weight=1)

    # --- Hardware Callbacks ---
    def _on_brightness_change(self, value):
        self.logic.set_brightness(int(float(value)))

    def _on_keyboard_change(self, value):
        self.logic.set_keyboard_brightness(int(float(value)))

    def _on_governor_change(self, governor):
        self.logic.set_cpu_governor(governor)

    # --- Connectivity Callbacks ---
    def _toggle_wifi(self):
        self.logic.set_wifi_status(self.wifi_var.get())

    def _toggle_bluetooth(self):
        self.logic.set_bluetooth_status(self.bt_var.get())

    # --- USB Callbacks ---
    def _suspend_selected_usb(self):
        count = 0
        for var, device in self.usb_vars:
            if var.get():
                self.logic.suspend_usb_device(device['location'], device['port'])
                count += 1
        if count > 0: self.logic.send_notification("USB Devices", f"{count} device(s) suspended.")

    def _resume_selected_usb(self):
        count = 0
        for var, device in self.usb_vars:
            if var.get():
                self.logic.resume_usb_device(device['location'], device['port'])
                count += 1
        if count > 0: self.logic.send_notification("USB Devices", f"{count} device(s) resumed.")

    # --- Profile Callbacks ---
    def _save_profile(self):
        profile_name = self.profile_name_entry.get()
        if not profile_name:
            messagebox.showwarning("Input Error", "Please enter a name for the profile.")
            return

        settings = [
            int(self.brightness_slider.get()),
            int(self.fan_slider.get()),
            int(self.keyboard_slider.get()),
            self.governor_var.get()
        ]
        self.logic.save_settings_to_profile(profile_name, settings)
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")
        # TODO: Refresh profile dropdown
        
    def _load_profile_button(self):
        self.apply_profile(self.selected_profile.get())

    def apply_profile(self, profile_name):
        settings = self.profiles.get(profile_name)
        if not settings:
            messagebox.showerror("Error", f"Could not load settings for '{profile_name}'.")
            return

        try:
            brightness, fan_speed, kbd_brightness, governor = settings
            
            # Apply to GUI
            self.brightness_slider.set(brightness)
            self.fan_slider.set(fan_speed) # Stays disabled, just sets value
            self.keyboard_slider.set(kbd_brightness)
            self.governor_var.set(governor)

            # Apply to Hardware
            self.logic.set_brightness(brightness)
            self.logic.set_keyboard_brightness(kbd_brightness)
            self.logic.set_cpu_governor(governor)
            
            messagebox.showinfo("Success", f"Profile '{profile_name}' loaded.")
        except Exception as e:
            messagebox.showerror("Profile Error", f"Error applying profile: {e}\nProfile may be outdated.")

    # --- Automatic Power Check Loop ---
    def _check_power_loop(self):
        try:
            current_status = self.logic.get_power_status()
            if current_status != self.last_power_status:
                self.last_power_status = current_status
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
        self.root.mainloop()