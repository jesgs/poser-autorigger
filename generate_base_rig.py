import bpy

def rename_all_bones(armature, prefix = ''):
    bones = armature.data.edit_bones

    for bone in bones:
        new_name = rename_bone(bone.name, prefix)
        if new_name != "":
            armature.data.edit_bones[bone.name].name = new_name


def rename_bone(name, prefix = ''):
    if "root" in name or "PROPERTIES" in name:
        return ""

    new_name = name
    if name.find('Left_') != -1:
        new_name = name[5:] + '.L'
    elif name.find('Right_') != -1:
        new_name = name[6:] + '.R'

    if name.find('l', 0, 1) != -1:
        new_name = name[1:] + '.L'
    elif name.find('r', 0, 1) != -1:
        new_name = name[1:] + '.R'

    return prefix + new_name


def setup_poser_figure(objects):
    # Before deselecting everything, apply scale/rotation
    # Poser's scale is 1/100 smaller than Blender, plus rotation is different as well
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.select_all(action='DESELECT')

    for obj in objects:
        bpy.context.view_layer.objects.active = bpy.context.view_layer.objects[obj.name]
        bpy.context.active_object.select_set(state=True)

        if obj.type == 'MESH':
            # check if mesh is parented to an armature
            if obj.parent.type == 'ARMATURE':
                # go into edit mode, select all loose geometry and delete it
                bpy.ops.object.editmode_toggle()

                # Poser's FBX export adds loose vertices at the borders between
                # vertex groups. These will cause problems when it comes time to
                # adjust weight-maps
                bpy.ops.mesh.select_loose()
                bpy.ops.mesh.delete(type='VERT')

                # Also symmetrize geometry to prevent issues with mirroring vertex groups
                # and manipulating geometry in sculpt-mode
                bpy.ops.mesh.symmetry_snap()
                bpy.ops.mesh.symmetry_snap(direction='POSITIVE_X')

                # remove the root or Body vertex groups — sometimes, the bone rename happens before processing the mesh
                vertex_group = obj.vertex_groups.get('Body') or obj.vertex_groups.get('root')
                if vertex_group:
                    obj.vertex_groups.remove(vertex_group)

                # create new weight-group for LowerAbdomen bone
                obj.vertex_groups.new(name="DEF-LowerAbdomen")
                obj.vertex_groups.active = obj.vertex_groups.get('DEF-LowerAbdomen')
                obj.vertex_groups.active_index = 1

                bpy.ops.object.editmode_toggle()

        if obj.type == 'ARMATURE':
            # maybe we could also change display to b-bone or stick?
            obj.show_in_front = True
            obj.display_type = 'WIRE'

            bpy.ops.object.editmode_toggle()  # go into edit mode
            bpy.context.object.data.display_type = 'BBONE'

            obj = bpy.context.object
            # fix some issues with bones coming from Poser
            edit_bones = obj.data.edit_bones

            fix_bones(edit_bones)
            create_root(edit_bones)
            create_lower_abdomen_bone(edit_bones)
            #create_pelvis_bones()

            rename_all_bones(obj, 'DEF-')

            create_properties_bone(edit_bones)

            arm_ik_bone_chains = [
                'Hand',
                'Forearm',
                'Shoulder',
                'Collar'
            ]
            leg_ik_bone_chains = [
                'Foot',
                'Shin',
                'Thigh',
                'Buttock'
            ]
            spine_ik_bone_chains = [
                'Hip',
                'LowerAbdomen',
                'Abdomen',
                'Chest',
                'Neck',
                'Head'
            ]

            spine_ik_chain = create_fkik_chains(obj.data.edit_bones, spine_ik_bone_chains, 'root', 'IK', '', 'THEME03', 0.004, False)
            spine_fk_chain = create_fkik_chains(obj.data.edit_bones, spine_ik_bone_chains, 'root', 'FK', '', 'THEME03', 0.002)

            # arm chains
            arm_ik_chain_left = create_fkik_chains(obj.data.edit_bones, arm_ik_bone_chains, 'DEF-Chest', 'IK', '.L', 'THEME01', 0.004)
            arm_ik_chain_right = create_fkik_chains(obj.data.edit_bones, arm_ik_bone_chains, 'DEF-Chest', 'IK', '.R', 'THEME01', 0.004)
            arm_fk_chain_left = create_fkik_chains(obj.data.edit_bones, arm_ik_bone_chains, 'DEF-Chest', 'FK', '.L', 'THEME03', 0.002)
            arm_fk_chain_right = create_fkik_chains(obj.data.edit_bones, arm_ik_bone_chains, 'DEF-Chest', 'FK', '.R', 'THEME03', 0.002)

            # leg chains
            leg_ik_chain_left = create_fkik_chains(obj.data.edit_bones, leg_ik_bone_chains, 'DEF-Hip', 'IK', '.L', 'THEME01', 0.004)
            leg_ik_chain_right = create_fkik_chains(obj.data.edit_bones, leg_ik_bone_chains, 'DEF-Hip', 'IK', '.R', 'THEME01', 0.004)
            leg_fk_chain_left = create_fkik_chains(obj.data.edit_bones, leg_ik_bone_chains, 'DEF-Hip', 'FK', '.L', 'THEME03', 0.002)
            leg_fk_chain_right = create_fkik_chains(obj.data.edit_bones, leg_ik_bone_chains, 'DEF-Hip', 'FK', '.R', 'THEME03', 0.002)

            # change bone-roll to Global +Z to prevent issues later on
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')

            # separate_armatures(figure_name, obj)
            # strip_trailing_digits_from_bones(obj)

            bpy.ops.object.editmode_toggle()  # we're done here

            # bpy.ops.object.posemode_toggle() # pose mode now — setting up constraints.

        bpy.ops.object.select_all(action='DESELECT')


