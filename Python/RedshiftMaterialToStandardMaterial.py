"""
Convert all redshift Materials in a scene to the rs standard Material
"""
import pymxs
rt = pymxs.runtime

oldShaders = rt.getClassInstances(rt.rsMaterial)
oldProperties = rt.getPropNames(rt.rsMaterial())

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
        rt.setProperty(newMat, prop, rt.getProperty(oldMat, propertyMap[prop][0]+"_map"))
        #mapAmountPropert
        rt.setProperty(newMat, prop + "_amount", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapamount"))
        #mapEnabledProperty
        rt.setProperty(newMat, prop + "_enable", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapenable"))
    elif (prop == "ms_radius"):
        #baseProperty
        radiusValue = rt.getProperty(oldMat, propertyMap[prop][0])
        rt.setProperty(newMat, prop, rt.point3(radiusValue, radiusValue, radiusValue))
        #mapProperty
        rt.setProperty(newMat, prop + "_map", rt.getProperty(oldMat, propertyMap[prop][0]+"_map"))
        #mapAmountPropert
        rt.setProperty(newMat, prop + "_mapamount", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapamount"))
        #mapEnabledProperty
        rt.setProperty(newMat, prop + "_mapenable", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapenable"))
    else:
        #baseProperty
        rt.setProperty(newMat, prop, rt.getProperty(oldMat, propertyMap[prop][0]))
        #mapProperty
        rt.setProperty(newMat, prop + "_map", rt.getProperty(oldMat, propertyMap[prop][0]+"_map"))
        #mapAmountPropert
        rt.setProperty(newMat, prop + "_mapamount", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapamount"))
        #mapEnabledProperty
        rt.setProperty(newMat, prop + "_mapenable", rt.getProperty(oldMat, propertyMap[prop][0]+"_mapenable"))

def replaceSetting(oldMat, newMat):
    for prop in oldProperties:
        try:
            rt.setProperty(newMat, str(prop), rt.getProperty(oldMat, str(prop)))
        except:
            pass
            
for oldMat in oldShaders:
    newMat = rt.rsStandardMaterial()
        
    replaceSetting(oldMat, newMat)
        
    for prop in propertyMap:
        replaceComponent(oldMat, newMat, prop)
            
    rt.replaceInstances(oldMat, newMat)
    newMat.name = oldMat.name