from pxr import Usd, UsdGeom, UsdUtils, Sdf, Gf
import os
from pymxs import runtime as rt

from PySide2 import QtCore, QtWidgets, QtGui
import qtmax

def exportShapes(tyflowNode, assetFolder):
    shapes = tyflowNode.getAllParticleShapeMeshes()
    nodes = []
    nodeIndex = []
    assets = []
    
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
            
    for node in nodes:
        rt.clearSelection()
        rt.select(node)
        fileName = node.name + ".usd"
        assetPath = os.path.join(assetFolder, fileName)
        rt.exportFile(assetPath, rt.name("noPrompt"), selectedOnly = True)
        assets.append(assetPath)
    rt.delete(nodes)
    
    return assets, nodeIndex

def cacheScene(targetFile, pointInstanceName, assetSubFolder):
    sel = rt.selection
    tyflowNode = sel[0]

    print(targetFile)

    if os.path.exists(targetFile):
        stage = Usd.Stage.Open(targetFile)
        stage.GetRootLayer().Clear()
    else:
        stage = Usd.Stage.CreateNew(targetFile)
        
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    pointInstancer = UsdGeom.PointInstancer.Define(stage, "/root/" + pointInstanceName)


    tyflowNode.updateParticles(0)

    assets, nodeIndexArray = exportShapes(tyflowNode, os.path.join(os.path.dirname(targetFile), assetSubFolder))

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


    pointInstancer.CreatePositionsAttr().Set(positionsArray)
    pointInstancer.CreateOrientationsAttr().Set(rotationArray)
    pointInstancer.CreateScalesAttr().Set(scaleArray)

    protoArray = pointInstancer.CreatePrototypesRel()
    pointInstancer.CreateProtoIndicesAttr().Set(nodeIndexArray)
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
        self.targetFile = QtWidgets.QLineEdit()
        self.targetFile.setText("C:/USDDev/tyflow01.usda")
        
        textLabelSubFolder = QtWidgets.QLabel("Assets subfolder:")
        self.subFolder = QtWidgets.QLineEdit()
        self.subFolder.setText("assets")
        
        textLabelPointName = QtWidgets.QLabel("PointInstancer Name:")
        self.PointName = QtWidgets.QLineEdit()
        self.PointName.setText("pointy")
        
        self.cacheButton = QtWidgets.QPushButton("Cache")
        self.cacheButton.clicked.connect(self.cacheButtonClick)
        
        self.boxlayout.addWidget(textLabelfilePath)
        self.boxlayout.addWidget(self.targetFile)
        self.boxlayout.addWidget(textLabelSubFolder)
        self.boxlayout.addWidget(self.subFolder)
        self.boxlayout.addWidget(textLabelPointName)
        self.boxlayout.addWidget(self.PointName)
        self.boxlayout.addStretch(0)
        self.boxlayout.addWidget(self.cacheButton)
        
        
    
    def cacheButtonClick(self):
        sel = rt.selection
        if len(sel) != 1:
            print("invalid selection, make sure to only selection a single tyflow object")
        elif rt.classOf(rt.selection[0]) == rt.tyFlow:
            cacheScene(self.targetFile.text(), self.PointName.text(), self.subFolder.text())
        else:
            print("tyflow object not selected")
        
    
    
if __name__ == "__main__":
    main_window = qtmax.GetQMaxMainWindow()
    widget = TyUSDCache(parent=main_window)
    widget.setWindowTitle("TyFlow USD Cache")
    widget.resize(335, 300)
    widget.show()
    