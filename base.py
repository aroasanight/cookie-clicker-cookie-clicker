# Update cookie counter displays
def update_counter_display():
    if session_counter_label and total_counter_label:
        session_counter_label.config(text=str(cookies_clicked_session))
        total_counter_label.config(text=str(cookies_clicked_total))

# Auto save options without showing a confirmation
def auto_save_options():
    global cookies_clicked_total
    
    try:
        # Get current options
        options = {
            'toggle_key': options_var['toggle_key'].get(),
            'check_interval_sec': int(interval_sec_var.get()),
            'check_interval_ms': int(interval_ms_var.get()),
            'confidence': float(confidence_var.get()),
            'image_path': options_var['image_path'].get(),
            'max_log_lines': MAX_LOG_LINES,
            'cookies_clicked_total': cookies_clicked_total
        }
        
        # Save to file silently
        with open(OPTIONS_FILE, 'wb') as f:
            pickle.dump(options, f)
            
    except Exception as e:
        print(f"Error auto-saving options: {e}")# Clear log button
    def clear_log():
        if log_text:
            log_text.config(state=tk.NORMAL)
            log_text.delete('1.0', tk.END)
            log_text.config(state=tk.DISABLED)
            log_message("Log cleared")
    
    ttk.Button(main_frame, text="Clear Log", command=clear_log).grid(row=12, column=0, columnspan=3, pady=5, sticky=tk.W)

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
DEFAULT_MAX_LOG_LINES = 1000
OPTIONS_FILE = 'options.pkl'

# Global variables
bot_running = False
stop_event = threading.Event()
golden_cookie_thread = None
keyboard_listener = None
log_text = None  # For the scrollable log window
MAX_LOG_LINES = 1000  # Maximum number of lines to keep in the log
cookies_clicked_session = 0  # Cookies clicked in current session
cookies_clicked_total = 0  # All-time cookies clicked

