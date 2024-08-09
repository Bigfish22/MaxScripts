from pxr import Usd, UsdGeom, UsdUtils, Sdf, Gf
import os
from pymxs import runtime as rt

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except:
    from PySide6 import QtCore, QtWidgets, QtGui
    
import qtmax

def findUniqueShapes(tyflowNode, nodesList):
    shapes = tyflowNode.getAllParticleShapeMeshes()
    nodeIndex = []
    nodes = nodesList
    
    for shape in shapes:
        if len(nodes) == 0:
            meshNode = rt.mesh()
            meshNode.mesh = shape
            nodes.append(meshNode)
            nodeIndex.append(0)
        else:
            found = False
            for i in range(len(nodes)):
                nodetriMesh = nodes[i].mesh
                if nodetriMesh.numverts == shape.numverts:
                    if rt.getVert(nodetriMesh, 1) == rt.getVert(shape, 1) and rt.getVert(nodetriMesh, shape.numverts) == rt.getVert(shape, shape.numverts):
                        nodeIndex.append(i)
                        found = True
                        break
            if found == False:
                meshNode = rt.mesh()
                meshNode.mesh = shape
                nodes.append(meshNode)
                nodeIndex.append(i + 1)
            
    return nodeIndex, nodes
    
def exportShapes(nodes, assetFolder):
    assets = []
    
    for node in nodes:
        singleNode = []
        singleNode.append(node)
        fileName = node.name + ".usd"
        assetPath = os.path.join(assetFolder, fileName)
        UsdOptions = rt.USDExporter.UIOptions
        UsdOptions.Meshes = True
        rt.USDExporter.ExportFile(assetPath, contentSource = rt.name("nodeList"), exportOptions = UsdOptions, nodeList = node)
        assets.append(assetPath)
        
    rt.delete(nodes)
    return assets

def cacheScene(targetFile, pointInstancePath, assetSubFolder, frameRange):
    sel = rt.selection
    tyflowNode = sel[0]

    print(targetFile)

    if os.path.exists(targetFile):
        stage = Usd.Stage.Open(targetFile)
        stage.GetRootLayer().Clear()
    else:
        stage = Usd.Stage.CreateNew(targetFile)
        
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    pointInstancer = UsdGeom.PointInstancer.Define(stage, pointInstancePath)

    posAttr = pointInstancer.CreatePositionsAttr()
    orientAttr = pointInstancer.CreateOrientationsAttr()
    scalesAttr = pointInstancer.CreateScalesAttr()
    protoIndicesAttr = pointInstancer.CreateProtoIndicesAttr()
    
    nodes = []
    for frame in range(frameRange[0], frameRange[1]+1):
        tyflowNode.updateParticles(frame)

        nodeIndexArray, nodes = findUniqueShapes(tyflowNode, nodes)

        positionsArray = []
        rotationArray = []
        scaleArray = []

        for matrix in tyflowNode.getAllParticleTMs():
            pos = matrix.position
            positionsArray.append(Gf.Vec3f(pos[0], pos[1], pos[2]))
            
            rotation = rt.normalize(matrix.rotation)
            rotationArray.append(Gf.Quath(-rotation.w, rotation.x, rotation.y, rotation.z))
            
            scale = matrix.scale
            scaleArray.append(Gf.Vec3f(scale[0], scale[1], scale[2]))
    
        if frameRange[0] != frameRange[1]:
            #set framerate
            stage.SetFramesPerSecond(rt.frameRate)
            
            posAttr.Set(positionsArray, frame)
            orientAttr.Set(rotationArray, frame)
            scalesAttr.Set(scaleArray, frame)
            
            protoIndicesAttr.Set(nodeIndexArray, frame)
        else:
            posAttr.Set(positionsArray)
            orientAttr.Set(rotationArray)
            scalesAttr.Set(scaleArray)
            
            protoIndicesAttr.Set(nodeIndexArray)
     
    assets = exportShapes(nodes, os.path.join(os.path.dirname(targetFile), assetSubFolder))


    protoArray = pointInstancer.CreatePrototypesRel()
    shapeId = 0
    for asset in assets:
        refPrim = stage.DefinePrim(pointInstancer.GetPath().AppendPath("shape" + str(shapeId)))
        refs = refPrim.GetReferences()
        refs.AddReference(asset)
        protoArray.AddTarget(refPrim.GetPath())
        shapeId += 1

    stage.Save()
    
