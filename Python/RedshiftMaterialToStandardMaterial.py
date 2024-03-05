"""
Convert all redshift Materials in a scene to the rs standard Material
"""
import pymxs
rt = pymxs.runtime

oldShaders = rt.getClassInstances(rt.rsMaterial)
oldProperties = dir(rt.rsMaterial())

#list newpropertyName:[OldPropertyName, add values or custom flags for handling all the weird edge cases]
propertyMap = {"base_color":["diffuse_color"],
"base_color_weight":["diffuse_weight"],
"bump_input":["bump_input"],
"coat_roughness":["coat_roughness"],
"displacement_input":["displacement_input"],
"metalness":["refl_metalness"],
"ms_color":["ms_color0"],
"ms_radius":["ms_radius0"],
}

def replaceComponent(oldMat, newMat, prop):
    
    if(prop == "displacement_input" or prop == "bump_input"):
        setattr(newMat, prop, getattr(oldMat, propertyMap[prop][0]+"_map"))
        #mapAmountPropert
        setattr(newMat, prop + "_amount", getattr(oldMat, propertyMap[prop][0]+"_mapamount"))
        #mapEnabledProperty
        setattr(newMat, prop + "_enable", getattr(oldMat, propertyMap[prop][0]+"_mapenable"))
    else:
        #baseProperty
        setattr(newMat, prop, getattr(oldMat, propertyMap[prop][0]))
        #mapProperty
        setattr(newMat, prop + "_map", getattr(oldMat, propertyMap[prop][0]+"_map"))
        #mapAmountPropert
        setattr(newMat, prop + "_mapamount", getattr(oldMat, propertyMap[prop][0]+"_mapamount"))
        #mapEnabledProperty
        setattr(newMat, prop + "_mapenable", getattr(oldMat, propertyMap[prop][0]+"_mapenable"))

def replaceSetting(oldMat, newMat):
    for prop in oldProperties:
        setattr(newMat, prop, getattr(oldMat, prop))

for oldMat in oldShaders:
    newMat = rt.rsStandardMaterial()
    
    replaceSetting(oldMat, newMat)
    
    for prop in propertyMap:
        replaceComponent(oldMat, newMat, prop)
        
    rt.replaceInstances(oldMat, newMat)
    newMat.name = oldMat.name
