import subprocess
import os

class AppLogic:
    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.bin_path = os.path.join(self.project_root, 'bin')
        
    def _run_c_tool(self, tool_name, args):
        """A generic helper to run a compiled C tool from the bin/ directory."""
        tool_path = os.path.join(self.bin_path, tool_name)

        if not os.path.exists(tool_path):
            print(f"Error: C tool not found at {tool_path}")
            print("Have you compiled the C code using the Makefile or build.sh script?")
            return None # Indicate failure

        command = ['sudo', tool_path] + args
        print(f"Core: Running command -> {' '.join(command)}")

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"Core: C tool output -> {result.stdout.strip()}")
            return result # Indicate success
        except subprocess.CalledProcessError as e:
            print(f"Core Error: C tool failed with exit code {e.returncode}")
            print(f"Core Error Output: {e.stderr.strip()}")
            return None # Indicate failure
    
    def set_brightness(self, value):

        print(f"Core: Received request to set brightness to {value}%")
        
        tool_path = os.path.join(self.bin_path, 'brightness_tool')
        
        # Build the command that will be executed in the terminal
        command = ['sudo', tool_path, str(value)]
        
        print(f"Core: Running command -> {' '.join(command)}")
        try:
            # Run the command
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # If the C tool returns an error, print it
            print(f"Core Error: C tool failed: {e.stderr.strip()}")
        except FileNotFoundError:
            print(f"Core Error: '{tool_path}' not found. Did you compile the C code?")
        
    def toggle_webcam(self, current_button_text):
        """
        Calls the C tool to enable or disable the webcam.
        'current_button_text' will be "Disable Webcam" or "Enable Webcam".
        """
        # Determine the action based on the button's current text
        action = 'disable' if "Disable" in current_button_text else 'enable'
        
        print(f"Core: Received request to {action} webcam.")
        self._run_c_tool('webcam_tool', [action])

