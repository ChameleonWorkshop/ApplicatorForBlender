bl_info = {
    "name": "Applicator for Blender",
    "author": "Andrew Buttigieg, Chameleon-Workshop.com",
    "version": (0, 7),
    "blender": (2, 83, 0),
    "location": "View3D > Toolbar > Applicator",
    "description": "Applies Apple Face Traking data to your characters",
    "warning": "",
    "wiki_url": "",
    "category": "Applicator",
}
#########################################################################
# Applicator Kit for Blender: Sync Apple AR Face Tracking Data to Blender
#
# Special Thanks to Jamie Dunbar for testing and feature guidance
#
# History:
# 0.1: Initial Version
# 0.2: Added rotation logic
# 0.3: Added smoothing frames selection
# 0.3: Fixed remove_keyframes to cater for negative keyframes
# 0.3: Allowed negative start frame
# 0.4: Fixed bug where one of the items were not selected
# 0.5: Added Face Control Rig Logic
# 0.6: Merged Mouth Controls into a single Control
# 0.7: Minor Fixes
# 
# © Copyright 2021 All Rights Reserved: Andrew Buttigieg (Chameleon-Workshop.com)
#########################################################################
import bpy
import os
import csv
import math
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty

bpy.types.Scene.app_head_mesh_target = bpy.props.PointerProperty(type=bpy.types.Mesh)
bpy.types.Scene.app_head_pivot_target = bpy.props.PointerProperty(type=bpy.types.Object)
bpy.types.Scene.app_eye_l_pivot_target = bpy.props.PointerProperty(type=bpy.types.Object)
bpy.types.Scene.app_eye_r_pivot_target = bpy.props.PointerProperty(type=bpy.types.Object)
bpy.types.Scene.app_rig_target = bpy.props.PointerProperty(type=bpy.types.Object)

