import subprocess
import os
import re
from .profile_manager import ProfileManager
from typing import List, Dict, Any

# Define the UPower config file and keys for reading/parsing
UPOWER_CONFIG_PATH = '/etc/UPower/UPower.conf'
UPOWER_CONFIG_KEYS = [
    'PercentageLow',
    'PercentageCritical',
    'PercentageAction',
    'CriticalPowerAction'
]

class AppLogic:
    """
    Core logic controller for the Linux Power Manager.
    Handles all interactions with the system hardware via C tools and kernel files.
    """
    
    # --- Configuration ---
    TARGET_DEVICES = ["3-10", "usb1", "usb2", "usb3", "usb4"]
    DEFAULT_DEVICE_PATH = "3-10"
    # ---------------------

    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')
        self.profile_manager = ProfileManager()
    
    # --- Helper Functions ---
    def _run_c_tool(self, tool_name, args, use_sudo=True):
        """
        Helper to run compiled C tools. 
        The 'args' list is passed directly as command-line arguments to the C executable.
        """
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
            print(f"Core Error: C tool failed: {e.stderr.strip()}")
            return None

    def _run_system_command(self, args):
        """Helper to run standard system commands."""
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            return result
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Core Error: System command failed: {e}")
            return None

    def _write_to_sys_file(self, sys_path: str, value: str):
        """Helper to write a value to a kernel file using 'echo ... | sudo tee ...'."""
        command = f'echo "{value}" | sudo tee {sys_path}'
        print(f"Core: Writing to sys file -> {command}")
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Core Error: Failed to write to {sys_path} (Value: {value}). Check 'sudo' permissions.")
            return False

    # --- USB Autosuspend Implementation (omitted for brevity) ---
    def get_usb_devices(self) -> List[Dict[str, Any]]:
        device_statuses = []
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            current_control = "N/A"
            device_name = f"USB Device {device_path}" 
            if os.path.exists(sys_path):
                try:
                    command = f'sudo cat {sys_path}'
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    current_control = result.stdout.strip()
                except subprocess.CalledProcessError:
                     current_control = "unknown (read failed)"
                product_path = f'/sys/bus/usb/devices/{device_path}/product'
                if os.path.exists(product_path):
                     try:
                         with open(product_path, 'r') as f:
                             device_name = f.read().strip()
                     except:
                         pass 
            device_statuses.append({'path': device_path, 'name': device_name, 'control': current_control})
        return device_statuses

    def enable_autosuspend_all(self):
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            if os.path.exists(sys_path): self._write_to_sys_file(sys_path, 'auto')
        self.send_notification("USB Control", "Autosuspend ENABLED for all target devices.")

    def disable_autosuspend_all(self):
        for device_path in self.TARGET_DEVICES:
            sys_path = f'/sys/bus/usb/devices/{device_path}/power/control'
            if os.path.exists(sys_path): self._write_to_sys_file(sys_path, 'on')
        self.send_notification("USB Control", "Autosuspend DISABLED for all target devices.")
    # --- End USB ---
    
    # --- Brightness, CPU Governor, Connectivity, Power Status (omitted for brevity) ---
    def get_brightness(self):
        result = self._run_c_tool('brightness_tool', ['0']) 
        if result and result.stdout:
            try: return int(result.stdout.strip())
            except ValueError: return None
        return None
    def set_brightness(self, value):
        self._run_c_tool('brightness_tool', ['1', str(value)])
    def get_cpu_governor(self):
        result = self._run_c_tool('governor_tool', ['get'])
        if result and result.stdout: return result.stdout.strip()
        return "schedutil" 
    def set_cpu_governor(self, governor):
        self._run_c_tool('governor_tool', ['set', governor])
    def get_wifi_status(self):
        result = self._run_system_command(['nmcli', 'radio', 'wifi'])
        return "enabled" in (result.stdout.strip() if result else "")
    def set_wifi_status(self, enable):
        state = 'on' if enable else 'off'
        self._run_system_command(['nmcli', 'radio', 'wifi', state])
    def get_bluetooth_status(self):
        result = self._run_system_command(['nmcli', 'radio', 'bluetooth'])
        return "enabled" in (result.stdout.strip() if result else "")
    def set_bluetooth_status(self, enable):
        state = 'on' if enable else 'off'
        self._run_system_command(['nmcli', 'radio', 'bluetooth', state])
    def get_power_status(self):
        result = self._run_c_tool('status_tool', [], use_sudo=False) 
        if result and result.stdout: return result.stdout.strip()
        return "online" 
    # --- End other controls ---

    # ----------------------------------------
    # --- UPower Configuration Implementation ---
    # ----------------------------------------

    def get_upower_config(self) -> Dict[str, str]:
        """Retrieves the current UPower configuration settings by reading the file."""
        settings = {}
        if not os.path.exists(UPOWER_CONFIG_PATH):
            return settings
        try:
            command = f'sudo cat {UPOWER_CONFIG_PATH}'
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            content = result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error reading UPower config (sudo cat failed): {e.stderr.strip()}")
            return settings

        for key in UPOWER_CONFIG_KEYS:
            match = re.search(r'^\s*' + re.escape(key) + r'=(.*?)(?:\s*#.*)?$', content, re.MULTILINE)
            if match:
                settings[key] = match.group(1).strip()
                
        return settings


    def set_upower_config(self, low: int, critical: int, action_pct: int, action_type: str) -> bool:
        """
        Sets the UPower configuration using the compiled C tool ('battery_saver_tool').
        Data flow: Python receives dynamic values and passes them as strings to the C tool.
        """
        
        # --- THIS IS THE CRITICAL STEP ---
        # 1. Convert all dynamic values to strings for command-line transmission
        args = [
            str(low), 
            str(critical), 
            str(action_pct), 
            action_type # action_type is already a string
        ]

        # 2. Call the C tool, passing the argument list
        result = self._run_c_tool('battery_saver_tool', args, use_sudo=False) 
        # ---------------------------------

        if result and result.returncode == 0:
            self.send_notification("UPower Config", "Configuration updated and service restarted.")
            return True
        else:
            print("UPower C Tool Output/Error:", result.stderr if result else "No output.")
            self.send_notification("UPower Config Error", "Failed to update UPower config. Check console.")
            return False

    # --- Profiles and Notifications (omitted for brevity) ---
    def get_all_profiles(self):
        return self.profile_manager.get_profiles()
    def save_settings_to_profile(self, profile_name, settings):
        self.profile_manager.save_profile(profile_name, settings)
    def send_notification(self, title, message):
        self._run_c_tool('notifier_tool', [title, message], use_sudo=False)