def fix_bones(edit_bones):
    # head and neck bone are off-center, let's fix
    edit_bones['Head'].head[0] = 0  # this should also move the tail of the neck bone since they're connected

    # let's also align tail of chest bone with head of neck bone
    # move the z and y axi, but we need to find the center
    chest_tail_y = edit_bones['Chest'].tail[1]
    chest_tail_z = edit_bones['Chest'].tail[2]
    neck_head_y = edit_bones['Neck'].head[1]
    neck_head_z = edit_bones['Neck'].head[2]
    center_y = (neck_head_y + chest_tail_y) / 2
    center_z = (neck_head_z + chest_tail_z) / 2

    edit_bones['Neck'].head[1] = center_y
    edit_bones['Neck'].head[2] = center_z
    edit_bones['Chest'].tail[1] = center_y
    edit_bones['Chest'].tail[2] = center_z

    # fix eyes and toe bones as well
    eye_y = edit_bones['Left_Eye'].tail[1]
    edit_bones['Left_Eye'].tail[1] = eye_y - -0.1
    edit_bones['Right_Eye'].tail[1] = eye_y - -0.1

    toe_y = edit_bones['Left_Toe'].tail[1]
    edit_bones['Left_Toe'].tail[1] = toe_y - -0.1
    edit_bones['Right_Toe'].tail[1] = toe_y - -0.1


def create_fkik_chains(edit_bones, bone_chains, parent = '', prefix = 'IK', suffix ='.L', palette = 'THEME01', bone_size = 0.002, create_handle = True):
    fkik_chains = []
    completed_fkik_chains = []
    for bone in edit_bones:
        for bc in bone_chains:
            if bone.name.find(bc) == -1:
                continue

            if bone.name.find(suffix) == -1:
                continue

            bone_name = bone.name
            fkik_bone_name = bone_name.replace('DEF', prefix)
            fkik_chains.append(fkik_bone_name)

    for i, fkik_chain_item in enumerate(fkik_chains):
        deform_bone_name = fkik_chain_item.replace(prefix, 'DEF')
        fkik_bone = edit_bones.new(fkik_chain_item)
        fkik_bone.use_deform = False

        match_bone_head_coordinates(deform_bone_name, edit_bones, fkik_bone)
        match_bone_tail_coordinates(deform_bone_name, edit_bones, fkik_bone)

        fkik_bone.bbone_z = fkik_bone.bbone_x = bone_size
        fkik_bone.color.palette = palette
        fkik_bone.use_connect = False

        # parenting
        if 0 == i:
            fkik_bone.parent = edit_bones[parent]
        else:
            fkik_bone.parent = edit_bones[fkik_chains[i - 1]]

        completed_fkik_chains.append(fkik_bone)

    # create IK target controls
    if prefix == 'IK' and create_handle:
        last = len(fkik_chains) - 1
        last_bone = edit_bones[fkik_chains[last]]
        ik_handle_name = fkik_chains[last].replace(prefix + '-', prefix + '-Target-')
        ik_handle = edit_bones.new(ik_handle_name)
        ik_handle.head = last_bone.head
        ik_handle.tail = last_bone.tail
        ik_handle.bbone_z = ik_handle.bbone_x = bone_size * 2
        ik_handle.length = bone_size * 10
        ik_handle.color.palette = palette
        completed_fkik_chains.append(ik_handle)

    return completed_fkik_chains


