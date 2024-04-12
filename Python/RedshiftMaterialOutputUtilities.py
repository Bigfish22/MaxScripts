from pymxs import runtime as rt
from PySide2 import QtCore, QtWidgets, QtGui
import qtmax
import os

rt.execute('fn storeIsolatedMaterial headNode = (global rsIsolatedMaterielStore = headNode)')

rt.execute("""MaterialInstanceCA = attributes rsClayHolder
            (
                parameters main rollout:params
               (
               originalMaterial type:#Material ui:originalMat
               )

            rollout params "Original Material"
               (
               materialButton originalMat
               )
            )""")

class RedshiftOutPutUltils(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(RedshiftOutPutUltils, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.isolateButton = QtWidgets.QPushButton("Isolate Map")
        self.isolateButton.clicked.connect(self.isolateMap)
        self.MoveCheckBox = QtWidgets.QCheckBox("Move Bump and Displacement")
        self.outPutButton = QtWidgets.QPushButton("Add output Node")
        self.outPutButton.clicked.connect(self.addOutputNodes)
        self.clayButton = QtWidgets.QPushButton("Add Clay")
        self.clayButton.clicked.connect(self.addClay)
        self.removeClayButton = QtWidgets.QPushButton("Remove Clay")
        self.removeClayButton.clicked.connect(self.removeClay)
        
        self.boxlayout = QtWidgets.QVBoxLayout(self)
        
        self.boxlayout.addWidget(self.isolateButton)
        self.boxlayout.addWidget(self.MoveCheckBox)
        self.boxlayout.addWidget(self.outPutButton)
        self.boxlayout.addWidget(self.clayButton)
        self.boxlayout.addWidget(self.removeClayButton)
        self.setLayout(self.boxlayout)

    def isolateMap(self):
        if rt.rsIsolatedMaterielStore != rt.undefined:
            for storedNode in rt.rsIsolatedMaterielStore:
                storedNode.surface_map = rt.undefined
            rt.rsIsolatedMaterielStore = rt.undefined
            
        mapNode = None
        headNodes = []
        
        slateView = rt.sme.GetView(rt.sme.activeView)
        selectedNodes = slateView.GetSelectedNodes()
        nodeLen = len(selectedNodes)
        if nodeLen > 0:
            mapNode = selectedNodes[0].reference
            for node in rt.refs.dependents(mapNode):
                if rt.classOf(node) == rt.rsMaterialOutput:
                    headNodes.append(node)
                    
        if mapNode and headNodes:
            for headNode in headNodes:
                headNode.surface_map = mapNode
            rt.storeIsolatedMaterial(headNodes)

    def __addOutputNode__(self, node, moveDispBump = False):
        newOutput = rt.rsMaterialOutput()
        rt.replaceInstances(node, newOutput)
        newOutput.surface = node
        if moveDispBump:
            if rt.classOf(node) == rt.rsStandardMaterial:
                newOutput.bumpMap = node.bump_input
                node.bump_input = rt.undefined
                newOutput.displacement = node.displacement_input
                node.displacement_input = rt.undefined
        
    def addOutputNodes(self):
        move = self.MoveCheckBox.isChecked()
        for geo in rt.selection:
            if rt.classOf(geo.material) == rt.rsMaterialOutput or geo.material == rt.undefined:
                continue
            if rt.classOf(geo.material) == rt.Multimaterial:
                for map in geo.material.materialList:
                    if map != rt.undefined and rt.classOf(map) != rt.rsMaterialOutput:
                        self.__addOutputNode__(map, move)
            else:
                self.__addOutputNode__(geo.material, move)
    
    def addClay(self):
        clayMaterial = rt.rsStandardMaterial()
        clayMaterial.name = "Clay_Override"
        clayMaterial.base_color = rt.color(134, 96, 43)
        clayMaterial.refl_roughness = 0.3
        
        for output in rt.getClassInstances(rt.rsMaterialOutput):
            rt.custAttributes.add(output, rt.MaterialInstanceCA)
            output.originalMaterial = output.surface
            output.surface = clayMaterial
            
    def removeClay(self):
        for output in rt.getClassInstances(rt.rsMaterialOutput):
            try:
                output.surface = output.originalMaterial
                rt.custAttributes.delete(output, rt.MaterialInstanceCA)
            except:
                pass

if __name__ == "__main__":
    main_window = qtmax.GetQMaxMainWindow()
    widget = RedshiftOutPutUltils(parent=main_window)
    widget.setWindowTitle("Redshift Output Utils")
    widget.resize(300, 200)
    widget.show()