import subprocess
import os

class AppLogic:
    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')

    def _run_c_tool(self, tool_name, args):
        tool_path = os.path.join(self.bin_path, tool_name)
        if not os.path.exists(tool_path):
            print(f"Error: C tool '{tool_path}' not found. Have you compiled it?")
            return None
        command = ['sudo', tool_path] + args
        print(f"Core: Running command -> {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Core Error: C tool failed: {e.stderr.strip()}")
            return None
    
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

    def set_brightness(self, value):
        print(f"Core: Received request to set brightness to {value}%")
        self._run_c_tool('brightness_tool', [str(value)])