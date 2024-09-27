from pymxs import runtime as rt
from math import pi
import json
import qtmax

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui


class CameraImporter(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(CameraImporter, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.boxlayout = QtWidgets.QVBoxLayout(self)
        
        self.camFile = QtWidgets.QLineEdit()
        self.camFile.setText("")
        
        self.importButton = QtWidgets.QPushButton("Create camera")
        self.importButton.clicked.connect(self.createCamera)
        
        self.boxlayout.addWidget(self.camFile)
        self.boxlayout.addWidget(self.importButton)
        
        
    def createCamera(self):
        with open(self.camFile.text(), "r") as file:
            dict = json.load(file)
            
            matrix = dict["cameraTransform"]["rows"]

            maxMatrix = rt.Matrix3(rt.point3(matrix[0][0], matrix[1][0], matrix[2][0]), 
                             rt.point3(matrix[0][1], matrix[1][1], matrix[2][1]), 
                             rt.point3(matrix[0][2], matrix[1][2], matrix[2][2]), 
                             rt.point3(matrix[0][3], matrix[1][3], matrix[2][3]))

            hFov = dict["horizontalFieldOfView"]
            cam = rt.Freecamera()
            cam.transform = maxMatrix
            cam.fov = fov * (180/pi) 
        
    
if __name__ == "__main__":
    main_window = qtmax.GetQMaxMainWindow()
    widget = CameraImporter(parent=main_window)
    widget.setWindowTitle("Camera importer")
    widget.resize(300, 90)
    widget.show()
    