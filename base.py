import pyautogui
import time
import threading
import pickle
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pynput import keyboard
from datetime import datetime

# Constants and defaults
DEFAULT_GOLDEN_COOKIE_IMAGE = 'golden_cookie.png'
DEFAULT_TOGGLE_KEY = 'f8'
DEFAULT_CHECK_INTERVAL_SEC = 0
DEFAULT_CHECK_INTERVAL_MS = 500
DEFAULT_CONFIDENCE_THRESHOLD = 0.90
OPTIONS_FILE = 'options.pkl'

# Global variables
bot_running = False
stop_event = threading.Event()
golden_cookie_thread = None
keyboard_listener = None
log_text = None  # For the scrollable log window

# Load saved options
def load_options():
    if os.path.exists(OPTIONS_FILE):
        try:
            with open(OPTIONS_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading options: {e}")
    
    # Default options
    return {
        'toggle_key': DEFAULT_TOGGLE_KEY,
        'check_interval_sec': DEFAULT_CHECK_INTERVAL_SEC,
        'check_interval_ms': DEFAULT_CHECK_INTERVAL_MS,
        'confidence': DEFAULT_CONFIDENCE_THRESHOLD,
        'image_path': DEFAULT_GOLDEN_COOKIE_IMAGE
    }

# Save options
def save_options(options):
    try:
        with open(OPTIONS_FILE, 'wb') as f:
            pickle.dump(options, f)
        print(f"Options saved to {OPTIONS_FILE}")
        return True
    except Exception as e:
        print(f"Error saving options: {e}")
        messagebox.showerror("Save Error", f"Could not save options: {e}")
        return False

# Toggle bot state
def toggle_bot():
    global bot_running
    bot_running = not bot_running
    update_status_display()
    status = "ON" if bot_running else "OFF"
    log_message(f"Bot toggled {status}")
    
# Log a message with timestamp to both console and log window
def log_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # Add to scrollable log if available
    if log_text:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, log_entry + "\n")
        log_text.see(tk.END)  # Auto-scroll to the bottom
        log_text.config(state=tk.DISABLED)

# Update the status display in the GUI
def update_status_display():
    if status_label:
        status_text = "ON" if bot_running else "OFF"
        status_color = "#4CAF50" if bot_running else "#F44336"  # Green or Red
        status_label.config(text=status_text, foreground=status_color)
        
    # Update toggle button text if it exists
    if toggle_button:
        button_text = "Turn OFF" if bot_running else "Turn ON"
        toggle_button.config(text=button_text)

# Key press event handler
def on_press(key):
    try:
        current_toggle_key = options_var['toggle_key'].get().lower()
        if hasattr(key, 'name') and key.name.lower() == current_toggle_key.lower():
            toggle_bot()
    except AttributeError:
        pass

# Cookie watcher function
def golden_cookie_watcher():
    global bot_running
    
    while not stop_event.is_set():
        if bot_running:
            try:
                # Get current values from the GUI
                confidence = float(confidence_var.get())
                image_path = options_var['image_path'].get()
                
                # Look for golden cookie
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    log_message(f"Found golden cookie at {location}")
                    original_pos = pyautogui.position()
                    pyautogui.click(location)
                    pyautogui.moveTo(original_pos)
            except Exception as e:
                # log_message(f"ERROR: {e}")
                pass
                
        # Calculate total interval in seconds
        interval_sec = int(interval_sec_var.get())
        interval_ms = int(interval_ms_var.get())
        total_interval = interval_sec + (interval_ms / 1000)
        
        # Sleep for the interval
        if total_interval > 0:
            time.sleep(total_interval)
        else:
            time.sleep(0.1)  # Minimum sleep to avoid CPU hogging

# Start the bot thread
def start_bot_thread():
    global golden_cookie_thread, keyboard_listener
    
    # Stop any existing thread
    if golden_cookie_thread and golden_cookie_thread.is_alive():
        stop_event.set()
        golden_cookie_thread.join(timeout=1)
        stop_event.clear()
    
    # Start new thread
    golden_cookie_thread = threading.Thread(target=golden_cookie_watcher)
    golden_cookie_thread.daemon = True
    golden_cookie_thread.start()
    
    # Start keyboard listener if needed
    if not keyboard_listener or not keyboard_listener.is_alive():
        keyboard_listener = keyboard.Listener(on_press=on_press)
        keyboard_listener.start()
    
    log_message(f"Press {options_var['toggle_key'].get().upper()} to toggle bot ON/OFF.")

# Save settings from GUI
def save_settings():
    # Update options from GUI
    options = {
        'toggle_key': options_var['toggle_key'].get(),
        'check_interval_sec': int(interval_sec_var.get()),
        'check_interval_ms': int(interval_ms_var.get()),
        'confidence': float(confidence_var.get()),
        'image_path': options_var['image_path'].get()
    }
    
    # Save to file
    if save_options(options):
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
        
    # Restart the bot thread with new settings
    start_bot_thread()

