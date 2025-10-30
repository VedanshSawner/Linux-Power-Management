import subprocess
import os
import re # This import was missing for your USB function
from .profile_manager import ProfileManager # Use relative import

class AppLogic:
    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')
        self.profile_manager = ProfileManager()

    def _run_c_tool(self, tool_name, args):
        tool_path = os.path.join(self.bin_path, tool_name)
        if not os.path.exists(tool_path):
            print(f"Error: C tool '{tool_path}' not found. Have you compiled it?")
            return None
        # Note: We run 'get' commands without sudo if possible, but reading /sys often needs it
        command = ['sudo', tool_path] + args
        print(f"Core: Running command -> {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Core Error: C tool failed: {e.stderr.strip()}")
            return None
    
    # ... (get_usb_devices, suspend_usb_device, etc. are the same) ...
    def get_usb_devices(self):
        """
        Calls the usb_manager_tool to get a list of controllable devices.
        Returns a list of dictionaries.
        """
        result = self._run_c_tool('usb_manager_tool', ['list'])
        if not result or not result.stdout:
            return []

        devices = []
        # Regex to find controllable ports with devices attached
        port_regex = re.compile(r'^\s*Port (\d+): \d+-\d+\.\d+ power \w+ lapic \d+ NAK (\w+), device=(\S+)')
        current_location = None

        for line in result.stdout.strip().split('\n'):
            if line.startswith("Current status for hub"):
                current_location = line.split()[-1] # Get hub location e.g., '1-1'
            
            match = port_regex.search(line)
            if match and current_location:
                port, status, name = match.groups()
                devices.append({
                    "location": current_location,
                    "port": port,
                    "name": name,
                    "status": status
                })
        return devices

    def suspend_usb_device(self, location, port):
        print(f"Core: Suspending USB device at {location} port {port}")
        self._run_c_tool('usb_manager_tool', ['suspend', location, port])

    def resume_usb_device(self, location, port):
        print(f"Core: Resuming USB device at {location} port {port}")
        self._run_c_tool('usb_manager_tool', ['resume', location, port])

    def send_notification(self, title, message):
        print(f"Core: Sending notification: {title} - {message}")
        self._run_c_tool('notifier_tool', [title, message])
    
    # --- IMPLEMENTED get_brightness ---
    def get_brightness(self):
        """Calls the C tool to get the current brightness percentage."""
        print("Core: Requesting current brightness...")
        result = self._run_c_tool('brightness_tool', ['0']) # Mode 0 = get
        
        if result and result.stdout:
            try:
                # The C tool prints just the percentage
                percentage = int(result.stdout.strip())
                return percentage
            except ValueError:
                print(f"Core Error: Could not parse brightness: {result.stdout}")
                return None
        return None

    # --- UPDATED set_brightness ---
    def set_brightness(self, value):
        """Calls the C tool to set the brightness percentage."""
        print(f"Core: Received request to set brightness to {value}%")
        self._run_c_tool('brightness_tool', ['1', str(value)]) # Mode 1 = set
    
    def get_all_profiles(self):
        """Gets all profiles from the profile manager."""
        profiles = self.profile_manager.get_profiles()
        return profiles

    def save_settings_to_profile(self, profile_name, settings):
        """Saves a list of settings to a named profile."""
        self.profile_manager.save_profile(profile_name, settings)