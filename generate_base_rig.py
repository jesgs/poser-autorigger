from typing import LiteralString

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

            armature = bpy.context.object

            # rigging_collection = armature.data.collections.new('Rigging')
            # deform_collection = armature.data.collections.new('Deform')
            # deform_collection.parent = rigging_collection

            # fix some issues with bones coming from Poser
            edit_bones = armature.data.edit_bones

            fix_bones(edit_bones)
            create_root(edit_bones)
            create_lower_abdomen_bone(edit_bones)
            #create_pelvis_bones()
            rename_all_bones(armature, 'DEF-')

            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')

            create_spine_fkik_chains(edit_bones)
            create_arm_fkik_chains(edit_bones)
            create_leg_fkik_chains(edit_bones)
            create_finger_fkik_chains(edit_bones)
            create_ik_control_bones(edit_bones, ['Hand', 'Forearm', 'Shoulder'])
            create_ik_control_bones(edit_bones, ['Hand', 'Forearm', 'Shoulder'], '.R')
            create_ik_control_bones(edit_bones, ['Foot', 'Shin', 'Thigh'], '.L', 'Knee', -0.625)
            create_ik_control_bones(edit_bones, ['Foot', 'Shin', 'Thigh'], '.R', 'Knee', -0.625)
            create_properties_bone(edit_bones)

            # change bone-roll to Global +Z to prevent issues later on
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')

            # separate_armatures(figure_name, obj)
            # strip_trailing_digits_from_bones(obj)

            bpy.ops.object.editmode_toggle()  # we're done here

            bpy.ops.object.posemode_toggle() # pose mode now — setting up constraints.

            # add constraints
            add_copy_constraints(armature, 'IK', 'FK')
            add_copy_constraints(armature, 'FK', 'DEF')
            add_ik_constraints(armature, 'CTRL-IK-Hand' , ['Forearm', 'Shoulder'], '.L', 'Elbow', 180)
            add_ik_constraints(armature, 'CTRL-IK-Hand' , ['Forearm', 'Shoulder'], '.R', 'Elbow', 0)
            add_ik_constraints(armature, 'CTRL-IK-Foot' , ['Shin', 'Thigh'], '.L', 'Knee', 180)
            add_ik_constraints(armature, 'CTRL-IK-Foot' , ['Shin', 'Thigh'], '.R', 'Knee', 0)

            # create IK target controls
            # if prefix == 'IK' and create_handle:
            #     print(fkik_chains)
            #     last = len(fkik_chains) - 1
            #     last_bone = edit_bones[fkik_chains[last]]
            #     ik_handle_name = fkik_chains[last].replace(prefix + '-', prefix + '-Target-')
            #     ik_handle = edit_bones.new(ik_handle_name)
            #     ik_handle.head = last_bone.head
            #     ik_handle.tail = last_bone.tail
            #     ik_handle.bbone_z = ik_handle.bbone_x = bone_size * 2
            #     ik_handle.length = bone_size * 10
            #     ik_handle.color.palette = palette
            #     completed_fkik_chains.append(ik_handle)

            #        bpy.ops.object.select_all(action='DESELECT')


def create_ik_control_bones(edit_bones, chain: list[LiteralString], side ='.L', pole_name ='Elbow', y_axis_position = 0.625):

    ctrl_prefix = 'CTRL'
    prefix = 'IK'
    ik_control_bone_name = ctrl_prefix + '-' + prefix + '-' + chain[0] + side
    ik_control_bone = edit_bones.new(ik_control_bone_name)
    first_bone = edit_bones[prefix + '-' + chain[0] + side]

    # position control bone to match first bone in chain but change dimensions
    ik_control_bone.head = first_bone.head
    ik_control_bone.tail = first_bone.tail
    ik_control_bone.bbone_x = first_bone.bbone_x * 2
    ik_control_bone.bbone_z = first_bone.bbone_z * 2
    ik_control_bone.length = first_bone.length - 0.01
    ik_control_bone.color.palette = 'THEME01'

    # create a pole target bone based off second bone in chain, but rotate 90 degrees and move on Y-axis
    ik_pole_bone_name = ctrl_prefix + '-' + prefix + '-Pole-' + pole_name + side
    ik_pole_position_bone = edit_bones[prefix + '-' + chain[1] + side]

    ik_pole_bone = edit_bones.new(ik_pole_bone_name)
    ik_pole_bone.head = ik_pole_position_bone.head
    ik_pole_bone.tail = ik_pole_position_bone.tail
    ik_pole_bone.bbone_x = ik_pole_position_bone.bbone_x * 2
    ik_pole_bone.bbone_z = ik_pole_position_bone.bbone_z * 2
    ik_pole_bone.color.palette = 'THEME09'
    ik_pole_bone.tail = [ik_pole_bone.head[0], y_axis_position, ik_pole_bone.head[2]]
    ik_pole_bone.head[1] = y_axis_position - 0.125


