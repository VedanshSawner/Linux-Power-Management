import tkinter as tk
from gui.main_window import ApplicationGUI
from core.app import AppLogic

if __name__ == "__main__":
    # Creates the logic controller
    logic = AppLogic()

    # Creates the GUI window
    root_window = tk.Tk()

    # Passes the logic controller TO the GUI
    app_gui = ApplicationGUI(root_window, logic)

    # Starts the application
    app_gui.run()
