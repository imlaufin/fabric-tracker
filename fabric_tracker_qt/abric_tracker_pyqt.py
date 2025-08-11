# fabric_tracker_pyqt.py
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

class FabricTrackerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fabric Tracker - PyQt")
        self.setGeometry(100, 100, 800, 600)

        label = QLabel("Welcome to Fabric Tracker (PyQt)", self)
        label.move(50, 50)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = FabricTrackerMainWindow()
    main_win.show()
    sys.exit(app.exec_())