def add_ik_constraints(armature, ik_target_name, chain: list[LiteralString], side = '.L', pole_name ='Elbow', pole_angle = 180):
    bones = armature.pose.bones
    chain_length = len(chain)
    ik_target_bone = bones.get(ik_target_name + side)
    ik_pole_bone = bones.get('CTRL-IK-Pole-' + pole_name + side)

    ik_constraint_bone_name = 'IK-' + chain[0] + side

    ik_constraint = bones[ik_constraint_bone_name].constraints.new('IK')
    ik_constraint.target = armature
    ik_constraint.subtarget = ik_target_bone.name
    ik_constraint.pole_target = armature
    ik_constraint.pole_angle = pole_angle
    ik_constraint.pole_subtarget = ik_pole_bone.name
    ik_constraint.chain_count = chain_length


def add_copy_constraints(armature, prefix_target, prefix_constraint):
    bones = armature.pose.bones

    for bone in bones:
        if not bone.name.startswith(prefix_target):
            continue

        constraint_bone_name = bone.name.replace(prefix_target, prefix_constraint)
        if constraint_bone_name not in bones:
            continue

        # Add the constraint itself
        constraint = bones[constraint_bone_name].constraints.new('COPY_TRANSFORMS')
        default_constraint_name = constraint.name
        constraint.name = default_constraint_name + ' ' + bone.name
        constraint.target = armature
        constraint.subtarget = bone.name


def create_leg_fkik_chains(edit_bones):
    # leg chains
    leg_fkik_bone_chain = [
        'Buttock',
        'Thigh',
        'Shin',
        'Foot',
        'Toe',
    ]
    create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'IK-Hip', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'IK-Hip', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'FK-Hip', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'FK-Hip', 'FK', '.R', 'THEME03', 0.002)


def create_arm_fkik_chains(edit_bones):
    # arm chains
    arm_fkik_bone_chain = [
        'Collar',
        'Shoulder',
        'Forearm',
        'Hand',
    ]
    create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'IK-Chest', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'IK-Chest', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'FK-Chest', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'FK-Chest', 'FK', '.R', 'THEME03', 0.002)


def create_spine_fkik_chains(edit_bones):
    # handle all fk/ik chains
    spine_fkik_bone_chain = [
        'Hip',
        'LowerAbdomen',
        'Abdomen',
        'Chest',
        'Neck',
        'Head'
    ]
    create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'IK', '', 'THEME09', 0.004, False, True)
    create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'FK', '', 'THEME04', 0.002, False, True)


def create_finger_fkik_chains(edit_bones):
    # ofml — finger chains now
    thumb_fkik_chain = [
        'Thumb_1',
        'Thumb_2',
        'Thumb_3',
    ]
    index_fkik_chain = [
        'Index_1',
        'Index_2',
        'Index_3',
    ]
    mid_fkik_chain = [
        'Mid_1',
        'Mid_2',
        'Mid_3',
    ]
    ring_fkik_chain = [
        'Ring_1',
        'Ring_2',
        'Ring_3',
    ]
    pinky_fkik_chain = [
        'Pinky_1',
        'Pinky_2',
        'Pinky_3',
    ]

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, index_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004)

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'IK-Hand.R', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, index_fkik_chain, 'IK-Hand.R', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'IK-Hand.R', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'IK-Hand.R', 'IK', '.R', 'THEME01', 0.004)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'IK-Hand.R', 'IK', '.R', 'THEME01', 0.004)

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, index_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'FK-Hand.R', 'FK', '.R', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, index_fkik_chain, 'FK-Hand.R', 'FK', '.R', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'FK-Hand.R', 'FK', '.R', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'FK-Hand.R', 'FK', '.R', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'FK-Hand.R', 'FK', '.R', 'THEME03', 0.002)


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


def create_fkik_chains(edit_bones, bone_chains, parent = '', prefix = 'IK', suffix ='.L', palette = 'THEME01', bone_size = 0.002, create_handle = True, strict = False):
    fkik_chains = []
    completed_fkik_chains = []
    for bc in bone_chains:
        for bone in edit_bones:
            deform_bone_name = 'DEF-' + bc + suffix
            if bone.name.find(bc) == -1:
                continue

            if deform_bone_name != bone.name:
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

class RigPoserArmature_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Poser"
    bl_category = "Rig Poser"
    bl_idname = "VIEW3D_PT_RigPoserArmature_PT_Panel"

    def draw(self, context):
        layout = self.layout
        op_row = layout.row(align=True)
        op_row.scale_y = 1.5

        op_row.operator("poser.generate_base_rig", icon="POSE_HLT")

classes = [RigPoserArmature_PT_Panel, GenerateBaseRig_Operator]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
