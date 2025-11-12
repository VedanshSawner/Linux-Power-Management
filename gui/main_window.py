import tkinter as tk
from tkinter import ttk, messagebox
import os

# ------------------------------
# --- IMPROVED APPLICATION GUI ---
# ------------------------------
class ApplicationGUI:
    """
    Modernized Tkinter GUI for the Linux Power Manager
    """

    def __init__(self, root, app_logic):
        self.root = root
        self.logic = app_logic
        self.root.title("⚡ Linux Power Manager")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)
        self.root.configure(bg="#f7f9fb")

        # --- Modern Theme ---
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f7f9fb")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TCheckbutton", font=("Segoe UI", 10), background="#f7f9fb")
        style.configure("TLabelframe", background="#f7f9fb", labelanchor="n", relief="ridge", padding=10)
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("TScale", background="#f7f9fb")

        # --- Layout: Sidebar + Main Area ---
        self.sidebar = ttk.Frame(self.root, width=180, relief="ridge", padding=10)
        self.sidebar.pack(side="left", fill="y")
        self.main_area = ttk.Frame(self.root)
        self.main_area.pack(side="right", expand=True, fill="both")

        # --- Quick Toolbar ---
        self.toolbar = ttk.Frame(self.main_area)
        self.toolbar.pack(fill="x", pady=(5, 0))
        ttk.Button(self.toolbar, text="🔋 Power Saver", command=lambda: self.apply_profile("Power Saver")).pack(side="left", padx=4)
        ttk.Button(self.toolbar, text="⚙️ Balanced", command=lambda: self.apply_profile("Balanced")).pack(side="left", padx=4)
        ttk.Button(self.toolbar, text="🚀 Performance", command=lambda: self.apply_profile("Performance")).pack(side="left", padx=4)

        # --- Create Frames ---
        self.frames = {}
        self.frames["Hardware"] = ttk.LabelFrame(self.main_area, text="Hardware Controls")
        self.frames["Connectivity"] = ttk.LabelFrame(self.main_area, text="Connectivity")
        self.frames["USB"] = ttk.LabelFrame(self.main_area, text="USB Power Control")
        self.frames["UPower"] = ttk.LabelFrame(self.main_area, text="UPower Shutdown Config")
        self.frames["Profiles"] = ttk.LabelFrame(self.main_area, text="Settings Profiles")

        # Populate frames
        self._create_hardware_controls(self.frames["Hardware"])
        self._create_connectivity_controls(self.frames["Connectivity"])
        self._create_usb_controls(self.frames["USB"])
        self._create_upower_controls(self.frames["UPower"])
        self._create_profile_controls(self.frames["Profiles"])

        # --- Sidebar Navigation ---
        ttk.Label(self.sidebar, text="⚡ Control Panels", font=("Segoe UI", 11, "bold")).pack(pady=5)
        for name in self.frames.keys():
            ttk.Button(self.sidebar, text=name, command=lambda n=name: self._show_frame(n)).pack(fill="x", pady=4)
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=10)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self.root, text="Loading system status...", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        # Placeholder
        self.keyboard_slider = ttk.Scale(self.root, from_=0, to=100, orient="horizontal")

        # Show initial frame
        self._show_frame("Hardware")

        # --- Power Loop ---
        self.last_power_status = self.logic.get_power_status()
        self._check_power_loop()
        self._update_status_bar()

    # -----------------------------
    # --- NAVIGATION & TOOLTIP ---
    # -----------------------------
    def _show_frame(self, name):
        """Switch between sections dynamically."""
        for f in self.frames.values():
            f.pack_forget()
        self.frames[name].pack(expand=True, fill="both", padx=15, pady=10)

    def _tooltip(self, widget, text):
        """Lightweight tooltip hover helper."""
        tip = tk.Toplevel(widget)
        tip.withdraw()
        tip.overrideredirect(True)
        lbl = ttk.Label(tip, text=text, background="#ffffe0", relief="solid", borderwidth=1, padding=3)
        lbl.pack()
        def enter(event):
            tip.deiconify()
            tip.geometry(f"+{widget.winfo_rootx()+20}+{widget.winfo_rooty()+20}")
        def leave(event):
            tip.withdraw()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    # -----------------------------
    # --- HARDWARE CONTROLS ---
    # -----------------------------
    def _create_hardware_controls(self, frame):
        ttk.Label(frame, text="Screen Brightness:").grid(row=0, column=0, sticky="w", pady=5)
        self.brightness_slider = ttk.Scale(frame, from_=0, to=100, orient="horizontal", command=self._on_brightness_change)
        self.brightness_slider.set(self.logic.get_brightness() or 80)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(frame, text="CPU Governor:").grid(row=1, column=0, sticky="w", pady=5)
        self.governor_options = ["powersave", "schedutil", "performance"]
        self.governor_var = tk.StringVar(value=self.logic.get_cpu_governor())
        gov_menu = ttk.OptionMenu(frame, self.governor_var, self.governor_var.get(), *self.governor_options, command=self._on_governor_change)
        gov_menu.grid(row=1, column=1, sticky="ew", padx=5)

        ttk.Label(frame, text="Fan Speed (N/A):").grid(row=2, column=0, sticky="w", pady=5)
        self.fan_slider = ttk.Scale(frame, from_=0, to=100, orient="horizontal")
        self.fan_slider.set(50)
        self.fan_slider.state(['disabled'])
        self.fan_slider.grid(row=2, column=1, sticky="ew", padx=5)

        frame.columnconfigure(1, weight=1)

    # -----------------------------
    # --- CONNECTIVITY CONTROLS ---
    # -----------------------------
    
    def _create_connectivity_controls(self, frame):
        self.wifi_var = tk.BooleanVar(value=self.logic.get_wifi_status())
        wifi_check = ttk.Checkbutton(frame, text="Enable Wi-Fi", variable=self.wifi_var, command=self._toggle_wifi)
        wifi_check.pack(side="left", padx=20, expand=True)
        self._tooltip(wifi_check, "Toggle wireless connectivity")

        self.bt_var = tk.BooleanVar(value=self.logic.get_bluetooth_status())
        bt_check = ttk.Checkbutton(frame, text="Enable Bluetooth", variable=self.bt_var, command=self._toggle_bluetooth)
        bt_check.pack(side="left", padx=20, expand=True)
        self._tooltip(bt_check, "Enable or disable Bluetooth adapter")

    # -----------------------------
    # --- USB CONTROLS ---
    # -----------------------------
    def _create_usb_controls(self, frame):
        devices = self.logic.get_usb_devices()
        if not devices:
            ttk.Label(frame, text="No controllable USB devices detected.").pack()
            return

        ttk.Label(frame, text="USB Device Power Control").pack(anchor="w", padx=10, pady=(5, 10))

        for device in devices:
            dev_frame = ttk.Frame(frame)
            dev_frame.pack(fill="x", padx=10, pady=5)

            info = f"{device['name']}  |  Path: {device['path']}  |  Status: {device['control']}"
            ttk.Label(dev_frame, text=info).pack(side="left", padx=5)

            ttk.Button(
                dev_frame,
                text="Enable Autosuspend",
                command=lambda d=device['path']: self._enable_autosuspend_selected(d)
            ).pack(side="left", padx=5)

            ttk.Button(
                dev_frame,
                text="Disable Autosuspend",
                command=lambda d=device['path']: self._disable_autosuspend_selected(d)
            ).pack(side="left", padx=5)

        ttk.Button(frame, text="🔄 Refresh", command=self._refresh_usb_status).pack(pady=10)

    # -----------------------------
    # --- UPOWER CONFIG ---
    # -----------------------------
    def _create_upower_controls(self, frame):
        config = self.logic.get_upower_config()
        self.upower_vars = {}
        keys = ['PercentageLow', 'PercentageCritical', 'PercentageAction', 'CriticalPowerAction']
        actions = ["HybridSleep", "Hibernate", "PowerOff", "Suspend", "None"]

        for i, key in enumerate(keys):
            ttk.Label(frame, text=f"{key}:").grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=config.get(key, "N/A"))
            self.upower_vars[key] = var
            if key != "CriticalPowerAction":
                ttk.Entry(frame, textvariable=var).grid(row=i, column=1, sticky="ew", padx=5)
            else:
                ttk.OptionMenu(frame, var, var.get(), *actions).grid(row=i, column=1, sticky="ew", padx=5)

        ttk.Button(frame, text="💾 Apply Settings", command=self._apply_upower_settings).grid(row=len(keys), column=0, columnspan=2, pady=10, sticky="ew")
        frame.columnconfigure(1, weight=1)

    # -----------------------------
    # --- PROFILE CONTROLS ---
    # -----------------------------
    def _create_profile_controls(self, frame):
        ttk.Label(frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.profile_name_entry = ttk.Entry(frame)
        self.profile_name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="💾 Save", command=self._save_profile).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="Load Profile:").grid(row=1, column=0, sticky="w", pady=10)
        self.profiles = self.logic.get_all_profiles()
        names = list(self.profiles.keys()) or ["No profiles"]
        self.selected_profile = tk.StringVar(value=names[0])
        ttk.OptionMenu(frame, self.selected_profile, names[0], *names).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="📂 Load", command=self._load_profile_button).grid(row=1, column=2, padx=5)
        frame.columnconfigure(1, weight=1)

    # -----------------------------
    # --- CALLBACKS ---
    # -----------------------------
    def _on_brightness_change(self, value): self.logic.set_brightness(int(float(value)))
    def _on_governor_change(self, val): self.logic.set_cpu_governor(val)
    def _toggle_wifi(self): self.logic.set_wifi_status(self.wifi_var.get())
    def _toggle_bluetooth(self): self.logic.set_bluetooth_status(self.bt_var.get())
    def _enable_autosuspend_selected(self, device_path):
        self.logic.enable_autosuspend(device_path)
        self._refresh_usb_status()

    def _disable_autosuspend_selected(self, device_path):
        self.logic.disable_autosuspend(device_path)
        self._refresh_usb_status()


    def _refresh_usb_status(self):
        self._show_frame("USB")

    def _apply_upower_settings(self):
        try:
            low = int(self.upower_vars['PercentageLow'].get())
            crit = int(self.upower_vars['PercentageCritical'].get())
            act = int(self.upower_vars['PercentageAction'].get())
            action = self.upower_vars['CriticalPowerAction'].get()
            if not self.logic.set_upower_config(low, crit, act, action):
                raise Exception("set_upower_config failed")
            messagebox.showinfo("Success", "UPower settings applied successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_profile(self):
        name = self.profile_name_entry.get()
        if not name:
            messagebox.showwarning("Input Error", "Enter a profile name.")
            return
        data = [int(self.brightness_slider.get()), int(self.fan_slider.get()), int(self.keyboard_slider.get()), self.governor_var.get()]
        self.logic.save_settings_to_profile(name, data)
        messagebox.showinfo("Saved", f"Profile '{name}' saved.")
        self.profiles = self.logic.get_all_profiles()

    def _load_profile_button(self):
        self.apply_profile(self.selected_profile.get())

    def apply_profile(self, name):
        settings = self.profiles.get(name)
        if not settings:
            messagebox.showerror("Error", f"Profile '{name}' not found.")
            return
        b, f, kb, g = settings
        self.brightness_slider.set(b)
        self.fan_slider.set(f)
        self.governor_var.set(g)
        self.logic.set_brightness(b)
        self.logic.set_cpu_governor(g)
        messagebox.showinfo("Loaded", f"Profile '{name}' applied.")

    # -----------------------------
    # --- STATUS & POWER CHECK ---
    # -----------------------------
    def _update_status_bar(self):
        try:
            power = self.logic.get_power_status()
            battery = self.logic.get_battery_percentage()
            self.status_bar.config(text=f"Power: {power.upper()} | Battery: {battery}%")
        except Exception as e:
            self.status_bar.config(text=f"Error reading status: {e}")
        self.root.after(5000, self._update_status_bar)

    def _check_power_loop(self):
        try:
            cur = self.logic.get_power_status()
            if cur != self.last_power_status:
                self.last_power_status = cur
                if cur == "online":
                    self.logic.send_notification("AC Power", "Plugged in, applying 'Balanced'")
                    self.apply_profile("Balanced")
                else:
                    self.logic.send_notification("Battery", "Unplugged, applying 'Power Saver'")
                    self.apply_profile("Power Saver")
        except Exception as e:
            print(f"Power check error: {e}")
        self.root.after(10000, self._check_power_loop)

    def run(self):
        self.root.mainloop()

