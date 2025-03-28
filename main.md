# Drivester

**Drivester** is a simple, keyboard-centric, and UI-based toolkit for testing and driving stepper motors at lightning speeds. 

## Features

- **Integrated Hardware Control:**  
  Directly communicate with stepper motor drivers via serial commands (or use a mocked serial interface for testing without hardware).

- **Integrated Musical Steppers:**  
  Mess with the age old trick of setting stepper motors to musical frequencies.

- **Real-Time Angle Mapping:**  
  Visualize and calibrate your motor's angle with an interactive dial.

- **Keyboard-Centric Operation:**  
  Global hotkeys allow you to control most functions without a mouse. The advantage is faster workflows, but you're able to use Drivester with whichever input you prefer. 

- **Packaging:**  
  Drivester can be packaged as a standalone desktop application using tools like PyInstaller for convenience.

---

## Installation

### Prerequisites
- Python 3.6 or higher
- `pip`

### Dependencies
Install required packages using:
```bash
pip install pyqt5 pyserial qdarkstyle
```

### Running in Development
Clone or download the repository and run:
```bash
python drivester.py
```

### Packaging as a Desktop App (Windows Example)
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   pyinstaller --name Drivester --icon=drivester_icon.ico --noconsole drivester.py
   ```
   This creates a standalone `Drivester.exe` that can be distributed.

---

## Usage

### Global Hotkeys
The default global hotkeys are:
- **Alt+A:** Toggle Start/Stop (or execute a step in Step mode)
- **Alt+1:** Switch to the Stepper Control tab
- **Alt+2:** Switch to the Music tab
- **Alt+3:** Switch to the Settings tab
- **Ctrl+Alt+R:** Reset Serial Port
- **Ctrl+Up / Ctrl+Down:** Increase/Decrease step value (in Stepper Control)
- **Ctrl+Shift+Up / Ctrl+Shift+Down:** Increase/Decrease BPM (in Music tab)
- **Ctrl+Shift+Right / Ctrl+Shift+Left:** Increase/Decrease Octave (in Music tab)

These can be modified in the Settings tab.

### Stepper Motor Music
Stepper motors can be set to resonate the frequencies of musical notes. This is a fully integrated feature in Drivester.   
- **Playing Notes:**  
  When the Music tab is active, use the keys `z x c v b n m a s d f g h j k l q w e r t y u i` to play notes from lowest to highest pitch.
- **Octave Transposition:**  
  Press `O` to shift the octave down or `P` to shift it up.
- **Configuration:**  
  Adjust the base frequency, note duration, and octave shift using the controls at the top of the Music tab.

### Angle Mapping Tab
- **Motor Selection:**  
  Choose your motor type from the presets or define your own parameters.
- **Calibration:**  
  Click "Set Current as Zero" to calibrate the current position as the zero angle.
- **Move to Angle:**  
  Enter a desired angle (0–359°) and click "Go" to command the motor.
- **Interactive Dial:**  
  The dial displays angle markings (minor ticks every 15° and major ticks every 45°). Drag the dial pointer to change the target angle; upon release, the motor is commanded to move to the new angle.
- **Real-Time Feedback:**  
  The current angle is continuously updated in the display.

### Stepper Control Tab
- **Basic Controls:**  
  Toggle motor start/stop, select direction, set speed, and execute a defined number of steps.
- **Modes:**  
  In continuous spin mode, the motor runs at a set speed. In step mode, pressing the toggle button executes a fixed number of steps.
- **Future Content:**  
  (Under development) Advanced parameters such as acceleration, deceleration, microstepping, homing, and multi-stepper support will become available in a later version.

### Settings Tab
- **Hotkey Remapping:**  
  Edit global hotkeys to customize keyboard shortcuts.
- **Appearance:**  
  Change the background color to match your preferences.
- **Apply Changes:**  
  Click "Apply Settings" to update the configuration immediately.

---

## Packaging & Distribution

To distribute Drivester as a standalone application:
1. Use PyInstaller to bundle the app into an executable:
   ```bash
   pyinstaller --name Drivester --icon=drivester_icon.ico --noconsole drivester.py
   ```
2. Optionally, create an installer (e.g., using Inno Setup on Windows) to package the executable with shortcuts and uninstall support.
3. The resulting application runs like any standard desktop program without requiring a separate terminal.

---

## Contributing

Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request on the repository.

---

## License

This project is licensed under the MIT License.

---

## Contact

For any inquiries or support, please contact admin@jason-shaw.com

---

Enjoy using Drivester!
```

