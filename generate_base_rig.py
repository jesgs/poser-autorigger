import sys
from typing import LiteralString
from mathutils import Matrix, Vector
import colorsys
import bpy
import math

bright_red = {
    'normal': colorsys.hsv_to_rgb(0.0, 1, 1),
    'select': colorsys.hsv_to_rgb(0.0, 1, 1),
    'active': colorsys.hsv_to_rgb(0.0, 0.25, 1),
}

bright_orange = {
    'normal': colorsys.hsv_to_rgb(0.0875, 1, 1),
    'select': colorsys.hsv_to_rgb(0.0875, 1, 1),
    'active': colorsys.hsv_to_rgb(0.0875, 0.25, 1),
}

bright_yellow = {
    'normal': colorsys.hsv_to_rgb(0.167, 1, 1),
    'select': colorsys.hsv_to_rgb(0.167, 1, 1),
    'active': colorsys.hsv_to_rgb(0.167, 0.25, 1),
}

bright_green = {
    'normal': colorsys.hsv_to_rgb(0.25, 1, 1),
    'select': colorsys.hsv_to_rgb(0.25, 1, 1),
    'active': colorsys.hsv_to_rgb(0.25, 0.25, 1),
}

bright_blue = {
    'normal': colorsys.hsv_to_rgb(0.625, 1, 1),
    'select': colorsys.hsv_to_rgb(0.625, 1, 1),
    'active': colorsys.hsv_to_rgb(0.625, 0.625, 1),
}


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

    # define some custom colors for certain bones

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
            create_ik_control_bones(edit_bones, ['Hand', 'Forearm', 'Shoulder',])
            create_ik_control_bones(edit_bones, ['Foot', 'Shin', 'Thigh',], '.L', 'Knee', -0.625)
            create_ik_control_bones(edit_bones, ['LowerAbdomen', 'Hip',], '', 'Hip')
            create_ik_control_bones(edit_bones, ['Chest', 'Abdomen', ], '', 'Chest')
            create_ik_control_bones(edit_bones, ['Head', 'Neck',], '', 'Neck')
            create_mch_shoulder_bones_and_controls(edit_bones)
            create_spine_control_bones(edit_bones)
            create_foot_roll_control_bones(edit_bones)

            # reposition spine IK controls and parent to spine controls
            bone_ctrl_ik_lowerabdomen = edit_bones['CTRL-IK-LowerAbdomen']
            bone_ctrl_ik_lowerabdomen.head = edit_bones['DEF-LowerAbdomen'].tail
            bone_ctrl_ik_lowerabdomen.parent = edit_bones['CTRL-Hip']
            assign_custom_color(bone_ctrl_ik_lowerabdomen, bright_green)

            bone_ctrl_ik_chest = edit_bones['CTRL-IK-Chest']
            bone_ctrl_ik_chest.head = edit_bones['DEF-Chest'].tail
            bone_ctrl_ik_chest.parent = edit_bones['CTRL-Chest']
            assign_custom_color(bone_ctrl_ik_chest, bright_green)

            bone_ctrl_ik_head = edit_bones['CTRL-IK-Head']
            bone_ctrl_ik_head.head = edit_bones['DEF-Head'].tail
            bone_ctrl_ik_head.parent = edit_bones['CTRL-Chest']
            bone_ctrl_ik_head.color.palette = 'CUSTOM'
            assign_custom_color(bone_ctrl_ik_head, bright_green)

            # spine pole bone colors
            assign_custom_color(edit_bones['CTRL-IK-Pole-Hip'], bright_blue)
            assign_custom_color(edit_bones['CTRL-IK-Pole-Chest'], bright_blue)
            assign_custom_color(edit_bones['CTRL-IK-Pole-Neck'], bright_blue)

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
            add_ik_constraints(armature, 'IK-Foot' , ['Shin', 'Thigh'], '.L', 'Knee', 180)
            add_ik_constraints(armature, 'CTRL-IK-LowerAbdomen', ['LowerAbdomen', 'Hip'], '', 'Hip', 90)
            add_ik_constraints(armature, 'CTRL-IK-Chest', ['Chest', 'Abdomen'], '', 'Chest', -90)
            add_ik_constraints(armature, 'CTRL-IK-Head', ['Head', 'Neck'], '', 'Neck', 90)
            setup_collar_constraints(armature)

            bpy.ops.object.editmode_toggle()
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.symmetrize(direction="POSITIVE_X")
            bpy.ops.object.posemode_toggle()
            # bpy.ops.object.select_all(action='DESELECT')


