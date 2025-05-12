# Important

Disable fancy graphics in Cookie Clicker's settings for Golden Cookie detection to function.

# Requirements

This script relies on the four modules PyAutoGUI, pynput, Pillow, and OpenCV. Either run `pip install -r requirements.txt`, or manually install the followin four modules:

```
pyautogui
pynput
pillow
opencv-python
```

# Features

- Built-in autoclicker that automatically finds the big cookie

- Autoclicker automatically disables on mouse move (re-enables if it moved to click a golden cookie)

- Adjustable Confidence Thresholds from GUI (0-1), individually adjustable for both the Big and Golden cookies

- Adjustable interval between clicks for big cookie, and adjustable interval between checks for golden cookies

- Adjustable keybinds for toggling Golden and Big cookie autoclickers separately with any function key F1 through F24

- Settings memory between program launches

- Stats counter, separate for golden cookies and the big cookie. Separate persistant counter between program launches.

# Default parameters

- Golden Cookie autoclicker is bound to F8, with a 500ms delay between scanning the screen for golden cookies.

- Big Cookie autoclicker is bound to F9, with 1ms delay between clicks.