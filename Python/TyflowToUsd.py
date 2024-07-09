from pxr import Usd, UsdGeom, UsdUtils, Sdf, Gf
import os
from pymxs import runtime as rt

sel = rt.selection

targetFile = "C:/USDDev/tyflow01.usda"

if os.path.exists(targetFile):
    stage = Usd.Stage.Open(targetFile)
    stage.GetRootLayer().Clear()
else:
    stage = Usd.Stage.CreateNew(targetFile)
    
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

pointInstancer = UsdGeom.PointInstancer.Define(stage, "/root/pointyBoi")
sphere = UsdGeom.Sphere.Define(stage, "/root/pointyBoi/sphere")
sphere.CreateRadiusAttr().Set(0.05)


sel[0].updateParticles(0)
positionsArray = sel[0].getAllParticlePositions()
vtArray = []
indexArray = []

for pos in positionsArray:
    vtArray.append(Gf.Vec3f(pos[0], pos[1], pos[2]))
    indexArray.append(0)

pointInstancer.CreatePositionsAttr().Set(vtArray)
protoArray = pointInstancer.CreatePrototypesRel()
pointInstancer.CreateProtoIndicesAttr().Set(indexArray)

protoArray.AddTarget(sphere.GetPath())

stage.Save()
