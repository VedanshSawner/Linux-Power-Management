import subprocess
import os
import re
from .profile_manager import ProfileManager
from typing import List, Dict, Any

class AppLogic:
    """
    Core logic controller for the Linux Power Manager.
    Handles all interactions with the system hardware via C tools and kernel files.
    """
    
    # --- Configuration ---
    # List of all devices/hubs the logic will control for autosuspend.
    TARGET_DEVICES = ["3-10", "usb1", "usb2", "usb3", "usb4"]
    
    # Primary device path. Used by the GUI for initial checks to ensure one target exists.
    DEFAULT_DEVICE_PATH = "3-10"
    # ---------------------

    def __init__(self):
        # Determine the project path to locate the compiled C tools in the 'bin' directory.
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')
        self.profile_manager = ProfileManager()
    
    # --- Helper Functions ---
    def _run_c_tool(self, tool_name, args, use_sudo=True):
        """Helper to run compiled C tools (e.g., brightness_tool, governor_tool)."""
        tool_path = os.path.join(self.bin_path, tool_name)
        if not os.path.exists(tool_path):
            print(f"Error: C tool '{tool_path}' not found. Have you compiled it?")
            return None
            
        command_base = ['sudo'] if use_sudo else []
        command = command_base + [tool_path] + args
        
        print(f"Core: Running command -> {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            # Catch failures, usually due to incorrect permissions or missing kernel files.
            print(f"Core Error: C tool failed: {e.stderr.strip()}")
            return None

    def _run_system_command(self, args):
        """Helper to run standard system commands (like 'nmcli' for connectivity)."""
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            return result
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Handle cases where the command itself is not installed or fails (e.g., Bluetooth not present)
            print(f"Core Error: System command failed: {e}")
            return None

    def _write_to_sys_file(self, sys_path: str, value: str):
        """
        Helper to write a value to a kernel file using 'echo ... | sudo tee ...'.
        Requires 'sudo' for execution.
        """
        command = f'echo "{value}" | sudo tee {sys_path}'
        print(f"Core: Writing to sys file -> {command}")
        try:
            # Use shell=True for piping with 'tee'
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Core Error: Failed to write to {sys_path} (Value: {value}). Check 'sudo' permissions.")
            return False

    # ------------------------------------
    # --- USB Autosuspend Implementation ---
    # ------------------------------------
    
    def get_usb_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieves the status ('on' or 'auto') for all devices listed in TARGET_DEVICES.
        """
        device_statuses = []
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            
            current_control = "N/A"
            device_name = f"USB Device {device_path}" 

            if os.path.exists(sys_path):
                try:
                    # Use 'sudo cat' via subprocess for reliable status reading
                    command = f'sudo cat {sys_path}'
                    result = subprocess.run(command, shell=True, check=True, 
                                            capture_output=True, text=True)
                    current_control = result.stdout.strip()
                except subprocess.CalledProcessError:
                     current_control = "unknown (read failed)"

                # Try to get a user-friendly name from the 'product' file
                product_path = f'/sys/bus/usb/devices/{device_path}/product'
                if os.path.exists(product_path):
                     try:
                         with open(product_path, 'r') as f:
                             device_name = f.read().strip()
                     except:
                         pass 

            device_statuses.append({
                'path': device_path,
                'name': device_name,
                'control': current_control # 'on', 'auto', or 'N/A'/'unknown'
            })
            
        return device_statuses

    def enable_autosuspend_all(self):
        """Sets power/control to 'auto' for ALL TARGET_DEVICES (ENABLES autosuspend)."""
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            if os.path.exists(sys_path):
                self._write_to_sys_file(sys_path, 'auto')
        self.send_notification("USB Control", "Autosuspend ENABLED for all target devices.")


    def disable_autosuspend_all(self):
        """Sets power/control to 'on' for ALL TARGET_DEVICES (DISABLES autosuspend/Full Power)."""
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            if os.path.exists(sys_path):
                self._write_to_sys_file(sys_path, 'on')
        self.send_notification("USB Control", "Autosuspend DISABLED for all target devices.")


    # --- Single/Legacy USB Methods ---
    # These methods are kept for backward compatibility with the existing GUI code (main_window.py).
    # They simply redirect to the control-all functions.
    def enable_autosuspend(self, device_path: str):
        """Legacy method: Redirects to control all devices."""
        self.enable_autosuspend_all()

    def disable_autosuspend(self, device_path: str):
        """Legacy method: Redirects to control all devices."""
        self.disable_autosuspend_all()
        
    def suspend_usb_device(self, location, port):
        """Legacy method: Redirects to control all devices."""
        print("Note: suspend_usb_device is deprecated. Using enable_autosuspend_all.")
        self.enable_autosuspend_all() 

    def resume_usb_device(self, location, port):
        """Legacy method: Redirects to control all devices."""
        print("Note: resume_usb_device is deprecated. Using disable_autosuspend_all.")
        self.disable_autosuspend_all() 
    # -------------------------------------------------------------------------
    
    # --- Brightness ---
    def get_brightness(self):
        """Gets the current screen brightness level via a C tool."""
        result = self._run_c_tool('brightness_tool', ['0']) 
        if result and result.stdout:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return None
        return None

    def set_brightness(self, value):
        """Sets the screen brightness level via a C tool."""
        self._run_c_tool('brightness_tool', ['1', str(value)])

    # --- CPU Governor ---
    def get_cpu_governor(self):
        """Gets the currently active CPU governor via a C tool."""
        result = self._run_c_tool('governor_tool', ['get'])
        if result and result.stdout:
            return result.stdout.strip()
        return "schedutil" 

    def set_cpu_governor(self, governor):
        """Sets the CPU governor (e.g., 'performance', 'powersave') via a C tool."""
        self._run_c_tool('governor_tool', ['set', governor])

    # --- Connectivity (Wi-Fi/Bluetooth) ---
    def get_wifi_status(self):
        """Checks Wi-Fi status using 'nmcli'."""
        result = self._run_system_command(['nmcli', 'radio', 'wifi'])
        return "enabled" in (result.stdout.strip() if result else "")

    def set_wifi_status(self, enable):
        """Sets Wi-Fi status using 'nmcli'."""
        state = 'on' if enable else 'off'
        self._run_system_command(['nmcli', 'radio', 'wifi', state])

    def get_bluetooth_status(self):
        """Checks Bluetooth status using 'nmcli'."""
        result = self._run_system_command(['nmcli', 'radio', 'bluetooth'])
        return "enabled" in (result.stdout.strip() if result else "")

    def set_bluetooth_status(self, enable):
        """Sets Bluetooth status using 'nmcli'."""
        state = 'on' if enable else 'off'
        self._run_system_command(['nmcli', 'radio', 'bluetooth', state])

    # --- Power Status ---
    def get_power_status(self):
        """Gets the current power status (e.g., 'online' or 'on battery') via a C tool."""
        result = self._run_c_tool('status_tool', [], use_sudo=False) 
        if result and result.stdout:
            return result.stdout.strip()
        return "online" 

    # --- Profiles ---
    def get_all_profiles(self):
        """Retrieves all saved profiles from the ProfileManager."""
        return self.profile_manager.get_profiles()

    def save_settings_to_profile(self, profile_name, settings):
        """Saves current settings to a named profile."""
        self.profile_manager.save_profile(profile_name, settings)

    # --- Notifications ---
    def send_notification(self, title, message):
        """Sends a desktop notification using a C tool (wrapper for notify-send)."""
        # Note: This is a system call, not a tkinter message.
        self._run_c_tool('notifier_tool', [title, message], use_sudo=False)
