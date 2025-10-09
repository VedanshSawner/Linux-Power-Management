import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ApplicationGUI:
    """The main graphical user interface for the Battery Manager."""

    def __init__(self, root, app_logic):
        self.root = root
        self.logic = app_logic
        self.root.title("Linux Battery Manager")
        self.root.geometry("400x450") # Increase height a bit
        self.root.resizable(False, False)

        usb_frame = ttk.LabelFrame(self.root, text="USB Device Power Management", padding=(20, 10))
        usb_frame.pack(padx=10, pady=10, fill="x", expand=True)

        self.usb_devices = []
        self.usb_vars = []
        self._create_usb_controls(usb_frame)

        style = ttk.Style(self.root)
        style.theme_use('clam')

        hardware_frame = ttk.LabelFrame(self.root, text="Hardware Controls", padding=(20, 10))
        hardware_frame.pack(padx=10, pady=10, fill="x", expand=True)
        profile_frame = ttk.LabelFrame(self.root, text="Settings Profiles", padding=(20, 10))
        profile_frame.pack(padx=10, pady=10, fill="x", expand=True)

        self._create_hardware_controls(hardware_frame)
        self._create_profile_controls(profile_frame)

    def _create_hardware_controls(self, parent_frame):
        """Creates the sliders and buttons for hardware control."""
        ttk.Label(parent_frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        self.brightness_slider.set(80)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(parent_frame, text="Fan Speed:").grid(row=1, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(parent_frame, from_=0, to=100, orient="horizontal", command=self._on_fan_change)
        self.fan_slider.set(50)
        self.fan_slider.grid(row=1, column=1, sticky="ew", padx=5)

        parent_frame.columnconfigure(1, weight=1)

    def _on_brightness_change(self, value):
        brightness_value = int(float(value))
        self.logic.set_brightness(brightness_value)

    def _on_fan_change(self, value):
        print(f"UI Event: Fan speed slider changed to {float(value):.0f}%")
    
    def _create_usb_controls(self, parent_frame):
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
        resumed_count = 0
        for var, device in self.usb_vars:
            if var.get():
                self.logic.resume_usb_device(device['location'], device['port'])
                resumed_count += 1
        
        if resumed_count > 0:
            self.logic.send_notification("USB Devices Resumed", f"{resumed_count} device(s) were resumed.")
        else:
            messagebox.showinfo("No Selection", "No USB devices were selected.")
        
    def _save_profile(self):
        profile_name = self.profile_name_entry.get()
        if not profile_name:
            messagebox.showwarning("Input Error", "Please enter a name for the profile.")
            return
        print(f"UI Event: Saving settings to profile '{profile_name}'")
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")

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
