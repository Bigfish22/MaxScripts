from pxr import Usd, UsdGeom, UsdUtils, Sdf, Gf
import os
from pymxs import runtime as rt
import time

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

def cacheScene(targetFile, pointInstancePath, assetSubFolder, frameRange, cachePos, cacheRot, cacheScale, cacheVel, cacheVelScale):
    processStart = time.perf_counter()
    sel = rt.selection
    tyflowNode = sel[0]

    print(targetFile)

    if os.path.exists(targetFile):
        stage = Usd.Stage.Open(targetFile)
        stage.GetRootLayer().Clear()
    else:
        stage = Usd.Stage.CreateNew(targetFile)
        
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    unitToMeters = {rt.name("inches") : 0.0254, rt.name("feet") : 0.3048, rt.name("miles") : 1609.34, rt.name("millimeters") : 0.001, rt.name("centimeters") : 0.01, rt.name("meters") : 1, rt.name("kilometers") : 1000}
    UsdGeom.SetStageMetersPerUnit(stage, unitToMeters[rt.units.SystemType])

    pointInstancer = UsdGeom.PointInstancer.Define(stage, pointInstancePath)
    
    if cachePos:
        posAttr = pointInstancer.CreatePositionsAttr()
    if cacheRot:
        orientAttr = pointInstancer.CreateOrientationsAttr()
    if cacheScale:
        scalesAttr = pointInstancer.CreateScalesAttr()
    if cacheVel:
        velAttr = pointInstancer.CreateVelocitiesAttr()
    
    protoIndicesAttr = pointInstancer.CreateProtoIndicesAttr()
    
    animated = False
    if frameRange[0] != frameRange[1]:
        animated = True
    else:
        cacheVel = False
    
    nodes = []
    for frame in range(frameRange[0], frameRange[1]+1):
        tyflowNode.updateParticles(frame)

        nodeIndexArray, nodes = findUniqueShapes(tyflowNode, nodes)

        positionsArray = []
        rotationArray = []
        scaleArray = []
        velArray = []
        
        if cacheVel:
            velocities = tyflowNode.getAllParticleVelocities()
        for i, matrix in enumerate(tyflowNode.getAllParticleTMs()):
            
            if cachePos:
                pos = matrix.position
                positionsArray.append(Gf.Vec3f(pos[0], pos[1], pos[2]))
            if cacheRot:
                rotation = rt.normalize(matrix.rotation)
                rotationArray.append(Gf.Quath(-rotation.w, rotation.x, rotation.y, rotation.z))
            if cacheScale:
                scale = matrix.scale
                scaleArray.append(Gf.Vec3f(scale[0], scale[1], scale[2]))
            
            if cacheVel:
                velocity = velocities[i] * cacheVelScale
                velArray.append(Gf.Vec3f(velocity[0], velocity[1], velocity[2]))
            
        if animated:
            if cachePos:
                posAttr.Set(positionsArray, frame)
            if cacheRot:
                orientAttr.Set(rotationArray, frame)
            if cacheScale:
                scalesAttr.Set(scaleArray, frame)
            if cacheVel:
                velAttr.Set(velArray, frame)
            
            protoIndicesAttr.Set(nodeIndexArray, frame)
        else:
            if cachePos:
                posAttr.Set(positionsArray)
            if cacheRot:
                orientAttr.Set(rotationArray)
            if cacheScale:
                scalesAttr.Set(scaleArray)
            
            protoIndicesAttr.Set(nodeIndexArray)
     
    assets = exportShapes(nodes, os.path.join(os.path.dirname(targetFile), assetSubFolder))

    if frameRange[0] != frameRange[1]:
        #save time settings
        stage.SetFramesPerSecond(rt.frameRate)
        stage.SetStartTimeCode(frameRange[0])
        stage.SetEndTimeCode(frameRange[1])
    
    protoArray = pointInstancer.CreatePrototypesRel()
    shapeId = 0
    for asset in assets:
        refPrim = stage.DefinePrim(pointInstancer.GetPath().AppendPath("shape" + str(shapeId)))
        refs = refPrim.GetReferences()
        refs.AddReference(asset)
        protoArray.AddTarget(refPrim.GetPath())
        shapeId += 1

    stage.Save()
    processEnd = time.perf_counter()
    print(f"cache Took {processEnd - processStart:0.4f} seconds")
    
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
        
        
        #channels
        self.channelEnablePos = QtWidgets.QCheckBox("Position")
        self.channelEnablePos.setChecked(True)
        self.channelEnableRot = QtWidgets.QCheckBox("Rotation")
        self.channelEnableRot.setChecked(True)
        self.channelEnableScale = QtWidgets.QCheckBox("Scale")
        self.channelEnableScale.setChecked(True)
        
        self.velBox = QtWidgets.QWidget()
        self.velBoxLayout = QtWidgets.QHBoxLayout(self.velBox)
        self.channelEnableVel = QtWidgets.QCheckBox("Velocity")
        self.channelEnableVel.setChecked(True)
        self.channelScaleVel = QtWidgets.QSpinBox()
        self.channelScaleVel.setRange(-10000, 10000)
        self.channelScaleVel.setValue(1)
        self.velBoxLayout.addWidget(self.channelEnableVel)
        self.velBoxLayout.addWidget(QtWidgets.QLabel("Scale:"))
        self.velBoxLayout.addWidget(self.channelScaleVel)
        
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
        
        self.boxlayout.addWidget(self.channelEnablePos)
        self.boxlayout.addWidget(self.channelEnableRot)
        self.boxlayout.addWidget(self.channelEnableScale)
        
        self.boxlayout.addWidget(self.velBox)
        
        self.boxlayout.addStretch(0)
        self.boxlayout.addWidget(self.cacheButton)
        
        
    
    def cacheButtonClick(self):
        sel = rt.selection
        if len(sel) != 1:
            print("invalid selection, make sure to only selection a single tyflow object")
        elif rt.classOf(rt.selection[0]) == rt.tyFlow:
            pos = self.channelEnablePos.isChecked()
            rot = self.channelEnableRot.isChecked()
            scale = self.channelEnableScale.isChecked()
            vel = self.channelEnableVel.isChecked()
            velScale = self.channelScaleVel.value()
            
            cacheScene(self.targetFile.text(), self.PointName.text(), self.subFolder.text(), [self.startTime.value(), self.endTime.value()], pos, rot, scale, vel, velScale)
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
    widget.resize(335, 600)
    widget.show()
    