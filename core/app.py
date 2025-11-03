import subprocess
import os
import re
from .profile_manager import ProfileManager

class AppLogic:
    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')
        self.profile_manager = ProfileManager()

    def _run_c_tool(self, tool_name, args, use_sudo=True):
        """Helper to run C tools. Now with optional sudo."""
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
        """Helper to run system commands (like nmcli) without sudo."""
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            return result
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Core Error: System command failed: {e}")
            return None

    # --- Brightness ---
    def get_brightness(self):
        result = self._run_c_tool('brightness_tool', ['0']) # Mode 0 = get
        if result and result.stdout:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return None
        return None

    def set_brightness(self, value):
        self._run_c_tool('brightness_tool', ['1', str(value)]) # Mode 1 = set

    # --- CPU Governor ---
    def get_cpu_governor(self):
        result = self._run_c_tool('governor_tool', ['get'])
        if result and result.stdout:
            return result.stdout.strip()
        return "schedutil" # Fallback

    def set_cpu_governor(self, governor):
        self._run_c_tool('governor_tool', ['set', governor])

    # --- Connectivity (Wi-Fi/Bluetooth) ---
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

    # --- Power Status ---
    def get_power_status(self):
        result = self._run_c_tool('status_tool', [], use_sudo=False) # No sudo needed
        if result and result.stdout:
            return result.stdout.strip()
        return "online" # Default to online

    # --- Profiles ---
    def get_all_profiles(self):
        return self.profile_manager.get_profiles()

    def save_settings_to_profile(self, profile_name, settings):
        self.profile_manager.save_profile(profile_name, settings)

    # --- USB / Notifications ---
    def get_usb_devices(self):
        result = self._run_c_tool('usb_manager_tool', ['list'])
        if not result or not result.stdout: return []
        devices = []
        port_regex = re.compile(r'^\s*Port (\d+): \d+-\d+\.\d+ power \w+ lapic \d+ NAK (\w+), device=(\S+)')
        current_location = None
        for line in result.stdout.strip().split('\n'):
            if line.startswith("Current status for hub"):
                current_location = line.split()[-1]
            match = port_regex.search(line)
            if match and current_location:
                devices.append({"location": current_location, "port": match.group(1), "name": match.group(3), "status": match.group(2)})
        return devices

    def suspend_usb_device(self, location, port):
        self._run_c_tool('usb_manager_tool', ['suspend', location, port])

    def resume_usb_device(self, location, port):
        self._run_c_tool('usb_manager_tool', ['resume', location, port])

    def send_notification(self, title, message):
        self._run_c_tool('notifier_tool', [title, message], use_sudo=False)