class TyUSDCache(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(TyUSDCache, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.boxlayout = QtWidgets.QVBoxLayout(self)
        
        textLabelfilePath = QtWidgets.QLabel("File path:")
        self.fileBox = QtWidgets.QWidget()
        self.fileBoxLayout = QtWidgets.QHBoxLayout(self.fileBox)
        
        self.targetFile = QtWidgets.QLineEdit()
        self.targetFile.setText("C:/USDDev/tyflow01.usda")
        self.targetFileButton = QtWidgets.QPushButton("...")
        self.targetFileButton.clicked.connect(self.setFilePathClick)
        
        self.fileBoxLayout.addWidget(self.targetFile)
        self.fileBoxLayout.addWidget(self.targetFileButton)
        
        
        textLabelSubFolder = QtWidgets.QLabel("Assets subfolder:")
        self.subFolder = QtWidgets.QLineEdit()
        self.subFolder.setText("assets")
        
        textLabelPointName = QtWidgets.QLabel("PointInstancer Path:")
        self.PointName = QtWidgets.QLineEdit()
        self.PointName.setText("/root/pointy")
        
        #Time values
        textLabelTimeRange = QtWidgets.QLabel("Time Range:")
        self.timeBox = QtWidgets.QWidget()
        self.timeBoxLayout = QtWidgets.QHBoxLayout(self.timeBox)
        self.startTime = QtWidgets.QSpinBox()
        self.startTime.setRange(-10000, 10000)
        self.endTime = QtWidgets.QSpinBox()
        self.endTime.setRange(-10000, 10000)
        self.getTimeRangeFromMaxButton = QtWidgets.QPushButton("Get From time Slider")
        self.getTimeRangeFromMaxButton.clicked.connect(self.getTimeFromMaxClicked)
        
        self.timeBoxLayout.addWidget(self.startTime)
        self.timeBoxLayout.addWidget(self.endTime)
        self.timeBoxLayout.addWidget(self.getTimeRangeFromMaxButton)
        
        self.cacheButton = QtWidgets.QPushButton("Cache")
        self.cacheButton.clicked.connect(self.cacheButtonClick)
        
        self.boxlayout.addWidget(textLabelfilePath)
        self.boxlayout.addWidget(self.fileBox)
        self.boxlayout.addWidget(textLabelSubFolder)
        self.boxlayout.addWidget(self.subFolder)
        self.boxlayout.addWidget(textLabelPointName)
        self.boxlayout.addWidget(self.PointName)
        self.boxlayout.addWidget(textLabelTimeRange)
        self.boxlayout.addWidget(self.timeBox)
        self.boxlayout.addStretch(0)
        self.boxlayout.addWidget(self.cacheButton)
        
        
    
    def cacheButtonClick(self):
        sel = rt.selection
        if len(sel) != 1:
            print("invalid selection, make sure to only selection a single tyflow object")
        elif rt.classOf(rt.selection[0]) == rt.tyFlow:
            cacheScene(self.targetFile.text(), self.PointName.text(), self.subFolder.text(), [self.startTime.value(), self.endTime.value()])
        else:
            print("tyflow object not selected")
        
    def setFilePathClick(self):
        folder = os.path.dirname(self.targetFile.text())
        path = QtWidgets.QFileDialog.getSaveFileName(self, str("Save usd"), folder, str("Usd files (*.usd, *.usda)"))
        if len(path[0]) > 0:
            self.targetFile.setText(path[0])
            
    def getTimeFromMaxClicked(self):
        print(rt.animationRange.end)
        self.startTime.setValue(int(rt.animationRange.start))
        self.endTime.setValue(int(rt.animationRange.end))
        
    
    
if __name__ == "__main__":
    main_window = qtmax.GetQMaxMainWindow()
    widget = TyUSDCache(parent=main_window)
    widget.setWindowTitle("TyFlow USD Cache")
    widget.resize(335, 300)
    widget.show()
    