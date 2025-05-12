# Important Info

1. Use `main.py` for the latest. v1, v2, v3, v4, and base are all "backups" (ie functioning versions with lesser features).

2. Disable fancy graphics in Cookie Clicker's settings for Golden Cookie detection to function.

3. Ensure you're using provided `golden_cookie.png` and `big_cookie.png` images.

4. With the default delay of 0ms on the big cookie autoclicker, this may cause high CPU usage. If this becomes a problem, set it to 1ms or above and only 1 thread will run instead of 100.

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