# Create the main GUI window
def create_gui():
    global status_label, confidence_var, interval_sec_var, interval_ms_var, options_var, toggle_button, log_text
    
    # Load saved options
    options = load_options()
    
    # Create root window
    root = tk.Tk()
    root.title("Golden Cookie Bot")
    root.geometry("500x500")  # Increased height for log box
    root.resizable(True, True)  # Allow resizing
    
    # Variables
    confidence_var = tk.StringVar(value=f"{options['confidence']:.2f}")
    interval_sec_var = tk.StringVar(value=str(options['check_interval_sec']))
    interval_ms_var = tk.StringVar(value=str(options['check_interval_ms']))
    
    options_var = {
        'toggle_key': tk.StringVar(value=options['toggle_key']),
        'image_path': tk.StringVar(value=options['image_path'])
    }
    
    # Main frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Golden Cookie Bot", font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
    
    # Confidence threshold
    ttk.Label(main_frame, text="Confidence Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
    confidence_entry = ttk.Entry(main_frame, textvariable=confidence_var, width=10)
    confidence_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
    
    # Check interval
    ttk.Label(main_frame, text="Check Interval:").grid(row=2, column=0, sticky=tk.W, pady=5)
    interval_frame = ttk.Frame(main_frame)
    interval_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
    
    interval_sec_entry = ttk.Entry(interval_frame, textvariable=interval_sec_var, width=3)
    interval_sec_entry.pack(side=tk.LEFT)
    ttk.Label(interval_frame, text="s").pack(side=tk.LEFT)
    
    interval_ms_entry = ttk.Entry(interval_frame, textvariable=interval_ms_var, width=3)
    interval_ms_entry.pack(side=tk.LEFT, padx=(5, 0))
    ttk.Label(interval_frame, text="ms").pack(side=tk.LEFT)
    
    # Toggle key
    ttk.Label(main_frame, text="Toggle Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
    toggle_key_entry = ttk.Entry(main_frame, textvariable=options_var['toggle_key'], width=10)
    toggle_key_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
    
    # Image path
    ttk.Label(main_frame, text="Image Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
    image_path_entry = ttk.Entry(main_frame, textvariable=options_var['image_path'], width=25)
    image_path_entry.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
    
    # Bot status
    status_frame = ttk.Frame(main_frame)
    status_frame.grid(row=5, column=0, columnspan=3, pady=10)
    
    ttk.Label(status_frame, text="Bot Status: ").pack(side=tk.LEFT)
    global status_label
    status_label = ttk.Label(status_frame, text="OFF", foreground="#F44336", font=("Arial", 10, "bold"))
    status_label.pack(side=tk.LEFT)
    
    # Toggle button
    toggle_button = ttk.Button(main_frame, text="Turn ON", command=toggle_bot)
    toggle_button.grid(row=6, column=0, columnspan=3, pady=5)
    
    # Hint for toggle key
    hint_text = f"Press {options['toggle_key']} to toggle bot ON/OFF"
    hint_label = ttk.Label(main_frame, text=hint_text, font=("Arial", 8), foreground="#666666")
    hint_label.grid(row=7, column=0, columnspan=3, pady=(0, 5))
    
    # Save button
    save_button = ttk.Button(main_frame, text="Save Settings", command=save_settings)
    save_button.grid(row=8, column=0, columnspan=3, pady=5)
    
    # Log section label
    log_label = ttk.Label(main_frame, text="Activity Log", font=("Arial", 10, "bold"))
    log_label.grid(row=9, column=0, columnspan=3, pady=(10, 5), sticky=tk.W)
    
    # Scrollable log text box
    log_text = scrolledtext.ScrolledText(main_frame, height=10, width=50, wrap=tk.WORD)
    log_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    log_text.config(state=tk.DISABLED)  # Make it read-only
    
    # Configure the row with the log to expand
    main_frame.grid_rowconfigure(10, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_columnconfigure(2, weight=1)
    
    # Update settings when the toggle key changes
    def update_hint(*args):
        hint_label.config(text=f"Press {options_var['toggle_key'].get()} to toggle bot ON/OFF")
    
    options_var['toggle_key'].trace_add("write", update_hint)
    
    # Start the bot thread
    start_bot_thread()
    
    # Add welcome message to log
    log_message("Bot started. Currently OFF.")
    
    # When window closes
    def on_closing():
        stop_event.set()
        if golden_cookie_thread and golden_cookie_thread.is_alive():
            golden_cookie_thread.join(timeout=1)
        if keyboard_listener and keyboard_listener.is_alive():
            keyboard_listener.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    return root

if __name__ == "__main__":
    root = create_gui()
    root.mainloop()