import sys
import math
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QComboBox, QSpinBox, QTextEdit, QTabWidget,
    QGroupBox, QGridLayout, QAction, QLineEdit, QMessageBox, QFormLayout,
    QShortcut, QToolButton
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QPoint, QEvent, QPointF
from PyQt5.QtGui import QKeySequence, QFont, QPainter, QPen, QBrush, QColor

# ----------------------------
# Serial Interface (placeholder/mock)
# ----------------------------
try:
    import serial
except ImportError:
    serial = None

class SerialInterface:
    def __init__(self, port='COM7', baudrate=115200):
        if serial is None:
            print("pySerial not installed; hardware commands will be mocked.")
            self.ser = None
            return
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
        except Exception as e:
            print("Failed to open serial port:", e)
            self.ser = None

    def send_command(self, command):
        if self.ser is not None and self.ser.is_open:
            self.ser.write((command + "\n").encode('utf-8'))
        else:
            print(f"[Mock] Command sent: {command}")

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

# ----------------------------
# Stepper Controller with advanced functions
# ----------------------------
class StepperController:
    def __init__(self, serial_interface):
        self.serial_interface = serial_interface
        self.running = False
        self.steps_per_rev = 200  # default full steps per revolution
        self.current_steps = 0    # simulated current steps
        self.calibration_offset_steps = 0
        # New parameters for acceleration and microstepping
        self.acceleration = 50    # RPM/s (default)
        self.deceleration = 50    # RPM/s (default)
        self.microstepping = 1    # multiplier: 1 = full step, 2 = half, etc.

    def start(self):
        self.serial_interface.send_command("START")
        self.running = True

    def stop(self):
        self.serial_interface.send_command("STOP")
        self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def set_speed(self, speed, unit="RPM"):
        self.serial_interface.send_command(f"SET_SPEED {speed} {unit}")

    def set_direction(self, direction):
        self.serial_interface.send_command(f"SET_DIRECTION {direction}")

    def step(self, steps):
        self.serial_interface.send_command(f"STEP {steps}")
        self.current_steps += steps

    def set_decay(self, decay_value):
        self.serial_interface.send_command(f"DECAY {decay_value}")

    def play_note(self, frequency, duration_ms):
        self.serial_interface.send_command(f"PLAY_NOTE {frequency} {duration_ms}")

    # Angle mapping functions
    def set_steps_per_rev(self, steps_rev):
        self.steps_per_rev = steps_rev

    def calibrate_zero(self):
        self.calibration_offset_steps = -self.current_steps
        self.serial_interface.send_command("CALIBRATE_ZERO")

    def move_to_angle(self, angle_degs):
        effective_steps = self.steps_per_rev * self.microstepping
        desired_steps = round(angle_degs / 360.0 * effective_steps)
        delta = desired_steps - (self.current_steps + self.calibration_offset_steps)
        self.step(delta)

    def get_angle_degs(self):
        effective_steps = self.steps_per_rev * self.microstepping
        raw_steps = self.current_steps + self.calibration_offset_steps
        angle = (raw_steps % effective_steps) * (360.0 / effective_steps)
        return angle

    # Advanced functions:
    def set_acceleration(self, accel):
        self.acceleration = accel
        self.serial_interface.send_command(f"SET_ACCELERATION {accel}")

    def set_deceleration(self, decel):
        self.deceleration = decel
        self.serial_interface.send_command(f"SET_DECELERATION {decel}")

    def home(self):
        self.serial_interface.send_command("HOME")
        self.current_steps = 0
        self.calibration_offset_steps = 0

    def move_relative(self, angle_degs):
        effective_steps = self.steps_per_rev * self.microstepping
        steps = round(angle_degs / 360.0 * effective_steps)
        self.step(steps)

    def set_microstepping(self, mode_multiplier):
        self.microstepping = mode_multiplier
        self.serial_interface.send_command(f"SET_MICROSTEPPING {mode_multiplier}")