supported_fps = (60, 50, 48, 30, 25, 24)
data_shapkey_names = ['eyeBlinkRight', 'eyeLookDownRight', 'eyeLookInRight', 'eyeLookOutRight', 'eyeLookUpRight', 'eyeSquintRight', 'eyeWideRight', 'eyeBlinkLeft', 'eyeLookDownLeft', 'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookUpLeft', 'eyeSquintLeft', 'eyeWideLeft', 'jawForward', 'jawRight', 'jawLeft', 'jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthRight', 'mouthLeft', 'mouthSmileRight', 'mouthSmileLeft', 'mouthFrownRight', 'mouthFrownLeft', 'mouthDimpleRight', 'mouthDimpleLeft', 'mouthStretchRight', 'mouthStretchLeft', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper', 'mouthPressRight', 'mouthPressLeft', 'mouthLowerDownRight', 'mouthLowerDownLeft', 'mouthUpperUpRight', 'mouthUpperUpLeft', 'browDownRight', 'browDownLeft', 'browInnerUp', 'browOuterUpRight', 'browOuterUpLeft', 'cheekPuff', 'cheekSquintRight', 'cheekSquintLeft', 'noseSneerRight', 'noseSneerLeft', 'tongueOut']
data_item_names = ['HeadYaw', 'HeadPitch', 'HeadRoll', 'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll', 'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll']
blendShapeLabels = {
    'eyeBlinkRight':'Eye Right - Blink',
    'eyeLookDownRight':'Eye Right - Look Down',
    'eyeLookInRight':'Eye Right - Look In',
    'eyeLookOutRight':'Eye Right - Look Out',
    'eyeLookUpRight':'Eye Right - Look Up',
    'eyeSquintRight':'Eye Right - Squint',
    'eyeWideRight':'Eye Right - Wide',
    'eyeBlinkLeft':'Eye Left - Blink',
    'eyeLookDownLeft':'Eye Left - Look Down',
    'eyeLookInLeft':'Eye Left - Look In',
    'eyeLookOutLeft':'Eye Left - Look Out',
    'eyeLookUpLeft':'Eye Left - Look Up',
    'eyeSquintLeft':'Eye Left - Squint',
    'eyeWideLeft':'Eye Left - Wide',
    'jawForward':'Jaw - Forward',
    'jawRight':'Jaw - Right',
    'jawLeft':'Jaw - Left',
    'jawOpen':'Jaw - Open',
    'mouthClose':'Mouth - Close',
    'mouthFunnel':'Mouth - Funnel',
    'mouthPucker':'Mouth - Pucker',
    'mouthRollLower':'Mouth - Roll - Lower',
    'mouthRollUpper':'Mouth - Roll - Upper',
    'mouthShrugLower':'Mouth - Shrug - Lower',
    'mouthShrugUpper':'Mouth - Shrug - Upper',
    'mouthRight':'Mouth - Right',
    'mouthSmileRight':'Mouth - Right - Smile',
    'mouthFrownRight':'Mouth - Right - Frown',
    'mouthDimpleRight':'Mouth - Right - Dimple',
    'mouthStretchRight':'Mouth - Right - Stretch',
    'mouthPressRight':'Mouth - Right - Press',
    'mouthLowerDownRight':'Mouth - Right - Lower Down',
    'mouthUpperUpRight':'Mouth - Right - Upper Up',
    'mouthLeft':'Mouth - Left',
    'mouthSmileLeft':'Mouth - Left - Smile',
    'mouthFrownLeft':'Mouth - Left - Frown',
    'mouthDimpleLeft':'Mouth - Left - Dimple',
    'mouthStretchLeft':'Mouth - Left - Stretch',
    'mouthPressLeft':'Mouth - Left - Press',
    'mouthLowerDownLeft':'Mouth - Left - Lower Down',
    'mouthUpperUpLeft':'Mouth - Left - Upper Up',
    'browInnerUp':'Brow - Inner Up',
    'browDownRight':'Brow - Right - Down',
    'browOuterUpRight':'Brow - Right - Outer Up',
    'browDownLeft':'Brow - Left - Down',
    'browOuterUpLeft':'Brow - Left - Outer Up',
    'cheekPuff':'Cheek - Puff',
    'cheekSquintRight':'Cheek - Right - Squint',
    'cheekSquintLeft':'Cheek - Left - Squint',
    'noseSneerRight':'Nose - Right - Sneer',
    'noseSneerLeft':'Nose - Left - Sneer',
    'tongueOut':'Tongue - Out'
}

################################################################    
#Properties Class
################################################################    
class ApplicatorProps(bpy.types.PropertyGroup):    
    capture_file_path: bpy.props.StringProperty(name="Capture File Path")
    capture_file_name: bpy.props.StringProperty(name="Capture File Name", default="(Select)")

    neutral_file_path: bpy.props.StringProperty(name="Neutral File Path")
    neutral_file_name: bpy.props.StringProperty(name="Neutral File Name", default="(Select)")

    mapping_file_path: bpy.props.StringProperty(name="Mapping File Path")
    mapping_file_name: bpy.props.StringProperty(name="Mapping File Name", default="(Select)")

    start_frame: bpy.props.IntProperty(name="Start Frame", default=1)
    skip_capture_frames: bpy.props.IntProperty(name="Skip Capture Frames", default=0, min=0)
    apply_shapekey_data: bpy.props.BoolProperty(name="Apply ShapeKey Data", default=True)
    apply_rotation_data: bpy.props.BoolProperty(name="Apply Rotation Data", default=True)
    clear_existing_keyframes: bpy.props.BoolProperty(name="Clear Existing Keyframes", default=True)
    smoothing_frames: bpy.props.EnumProperty(
        name='Smoothing Frames',
        description='Select the number of frames to use when applying the smoothing algorithm',
        default='S7',
        items = [
            ('S0', 'No smoothing', ''),
            ('S3', '3 Frames', ''),
            ('S5', '5 Frames', ''),
            ('S7', '7 Frames', ''),
            ('S9', '9 Frames', ''),
            ('S11', '11 Frames', '')
        ]
    )
        
    def clear(self):
        self.capture_file_name = ''

################################################################    
# Target Panel
################################################################    
class ApplicatorTargetPanel(bpy.types.Panel):
    bl_label = "Targets"
    bl_idname = "VIEW_PT_ApplicatorTargetPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Applicator'
       
    def draw(self, context):
        scene = context.scene
        props = scene.ApplicatorProps
        layout = self.layout
        layout.prop_search(context.scene, "app_head_mesh_target", context.scene, "objects", text="Head Mesh")
        layout.prop_search(context.scene, "app_head_pivot_target", context.scene, "objects", text="Head Pivot")
        layout.prop_search(context.scene, "app_eye_l_pivot_target", context.scene, "objects", text="Left Eye Pivot")
        layout.prop_search(context.scene, "app_eye_r_pivot_target", context.scene, "objects", text="Right Eye Pivot")
        
        
        #Mapping File
        layout.label(text="Mapping File:")
        row = layout.row()
        row.label(text=props.mapping_file_name)
        sub = row.row()
        sub.scale_x = 0.3
        sub.operator("applicator.mapping_file_browser", text="...")
        row.operator("applicator.mapping_file_clear", text="", icon="X")
        
        #button
        layout.operator("applicator.create_rig", text="Create Face Rig")

      
################################################################    
# Data Panel
################################################################    
class ApplicatorDataPanel(bpy.types.Panel):
    bl_label = "Data"
    bl_idname = "VIEW_PT_ApplicatorDataPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Applicator'
        
    def draw(self, context):
        scene = context.scene
        props = scene.ApplicatorProps
        layout = self.layout
        
        # Capture File
        layout.label(text="Capture File:")
        row = layout.row()
        row.label(text=props.capture_file_name)
        sub = row.row()
        sub.scale_x = 0.3
        sub.operator("applicator.capture_file_browser", text="...")
        row.operator("applicator.capture_file_clear", text="", icon="X")
                
        #Neutral File
        layout.label(text="Neutral File (optional):")
        row = layout.row()
        row.label(text=props.neutral_file_name)
        sub = row.row()
        sub.scale_x = 0.3
        sub.operator("applicator.neutral_file_browser", text="...")
        row.operator("applicator.neutral_file_clear", text="", icon="X")
                
        #Mapping File
        layout.label(text="Mapping File:")
        row = layout.row()
        row.label(text=props.mapping_file_name)
        sub = row.row()
        sub.scale_x = 0.3
        sub.operator("applicator.mapping_file_browser", text="...")
        row.operator("applicator.mapping_file_clear", text="", icon="X")

################################################################    
# Mapping Panel
################################################################    
class ApplicatorMappingPanel(bpy.types.Panel):
    bl_label = "Mapping"
    bl_idname = "VIEW_PT_ApplicatorMappingPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Applicator'
            
    def draw(self, context):
        scene = context.scene
        props = scene.ApplicatorProps
        layout = self.layout
        
        layout.label(text="<TODO>")

################################################################    
# Apply Panel
################################################################    
class ApplicatorApplyPanel(bpy.types.Panel):
    bl_label = "Apply"
    bl_idname = "VIEW_PT_ApplicatorApplyPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Applicator'
            
    def draw(self, context):
        scene = context.scene
        props = scene.ApplicatorProps
        layout = self.layout
        
        layout.prop_search(context.scene, "app_rig_target", context.scene, "objects", text="Target Rig")
        layout.prop(props, "start_frame")
        layout.prop(props, "skip_capture_frames")
        layout.prop(props, "smoothing_frames")
        layout.prop(props, "apply_shapekey_data")
        layout.prop(props, "apply_rotation_data")
        layout.prop(props, "clear_existing_keyframes")
        
        row = layout.row()
        row.scale_y = 2
        row.operator('applicator.apply', text="Apply")

################################################################    
# Create Face Rig
################################################################    
class ApplicatorCreateFaceRig(bpy.types.Operator): 
    bl_idname = "applicator.create_rig" 
    bl_label = "Create Face Rig" 
    bl_description = "Create the Face Rig" 

    ################################################################    
    # Validate the settings
    ################################################################    
    def ValidateSettings(self, head_mesh, props):
        is_valid = True
        messages = []
        mapping_file_cols = ['Type', 'Name', 'Target', 'Enabled', 'Multiplier', 'ValueShift', 'Smooth']

        #Head Selected?
        if head_mesh == None:
            is_valid = False           
            messages.append("- No head mesh select. Please select the head mesh.")

        #Head has Shape Keys
        elif head_mesh.shape_keys == None:
            is_valid = False           
            messages.append("- Head mesh has no shape keys. Data is applied to Shape Keys.")

        #Mapping File Selected?
        if props.mapping_file_path == None or props.mapping_file_path == '':
            is_valid = False
            messages.append("- Mapping File missing. Please select the Mapping File.")

        #Mapping File Exists?
        elif os.path.exists(props.mapping_file_path) == False:
            is_valid = False
            messages.append("- Selected Mapping File does not exist. Please reselect the Mapping File.")

        #Mapping File a csv?
        else:
            filename, extension = os.path.splitext(props.mapping_file_path.lower())
            if extension != ".csv":
                is_valid = False
                messages.append('- Incorrect Mapping File type. Please select a .csv file.')
            #Mapping file has the right columns
            else:
                valid_cols, missing_cols = validate_csv(props.mapping_file_path, mapping_file_cols)
                if valid_cols == False:
                    is_valid = False
                    messages.append('- Invalid Mapping File format. Missing columns: ' + ', '.join(str(x) for x in missing_cols))
                
        return is_valid, messages

    ################################################################    
    # Gets the object's collection
    ################################################################        
    def get_collection_for_object(self, collection, object, type):
        #search child collections
        for coll in collection.children:
            result = self.get_collection_for_object(coll, object, type)
            if result != None:
                return result
            
        #check if the object is in the collection
        for coll_obj in collection.all_objects:
            if coll_obj.type == type and coll_obj.name == object.name:
                #found it
                return collection
            
        #didn't find it, return None    
        return None
    
    ################################################################    
    # Gets the object form the collection
    ################################################################        
    def get_object(self, collection, name, type):
        result = None
        for coll_obj in collection.all_objects:
            if coll_obj.type == type and coll_obj.name == name:
                result = coll_obj
                break
        return result
        
    ################################################################    
    # Delete the Applicator rig & collection
    ################################################################        
    def del_existing_rig(self):
        bpy.ops.object.select_all(action='DESELECT')

        #delete the collection if it exists
        rig_coll = None
        try:
            rig_coll = bpy.data.collections['ApplicatorRig']
        except:
            rig_coll = None

        if rig_coll != None:
            for obj in rig_coll.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(rig_coll)

        #delete the armature if it exists
        armature_obj = None
        try:
            armature_obj = bpy.data.objects['ApplicatorFaceRig']
        except:
            armature_obj = None

        if armature_obj != None:
            try:
                armature_obj.select_set(True)
                bpy.ops.object.delete()
            except:
                armature_obj = None

    ################################################################    
    # Add Empties
    ################################################################        
    def add_empties(self, rig_collection):
        
        #add empty for head
        headEmpty = self.get_object(rig_collection, 'ApplicatorHeadEmpty', 'EMPTY')
        if headEmpty == None: #should't exist
            headEmpty = bpy.data.objects.new("ApplicatorHeadEmpty", None )
            headEmpty.empty_display_size = 0.2
            headEmpty.empty_display_type = 'CUBE'
            headEmpty.hide_viewport = True
            rig_collection.objects.link(headEmpty)

        #add empty for eyes
        eyeEmpty = self.get_object(rig_collection, 'ApplicatorEyeEmpty', 'EMPTY')
        if eyeEmpty == None:
            eyeEmpty = bpy.data.objects.new('ApplicatorEyeEmpty', None )
            eyeEmpty.empty_display_size = 0.06
            eyeEmpty.empty_display_type = 'CONE'
            eyeEmpty.hide_viewport = True
            rig_collection.objects.link(eyeEmpty)

        #add empty for nose
        noseEmpty = self.get_object(rig_collection, 'ApplicatorNoseEmpty', 'EMPTY')
        if noseEmpty == None: #should't exist
            noseEmpty = bpy.data.objects.new('ApplicatorNoseEmpty', None )
            noseEmpty.empty_display_size = 0.03
            noseEmpty.empty_display_type = 'CUBE'
            noseEmpty.hide_viewport = True
            rig_collection.objects.link(noseEmpty)

        #add empty for mouth
        mouthEmpty = self.get_object(rig_collection, 'ApplicatorMouthEmpty', 'EMPTY')
        if mouthEmpty == None: #should't exist
            mouthEmpty = bpy.data.objects.new('ApplicatorMouthEmpty', None )
            mouthEmpty.empty_display_size = 0.02
            mouthEmpty.empty_display_type = 'CUBE'
            mouthEmpty.hide_viewport = True
            rig_collection.objects.link(mouthEmpty)
            
        #add empty for brows
        browsEmpty = self.get_object(rig_collection, 'ApplicatorBrowsEmpty', 'EMPTY')
        if browsEmpty == None: #should't exist
            browsEmpty = bpy.data.objects.new('ApplicatorBrowsEmpty', None )
            browsEmpty.empty_display_size = 0.02
            browsEmpty.empty_display_type = 'CUBE'
            browsEmpty.hide_viewport = True
            rig_collection.objects.link(browsEmpty)
        
        return headEmpty, eyeEmpty, noseEmpty, mouthEmpty, browsEmpty
        
    ################################################################    
    # Add the face rig
    ################################################################        
    def add_face_rig(self, rig_collection, headEmpty, eyeEmpty, noseEmpty, mouthEmpty, browsEmpty):
        #lookup the current armatures names + object names (total hack; but it works)
        current_armature_names = []
        current_armature_obj_names = []

        for arm in bpy.data.armatures:
            current_armature_names.append(arm.name)
            
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                current_armature_obj_names.append(obj.name)

        #add a new armature and move to collection (ish)
        bpy.ops.object.armature_add()
        bpy.ops.object.collection_link(collection=rig_collection.name)

        #find the newly created armature
        armature = None
        for arm in bpy.data.armatures:
            if arm.name not in current_armature_names:
                armature = arm
                armature.name = 'ApplicatorFaceRig'
                break

        #find the newly created armature object
        armature_obj = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.name not in current_armature_obj_names:
                armature_obj = obj
                armature_obj.name = 'ApplicatorFaceRig'
                break

        #select the armature obejct
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = armature_obj

        #go into edit mode
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        edit_bones = armature.edit_bones
        
        #remove the default bone
        edit_bones.remove(edit_bones[0])

        #rename Bone to Head
        head_bone = edit_bones.new('Head')
        head_bone.head = (0, 0, 0.0)
        head_bone.tail = (0, 1, 0.0)

        #Add Eye_R Bone
        eye_r = edit_bones.new('Eye_R')
        eye_r.head = (-0.1, -0.2, 0.04)
        eye_r.tail = (-0.1, 0.8, 0.04)
        eye_r.parent = head_bone

        #Add Eye_L Bone
        eye_l = edit_bones.new('Eye_L')
        eye_l.head = (0.1, -0.2, 0.04)
        eye_l.tail = (0.1, 0.8, 0.04)
        eye_l.parent = head_bone
        
        #Add Brows Bone
        brows = edit_bones.new('Brows')
        brows.head = (0.0, -0.2, 0.15)
        brows.tail = (0.0, 0.8, 0.15)
        brows.parent = head_bone

        #Add Nose Bone
        nose = edit_bones.new('Nose')
        nose.head = (0.0, -0.23, -0.03)
        nose.tail = (0.0, 0.8, -0.03)
        nose.parent = head_bone

        #Add Mouth Bone
        mouth = edit_bones.new('Mouth')
        mouth.head = (0.0, -0.18, -0.12)
        mouth.tail = (0.0, 0.8, -0.12)
        mouth.parent = head_bone

        #go back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        #assign the custom shapes
        armature_obj.pose.bones['Head'].custom_shape = headEmpty
        armature_obj.pose.bones['Eye_R'].custom_shape = eyeEmpty
        armature_obj.pose.bones['Eye_L'].custom_shape = eyeEmpty
        armature_obj.pose.bones['Brows'].custom_shape = browsEmpty
        armature_obj.pose.bones['Brows'].scale[0] = 8
        armature_obj.pose.bones['Nose'].custom_shape = noseEmpty
        armature_obj.pose.bones['Mouth'].custom_shape = mouthEmpty
        armature_obj.pose.bones['Mouth'].scale[0] = 8

        #move 1 unit left, 1 unit up
        armature_obj.location = (1.0, 0.0, 1.0)

        return armature_obj, armature

    ################################################################    
    # Add Custom Properties to the target bone, and sets them as drivers to the shape key  
    ################################################################      
    def add_shape_key_drivers(self, armature_obj, target_mesh, bone_name, properties):
        ##########################
        #add the custom properties
        ##########################
        rna_ui = {}
        for property in properties:
            name = property[0]
            min = property[1]
            max = property[2]
            value = property[3]
            shape_key_name = property[4]
            
            #only add custom property if it has a shapekey to drive
            if shape_key_name != None:
                #add the property        
                armature_obj.pose.bones[bone_name][name] = value
                
                #set the config the dictionary
                rna_ui[name] = {"min":min, "max":max}

        #set the property config
        if not armature_obj.pose.bones[bone_name].get('_RNA_UI'):
            armature_obj.pose.bones[bone_name]['_RNA_UI'] = {}
        armature_obj.pose.bones[bone_name]['_RNA_UI'] = rna_ui
    
        ##########################
        #add the drivers
        ##########################
        for property in properties:
            name = property[0]
            shape_key_name = property[4]

           #only add driver if it has a shapekey to drive
            if shape_key_name != None:
                shape_key = target_mesh.shape_keys.key_blocks[shape_key_name]
                shape_key.driver_remove('value') #removed if exists. no error otherwise
                driver = shape_key.driver_add('value').driver
                driver.type ='AVERAGE'
                driver_var = driver.variables.new()
                driver_var.type = 'SINGLE_PROP'
                driver_var.targets[0].id = armature_obj
                driver_var.targets[0].data_path = 'pose.bones["' + bone_name + '"]["' + name + '"]'

    ################################################################    
    # Adds the rotation drivers to the head and eyes  
    ################################################################      
    def add_rotation_drivers(self, armature_obj, target_pivot, bone_name):
        if target_pivot != None:
            target_pivot.driver_remove('rotation_euler')
            driver_x = target_pivot.driver_add('rotation_euler', 0).driver
            driver_y = target_pivot.driver_add('rotation_euler', 1).driver
            driver_z = target_pivot.driver_add('rotation_euler', 2).driver

            driver_x.type ='AVERAGE'
            driver_y.type ='AVERAGE'
            driver_z.type ='AVERAGE'
            
            driver_var_x = driver_x.variables.new()
            driver_var_y = driver_y.variables.new()
            driver_var_z = driver_z.variables.new()

            driver_var_x.type = 'SINGLE_PROP'
            driver_var_y.type = 'SINGLE_PROP'
            driver_var_z.type = 'SINGLE_PROP'
            
            driver_var_x.targets[0].id = armature_obj
            driver_var_y.targets[0].id = armature_obj
            driver_var_z.targets[0].id = armature_obj

            driver_var_x.targets[0].data_path = 'pose.bones["' + bone_name + '"].rotation_quaternion[1]'
            driver_var_y.targets[0].data_path = 'pose.bones["' + bone_name + '"].rotation_quaternion[2]'
            driver_var_z.targets[0].data_path = 'pose.bones["' + bone_name + '"].rotation_quaternion[3]'
        
    def get_target_shape_key(self, target_mesh, mapping_data, blend_shape_name):
        result = None
        target_shape_key = None
        
        #get the target shape key name of the mapping
        mapping_lines = [mapping for mapping in mapping_data if mapping['Type'] == 'BlendShape' and mapping['Name'] == blend_shape_name]
        if len(mapping_lines) > 0:
            target_shape_key = mapping_lines[0]['Target']

        #make sure the mapped shapekey exists in the target mesh
        if target_shape_key.strip() != '':
            if target_shape_key in target_mesh.shape_keys.key_blocks:
                result = target_shape_key
        
        return result

    ################################################################    
    # Execute logic
    ################################################################        
    def execute(self, context):
        props = context.scene.ApplicatorProps
        head_mesh = context.scene.app_head_mesh_target
        head_pivot = context.scene.app_head_pivot_target
        eye_l_pivot = context.scene.app_eye_l_pivot_target
        eye_r_pivot = context.scene.app_eye_r_pivot_target
        
        #reset cursor location to world root
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

        #make sure we are in object mode
        if bpy.context.object != None and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        #deselect if any selected objects
        bpy.ops.object.select_all(action='DESELECT')

        #validate the settings
        is_valid, messages = self.ValidateSettings(head_mesh, props)
        
        if is_valid:
            #cleanup any existing rig
            self.del_existing_rig()
            
            #get the collection the head mesh is in
            head_mesh_collection = self.get_collection_for_object(bpy.context.scene.collection, head_mesh, 'MESH')
            
            #create the rig collection
            rig_collection = bpy.data.collections.new('ApplicatorRig')
            head_mesh_collection.children.link(rig_collection)
                    
            #add the empties
            headEmpty, eyeEmpty, noseEmpty, mouthEmpty, browsEmpty = self.add_empties(rig_collection)            
            
            #add the face rig
            face_rig_object, face_rig_armature = self.add_face_rig(rig_collection, headEmpty, eyeEmpty, noseEmpty, mouthEmpty, browsEmpty)

            #get the mapping data
            mapping_data = list_csv_data(props.mapping_file_path)
            
            #add the propertes and drivers
            eye_r_properties = [
                #name, min, max, value, shapeKey
                [blendShapeLabels['eyeBlinkRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeBlinkRight')],
                [blendShapeLabels['eyeLookDownRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookDownRight')],
                [blendShapeLabels['eyeLookInRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookInRight')],
                [blendShapeLabels['eyeLookOutRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookOutRight')],
                [blendShapeLabels['eyeLookUpRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookUpRight')],
                [blendShapeLabels['eyeSquintRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeSquintRight')],
                [blendShapeLabels['eyeWideRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeWideRight')]
            ]
            eye_l_properties = [
                [blendShapeLabels['eyeBlinkLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeBlinkLeft')],
                [blendShapeLabels['eyeLookDownLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookDownLeft')],
                [blendShapeLabels['eyeLookInLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookInLeft')],
                [blendShapeLabels['eyeLookOutLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookOutLeft')],
                [blendShapeLabels['eyeLookUpLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeLookUpLeft')],
                [blendShapeLabels['eyeSquintLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeSquintLeft')],
                [blendShapeLabels['eyeWideLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'eyeWideLeft')]
            ]
            mouth_properties = [
                [blendShapeLabels['jawForward'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'jawForward')],
                [blendShapeLabels['jawRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'jawRight')],
                [blendShapeLabels['jawLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'jawLeft')],
                [blendShapeLabels['jawOpen'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'jawOpen')],
                [blendShapeLabels['mouthClose'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthClose')],
                [blendShapeLabels['mouthFunnel'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthFunnel')],
                [blendShapeLabels['mouthPucker'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthPucker')],
                [blendShapeLabels['mouthRollLower'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthRollLower')],
                [blendShapeLabels['mouthRollUpper'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthRollUpper')],
                [blendShapeLabels['mouthShrugLower'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthShrugLower')],
                [blendShapeLabels['mouthShrugUpper'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthShrugUpper')],
                [blendShapeLabels['tongueOut'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'tongueOut')],
                [blendShapeLabels['mouthLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthLeft')],
                [blendShapeLabels['mouthSmileLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthSmileLeft')],
                [blendShapeLabels['mouthFrownLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthFrownLeft')],
                [blendShapeLabels['mouthDimpleLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthDimpleLeft')],
                [blendShapeLabels['mouthStretchLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthStretchLeft')],
                [blendShapeLabels['mouthPressLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthPressLeft')],
                [blendShapeLabels['mouthLowerDownLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthLowerDownLeft')],
                [blendShapeLabels['mouthUpperUpLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthUpperUpLeft')],
                [blendShapeLabels['mouthRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthRight')],
                [blendShapeLabels['mouthSmileRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthSmileRight')],
                [blendShapeLabels['mouthFrownRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthFrownRight')],
                [blendShapeLabels['mouthDimpleRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthDimpleRight')],
                [blendShapeLabels['mouthStretchRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthStretchRight')],
                [blendShapeLabels['mouthPressRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthPressRight')],
                [blendShapeLabels['mouthLowerDownRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthLowerDownRight')],
                [blendShapeLabels['mouthUpperUpRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'mouthUpperUpRight')]
            ]
            brows_properties = [
                [blendShapeLabels['browDownRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'browDownRight')],
                [blendShapeLabels['browDownLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'browDownLeft')],
                [blendShapeLabels['browInnerUp'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'browInnerUp')],
                [blendShapeLabels['browOuterUpRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'browOuterUpRight')],
                [blendShapeLabels['browOuterUpLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'browOuterUpLeft')]
            ]
            nose_properties = [
                [blendShapeLabels['cheekPuff'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'cheekPuff')],
                [blendShapeLabels['cheekSquintRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'cheekSquintRight')],
                [blendShapeLabels['cheekSquintLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'cheekSquintLeft')],
                [blendShapeLabels['noseSneerRight'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'noseSneerRight')],
                [blendShapeLabels['noseSneerLeft'], 0.0, 1.0, 0.0, self.get_target_shape_key(head_mesh, mapping_data, 'noseSneerLeft')]
            ]
            self.add_shape_key_drivers(face_rig_object, head_mesh, 'Eye_L', eye_l_properties)
            self.add_shape_key_drivers(face_rig_object, head_mesh, 'Eye_R', eye_r_properties)
            self.add_shape_key_drivers(face_rig_object, head_mesh, 'Nose', nose_properties)
            self.add_shape_key_drivers(face_rig_object, head_mesh, 'Mouth', mouth_properties)
            self.add_shape_key_drivers(face_rig_object, head_mesh, 'Brows', brows_properties)

            #add the rotation drivers
            self.add_rotation_drivers(face_rig_object, head_pivot, 'Head')
            self.add_rotation_drivers(face_rig_object, eye_l_pivot, 'Eye_L')
            self.add_rotation_drivers(face_rig_object, eye_r_pivot, 'Eye_R')
            
            #set the target rig control to the newly created rig
            context.scene.app_rig_target = face_rig_object
            
            show_message_box(['Face Rig Created'], 'Success')
        else:
            #Display the errors
            show_message_box(messages, "Validation error", 'CANCEL')         
        
        return {'FINISHED'}

      
################################################################    
# Select Capture File
################################################################    
class ApplicatorSelectCaptureFile(bpy.types.Operator, ImportHelper): 
    bl_idname = "applicator.capture_file_browser"
    bl_description = "Select the capture file."
    bl_label = "Select" 

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(
        default='*.csv',
        options={'HIDDEN'}
    )
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        filename = os.path.basename(self.filepath)
        props = context.scene.ApplicatorProps
        props.capture_file_path = self.filepath
        props.capture_file_name = filename
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

################################################################    
# Clear Capture File
################################################################    
class ApplicatorClearCaptureFile(bpy.types.Operator): 
    bl_idname = "applicator.capture_file_clear" 
    bl_label = "Clear" 
    bl_description = "Clear the capture file" 

    def execute(self, context):
        props = context.scene.ApplicatorProps
        props.capture_file_path = ''
        props.capture_file_name = '(Select)'
        return {'FINISHED'}
    
################################################################    
# Select Neutral File
################################################################    
class ApplicatorSelectNeutralFile(bpy.types.Operator, ImportHelper): 
    bl_idname = "applicator.neutral_file_browser" 
    bl_description = "Select the neutral file."
    bl_label = "Select" 

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(
        default='*.csv',
        options={'HIDDEN'}
    )
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        filename = os.path.basename(self.filepath)
        props = context.scene.ApplicatorProps
        props.neutral_file_path = self.filepath
        props.neutral_file_name = filename
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

################################################################    
# Clear Neutral File
################################################################    
class ApplicatorClearNeutralFile(bpy.types.Operator): 
    bl_idname = "applicator.neutral_file_clear" 
    bl_label = "Clear" 
    bl_description = "Clear the neutral file" 

    def execute(self, context):
        props = context.scene.ApplicatorProps
        props.neutral_file_path = ''
        props.neutral_file_name = '(Select)'
        return {'FINISHED'}

################################################################    
# Select Mapping File
################################################################    
class ApplicatorSelectMappingFile(bpy.types.Operator, ImportHelper): 
    bl_idname = "applicator.mapping_file_browser" 
    bl_description = "Select the mapping file."
    bl_label = "Select"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(
        default='*.csv',
        options={'HIDDEN'}
    )
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        filename = os.path.basename(self.filepath)
        props = context.scene.ApplicatorProps
        props.mapping_file_path = self.filepath
        props.mapping_file_name = filename
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}   

################################################################    
# Clear Mapping File
################################################################    
class ApplicatorClearMappingFile(bpy.types.Operator): 
    bl_idname = "applicator.mapping_file_clear" 
    bl_label = "Clear" 
    bl_description = "Clear the mapping file" 

    def execute(self, context):
        props = context.scene.ApplicatorProps
        props.mapping_file_path = ''
        props.mapping_file_name = '(Select)'
        return {'FINISHED'}
    
################################################################    
# Apply
################################################################    
class ApplicatorApply(bpy.types.Operator):
    bl_idname = "applicator.apply"
    bl_label = "Apply"
    
    ################################################################    
    # Validate the settings
    ################################################################    
    def ValidateSettings(self, target_rig, props):
        is_valid = True
        messages = []
        mapping_file_cols = ['Type', 'Name', 'Target', 'Enabled', 'Multiplier', 'ValueShift', 'Smooth']
        data_file_columns = []
        data_file_columns.extend(data_shapkey_names)
        data_file_columns.extend(data_item_names)

        #validate frame rate
        fps = bpy.context.scene.render.fps
        if fps not in supported_fps:
            is_valid = False
            messages.append('- Unsupported Frame Rate. Supported Frame Rates: ' + ', '.join(str(x) for x in supported_fps))

        #Rig Selected?
        if target_rig == None:
            is_valid = False           
            messages.append("- No Target Rig select. Please select the Target Rig.")
        elif target_rig.type != 'ARMATURE':
            is_valid = False           
            messages.append("- Target Rig must be an Armature.")
        else:
            #validate we have the desired target bones
            has_head = False
            has_eye_l = False
            has_eye_r = False
            for bone in target_rig.pose.bones:
                if bone.name == 'Head':
                    print('head')
                    has_head = True
                if bone.name == 'Eye_L':
                    has_eye_l = True
                if bone.name == 'Eye_R':
                    has_eye_r = True

            if has_head == False:
                is_valid = False 
                messages.append("- Target Rig missing Head bone.")
            if has_eye_l == False:
                is_valid = False 
                messages.append("- Target Rig missing Eye_L bone.")
            if has_eye_r == False:
                is_valid = False 
                messages.append("- Target Rig missing Eye_R bone.")
                
        #Capture File Selected?
        if props.capture_file_path == None or props.capture_file_path == '':
            is_valid = False
            messages.append("- Capture File missing. Please select the Capture File.")

        #Capture File Exists?
        elif os.path.exists(props.capture_file_path) == False:
            is_valid = False
            messages.append("- Selected Capture File does not exist. Please reselect the Capture File.")

        #Capture File a csv?
        else:
            filename, extension = os.path.splitext(props.capture_file_path.lower())
            if extension != ".csv":
                is_valid = False
                messages.append('- Incorrect Capture File type. Please select a .csv file.')
            #Capture file has the right columns
            else:
                valid_cols, missing_cols = validate_csv(props.capture_file_path, data_file_columns)
                if valid_cols == False:
                    is_valid = False
                    messages.append('- Invalid Capture File format. Missing columns: ' + ', '.join(str(x) for x in missing_cols))
                
        #Neutral File doesn't need to be selected
        if props.neutral_file_path != None and props.neutral_file_path != '':
            #Neutral File Exists?
            if os.path.exists(props.neutral_file_path) == False:
                is_valid = False
                messages.append("- Selected Neutral File does not exist. Please reselect the Neutral File.")
            #Neutral File a csv?
            else:
                filename, extension = os.path.splitext(props.neutral_file_path.lower())
                if extension != ".csv":
                    is_valid = False
                    messages.append('- Incorrect Neutral File type. Please select a .csv file.')
                #Neutral file has the right columns
                else:
                    valid_cols, missing_cols = validate_csv(props.neutral_file_path, data_file_columns)
                    if valid_cols == False:
                        is_valid = False
                        messages.append('- Invalid Neutral File format. Missing columns: ' + ', '.join(str(x) for x in missing_cols))

        #Mapping File Selected?
        if props.mapping_file_path == None or props.mapping_file_path == '':
            is_valid = False
            messages.append("- Mapping File missing. Please select the Mapping File.")

        #Mapping File Exists?
        elif os.path.exists(props.mapping_file_path) == False:
            is_valid = False
            messages.append("- Selected Mapping File does not exist. Please reselect the Mapping File.")

        #Mapping File a csv?
        else:
            filename, extension = os.path.splitext(props.mapping_file_path.lower())
            if extension != ".csv":
                is_valid = False
                messages.append('- Incorrect Mapping File type. Please select a .csv file.')
            #Mapping file has the right columns
            else:
                valid_cols, missing_cols = validate_csv(props.mapping_file_path, mapping_file_cols)
                if valid_cols == False:
                    is_valid = False
                    messages.append('- Invalid Mapping File format. Missing columns: ' + ', '.join(str(x) for x in missing_cols))
                
        return is_valid, messages
    
    
    ################################################################    
    # Apply the blendshape data to the shapekeys
    ################################################################    
    def apply_blendshape_data(self, target_bone, blendshape_name, multiplier, value_shift, smooth, capture_frames, face_neutral, apply_capture_frames_to, start_frame, skip_capture_frames, smooth_frames):
        #make sure the property exists
        blendShapeLabel = blendShapeLabels[blendshape_name]
        propertyName = '["' + blendShapeLabel + '"]'
        try:
            prop = target_bone[blendShapeLabel] #this will fail if it doesn't exist
        except:
            #property doesnt exist, so we skip it
            prop = None
                
        if prop != None:
            current_frame_no = start_frame

            #determine the number of smoothing shift frames
            smooth_shift = 0
            if smooth_frames == 'S3':
                smooth_shift = 1
            elif smooth_frames == 'S5':
                smooth_shift = 2
            elif smooth_frames == 'S7':
                smooth_shift = 3
            elif smooth_frames == 'S9':
                smooth_shift = 4
            elif smooth_frames == 'S11':
                smooth_shift = 5     

            #loop the capture frames and apply the morph strength
            capture_frames_count = len(capture_frames)
            if capture_frames_count > skip_capture_frames:
                for y in range(skip_capture_frames, capture_frames_count):
                    capture_frame = capture_frames[y]

                    #first test if we are applying this frame??
                    if apply_capture_frames_to[y] == True:
                        #get the strength (smooth style)
                        if smooth.upper() == 'Y':
                            #smoothing applies a rolling average using the current frame, previous # frames, and next # frames                           
                            range_count = 0
                            range_sum = 0.0
                            for x in range(y - smooth_shift, y + 1 + smooth_shift):
                                if x >=0 and x < capture_frames_count:
                                    range_frame = capture_frames[x]
                                    range_count += 1
                                    capture_frame = range_frame[blendshape_name]
                                    if 'E' in capture_frame: #cater for when numbers are super low
                                        capture_frame_value = 0.0
                                    else:
                                        capture_frame_value = float(capture_frame)
                                    range_sum += capture_frame_value
                            strength = range_sum / range_count
                        else:
                            capture_frame = capture_frames[y]
                            if 'E' in capture_frame[blendshape_name]: #cater for when numbers are super low
                                strength = 0.0
                            else:
                                strength = float(capture_frame[blendshape_name])
                        
                        #make sure the strength is within the range 0-1			
                        if strength > 1:
                            strength = 1
                        elif strength < 0:
                            strength = 0
                        
                        #apply the value shift
                        strength = strength + value_shift
                        
                        #apply the miltiplier
                        strength = strength * multiplier
                            
                        #apply the Neutralizer
                        #(Actual - Neutral)/(1-Neutral)
                        strength = (strength - face_neutral[blendshape_name]) / (1 - face_neutral[blendshape_name])
                        strength = round(strength ,4)
                
                        #set the keyframe
                        target_bone[blendShapeLabel] = strength
                        target_bone.keyframe_insert(data_path=propertyName, frame = current_frame_no)
                        
                        #incrament the frame counter
                        current_frame_no += 1
    
    ################################################################    
    # get the strength value
    ################################################################        
    def get_strength(self, y, capture_frames, capture_frames_count, mapping, smooth_shift):
        strength = 0.0
        capture_item_name = mapping['Name']
        target_axis = mapping['Target']
        enabled = mapping['Enabled']
        multiplier = float(mapping['Multiplier'])
        value_shift = float(mapping['ValueShift'])
        smooth = mapping['Smooth']
        
        if enabled.upper() == 'Y':
            #get the strength (smooth style)
            if smooth.upper() == 'Y':
                #smoothing applies a rolling average using the current frame, previous # frames, and next # frames
                range_count = 0
                range_sum = 0.0
                for x in range(y - smooth_shift, y + 1 + smooth_shift):
                    if x >=0 and x < capture_frames_count:
                        range_frame = capture_frames[x]
                        range_count += 1
                        capture_frame = range_frame[capture_item_name]
                        if 'E' in capture_frame: #cater for when numbers are super low
                            capture_frame_value = 0.0
                        else:
                            capture_frame_value = float(capture_frame)
                        range_sum += capture_frame_value
                strength = range_sum / range_count
            else:
                capture_frame = capture_frames[y]
                if 'E' in capture_frame[capture_item_name]: #cater for when numbers are super low
                    strength = 0.0
                else:
                    strength = float(capture_frame[capture_item_name])
            
            #make sure the strength is within the range 0-1			
            if strength > 1:
                strength = 1
            elif strength < -1:
                strength = -1
            
            #apply the value shift
            strength = strength + value_shift
                        
            #apply the miltiplier
            strength = strength * multiplier
        
        return strength
                         
    ################################################################    
    # get the rotation
    ################################################################        
    def get_rotation_quaternion(self, yaw_strength, yaw_mapping, pitch_strength, pitch_mapping, roll_strength, roll_mapping):
        w = 1.0
        x = 0.0
        y = 0.0
        z = 0.0
        
        yaw_enabled = yaw_mapping['Enabled']
        yaw_target = yaw_mapping['Target']
        pitch_enabled = pitch_mapping['Enabled']
        pitch_target = pitch_mapping['Target']
        roll_enabled = roll_mapping['Enabled']
        roll_target = roll_mapping['Target']
        
        if yaw_enabled.upper() == 'Y' and yaw_target != None:
            if yaw_target.upper() == 'X':
                x = yaw_strength
            elif yaw_target.upper() == 'Y':
                y = yaw_strength
            elif yaw_target.upper() == 'Z':
                z = yaw_strength
            
        if pitch_enabled.upper() == 'Y' and pitch_target != None:
            if pitch_target.upper() == 'X':
                x = pitch_strength
            elif pitch_target.upper() == 'Y':
                y = pitch_strength
            elif pitch_target.upper() == 'Z':
                z = pitch_strength
            
        if roll_enabled.upper() == 'Y' and roll_target != None:
            if roll_target.upper() == 'X':
                x = roll_strength
            elif roll_target.upper() == 'Y':
                y = roll_strength
            elif roll_target.upper() == 'Z':
                z = roll_strength

        return [w, x, y, z]

    ################################################################    
    # Apply the item rotations
    ################################################################    
    def apply_item_data(self, 
        target_object, yaw_mapping, pitch_mapping, roll_mapping,
        capture_frames, apply_capture_frames_to, start_frame, skip_capture_frames, smooth_frames):
        current_frame_no = start_frame

        #loop the capture frames and apply the morph strength
        capture_frames_count = len(capture_frames)
        if capture_frames_count > skip_capture_frames:
            
            #determine the number of smoothing shift frames
            smooth_shift = 0
            if smooth_frames == 'S3':
                smooth_shift = 1
            elif smooth_frames == 'S5':
                smooth_shift = 2
            elif smooth_frames == 'S7':
                smooth_shift = 3
            elif smooth_frames == 'S9':
                smooth_shift = 4
            elif smooth_frames == 'S11':
                smooth_shift = 5  
            
            for y in range(skip_capture_frames, capture_frames_count):
                capture_frame = capture_frames[y]

                #first test if we are applying this frame??
                if apply_capture_frames_to[y] == True:
                    yaw_strength = self.get_strength(y, capture_frames, capture_frames_count, yaw_mapping, smooth_shift)
                    pitch_strength =  self.get_strength(y, capture_frames, capture_frames_count, pitch_mapping, smooth_shift)
                    roll_strength = self.get_strength(y, capture_frames, capture_frames_count, roll_mapping, smooth_shift)
                                            
                    #set the rotation
                    rotation_quaternion = self.get_rotation_quaternion(yaw_strength, yaw_mapping, pitch_strength, pitch_mapping, roll_strength, roll_mapping)
                    target_object.rotation_quaternion = rotation_quaternion
                    target_object.keyframe_insert(data_path='rotation_quaternion', frame=current_frame_no)
                    
                    #incrament the frame counter
                    current_frame_no += 1
    
    ################################################################    
    # Apply execution
    ################################################################    
    def execute(self, context):
        props = context.scene.ApplicatorProps
        target_rig = context.scene.app_rig_target
        start_frame = props.start_frame
        skip_capture_frames = props.skip_capture_frames
        smooth_frames = props.smoothing_frames
        fps = bpy.context.scene.render.fps
        
        #make sure we are in object mode
        if bpy.context.object != None and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        #deselect if any selected objects
        bpy.ops.object.select_all(action='DESELECT')

        #validate the settings
        is_valid, messages = self.ValidateSettings(target_rig, props)            
        
        if is_valid:
            #get the capture frames from the file
            capture_frames = list_csv_data(props.capture_file_path)

            #get face neutral frames
            face_neutral_frames = None
            if props.neutral_file_path != None and props.neutral_file_path != '':
                face_neutral_frames = list_csv_data(props.neutral_file_path)
            
            #get the face zero values
            face_neutral = get_face_neutral_from_frames(data_shapkey_names, face_neutral_frames)

            #get the mapping data
            mapping_data = list_csv_data(props.mapping_file_path)

            #remove existing keyframes
            if props.clear_existing_keyframes == True:
                remove_keyframes(target_rig, props.apply_shapekey_data, props.apply_rotation_data)

            #see which frames we are apply the capture data to
            #these are the frames from the file we are to apply to the scene 
            apply_capture_frames_to = list_apply_capture_frames_to(fps, len(capture_frames))

            #apply ShapeKey data
            if props.apply_shapekey_data == True:
                eye_r_bone = target_rig.pose.bones['Eye_R']
                eye_l_bone = target_rig.pose.bones['Eye_L']
                brows_bone = target_rig.pose.bones['Brows']
                nose_bone = target_rig.pose.bones['Nose']
                mouth_bone = target_rig.pose.bones['Mouth']
                
                prop_bones = [eye_r_bone, eye_l_bone, brows_bone, nose_bone, mouth_bone]
                for prop_bone in prop_bones:
                    blendshape_mappings = [mapping for mapping in mapping_data if mapping['Type'].upper() == 'BLENDSHAPE' and mapping['Enabled'].upper() == 'Y']
                    for blendshape_mapping in blendshape_mappings:
                        self.apply_blendshape_data(
                            prop_bone,
                            blendshape_mapping['Name'], 
                            float(blendshape_mapping['Multiplier']), 
                            float(blendshape_mapping['ValueShift']), 
                            blendshape_mapping['Smooth'], 
                            capture_frames, 
                            face_neutral, 
                            apply_capture_frames_to, 
                            start_frame, 
                            skip_capture_frames,
                            smooth_frames)
        
            #apply rotation data
            if props.apply_rotation_data == True:
                head_bone = target_rig.pose.bones['Head']
                eye_l_bone = target_rig.pose.bones['Eye_L']
                eye_r_bone = target_rig.pose.bones['Eye_R']
                
                head_yaw_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'HEADYAW']
                head_pitch_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'HEADPITCH']
                head_roll_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'HEADROLL']
                left_eye_yaw_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'LEFTEYEYAW']
                left_eye_pitch_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'LEFTEYEPITCH']
                left_eye_roll_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'LEFTEYEROLL']
                right_eye_yaw_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'RIGHTEYEYAW']
                right_eye_pitch_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'RIGHTEYEPITCH']
                right_eye_roll_mappings = [mapping for mapping in mapping_data if mapping['Name'].upper() == 'RIGHTEYEROLL']
                
                #Head Logic
                self.apply_item_data(
                    head_bone, head_yaw_mappings[0], head_pitch_mappings[0], head_roll_mappings[0],
                    capture_frames, apply_capture_frames_to, start_frame, skip_capture_frames, smooth_frames)

                #LeftEye Logic
                self.apply_item_data(
                    eye_l_bone, left_eye_yaw_mappings[0], left_eye_pitch_mappings[0], left_eye_roll_mappings[0],
                    capture_frames, apply_capture_frames_to, start_frame, skip_capture_frames, smooth_frames)

                #RightEye Logic
                self.apply_item_data(
                    eye_r_bone, right_eye_yaw_mappings[0], right_eye_pitch_mappings[0], right_eye_roll_mappings[0],
                    capture_frames, apply_capture_frames_to, start_frame, skip_capture_frames, smooth_frames)
                        
            #done
            show_message_box(["Processing completed. Face capture data has been applied"], "Processing complete", 'INFO')
        else:
            #Display the errors
            show_message_box(messages, "Validation error", 'CANCEL') 
        
        return {'FINISHED'}


################################################################    
# Message Boxes
################################################################    
def show_message_box(messages = [], title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        for message in messages:
            self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

################################################################    
# Validate csv columns
# This ckecks the expected columns exists in the csv. 
# Other columns can exists, but lets make sure the ones we want is there
################################################################    
def validate_csv(csv_path, expected_columns):
    result = True
    missing_columns = []
    
    with open(csv_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            for expected_column in expected_columns:
                if expected_column not in row:
                    result = False
                    missing_columns.append(expected_column)
            break

    return result, missing_columns

#######################################################################
# Gets the data as list of dictionary items
#######################################################################
def list_csv_data(capture_path):
    result = []
    with open(capture_path) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            result.append(row)
    return result

#######################################################################
# Gets the used frame range
# Frame range can be larger than the scene's range (typical for mocap data)
# So we check what has been used
#######################################################################
def used_frame_range():
    frame_range_start = 0
    frame_range_end = 0
    for action in bpy.data.actions:
        if action.frame_range[0] < frame_range_start:
            frame_range_start = action.frame_range[0]
        
        if action.frame_range[1] > frame_range_end:
            frame_range_end = action.frame_range[1]
            
    return frame_range_start, frame_range_end

#######################################################################
# Delete the keyframes on the object
#######################################################################
def remove_keyframes_for_object(object, frame_range_start, frame_range_end, data_path):
    for frame in range(int(frame_range_start), int(frame_range_end) + 1):    
        try:
            object.keyframe_delete(data_path=data_path, frame=frame)
        except RuntimeError:
            #No Data.
            break

#######################################################################
# Removes the keyframes from the target rig
#######################################################################
def remove_keyframes(target_rig, remove_property_keyframes, remove_transform_keyframes):
    frame_range_start, frame_range_end = used_frame_range()
    if frame_range_start != 0 or frame_range_end != 0:
        head_bone = target_rig.pose.bones['Head']
        eye_l_bone = target_rig.pose.bones['Eye_L']
        eye_r_bone = target_rig.pose.bones['Eye_R']

        if remove_property_keyframes:
            #head - custom properties
            for blendShapeLabel in blendShapeLabels.values():
                try:
                    prop = head_bone[blendShapeLabel] #this will fail if it doesn't exist
                    remove_keyframes_for_object(head_bone, frame_range_start, frame_range_end, '["' + blendShapeLabel + '"]')
                    head_bone[blendShapeLabel] = 0.0
                except:
                    #property doesnt exist, sowe skip it
                    prop = None
        
        if remove_transform_keyframes:
            #left eye - rotation_quaternion
            remove_keyframes_for_object(eye_l_bone, frame_range_start, frame_range_end, 'rotation_quaternion')
            eye_l_bone.rotation_quaternion[0] = 1.0 #w
            eye_l_bone.rotation_quaternion[1] = 0.0 #x
            eye_l_bone.rotation_quaternion[2] = 0.0 #y
            eye_l_bone.rotation_quaternion[3] = 0.0 #z

            #left eye - location
            remove_keyframes_for_object(eye_l_bone, frame_range_start, frame_range_end, 'location')
            eye_l_bone.location[0] = 0.0 #x
            eye_l_bone.location[1] = 0.0 #y
            eye_l_bone.location[2] = 0.0 #z

            #left eye - location
            remove_keyframes_for_object(eye_l_bone, frame_range_start, frame_range_end, 'scale')
            eye_l_bone.scale[0] = 1.0 #x
            eye_l_bone.scale[1] = 1.0 #y
            eye_l_bone.scale[2] = 1.0 #z

            #right eye - rotation_quaternion
            remove_keyframes_for_object(eye_r_bone, frame_range_start, frame_range_end, 'rotation_quaternion')
            eye_r_bone.rotation_quaternion[1] = 0.0 #x
            eye_r_bone.rotation_quaternion[2] = 0.0 #y
            eye_r_bone.rotation_quaternion[3] = 0.0 #z
            
            #right eye - location
            remove_keyframes_for_object(eye_r_bone, frame_range_start, frame_range_end, 'location')
            eye_r_bone.location[0] = 0.0 #x
            eye_r_bone.location[1] = 0.0 #y
            eye_r_bone.location[2] = 0.0 #z

            #right eye - location
            remove_keyframes_for_object(eye_r_bone, frame_range_start, frame_range_end, 'scale')
            eye_r_bone.scale[0] = 1.0 #x
            eye_r_bone.scale[1] = 1.0 #y
            eye_r_bone.scale[2] = 1.0 #z
            
            #head - rotation_quaternion
            remove_keyframes_for_object(head_bone, frame_range_start, frame_range_end, 'rotation_quaternion')
            head_bone.rotation_quaternion[1] = 0.0 #x
            head_bone.rotation_quaternion[2] = 0.0 #y
            head_bone.rotation_quaternion[3] = 0.0 #z
            
            #head - location
            remove_keyframes_for_object(head_bone, frame_range_start, frame_range_end, 'location')
            head_bone.location[0] = 0.0 #x
            head_bone.location[1] = 0.0 #y
            head_bone.location[2] = 0.0 #z

            #head - location
            remove_keyframes_for_object(head_bone, frame_range_start, frame_range_end, 'scale')
            head_bone.scale[0] = 1.0 #x
            head_bone.scale[1] = 1.0 #y
            head_bone.scale[2] = 1.0 #z


#######################################################################
# Determines which capture frames are applied to scene based on the scenes frame rate
# This function return a list of booleans representing which capture frames to apply
#######################################################################
def list_apply_capture_frames_to(fps, capture_frame_count):
    result = []
    apply_pattern = []

    #set the apply pattern
    if fps == 24.0 or fps == 23.98:
        #YnYnYnnnYnYnnnYnYnYn|YnYnYnnnYnYnnnYnYnYn|YnYnYnnnYnYnnnYnYnYn|...
        apply_pattern = [True, False, True, False, True, False, False, False, True, False, True, False, False, False, True, False, True, False, True, False]	
    elif fps == 25.0:		
        #YnYnYnYnYnnn|YnYnYnYnYnnn|YnYnYnYnYnnn|....
        apply_pattern = [True, False, True, False, True, False, True, False, True, False, False, False]
    elif fps == 30.0 or fps == 29.97:
        #Yn|Yn|Yn|...
        apply_pattern = [True, False]
    elif fps == 48.0:
        #YYYnYYnYYY|YYYnYYnYYY|YYYnYYnYYY|...
        apply_pattern = [True, True, True, False, True, True, False, True, True, True]	
    elif fps == 50.0:
        #YYYYYn|YYYYYn|YYYYYn|...
        apply_pattern = [True, True, True, True, True, False]
    else: #60/59.94
        #Y|Y|Y|...
        apply_pattern = [True]

    #string together to make the apply_capture_frames list to cover the length of the capture frames
    while len(result) <= capture_frame_count:
        result.extend(apply_pattern)
    
    #return the results
    return result

#######################################################################
# gets the face zero data 
# ARKit picks up the captured face's neautral weights differently
# so this is used to offset thoes charcteristics and give a more natral result
# the zero value is calulated by vareraging the middle thrid of frame values
# if no zero face frames are provide, then it will default to 0
#######################################################################
def get_face_neutral_from_frames(shapekey_names, face_neutral_frames):
    result = { shapekey_name : 0.0 for shapekey_name in shapekey_names }
    shapekey_tally = { shapekey_name : 0.0 for shapekey_name in shapekey_names }
    
    #calculate if we have data
    if face_neutral_frames != None:		
        #get the middle third
        frame_count = len(face_neutral_frames)
        frame_start = int(frame_count / 3)
        frame_end = int(frame_start) * 2		
        
        #tally up the rows
        for x in range(frame_start, frame_end):
            face_neutral_frame = face_neutral_frames[x]
            for shapekey_name in shapekey_names:
                #cater for very low numbers
                shapekey_value_str = face_neutral_frame[shapekey_name]
                if 'E' in shapekey_value_str:
                    shapekey_value = 0.0
                else:
                    shapekey_value = float(shapekey_value_str)

                if shapekey_value > 1:
                    shapekey_value = 1
                elif shapekey_value < 0:
                    shapekey_value = 0	

                shapekey_tally[shapekey_name] += shapekey_value
        
        #divde by number of frames in the range (i.e. frame_start)
        for shapekey_name in shapekey_names:
            result[shapekey_name] = round(shapekey_tally[shapekey_name] / frame_start, 10)
        
    return result
    
################################################################    
# Registration
################################################################    
def register():
    bpy.utils.register_class(ApplicatorProps)
    bpy.utils.register_class(ApplicatorTargetPanel)
    bpy.utils.register_class(ApplicatorDataPanel)
    #bpy.utils.register_class(ApplicatorMappingPanel)
    bpy.utils.register_class(ApplicatorApplyPanel)
    
    bpy.utils.register_class(ApplicatorCreateFaceRig)
    bpy.utils.register_class(ApplicatorSelectCaptureFile)
    bpy.utils.register_class(ApplicatorClearCaptureFile)
    
    bpy.utils.register_class(ApplicatorSelectNeutralFile)
    bpy.utils.register_class(ApplicatorClearNeutralFile)
    
    bpy.utils.register_class(ApplicatorSelectMappingFile)
    bpy.utils.register_class(ApplicatorClearMappingFile)
    
    bpy.utils.register_class(ApplicatorApply)
    
    # Register the Props
    bpy.types.Scene.ApplicatorProps = bpy.props.PointerProperty(type=ApplicatorProps)
 
def unregister():
    bpy.utils.unregister_class(ApplicatorProps)
    bpy.utils.unregister_class(ApplicatorTargetPanel)
    bpy.utils.unregister_class(ApplicatorDataPanel)
    #bpy.utils.unregister_class(ApplicatorMappingPanel)
    bpy.utils.unregister_class(ApplicatorApplyPanel)
 
    bpy.utils.unregister_class(ApplicatorCreateFaceRig)
    bpy.utils.unregister_class(ApplicatorSelectCaptureFile)
    bpy.utils.unregister_class(ApplicatorClearCaptureFile)
    
    bpy.utils.unregister_class(ApplicatorSelectNeutralFile)
    bpy.utils.unregister_class(ApplicatorClearNeutralFile)
    
    bpy.utils.unregister_class(ApplicatorSelectMappingFile)
    bpy.utils.unregister_class(ApplicatorClearMappingFile)
    
    bpy.utils.unregister_class(ApplicatorApply)

if __name__ == "__main__":
    register()