# Load saved options
def load_options():
    if os.path.exists(OPTIONS_FILE):
        try:
            with open(OPTIONS_FILE, 'rb') as f:
                options = pickle.load(f)
                # Update global cookie counter
                global cookies_clicked_total
                if 'cookies_clicked_total' in options:
                    cookies_clicked_total = options['cookies_clicked_total']
                return options
        except Exception as e:
            print(f"Error loading options: {e}")
    
    # Default options
    return {
        'toggle_key': DEFAULT_TOGGLE_KEY,
        'check_interval_sec': DEFAULT_CHECK_INTERVAL_SEC,
        'check_interval_ms': DEFAULT_CHECK_INTERVAL_MS,
        'confidence': DEFAULT_CONFIDENCE_THRESHOLD,
        'image_path': DEFAULT_GOLDEN_COOKIE_IMAGE,
        'max_log_lines': DEFAULT_MAX_LOG_LINES,
        'cookies_clicked_total': 0
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
        
        # Add the new log entry
        log_text.insert(tk.END, log_entry + "\n")
        
        # Check if we exceeded the maximum number of lines
        num_lines = int(log_text.index('end-1c').split('.')[0])
        if num_lines > MAX_LOG_LINES:
            # Calculate how many lines to remove
            lines_to_remove = num_lines - MAX_LOG_LINES
            # Delete the oldest lines
            log_text.delete('1.0', f"{lines_to_remove + 1}.0")
            
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
    global bot_running, cookies_clicked_session, cookies_clicked_total
    
    while not stop_event.is_set():
        if bot_running:
            try:
                # Get current values from the GUI
                confidence = float(confidence_var.get())
                image_path = options_var['image_path'].get()
                
                # Look for golden cookie
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    # Increment cookie counters
                    cookies_clicked_session += 1
                    cookies_clicked_total += 1
                    # Update the counter labels if they exist
                    update_counter_display()
                    
                    log_message(f"Found golden cookie at {location} (Session: {cookies_clicked_session}, Total: {cookies_clicked_total})")
                    original_pos = pyautogui.position()
                    pyautogui.click(location)
                    pyautogui.moveTo(original_pos)
                    
                    # Auto-save the updated total count
                    auto_save_options()
            except Exception as e:
                log_message(f"ERROR: {e}")
                
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
    global cookies_clicked_total
    
    # Update options from GUI
    options = {
        'toggle_key': options_var['toggle_key'].get(),
        'check_interval_sec': int(interval_sec_var.get()),
        'check_interval_ms': int(interval_ms_var.get()),
        'confidence': float(confidence_var.get()),
        'image_path': options_var['image_path'].get(),
        'max_log_lines': MAX_LOG_LINES,
        'cookies_clicked_total': cookies_clicked_total
    }
    
    # Save to file
    if save_options(options):
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
        
    # Restart the bot thread with new settings
    start_bot_thread()

# Create the main GUI window
def create_gui():
    global status_label, confidence_var, interval_sec_var, interval_ms_var, options_var, toggle_button, log_text, MAX_LOG_LINES
    global session_counter_label, total_counter_label
    
    # Load saved options
    options = load_options()
    
    # Create root window
    root = tk.Tk()
    root.title("Golden Cookie Bot")
    root.geometry("500x550")  # Increased height for log box and counters
    root.resizable(True, True)  # Allow resizing
    
    # Variables
    confidence_var = tk.StringVar(value=f"{options['confidence']:.2f}")
    interval_sec_var = tk.StringVar(value=str(options['check_interval_sec']))
    interval_ms_var = tk.StringVar(value=str(options['check_interval_ms']))
    
    options_var = {
        'toggle_key': tk.StringVar(value=options['toggle_key']),
        'image_path': tk.StringVar(value=options['image_path'])
    }
    
    # Create a variable for max log lines if it's in the options
    if 'max_log_lines' in options:
        MAX_LOG_LINES = options['max_log_lines']
    
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
    
    # Cookie counter section
    counter_frame = ttk.Frame(main_frame)
    counter_frame.grid(row=7, column=0, columnspan=3, pady=5)
    
    # Session counter
    session_counter_container = ttk.Frame(counter_frame)
    session_counter_container.pack(side=tk.LEFT, padx=(0, 20))
    
    ttk.Label(session_counter_container, text="Session Cookies:", font=("Arial", 9)).pack(side=tk.LEFT)
    session_counter_label = ttk.Label(session_counter_container, text=str(cookies_clicked_session), 
                                    font=("Arial", 9, "bold"))
    session_counter_label.pack(side=tk.LEFT, padx=(5, 0))
    
    # Reset button for session counter
    def reset_session_counter():
        global cookies_clicked_session
        cookies_clicked_session = 0
        update_counter_display()
        log_message("Session counter reset to 0")
        
    ttk.Button(session_counter_container, text="Reset", command=reset_session_counter, 
              width=5).pack(side=tk.LEFT, padx=(5, 0))
    
    # Total counter
    total_counter_container = ttk.Frame(counter_frame)
    total_counter_container.pack(side=tk.LEFT)
    
    ttk.Label(total_counter_container, text="Total Cookies:", font=("Arial", 9)).pack(side=tk.LEFT)
    total_counter_label = ttk.Label(total_counter_container, text=str(cookies_clicked_total), 
                                   font=("Arial", 9, "bold"))
    total_counter_label.pack(side=tk.LEFT, padx=(5, 0))
    
    # Reset button for total counter
    def reset_total_counter():
        global cookies_clicked_total
        cookies_clicked_total = 0
        update_counter_display()
        auto_save_options()
        log_message("Total cookies counter reset to 0")
        
    ttk.Button(total_counter_container, text="Reset", command=reset_total_counter, 
              width=5).pack(side=tk.LEFT, padx=(5, 0))
    
    # Hint for toggle key
    hint_text = f"Press {options['toggle_key']} to toggle bot ON/OFF"
    hint_label = ttk.Label(main_frame, text=hint_text, font=("Arial", 8), foreground="#666666")
    hint_label.grid(row=8, column=0, columnspan=3, pady=(0, 5))
    
    # Save button
    save_button = ttk.Button(main_frame, text="Save Settings", command=save_settings)
    save_button.grid(row=9, column=0, columnspan=3, pady=5)
    
    # Log section label
    log_label_frame = ttk.Frame(main_frame)
    log_label_frame.grid(row=10, column=0, columnspan=3, pady=(10, 5), sticky=tk.W)
    
    log_label = ttk.Label(log_label_frame, text="Activity Log", font=("Arial", 10, "bold"))
    log_label.pack(side=tk.LEFT)
    
    # Log lines configuration
    log_lines_frame = ttk.Frame(log_label_frame)
    log_lines_frame.pack(side=tk.RIGHT, padx=(10, 0))
    
    ttk.Label(log_lines_frame, text="Max lines:").pack(side=tk.LEFT)
    max_lines_var = tk.StringVar(value=str(MAX_LOG_LINES))
    max_lines_entry = ttk.Entry(log_lines_frame, textvariable=max_lines_var, width=5)
    max_lines_entry.pack(side=tk.LEFT, padx=(5, 0))
    
    # Function to update max lines
    def update_max_lines():
        global MAX_LOG_LINES
        try:
            new_max = int(max_lines_var.get())
            if new_max > 0:
                MAX_LOG_LINES = new_max
                options['max_log_lines'] = new_max
                save_options(options)
                log_message(f"Maximum log lines set to {MAX_LOG_LINES}")
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid number for maximum lines.")
    
    ttk.Button(log_lines_frame, text="Set", command=update_max_lines, width=3).pack(side=tk.LEFT, padx=(5, 0))
    
    # Scrollable log text box
    log_text = scrolledtext.ScrolledText(main_frame, height=10, width=50, wrap=tk.WORD)
    log_text.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    log_text.config(state=tk.DISABLED)  # Make it read-only
    
    # Configure the row with the log to expand
    main_frame.grid_rowconfigure(11, weight=1)
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
        log_message("Saving settings and shutting down...")
        
        # Save the current total cookies before exiting
        auto_save_options()
        
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