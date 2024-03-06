"""
convert UsdPreviewSurface Materials to redshiftStandardMaterial
"""

import pymxs
rt = pymxs.runtime

mapping = {"diffuseColor"    :"base_color",
        "diffuseColor_map" :"base_color_map",
        "metallic"         :"metalness",
        "metallic_map"     :"metalness_map",
        "specularcolor"    :"refl_color",
        "specularColor_map":"refl_color_map",
        "roughness"        :"refl_roughness",
        "roughness_map"    :"refl_roughness_map",
        "normal_map"       :"bump_input",
        "emissiveColor"    :"emission_color",
        "emissiveColor_map":"emission_color_map",
        "displacement_map" :"displacement_input",
        "ior"              :"refl_ior",
        "ior_map"          :"refl_ior_map",
        "clearcoat"        :"coat_weight",
        "clearcoat_map"    :"coat_weight_map",
        "clearcoatRoughness":"coat_roughness",
        "clearcoatRoughness_map":"coat_roughness_map"}

def handleMap(material, slot):
    textureMap = getattr(material, slot)
    if textureMap is not None:
        filePath = textureMap.sourcemap.filename
        
        rsTexture = rt.rsTexture()
        rsTexture.name = textureMap.name
        rsTexture.tex0_filename = filePath
        if slot == "diffuseColor_map":
            rsTexture.tex0_colorSpace = 'sRGB'
            setattr(rsMat, mapping[slot], rsTexture)
        elif slot == "normal_map":
            rsTexture.tex0_colorSpace = 'Raw'
            bump = rt.rsBumpMap()
            bump.Input_map = rsTexture
            bump.inputType = 1
            setattr(rsMat, mapping[slot], bump)
        else:
            rsTexture.tex0_colorSpace = 'Raw'
            setattr(rsMat, mapping[slot], rsTexture)

for material in rt.getclassinstances(rt.MaxUsdPreviewSurface):
    rsMat = rt.rsStandardMaterial()
    for slot in mapping:
        if slot.endswith("_map"):
            handleMap(material, slot)
        else:
            previewAttr = getattr(material, slot)
            if mapping[slot]:
                redshiftAttr = setattr(material, mapping[slot], previewAttr)

        if material.opacityThreshold > 0 and material.opacity_map:
            spriteMat = rt.rsSprite()
            spriteMat.Input_map = rsMat
            opacityMap = material.opacity_map.sourcemap.filename
            rt.replaceInstances(material, spriteMat)
        else:
            rsMat.refr_weight = 1 - material.opacity
            rt.replaceInstances(material, rsMat)
