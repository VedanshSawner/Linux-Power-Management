import json
import os
import pwd # Import the password database module

def get_real_homedir():
    """Gets the home directory of the user who invoked sudo."""
    try:
        # SUDO_USER environment variable is set by sudo
        username = os.environ.get('SUDO_USER')
        if username:
            # Use pwd to get the user's real home directory
            return pwd.getpwnam(username).pw_dir
    except (KeyError, TypeError):
        # Fallback if SUDO_USER is not set or user not found
        pass
    
    # If not running under sudo, or if lookup fails, use the normal method
    return os.path.expanduser("~")

# --- Use the new function to define the config path ---
CONFIG_DIR = os.path.join(get_real_homedir(), ".config", "battery_manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "profiles.json")

class ProfileManager:
    """Handles reading and writing settings to profiles.json."""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump({}, f) # Create an empty JSON file if it doesn't exist

    def get_profiles(self):
        """Returns all profiles from the JSON file."""
        print(f"ProfileManager: Reading from {CONFIG_FILE}") # Add a debug print
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_profile(self, profile_name, settings_list):
        """Saves a single profile to the JSON file."""
        profiles = self.get_profiles()
        profiles[profile_name] = settings_list
        with open(CONFIG_FILE, 'w') as f:
            json.dump(profiles, f, indent=2)
        print(f"Profile '{profile_name}' saved with settings: {settings_list}")
        print("all profiles:")
        for p in profiles:
            print(p)