def create_foot_roll_control_bones(edit_bones):
    # create and position bones for foot roll mechanism
    # Bones (Symmetrized):
    # MCH-Roll-Toe.L (parented to MCH-Foot-Rollback.L)
    # MCH-Roll-Foot.L (parented to MCH-Foot-Rollback.L)
    # Roll-Foot.L (parented to CTRL-IK-Foot.L)
    # MCH-Foot-Rollback.L (parented to Roll-Foot.L)
    # CTRL-Foot-Roll.L (parented to CTRL-IK-Foot.L
    #

    bone_ik_toe = edit_bones['IK-Toe.L']
    bone_ik_foot = edit_bones['IK-Foot.L']


    bone_mch_roll_toe = edit_bones.new('MCH-Roll-Toe.L')
    bone_mch_roll_foot = edit_bones.new('MCH-Roll-Foot.L')
    bone_roll_foot = edit_bones.new('Roll-Foot.L')
    bone_mch_foot_rollback = edit_bones.new('MCH-Foot-Rollback.L')
    bone_ctrl_foot_roll = edit_bones.new('CTRL-Foot-Roll.L')
    bone_ctrl_ik_foot = edit_bones.new('CTRL-IK-Foot.L')

    # set up parenting
    bone_ik_toe.parent = bone_mch_roll_toe
    bone_ik_foot.parent = bone_mch_roll_foot
    bone_mch_roll_toe.parent = bone_mch_foot_rollback
    bone_mch_roll_foot.parent = bone_mch_foot_rollback
    bone_roll_foot.parent = bone_ctrl_ik_foot
    bone_mch_foot_rollback.parent = bone_roll_foot
    bone_ctrl_foot_roll.parent = bone_ctrl_ik_foot

    # position bones



def setup_collar_constraints(armature):
    bones = armature.pose.bones

    bone_ik_ctrl_hand = bones['CTRL-IK-Hand.L']
    bone_ik_collar = bones['IK-Collar.L']
    bone_mch_collar = bones['MCH-Collar.L']
    bone_mch_collar__damped_track = bones['MCH-Collar-DampedTrack.L']
    bone_mch_collar__target = bones['MCH-Collar-Target.L']

    # add Copy Rotations constraint to MCH-Collar from MCH-Collar-DampedTrack
    mch_collar_copy_rotation_constraint = bone_mch_collar.constraints.new('COPY_ROTATION')
    mch_collar_copy_rotation_constraint.target = armature
    mch_collar_copy_rotation_constraint.subtarget = bone_mch_collar__damped_track.name

    # add Damped Track constraint to MCH-Collar-DampedTrack
    mch_collar__damped_track_constraint = bone_mch_collar__damped_track.constraints.new('DAMPED_TRACK')
    mch_collar__damped_track_constraint.target = armature
    mch_collar__damped_track_constraint.subtarget = bone_mch_collar__target.name
    mch_collar__damped_track_constraint.track_axis = 'TRACK_Y'

    # add Copy Location constraints to bone_mch_collar__target from bone_ik_ctrl_hand
    # these constraints will need drivers assigned to determine influence amount when moving the
    # IK control
    add_copylocation_constraint(
        pose_bone=bone_mch_collar__target,
        target_bone=bone_ik_ctrl_hand,
        target_object=armature,
        name='Copy Location (+Z)',
        use_y=False
    )

    add_copylocation_constraint(
        pose_bone=bone_mch_collar__target,
        target_bone=bone_ik_ctrl_hand,
        target_object=armature,
        name='Copy Location (-Z)',
        use_y=False,
        influence=0.0
    )

    add_copylocation_constraint(
        pose_bone=bone_mch_collar__target,
        target_bone=bone_ik_ctrl_hand,
        target_object=armature,
        name='Copy Location (+/-Y)',
        use_x=False,
        use_y=True,
        use_z=False,
        owner_space='WORLD',
        target_space='WORLD'
    )


def add_copylocation_constraint(pose_bone, target_bone, target_object, name = 'Copy Location', use_x = True, use_y = True, use_z = True, invert_x = False, invert_y = False, invert_z = False, use_offset = False, head_tail = 0.0, owner_space='LOCAL', target_space='LOCAL', influence = 1.0):
    cl = pose_bone.constraints.new('COPY_LOCATION')
    cl.name = name
    cl.target = target_object
    cl.subtarget = target_bone.name
    cl.use_x = use_x
    cl.use_y = use_y
    cl.use_z = use_z
    cl.invert_x = invert_x
    cl.invert_y = invert_y
    cl.invert_z = invert_z
    cl.use_offset = use_offset
    cl.head_tail = head_tail
    cl.owner_space = owner_space
    cl.target_space = target_space
    cl.influence = influence

