import os
import re
import subprocess
from typing import List, Dict, Any
from .profile_manager import ProfileManager

# ================================================================
#  Constants & Global Configuration
# ================================================================

UPOWER_CONFIG_PATH = "/etc/UPower/UPower.conf"
UPOWER_CONFIG_KEYS = [
    "PercentageLow",
    "PercentageCritical",
    "PercentageAction",
    "CriticalPowerAction",
]


# ================================================================
#  Main Logic Controller
# ================================================================

class AppLogic:
    """
    Core logic controller for the Linux Power Manager.
    Handles system-level operations like power configuration,
    device autosuspend, connectivity toggles, and UPower management.
    """

    # --- Configuration ---
    TARGET_DEVICES = ["3-10", "usb1", "usb2", "usb3", "usb4"]
    DEFAULT_DEVICE_PATH = "3-10"
    # ---------------------

    def __init__(self):
        self.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
        self.bin_path = os.path.join(self.project_root, "bin")
        self.profile_manager = ProfileManager()

    # ================================================================
    #  Internal Helpers
    # ================================================================

    def _run_c_tool(self, tool_name: str, args: List[str], use_sudo: bool = True):
        """
        Helper to run compiled C tools safely.
        Example: self._run_c_tool('brightness_tool', ['1', '80'])
        """
        tool_path = os.path.join(self.bin_path, tool_name)
        if not os.path.exists(tool_path):
            print(f"[ERROR] Missing C tool: {tool_path}")
            return None

        command = (["sudo"] if use_sudo else []) + [tool_path] + args
        print(f"[RUN] {' '.join(command)}")

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"[C TOOL ERROR] {tool_name}: {e.stderr.strip()}")
            return None

    def _run_system_command(self, args: List[str]):
        """Helper to run standard Linux shell commands."""
        try:
            return subprocess.run(args, capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[SYSTEM ERROR] {' '.join(args)} → {e}")
            return None

    def _write_to_sys_file(self, sys_path: str, value: str):
        """Helper to write a value to kernel sysfs files (requires sudo)."""
        command = f'echo "{value}" | sudo tee {sys_path}'
        print(f"[WRITE] {command}")
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError:
            print(f"[WRITE ERROR] Could not write '{value}' → {sys_path}")
            return False

    # ================================================================
    #  USB Autosuspend
    # ================================================================

    def get_usb_devices(self) -> List[Dict[str, Any]]:
        """Retrieve a list of USB devices with their current autosuspend status."""
        device_statuses = []

        for device_path in self.TARGET_DEVICES:
            sys_path = f"/sys/bus/usb/devices/{device_path}/power/control"
            control = "N/A"
            name = f"USB Device {device_path}"

            if os.path.exists(sys_path):
                try:
                    result = subprocess.run(
                        f"sudo cat {sys_path}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    control = result.stdout.strip()
                except subprocess.CalledProcessError:
                    control = "unknown (read failed)"

                # Try to read device name
                product_path = f"/sys/bus/usb/devices/{device_path}/product"
                if os.path.exists(product_path):
                    try:
                        with open(product_path, "r") as f:
                            name = f.read().strip()
                    except Exception:
                        pass

            device_statuses.append({"path": device_path, "name": name, "control": control})
        return device_statuses
    
    def enable_autosuspend(self, device_path):
        """Enable autosuspend for a specific USB device."""
        path = f"/sys/bus/usb/devices/{device_path}/power/control"
        if os.path.exists(path):
            try:
                self._write_to_sys_file(path, "auto")
                self.send_notification("USB Control", f"Autosuspend ENABLED for {device_path}")
            except Exception as e:
                print(f"[ERROR] Enabling autosuspend for {device_path}: {e}")
        else:
            print(f"[WARN] Device not found: {device_path}")

    def disable_autosuspend(self, device_path):
        """Disable autosuspend for a specific USB device."""
        path = f"/sys/bus/usb/devices/{device_path}/power/control"
        if os.path.exists(path):
            try:
                self._write_to_sys_file(path, "on")
                self.send_notification("USB Control", f"Autosuspend DISABLED for {device_path}")
            except Exception as e:
                print(f"[ERROR] Disabling autosuspend for {device_path}: {e}")
        else:
            print(f"[WARN] Device not found: {device_path}")
    # =========================================
    #  Brightness & CPU Governor
    # ================================================================

    def get_brightness(self):
        result = self._run_c_tool("brightness_tool", ["0"])
        if result and result.stdout:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return None
        return None

    def set_brightness(self, value: int):
        self._run_c_tool("brightness_tool", ["1", str(value)])

    def get_cpu_governor(self):
        result = self._run_c_tool("governor_tool", ["get"])
        return result.stdout.strip() if result and result.stdout else "schedutil"

    def set_cpu_governor(self, governor: str):
        self._run_c_tool("governor_tool", ["set", governor])

    # ================================================================
    #  Connectivity Controls
    # ================================================================

    def get_wifi_status(self):
        result = self._run_system_command(["nmcli", "radio", "wifi"])
        return "enabled" in (result.stdout.strip() if result else "")

    def set_wifi_status(self, enable: bool):
        self._run_system_command(["nmcli", "radio", "wifi", "on" if enable else "off"])

    def get_bluetooth_status(self):
        result = self._run_system_command(["rfkill", "list", "bluetooth"])
        if not result or not result.stdout:
            return False
        output = result.stdout.lower()
        return "soft blocked: no" in output and "hard blocked: no" in output

    def set_bluetooth_status(self, enable: bool):
        self._run_system_command(["rfkill", "unblock" if enable else "block", "bluetooth"])


    # ================================================================
    #  Power Status
    # ================================================================

    def get_power_status(self):
        """Returns whether the system is on AC or battery."""
        result = self._run_c_tool("status_tool", [], use_sudo=False)
        return result.stdout.strip() if result and result.stdout else "online"
    def get_battery_percentage(self):
        """"Returns the battery percentage."""
        try:
            with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0 # Default if path doesn't exist or BAT0 isn't found

    # ================================================================
    #  UPower Configuration Management
    # ================================================================

    def get_upower_config(self) -> Dict[str, str]:
        """Parse /etc/UPower/UPower.conf to read current thresholds and actions."""
        settings = {}
        if not os.path.exists(UPOWER_CONFIG_PATH):
            return settings

        try:
            result = subprocess.run(
                f"sudo cat {UPOWER_CONFIG_PATH}",
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            content = result.stdout
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to read UPower config: {e.stderr.strip()}")
            return settings

        for key in UPOWER_CONFIG_KEYS:
            match = re.search(rf"^\s*{re.escape(key)}=(.*?)(?:\s*#.*)?$", content, re.MULTILINE)
            if match:
                settings[key] = match.group(1).strip()

        return settings

    def set_upower_config(self, low: int, critical: int, action_pct: int, action_type: str) -> bool:
        """
        Update UPower.conf via the compiled 'battery_saver_tool'.
        Args are passed as CLI arguments to the C tool.
        """
        args = [str(low), str(critical), str(action_pct), action_type]
        result = self._run_c_tool("battery_saver_tool", args, use_sudo=False)

        if result and result.returncode == 0:
            self.send_notification("UPower Config", "Configuration updated successfully.")
            return True

        print("[ERROR] Failed to update UPower config.")
        self.send_notification("UPower Config Error", "Failed to update configuration.")
        return False

    # ================================================================
    #  Profile Management & Notifications
    # ================================================================

    def get_all_profiles(self):
        return self.profile_manager.get_profiles()

    def save_settings_to_profile(self, profile_name: str, settings: Dict[str, Any]):
        self.profile_manager.save_profile(profile_name, settings)

    def send_notification(self, title: str, message: str):
        """Trigger a system notification via notifier_tool."""
        self._run_c_tool("notifier_tool", [title, message], use_sudo=False)