def match_bone_tail_coordinates(deform_bone_name, edit_bones, bone):
    bone.tail = edit_bones[deform_bone_name].tail


def match_bone_head_coordinates(deform_bone_name, edit_bones, bone):
    bone.head = edit_bones[deform_bone_name].head


def create_pelvis_bones():
    pass
    # create pelvis and buttock bones but first rename the current buttock bones
    # edit_bones['Left_Buttock'].name = 'Left_Hip'
    # edit_bones['Right_Buttock'].name = 'Right_Hip'
    #
    # bone_left_pelvis = edit_bones.new('Left_Pelvis')
    # bone_right_pelvis = edit_bones.new('Right_Pelvis')
    # bone_left_buttock = edit_bones.new('Left_Buttock')
    # bone_right_buttock = edit_bones.new('Right_Buttock')
    # bone_left_pelvis.parent = edit_bones['Hip']
    # bone_right_pelvis.parent = edit_bones['Hip']
    # bone_left_buttock.parent = bone_left_pelvis
    # bone_right_buttock.parent = bone_right_pelvis


def create_properties_bone(edit_bones):
    # create new properties bone
    properties_bone = edit_bones.new('PROPERTIES')
    properties_bone.parent = edit_bones['root']
    properties_bone.head = [0, 0, 0]
    properties_bone.tail = [0, 0.25, 0]
    properties_bone.use_deform = False

    properties_bone.color.palette = 'THEME03'
    properties_bone.bbone_z = 0.01
    properties_bone.bbone_x = 0.01


def create_lower_abdomen_bone(edit_bones):
    # create new LowerAbdomen bone, move to between hip and abdomen, make hip its parent,
    # then parent abdomen to new bone
    bone_lower_abdomen = edit_bones.new('LowerAbdomen')

    bone_lower_abdomen.head = edit_bones['Hip'].tail
    bone_lower_abdomen.tail = edit_bones['Abdomen'].head

    bone_lower_abdomen.parent = edit_bones['Hip']
    edit_bones['Abdomen'].parent = bone_lower_abdomen
    bone_lower_abdomen.bbone_z = 0.001
    bone_lower_abdomen.bbone_x = 0.001


def create_root(edit_bones):
    # rename Body to root, disconnect, and drop to 0
    edit_bones['Hip'].use_connect = False
    edit_bones['Body'].use_deform = False
    edit_bones['Body'].head = [0, 0, 0]
    edit_bones['Body'].tail = [0, 0.5, 0]
    edit_bones['Body'].color.palette = 'THEME09'
    edit_bones['Body'].name = 'root'


class GenerateBaseRig_Operator(bpy.types.Operator):
    bl_idname = "poser.generate_base_rig"
    bl_label = "Generate Base Rig"
    bl_description = "Generate Base Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.scene.objects) == 0:
            return False

        return True

    def execute(self, context):
        setup_poser_figure(context.selected_objects)
        return {'FINISHED'}

class RigPoserArmature_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Poser"
    bl_category = "Rig Poser"

    def draw(self, context):
        layout = self.layout
        op_row = layout.row(align=True)
        op_row.scale_y = 1.5

        op_row.operator("poser.generate_base_rig", icon="POSE_HLT")

classes = [RigPoserArmature_Panel, GenerateBaseRig_Operator]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()