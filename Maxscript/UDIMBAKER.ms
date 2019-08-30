-------------------------------------------------------------------------------------------------------------------------------
-- UDIM BAKER 1.1
-- Bakes any udim tiles that exist on the selected base objects. No projection mapping support for now.
-- Currently the baseobject has to be an editablepoly as that is what it reads the tiles from. But it should still work 
-- if there are other mesh based modifiers in the stack like a turbosmooth.
-- Pathing is set based on your max project: project\sceneassets\images\OBJECTNAME_ELEMENTNAME.UDIM.tif
-- ie. "C:\Users\Benjamin\Documents\3dsMax\sceneassets\images\Box002_diffuseMap.1002.tif"
-- question? suggestions: benjaminmikhaiel@gmail.com

--changelog 
--1.0 initial_version
--1.1 changed output format to 16bit tif with alpha
-------------------------------------------------------------------------------------------------------------------------------

--setup some basic parameters cause.
elementList = BakeElement.classes
elementListName = #()
bResolution = 1024
bElementName = elementList[1]
bPadding = 8
--make a string elementlist so the dropdown list doesn't kill itself.
for i in elementList do
(
	append elementListName (i as string)
)


-- Takes polyObj and returns the UV tiles as an array
fn findUDIM polyObj =
(
	local tileArray = #()
	local VertexCount = polyop.getNumMapVerts polyObj.baseobject 1
	for i = 1 to VertexCount do
	(
		vertPos = polyop.getMapVert polyObj.baseobject 1 i
		appendifunique tileArray [vertPos.x as integer, vertPos.y as integer]
	)
	return tileArray
)

-- Converts a vector 2 to UDIM naming convention
fn ToUDIM xy =
(
	return (1000+(xy.x+1)+(xy.y*10)) as integer
)

--This function sets up our element and then triggers the renderer itself
fn BakeUDIMS polyObj size UDIM bChannel=
(
	--Clear all Bake Elements so I dont have to deal with garbage baking
	polyObj.iNodeBakeProperties.removeAllBakeElements()
	--create element
	bElem = bElementName()
	bElem.outputSzX = bElem.outputSzY = size
	bElem.fileType = (getDir #image+"\\"+polyObj.name+"_"+(bElementName as string)+"."+(UDIM as string)+".tif")
	bElem.fileName = filenameFromPath bElem.fileType
	--add the bake elements to the actual object.
	polyObj.INodeBakeProperties.addBakeElement bElem --add first element
	polyObj.INodeBakeProperties.bakeEnabled = true --enabling baking
	polyObj.INodeBakeProperties.bakeChannel = bChannel
	polyObj.INodeBakeProperties.nDilations = bPadding
	
	select polyObj --we are baking the selection, so we select the object --Call the renderer to bake both elements:
    render rendertype:#bakeSelected vfb:off progressBar:true outputSize:[size,size]
)

--Builds the UI and some of the more basic logic
try (destroyDialog ::UDIMBAKE) catch()

rollout UDIMBAKE "UDIM Baker" 
(
	dropdownlist elementSelect "Element" Items:elementListName
	dropdownlist resSelect "Resolution" selection: 3 Items:#("256", "512", "1024", "2048", "4096", "8192")
	dropdownlist padSelect "Padding" selection: 3 Items:#("0", "4", "8", "16", "32", "64")
	button btn1 "Bake" width:131 height:20

	-- set Element from dropdown.
	on elementSelect selected i do
	(
		bElementName = elementList[elementSelect.selection]
		print bElementName
	)

		-- set resolution from dropdown.
	on resSelect selected i do
	(
		bResolution = resSelect.selected as integer
	)
		
		-- set padding from dropdown.
	on padSelect selected i do
	(
		bPadding = padSelect.selected as integer
	)

	on btn1 pressed  do 
	(
		-- create an array of whats selected when we hit bake
		SelectedObj = selection as array
		--Setup the tif settings for saving
		tif.itifio.setType #color16
		tif.itifio.setCompression #none
		tif.itifio.setAlpha #true

-- TODO: ADD A CHECK FOR NON VRAY ELEMENT IF VRAY IS ENABLED TO PREVENT CRASH
-- if (renderers.current as string) == ((vray as string) + ":" + (vray as string)) then
-- (
-- )
-- TODO: ADD A CHECK FOR ILLEGAL UDIM POSITIONS (negative tile locations)

	--Trigger all our functions and do the uv shuffle
		For i in SelectedObj do
		(
		try(
			--copy the uv channel so we arnt shuffling around the uvs that are used in the shader.
			bChannel = polyOp.getNumMaps i.baseobject
			channelInfo.CopyChannel i 3 1
			channelInfo.PasteChannel i 3 bChannel
			
			OffUV = UVW_xform()
			OffUV.Map_Channel = bChannel
			addmodifier i OffUV
		
			tileArray = findUDIM i
			For tile = 1 to tileArray.count do
			(
				OFFUV.U_Offset = -tileArray[tile].x
				OFFUV.V_Offset = -tileArray[tile].y
				BakeUDIMS i bResolution (toUDIM tileArray[tile]) bChannel
			)
			--cleanup our modifier used for offsetting
			deleteModifier i (i.modifiers[#UVW_Mapping_Paste])
			deleteModifier i (i.modifiers[#UVW_Xform])
		)catch()
		)
	)
)
createDialog UDIMBAKE height:180 width:150 pos:[150,150]