# ----------------------------
# Helper function to create info icons (fixed size and no focus)
# ----------------------------
def createInfoIcon(tooltip_text):
    infoBtn = QToolButton()
    infoBtn.setText("i")
    infoBtn.setToolTip(tooltip_text)
    infoBtn.setAutoRaise(True)
    infoBtn.setFocusPolicy(Qt.NoFocus)
    infoBtn.setFixedSize(20, 20)
    infoBtn.setStyleSheet("color: #999; font-weight: bold;")
    return infoBtn

# ----------------------------
# Music Tab (with added tooltips)
# ----------------------------
class MusicTab(QWidget):
    notePressed = pyqtSignal(float, int)  # freq, duration

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Tuning & Duration configuration
        configLayout = QHBoxLayout()
        label1 = QLabel("Base Frequency (Hz):")
        label1.setToolTip("Set the starting frequency for note calculations.")
        configLayout.addWidget(label1)
        configLayout.addWidget(createInfoIcon("The base frequency is used to compute note frequencies using the semitone ratio."))
        self.baseFreqSpin = QSpinBox()
        self.baseFreqSpin.setRange(50, 2000)
        self.baseFreqSpin.setValue(220)
        self.baseFreqSpin.setToolTip("Base frequency for the keyboard notes.")
        configLayout.addWidget(self.baseFreqSpin)
        label2 = QLabel("Note Duration (ms):")
        label2.setToolTip("Duration that each note is played.")
        configLayout.addWidget(label2)
        configLayout.addWidget(createInfoIcon("Adjust how long (in ms) each note is played."))
        self.noteDurSpin = QSpinBox()
        self.noteDurSpin.setRange(50, 2000)
        self.noteDurSpin.setValue(500)
        self.noteDurSpin.setToolTip("Set the duration for each note (in milliseconds).")
        configLayout.addWidget(self.noteDurSpin)
        label3 = QLabel("Octave Shift:")
        label3.setToolTip("Shift the octave up or down for the notes.")
        configLayout.addWidget(label3)
        configLayout.addWidget(createInfoIcon("Positive values shift the pitch up; negative values shift it down."))
        self.octaveShiftSpin = QSpinBox()
        self.octaveShiftSpin.setRange(-4, 4)
        self.octaveShiftSpin.setValue(0)
        self.octaveShiftSpin.setToolTip("Adjust the octave (up or down).")
        configLayout.addWidget(self.octaveShiftSpin)
        layout.addLayout(configLayout)
        # Prominent keyboard visualization
        self.keySequence = "z x c v b n m a s d f g h j k l q w e r t y u i".split()
        keyWidget = QWidget()
        keyLayout = QHBoxLayout(keyWidget)
        keyLayout.setSpacing(5)
        keyLayout.setContentsMargins(5, 5, 5, 5)
        self.keys = []
        for i, letter in enumerate(self.keySequence):
            btn = QPushButton(letter.upper())
            btn.setFixedHeight(120)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: #ddd;
                    border: 2px solid #555;
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #ff9900;
                }
            """)
            btn.setToolTip(f"Play note: {letter.upper()}")
            btn.clicked.connect(lambda checked, idx=i: self.playSemitone(idx))
            keyLayout.addWidget(btn)
            self.keys.append(btn)
        layout.addWidget(keyWidget)
        # Instruction label
        instr = QLabel("Press keys: " + " ".join(self.keySequence).upper() +
                       "\nPress 'O' to transpose octave down, 'P' to transpose up.")
        instr.setStyleSheet("color: #ccc;")
        instr.setToolTip("Keyboard mapping: Use the displayed keys to play musical notes.")
        layout.addWidget(instr)
        # Log area
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        self.logText.setToolTip("Logs note events and parameters.")
        layout.addWidget(self.logText)

    def playSemitone(self, idx):
        baseFreq = self.baseFreqSpin.value()
        duration = self.noteDurSpin.value()
        octaveShift = self.octaveShiftSpin.value()
        semitone_ratio = 2 ** (1/12)
        freq = baseFreq * (semitone_ratio ** idx)
        freq *= (2 ** octaveShift)
        self.logText.append(f"Note {idx}: {freq:.2f} Hz, Duration: {duration} ms")
        self.controller.play_note(freq, duration)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            super().keyPressEvent(event)
            return
        pressed = event.text().lower()
        if pressed in self.keySequence:
            idx = self.keySequence.index(pressed)
            self.playSemitone(idx)
        elif pressed == 'o':
            self.octaveShiftSpin.setValue(self.octaveShiftSpin.value() - 1)
        elif pressed == 'p':
            self.octaveShiftSpin.setValue(self.octaveShiftSpin.value() + 1)
        else:
            super().keyPressEvent(event)

# ----------------------------
# Stepper Control Tab with Motor Mode dropdown, enhanced Start/Stop button, and executeToggleOrStep()
# ----------------------------
class StepperControlTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Start/Stop button at top (already added above mode group)
        self.toggleButton = QPushButton("Toggle Start/Stop (Alt+A)")
        self.toggleButton.setToolTip("Click to toggle motor start/stop (or execute a step in Step mode). Hotkey: Alt+A")
        self.toggleButton.setMinimumHeight(60)
        self.toggleButton.setStyleSheet("background-color: #3a3a3a; color: #ddd; font-size: 32px;")
        self.toggleButton.clicked.connect(lambda: self.controller.toggle())
        layout.addWidget(self.toggleButton)

        # Motor Mode Group
        modeGroup = QGroupBox("Motor Mode")
        modeGroup.setToolTip("Select the motor control mode. In 'Spin' mode the motor runs continuously; in 'Step' mode, a fixed number of steps are executed.")
        modeLayout = QHBoxLayout()
        modeLabel = QLabel("Mode:")
        modeLayout.addWidget(modeLabel)
        self.modeCombo = QComboBox()
        self.modeCombo.addItems(["Spin", "Step"])
        self.modeCombo.setToolTip("Choose between continuous spin or executing a single step move.")
        self.modeCombo.currentIndexChanged.connect(self.updateModeUI)
        modeLayout.addWidget(self.modeCombo)
        modeLayout.addWidget(createInfoIcon("Select 'Spin' for continuous rotation or 'Step' for one-shot step movement."))
        modeGroup.setLayout(modeLayout)
        layout.addWidget(modeGroup)

        # Mode Parameter container (shows Speed or Step Count)
        self.modeParamWidget = QWidget()
        self.modeParamLayout = QHBoxLayout()
        self.modeParamWidget.setLayout(self.modeParamLayout)
        self.modeParamLabel = QLabel("Speed (RPM):")
        self.modeParamSpin = QSpinBox()
        self.modeParamSpin.setRange(1, 5000)
        self.modeParamSpin.setValue(120)
        self.modeParamSpin.setToolTip("Set the motor speed in RPM when in Spin mode.")
        self.modeParamLayout.addWidget(self.modeParamLabel)
        self.modeParamLayout.addWidget(self.modeParamSpin)
        layout.addWidget(self.modeParamWidget)

        # Basic Controls Group
        basicGroup = QGroupBox("Basic Stepper Controls")
        basicGroup.setToolTip("Controls for motor direction and decay.")
        glayout = QGridLayout()
        # Direction control
        dirLabel = QLabel("Direction:")
        dirLabel.setToolTip("Select motor rotation direction (CW or CCW).")
        glayout.addWidget(dirLabel, 0, 0)
        self.directionCombo = QComboBox()
        self.directionCombo.addItems(["CW", "CCW"])
        self.directionCombo.setToolTip("Choose the rotation direction.")
        self.directionCombo.currentTextChanged.connect(lambda d: self.controller.set_direction(d))
        glayout.addWidget(self.directionCombo, 0, 1)
        glayout.addWidget(createInfoIcon("Select the desired rotation direction."), 0, 2)
        # Decay control
        decayLabel = QLabel("Decay:")
        decayLabel.setToolTip("Adjust the decay parameter for motor current control.")
        glayout.addWidget(decayLabel, 1, 0)
        self.decaySlider = QSlider(Qt.Horizontal)
        self.decaySlider.setRange(0, 100)
        self.decaySlider.setValue(50)
        self.decaySlider.setToolTip("Set the decay rate for motor current.")
        self.decaySlider.valueChanged.connect(lambda v: self.controller.set_decay(v))
        glayout.addWidget(self.decaySlider, 1, 1, 1, 2)
        basicGroup.setLayout(glayout)
        layout.addWidget(basicGroup)

        # Advanced Controls Group (greyed out with a notice)
        advGroup = QGroupBox("Advanced Controls (Under Development)")
        advGroup.setToolTip("These controls are under development and currently disabled.")
        advGroup.setEnabled(False)
        advLayout = QGridLayout()
        accLabel = QLabel("Acceleration (RPM/s):")
        accLabel.setToolTip("Set motor acceleration rate.")
        advLayout.addWidget(accLabel, 0, 0)
        self.accelSpin = QSpinBox()
        self.accelSpin.setRange(1, 1000)
        self.accelSpin.setValue(self.controller.acceleration)
        self.accelSpin.setToolTip("Change how quickly the motor speeds up.")
        self.accelSpin.valueChanged.connect(lambda v: self.controller.set_acceleration(v))
        advLayout.addWidget(self.accelSpin, 0, 1)
        decLabel = QLabel("Deceleration (RPM/s):")
        decLabel.setToolTip("Set motor deceleration rate.")
        advLayout.addWidget(decLabel, 1, 0)
        self.decelSpin = QSpinBox()
        self.decelSpin.setRange(1, 1000)
        self.decelSpin.setValue(self.controller.deceleration)
        self.decelSpin.setToolTip("Change how quickly the motor slows down.")
        self.decelSpin.valueChanged.connect(lambda v: self.controller.set_deceleration(v))
        advLayout.addWidget(self.decelSpin, 1, 1)
        microLabel = QLabel("Microstepping Mode:")
        microLabel.setToolTip("Select the microstepping resolution.")
        advLayout.addWidget(microLabel, 2, 0)
        self.microCombo = QComboBox()
        self.microCombo.addItems(["Full Step (x1)", "Half Step (x2)", "Quarter Step (x4)", "Eighth Step (x8)", "Sixteenth Step (x16)"])
        self.microCombo.setToolTip("Choose the microstepping setting.")
        self.microCombo.currentIndexChanged.connect(self.changeMicrostepping)
        advLayout.addWidget(self.microCombo, 2, 1)
        self.homeButton = QPushButton("Home Motor")
        self.homeButton.setToolTip("Set current position as home (zero) or perform a homing move.")
        self.homeButton.clicked.connect(self.controller.home)
        advLayout.addWidget(self.homeButton, 3, 0, 1, 2)
        noticeLabel = QLabel("Note: Advanced controls are under development and will be available in the next version.")
        noticeLabel.setStyleSheet("color: #888; font-style: italic;")
        advLayout.addWidget(noticeLabel, 4, 0, 1, 2)
        advGroup.setLayout(advLayout)
        layout.addWidget(advGroup)

        # Connect spin box value changes in Spin mode to update speed
        self.modeParamSpin.valueChanged.connect(self.updateSpeed)

        self.updateModeUI()

    def updateModeUI(self):
        mode = self.modeCombo.currentIndex()  # 0: Spin, 1: Step
        if mode == 0:
            self.modeParamLabel.setText("Speed (RPM):")
            self.modeParamSpin.setToolTip("Set the motor speed in RPM.")
            try:
                self.toggleButton.clicked.disconnect()
            except Exception:
                pass
            self.toggleButton.clicked.connect(lambda: self.controller.toggle())
            self.toggleButton.setText("Toggle Start/Stop (Alt+A)")
            self.toggleButton.setStyleSheet("background-color: #3a3a3a; color: #ddd; font-size: 32px;")
            # Update speed immediately when switching to spin mode:
            self.controller.set_speed(self.modeParamSpin.value(), "RPM")
        else:
            self.modeParamLabel.setText("Step Count:")
            self.modeParamSpin.setToolTip("Set the number of steps to execute.")
            self.controller.stop()
            try:
                self.toggleButton.clicked.disconnect()
            except Exception:
                pass
            self.toggleButton.clicked.connect(lambda: self.controller.step(self.modeParamSpin.value()))
            self.toggleButton.setText("Execute Step (Alt+A)")
            self.toggleButton.setStyleSheet("background-color: #ff9900; color: #222; font-weight: bold; font-size: 16px;")

    def updateSpeed(self, value):
        if self.modeCombo.currentIndex() == 0:
            self.controller.set_speed(value, "RPM")

    def changeMicrostepping(self, index):
        multipliers = [1, 2, 4, 8, 16]
        mode = multipliers[index]
        self.controller.set_microstepping(mode)

    def executeToggleOrStep(self):
        mode = self.modeCombo.currentIndex()
        if mode == 0:
            self.controller.toggle()
        else:
            self.controller.step(self.modeParamSpin.value())

# ----------------------------
# Angle Mapping Tab with Interactive Dial and Angle Display (with tooltips)
# ----------------------------
class AngleMappingTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAngle)
        self.timer.start(100)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        motorGroup = QGroupBox("Motor Selection")
        motorGroup.setToolTip("Select a motor type and set its steps per revolution.")
        mgLayout = QHBoxLayout()
        mgLayout.addWidget(QLabel("Motor:"))
        self.motorCombo = QComboBox()
        self.motorCombo.addItems(["NEMA17", "NEMA23", "28BYJ-48", "Custom"])
        self.motorCombo.setToolTip("Choose a common motor type or select Custom.")
        self.motorCombo.currentIndexChanged.connect(self.onMotorSelect)
        mgLayout.addWidget(self.motorCombo)
        mgLayout.addWidget(QLabel("Steps/Rev:"))
        self.stepsRevSpin = QSpinBox()
        self.stepsRevSpin.setRange(1, 100000)
        self.stepsRevSpin.setValue(200)
        self.stepsRevSpin.setToolTip("Set the number of full steps per revolution (adjust for microstepping).")
        self.stepsRevSpin.valueChanged.connect(lambda v: self.controller.set_steps_per_rev(v))
        mgLayout.addWidget(self.stepsRevSpin)
        motorGroup.setLayout(mgLayout)
        layout.addWidget(motorGroup)

        calGroup = QGroupBox("Calibration")
        calGroup.setToolTip("Calibrate the motor by setting the current position as zero.")
        calLayout = QHBoxLayout()
        self.calButton = QPushButton("Set Current as Zero")
        self.calButton.setToolTip("Calibrate current position as zero angle.")
        self.calButton.clicked.connect(self.controller.calibrate_zero)
        calLayout.addWidget(self.calButton)
        calGroup.setLayout(calLayout)
        layout.addWidget(calGroup)

        moveGroup = QGroupBox("Move to Angle")
        moveGroup.setToolTip("Command the motor to move to a specific angle.")
        mvLayout = QHBoxLayout()
        mvLayout.addWidget(QLabel("Angle (°):"))
        self.moveAngleSpin = QSpinBox()
        self.moveAngleSpin.setRange(0, 359)
        self.moveAngleSpin.setToolTip("Enter target angle (0–359 degrees).")
        mvLayout.addWidget(self.moveAngleSpin)
        self.moveBtn = QPushButton("Go")
        self.moveBtn.setToolTip("Move motor to the specified angle.")
        self.moveBtn.clicked.connect(self.onMoveAngle)
        mvLayout.addWidget(self.moveBtn)
        moveGroup.setLayout(mvLayout)
        layout.addWidget(moveGroup)

        self.currentAngleLabel = QLabel("Current Angle: 0°")
        self.currentAngleLabel.setToolTip("Displays current measured angle of the motor.")
        layout.addWidget(self.currentAngleLabel)

        self.dialWidget = AngleDialWidget(self.controller)
        self.dialWidget.setToolTip("Drag the dial to change target angle.")
        layout.addWidget(self.dialWidget)

    def onMotorSelect(self):
        choice = self.motorCombo.currentText()
        if choice == "NEMA17":
            self.stepsRevSpin.setValue(200)
        elif choice == "NEMA23":
            self.stepsRevSpin.setValue(200)
        elif choice == "28BYJ-48":
            self.stepsRevSpin.setValue(2048)
        self.controller.set_steps_per_rev(self.stepsRevSpin.value())

    def onMoveAngle(self):
        angle = self.moveAngleSpin.value()
        self.controller.move_to_angle(angle)
        self.dialWidget.setAngle(angle)

    def updateAngle(self):
        angle = self.controller.get_angle_degs()
        self.currentAngleLabel.setText(f"Current Angle: {angle:.1f}°")
        self.dialWidget.setAngle(angle)

# ----------------------------
# Interactive Angle Dial Widget (unchanged)
# ----------------------------
class AngleDialWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.currentAngle = 0.0
        self.dragging = False
        self.setMinimumSize(300, 300)

    def setAngle(self, angle):
        self.currentAngle = angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        size = min(rect.width(), rect.height())
        center = rect.center()
        radius = int(size * 0.4)
        painter.setPen(QPen(QColor("#888"), 2))
        painter.setBrush(QBrush(QColor("#333")))
        painter.drawEllipse(center, radius, radius)
        for deg in range(0, 360, 15):
            angleRad = math.radians(deg)
            if deg % 45 == 0:
                tickLength = 15
                penWidth = 2
            else:
                tickLength = 8
                penWidth = 1
            painter.setPen(QPen(QColor("#aaa"), penWidth))
            x1 = int(center.x() + radius * math.cos(angleRad))
            y1 = int(center.y() + radius * math.sin(angleRad))
            x2 = int(center.x() + (radius - tickLength) * math.cos(angleRad))
            y2 = int(center.y() + (radius - tickLength) * math.sin(angleRad))
            painter.drawLine(x1, y1, x2, y2)
            if deg % 45 == 0:
                labelDist = radius + 20
                lx = int(center.x() + labelDist * math.cos(angleRad))
                ly = int(center.y() + labelDist * math.sin(angleRad))
                painter.setPen(QPen(QColor("#ccc")))
                painter.drawText(lx - 10, ly + 5, f"{deg}°")
        painter.setPen(QPen(QColor("#ff9900"), 4))
        angleRad = math.radians(self.currentAngle)
        px = int(center.x() + radius * 0.9 * math.cos(angleRad))
        py = int(center.y() + radius * 0.9 * math.sin(angleRad))
        painter.drawLine(center.x(), center.y(), px, py)

    def mousePressEvent(self, event):
        center = self.rect().center()
        dx = event.pos().x() - center.x()
        dy = event.pos().y() - center.y()
        distance = math.hypot(dx, dy)
        radius = self.width() * 0.4
        if distance <= radius + 20:
            self.dragging = True
            self.updateAngleFromPos(event.pos())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.updateAngleFromPos(event.pos())

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            newAngle = self.currentAngle
            self.controller.move_to_angle(newAngle)

    def updateAngleFromPos(self, pos):
        center = self.rect().center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        self.currentAngle = angle
        self.update()

# ----------------------------
# Settings Tab (with improved tooltips)
# ----------------------------
class SettingsTab(QWidget):
    settingsApplied = pyqtSignal(dict, dict, dict, dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.globalHotkeys = {
            "Toggle Start/Stop": "Alt+A",
            "Stepper Tab": "Alt+1",
            "Music Tab": "Alt+2",
            "Settings Tab": "Alt+3",
            "Reset Serial Port": "Ctrl+Alt+R",
            "Increase Step Value": "Ctrl+Up",
            "Decrease Step Value": "Ctrl+Down",
            "Increase BPM": "Ctrl+Shift+Up",
            "Decrease BPM": "Ctrl+Shift+Down",
            "Increase Octave": "Ctrl+Shift+Right",
            "Decrease Octave": "Ctrl+Shift+Left"
        }
        self.whiteKeyMapping = {}
        self.blackKeyMapping = {}
        self.appearance = {"bgColor": "#2f2f2f"}
        self.initUI()
        self.loadDefaults()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        title = QLabel("Stepster Settings")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setToolTip("Configure global hotkeys and appearance settings.")
        layout.addWidget(title)
        ghGroup = QGroupBox("Global Hotkeys")
        ghLayout = QFormLayout()
        self.ghEdits = {}
        for action, key in self.globalHotkeys.items():
            edit = QLineEdit()
            edit.setToolTip(f"Set hotkey for: {action}")
            self.ghEdits[action] = edit
            ghLayout.addRow(QLabel(action + ":"), edit)
        ghGroup.setLayout(ghLayout)
        layout.addWidget(ghGroup)
        appGroup = QGroupBox("Appearance")
        appLayout = QFormLayout()
        self.bgColorEdit = QLineEdit()
        self.bgColorEdit.setToolTip("Set the main background color (e.g., #2f2f2f).")
        appLayout.addRow(QLabel("Background Color:"), self.bgColorEdit)
        appGroup.setLayout(appLayout)
        layout.addWidget(appGroup)
        applyBtn = QPushButton("Apply Settings")
        applyBtn.setToolTip("Click to apply all changed settings immediately.")
        applyBtn.clicked.connect(self.applySettings)
        layout.addWidget(applyBtn)
        layout.addStretch()

    def loadDefaults(self):
        for action, key in self.globalHotkeys.items():
            self.ghEdits[action].setText(key)
        self.bgColorEdit.setText(self.appearance["bgColor"])

    def applySettings(self):
        newGlobal = {action: self.ghEdits[action].text() for action in self.ghEdits}
        newWhite = {}
        newBlack = {}
        newAppearance = {"bgColor": self.bgColorEdit.text()}
        self.settingsApplied.emit(newGlobal, newWhite, newBlack, newAppearance)
        QMessageBox.information(self, "Settings", "Settings have been updated.")

# ----------------------------
# Main Window with Drivester branding and hotkey info area
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.globalHotkeys = {
            "Toggle Start/Stop": "Alt+A",
            "Stepper Tab": "Alt+1",
            "Music Tab": "Alt+2",
            "Settings Tab": "Alt+3",
            "Reset Serial Port": "Ctrl+Alt+R",
            "Increase Step Value": "Ctrl+Up",
            "Decrease Step Value": "Ctrl+Down",
            "Increase BPM": "Ctrl+Shift+Up",
            "Decrease BPM": "Ctrl+Shift+Down",
            "Increase Octave": "Ctrl+Shift+Right",
            "Decrease Octave": "Ctrl+Shift+Left"
        }
        self.shortcutList = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Drivester")
        self.resize(1200, 800)
        # Container with top branding and hotkey info
        container = QWidget()
        containerLayout = QVBoxLayout(container)
        # Branding Title
        brandingLabel = QLabel("Drivester")
        brandingLabel.setFont(QFont("Arial", 28, QFont.Bold))
        brandingLabel.setStyleSheet("color: #ff9900;")
        brandingLabel.setAlignment(Qt.AlignCenter)
        containerLayout.addWidget(brandingLabel)
        # Branding Subtitle
        brandingSubtitle = QLabel("https://github.com/jasonshaw0")
        brandingSubtitle.setFont(QFont("Arial", 12, QFont.Bold))
        brandingSubtitle.setStyleSheet("color: #ff9900;")
        brandingSubtitle.setAlignment(Qt.AlignCenter)
        containerLayout.addWidget(brandingSubtitle)
        # Hotkeys Info Area (smaller font, but not too small)
        hotkeysText = "Global Hotkeys:\n"
        for action, key in self.globalHotkeys.items():
            hotkeysText += f"  {action}: {key}\n"
        hotkeyLabel = QLabel(hotkeysText)
        hotkeyLabel.setStyleSheet("background-color: #444; color: #ddd; padding: 5px; font-size: 22px;")
        hotkeyLabel.setToolTip("List of all global hotkeys.")
        containerLayout.addWidget(hotkeyLabel)
        # Tab Widget
        self.tabWidget = QTabWidget()
        self.stepperTab = StepperControlTab(self.controller)
        self.musicTab = MusicTab(self.controller)
        self.angleTab = AngleMappingTab(self.controller)
        self.settingsTab = SettingsTab()
        self.settingsTab.settingsApplied.connect(self.applySettings)
        self.tabWidget.addTab(self.stepperTab, "Stepper")
        self.tabWidget.addTab(self.musicTab, "Music")
        self.tabWidget.addTab(self.angleTab, "Angle Mapping")
        self.tabWidget.addTab(self.settingsTab, "Settings")
        containerLayout.addWidget(self.tabWidget)
        self.setCentralWidget(container)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("File")
        exitAction = QAction("Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        helpMenu = menubar.addMenu("Help")
        aboutAction = QAction("About Drivester", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.updateGlobalShortcuts()
        self.applyStyleSheet()

    def updateGlobalShortcuts(self):
        for sc in self.shortcutList:
            sc.disconnect()
            del sc
        self.shortcutList.clear()
        mapping = self.globalHotkeys
        sc = QShortcut(QKeySequence(mapping["Toggle Start/Stop"]), self)
        sc.activated.connect(self.stepperTab.executeToggleOrStep)
        self.shortcutList.append(sc)
        stepperSc = QShortcut(QKeySequence(mapping["Stepper Tab"]), self)
        stepperSc.activated.connect(lambda: self.tabWidget.setCurrentWidget(self.stepperTab))
        self.shortcutList.append(stepperSc)
        musicSc = QShortcut(QKeySequence(mapping["Music Tab"]), self)
        musicSc.activated.connect(lambda: self.tabWidget.setCurrentWidget(self.musicTab))
        self.shortcutList.append(musicSc)
        settingsSc = QShortcut(QKeySequence(mapping["Settings Tab"]), self)
        settingsSc.activated.connect(lambda: self.tabWidget.setCurrentWidget(self.settingsTab))
        self.shortcutList.append(settingsSc)
        resetSc = QShortcut(QKeySequence(mapping["Reset Serial Port"]), self)
        resetSc.activated.connect(self.resetSerial)
        self.shortcutList.append(resetSc)
        incStep = QShortcut(QKeySequence(mapping["Increase Step Value"]), self)
        incStep.activated.connect(lambda: self.stepperTab.modeParamSpin.setValue(self.stepperTab.modeParamSpin.value() + 1))
        self.shortcutList.append(incStep)
        decStep = QShortcut(QKeySequence(mapping["Decrease Step Value"]), self)
        decStep.activated.connect(lambda: self.stepperTab.modeParamSpin.setValue(max(1, self.stepperTab.modeParamSpin.value() - 1)))
        self.shortcutList.append(decStep)

    def resetSerial(self):
        self.controller.serial_interface.close()
        print("Serial port reset (mock).")

    def showAbout(self):
        authorInfo = "\n\nCreated by Jason Shaw\nContact: admin@jason-shaw.com"
        msg = (
            "Drivester\nAdvanced Stepper & Music Controller\nVersion 1.0\n" +
            authorInfo +
            "\n\nGlobal Hotkeys:\n"
        )
        for action, key in self.globalHotkeys.items():
            msg += f"  {action}: {key}\n"
        QMessageBox.about(self, "About Drivester", msg)

    def applySettings(self, newGlobal, newWhite, newBlack, newAppearance):
        self.globalHotkeys = newGlobal
        self.updateGlobalShortcuts()
        self.applyStyleSheet(newAppearance["bgColor"])
        print("Settings applied & UI updated.")

    def applyStyleSheet(self, bg="#2f2f2f"):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg};
            }}
            QTabWidget::pane {{
                background-color: #2a2a2a;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #444;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
            QPushButton {{
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: #444;
            }}
            QLabel {{
                color: #ccc;
            }}
            QSpinBox, QLineEdit, QComboBox, QTextEdit {{
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #444;
                height: 6px;
                background: #333;
            }}
            QSlider::handle:horizontal {{
                background: #ff9900;
                width: 14px;
            }}
        """)

# Add the executeToggleOrStep method to StepperControlTab
def executeToggleOrStep(self):
    mode = self.modeCombo.currentIndex()
    if mode == 0:
        self.controller.toggle()
    else:
        self.controller.step(self.modeParamSpin.value())

StepperControlTab.executeToggleOrStep = executeToggleOrStep

# ----------------------------
# Main Entry
# ----------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Drivester")
    try:
        from qdarkstyle import load_stylesheet_pyqt5
        app.setStyleSheet(load_stylesheet_pyqt5())
    except ImportError:
        pass
    serial_interface = SerialInterface(port='COM7', baudrate=115200)
    controller = StepperController(serial_interface)
    # Set default speed at startup (Spin mode default)
    controller.set_speed(120, "RPM")
    mainWin = MainWindow(controller)
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
