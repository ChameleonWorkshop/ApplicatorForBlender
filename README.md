# Applicator For Blender

**Applicator for Blender** allow you to apply Apple ARKit Face Tracking data from your iPhone or iPad with a TrueDepth camera to your characters in Blender. Apple ARKit Face Tracking enables your iPhone or iPad to track a performer’s head location as well as [over 50 unique Blend Shape coefficients](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation) (ShapeKeys in Blender), all at 60 frames per second. With **Applicator for Blender**, you can take this data and apply it to your characters in Blender in 5 Easy Steps:

1. Define your mapping file
2. Record your face capture performance
3. Transfer the data to your computer
4. Add the simple face rig to your character (with the Applicator plugin)
5. Apply the data to your character

### **Key Features:**
- **Mapping File:** allows you to configure the target ShapeKeys and Items to apply tracking data to
- **Independent Enable/Disable:** gives you full control over which data points to apply to your scene
- **Multiplier:** sometimes the capture is just too subtle (or too extreme) and not giving you the performance, you need. The multiplier allows you increase (or decrease) the value of the tracking data to your scene
- **Value Shift:** like the multiplier, the value shift allows you to tweak the performance, but rather than multiplying the tracking data, it shifts the value up or down using a constant value (super handy for adjusting head rotation data)
- **Smoothing Algorithm:** optionally apply a smoothing algorithm to the tracking data
- **FPS Conversion:** automatically converts the 60fps recording data to scene’s fps. Support fps options: 60, 50, 48, 30, 29.97, 25 and 24.
- **Neutral Algorithm:** by optionally providing a neutral facial capture (~5 seconds recording of the performer’s face in a neutral state), the algorithm adjusts the capture data to cater for the unique facial shape of the performer.
- **Start Frame:** specify which frame to start the data application to
- **Skip Capture Frames:** specify how many frames from the recording you’d like to skip

### **Supported Face Tracking Apps:**
Applicator Kit does not capture face tracking data, it only applies the data to your scenes in Modo. Please use [Live Link Face](https://apps.apple.com/us/app/live-link-face/id1495370836) (free courtesy of Unreal Engine) to capture the facial performance.

### **Installation:**
1. Download Applicator.py
2. Edit > Preferences... > Add-ons > Install...
3. Locate and select Applicator.py
4. Click Install Add-on
5. Enable Applicator Add-on
6. Close Preferences Window

![Installation](/ReadmeImages/01_Install.gif "Installation")

### **Create Face Rig:**
1. Toolbar > Applicator
2. Select
    1. Head Mesh: This mesh has the target shape keys
    2. Head Pivot (Optional): This is the object that controls the head's rotation
    3. Left Eye Pivot (Optional): This is the object that controls the left eye's rotation
    4. Right Eye Pivot (Optional): This is the object that controls the right eye's rotation
3. Select the Mapping file (... button)
4. Click Create Face Rig

![Create Face Rig](/ReadmeImages/02_CreateRig.gif "Create Face Rig")

### **Explore Face Rig:**
1. Toolbar > Item
2. Select ApplicatorFaceRig
3. Switch to Pose Mode
4. Select the desired object
5. Under Properies slide the desired driver

Note: Rotating the Head or Eye objects will rotate the character's head and eyes

![Explore Face Rig](/ReadmeImages/03_ExploreRig.gif "Explore Face Rig")

### **Apply Face Capture:**
1. Toolbar > Applicator
2. Select your Data files
    1. Capture File: Your facial capture performance
    2. Neutral File (Optional): The neutral file is a static recording of the actors face. This helps create a better results.
    3. Mapping File: This should already be selected from when the Rig was created
3. Select Target Rig (This too should already be selected from when the Rig was created)
4. Set remaning options
5. Click Apply

![Apply Face Capture](/ReadmeImages/04_Apply.gif "Apply Face Capture")