def create_mch_shoulder_bones_and_controls(edit_bones):
    # what we need:
    # IK-Collar (both sides)
    # X/Y axis of Hand tail
    # grab existing bones for coordinates and alignment
    bpy.ops.armature.select_all(action='DESELECT')
    bone_ik_collar_bone = edit_bones['IK-Collar.L']
    bone_ik_hand_bone = edit_bones['IK-Hand.L']
    bone_ik_ctrl_hand = edit_bones['CTRL-IK-Hand.L']

    # create new bones
    bone_mch_collar_bone = edit_bones.new('MCH-Collar.L')
    bone_mch_collar_bone.display_type = 'OCTAHEDRAL'
    assign_custom_color(bone_mch_collar_bone, bright_orange)
    bone_mch_collar_bone.select = True

    bone_mch_collar__damped_track = edit_bones.new('MCH-Collar-DampedTrack.L')
    bone_mch_collar__damped_track.display_type = 'STICK'
    assign_custom_color(bone_mch_collar__damped_track, bright_yellow)
    bone_mch_collar__damped_track.select = True

    bone_mch_collar__target = edit_bones.new('MCH-Collar-Target.L')
    bone_mch_collar__target.display_type = 'OCTAHEDRAL'
    assign_custom_color(bone_mch_collar__target, bright_orange)
    bone_mch_collar__target.select = True

    edit_bones.active = bone_mch_collar__target

    # move the MCH bone to match the current IK bone
    bone_mch_collar_bone.head = bone_ik_collar_bone.head
    bone_mch_collar_bone.tail = bone_ik_collar_bone.tail
    bone_mch_collar__damped_track.head = bone_ik_collar_bone.head
    bone_mch_collar__damped_track.tail = bone_ik_hand_bone.head
    bone_mch_collar__target.head = bone_mch_collar__damped_track.tail

    # align damped track bone to collar bone
    align_bone_to_source(bone_mch_collar__damped_track, bone_ik_collar_bone)

    bone_mch_collar__target.head = bone_mch_collar__damped_track.tail
    bone_mch_collar__target.tail = [bone_mch_collar__damped_track.tail[0], 0.1, bone_mch_collar__damped_track.tail[2]]

    bone_ik_collar_bone.parent = bone_mch_collar_bone

    # align target bone to ik control
    align_bone_to_source(bone_mch_collar__target, bone_ik_ctrl_hand)


def align_bone_to_source(source_bone, target_bone):
    target_dir = target_bone.tail - target_bone.head
    source_dir = source_bone.tail - source_bone.head

    rotation_q = source_dir.rotation_difference(target_dir)

    location, rotation, scale = source_bone.matrix.decompose()
    new_rotation = rotation_q @ rotation
    source_bone.matrix = Matrix.LocRotScale(location, new_rotation, scale)


def assign_custom_color(bone, color: dict[str, tuple[float, float, float]]):
    bone.color.palette = 'CUSTOM'
    bone.color.custom.normal = color['normal']
    bone.color.custom.select = color['select']
    bone.color.custom.active = color['active']


def create_spine_control_bones(edit_bones):
    # create spine control bones
    bone_ctrl_torso = edit_bones.new('CTRL-Torso')
    bone_ctrl_torso.use_deform = False
    bone_ctrl_torso.head = edit_bones['DEF-Hip'].head
    bone_ctrl_torso.tail = edit_bones['DEF-LowerAbdomen'].tail
    bone_ctrl_torso.color.palette = 'THEME09'
    bone_ctrl_torso.display_type = 'OCTAHEDRAL'

    bone_ctrl_hip = edit_bones.new('CTRL-Hip')
    bone_ctrl_hip.use_deform = False
    bone_ctrl_hip.head = edit_bones['DEF-Hip'].head
    bone_ctrl_hip.tail = edit_bones['DEF-Hip'].tail
    bone_ctrl_hip.color.palette = 'THEME09'
    bone_ctrl_hip.display_type = 'OCTAHEDRAL'
    bone_ctrl_hip.parent = bone_ctrl_torso

    bone_ctrl_chest = edit_bones.new('CTRL-Chest')
    bone_ctrl_chest.use_deform = False
    bone_ctrl_chest.head = edit_bones['DEF-Chest'].head
    bone_ctrl_chest.tail = edit_bones['DEF-Chest'].tail
    bone_ctrl_chest.color.palette = 'THEME09'
    bone_ctrl_chest.display_type = 'OCTAHEDRAL'
    bone_ctrl_chest.parent = bone_ctrl_torso


def create_ik_control_bones(edit_bones, chain: list[LiteralString], side ='.L', pole_name = 'Elbow', y_axis_position = 0.625, control_color = 'THEME01', pole_color = 'THEME09'):

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
    ik_control_bone.color.palette = control_color

    # create a pole target bone based off second bone in chain, but rotate 90 degrees and move on Y-axis
    ik_pole_bone_name = ctrl_prefix + '-' + prefix + '-Pole-' + pole_name + side
    ik_pole_position_bone = edit_bones[prefix + '-' + chain[1] + side]

    ik_pole_bone = edit_bones.new(ik_pole_bone_name)
    ik_pole_bone.head = ik_pole_position_bone.head
    ik_pole_bone.tail = ik_pole_position_bone.tail
    ik_pole_bone.bbone_x = ik_pole_position_bone.bbone_x * 2
    ik_pole_bone.bbone_z = ik_pole_position_bone.bbone_z * 2
    ik_pole_bone.color.palette = pole_color
    ik_pole_bone.tail = [ik_pole_bone.head[0], y_axis_position, ik_pole_bone.head[2]]
    ik_pole_bone.head[1] = y_axis_position - 0.125

    ik_pole_bone.parent = ik_control_bone


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
    ik_constraint.pole_angle = math.radians(pole_angle)
    ik_constraint.pole_subtarget = ik_pole_bone.name
    ik_constraint.chain_count = chain_length
    ik_constraint.enabled = True


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
