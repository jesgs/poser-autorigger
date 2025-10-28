from typing import LiteralString, Sequence, Literal
from mathutils import Matrix, Vector
from bpy.types import ArmatureEditBones, EditBone
import mathutils
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
            create_eye_control_bones(edit_bones)

            misc_bone_creation_cleanup(edit_bones)

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
            setup_foot_roll_constraints(armature)
            setup_eye_tracking_constraints(armature)

            bpy.ops.object.editmode_toggle()
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.symmetrize(direction="POSITIVE_X")
            bpy.ops.object.posemode_toggle()
            # bpy.ops.object.select_all(action='DESELECT')


def misc_bone_creation_cleanup(edit_bones: ArmatureEditBones):
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


def setup_eye_tracking_constraints(armature):
    pose_bones = armature.pose.bones
    # assign copy constraint from MCH-Eye.L to DEF-Eye.L
    bone_mch_eye_left = pose_bones['MCH-Eye.L']
    bone_eye_left = pose_bones['DEF-Eye.L']
    bone_ctrl_eye_target_left = pose_bones['CTRL-Eye_Target.L']

    add_copyrotation_constraint(
        pose_bone=bone_eye_left,
        target_bone=bone_mch_eye_left,
        target_object=armature,
        owner_space='WORLD',
        target_space='WORLD',
    )

    add_damped_track_constraint(
        pose_bone=bone_mch_eye_left,
        target_bone=bone_ctrl_eye_target_left.name,
        target_object=armature,
        track_axis='TRACK_Y'
    )


def add_damped_track_constraint(pose_bone, target_bone, target_object, head_tail=0.0, track_axis='TRACK_X'):
    dt = pose_bone.constraints.new('DAMPED_TRACK')
    dt.subtarget = target_bone
    dt.target = target_object
    dt.head_tail = head_tail
    dt.track_axis = track_axis


def create_eye_control_bones(edit_bones):
    # create main eye track and two eye track bones
    bone_eye_left = edit_bones['DEF-Eye.L']

    create_bone(
        edit_bones=edit_bones,
        name='MCH-Eye.L',
        head=bone_eye_left.head,
        tail=[bone_eye_left.tail[0], bone_eye_left.tail[1] + 0.005, bone_eye_left.tail[2]],
        use_deform=False,
        parent=bone_eye_left.parent,
        bbone_size=bone_eye_left.bbone_z * 2
    )

    bone_ctrl_eye_target = create_bone(
        edit_bones=edit_bones,
        name='CTRL-Eye_Target',
        head=[0, -0.25, bone_eye_left.head[2]],
        tail=[0, -0.27, bone_eye_left.head[2]],
        use_deform=False,
        parent=None,
        bbone_size=bone_eye_left.bbone_x,
        custom_color=bright_blue
    )

    create_bone(
        edit_bones=edit_bones,
        name='CTRL-Eye_Target.L',
        parent=bone_ctrl_eye_target,
        head=[bone_eye_left.head[0], -0.25, bone_eye_left.head[2]],
        tail=[bone_eye_left.head[0], -0.27, bone_eye_left.head[2]],
        bbone_size=bone_eye_left.bbone_x,
        custom_color=bright_yellow
    )


def setup_foot_roll_constraints(armature):
    pose_bones = armature.pose.bones

    bone_mch_roll_toe = pose_bones['MCH-Roll-Toe.L']
    bone_mch_roll_foot = pose_bones['MCH-Roll-Foot.L']
    bone_ctrl_foot_roll = pose_bones['CTRL-Foot-Roll.L']
    bone_ctrl_foot_roll.lock_rotation = [False, True, True]

    # add_transformation_constraint()
    add_copylocation_constraint(
        pose_bone=bone_mch_roll_foot,
        target_bone=bone_mch_roll_toe,
        target_object=armature,
        head_tail=1.0,
        owner_space='WORLD',
        target_space='WORLD',
    )

    add_transformation_constraint(
        pose_bone=bone_mch_roll_toe,
        target_bone=bone_ctrl_foot_roll,
        target_object=armature,
        target_space='LOCAL',
        owner_space='LOCAL',
        map_from='ROTATION',
        from_max_x_rot=181.0,
        from_min_x_rot=90.0,
        map_to='ROTATION',
        to_min_x_rot=0.0,
        to_max_x_rot=113.0
    )

    add_transformation_constraint(
        pose_bone=bone_mch_roll_foot,
        target_bone=bone_ctrl_foot_roll,
        target_object=armature,
        target_space='LOCAL',
        owner_space='LOCAL',
        map_from='ROTATION',
        from_min_x_rot=0.0,
        from_max_x_rot=90.0,
        map_to='ROTATION',
        to_min_x_rot=0.0,
        to_max_x_rot=90.0
    )

    add_limitrotation_constraint(
        pose_bone=bone_ctrl_foot_roll,
        use_limit_x=True,
        min_x=0.0,
        max_x=math.radians(179.0)
    )


def create_bone(edit_bones: ArmatureEditBones, name:str, bbone_size:float=0.001, head:Vector|Sequence[float]=0.0, tail:Vector|Sequence[float]=0.0, length:float=None, parent:EditBone=None, display_type:Literal["ARMATURE_DEFINED", "OCTAHEDRAL", "STICK", "BBONE", "ENVELOPE", "WIRE"]="ARMATURE_DEFINED", use_deform=False, use_connect=False,
                palette:Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"]='CUSTOM', custom_color: dict[str, tuple[float, float, float]] = None) -> EditBone:
    new_bone = edit_bones.new(name)
    new_bone.head = head
    new_bone.tail = tail
    new_bone.parent = parent
    new_bone.use_deform = use_deform
    new_bone.use_connect = use_connect
    new_bone.display_type = display_type
    new_bone.bbone_x = new_bone.bbone_z = bbone_size

    if length is not None:
        new_bone.length = length

    if palette == 'CUSTOM' and custom_color is not None:
        assign_custom_color(new_bone, custom_color)
    else:
        new_bone.color.palette = palette

    return new_bone


def create_foot_roll_control_bones(edit_bones):
    # create and position bones for foot roll mechanism
    # Bones (Symmetrized):
    # MCH-Roll-Toe.L (parented to MCH-Foot-Rollback.L)
    # MCH-Roll-Foot.L (parented to MCH-Foot-Rollback.L)
    # Roll-Foot.L (parented to CTRL-IK-Foot.L)
    # MCH-Foot-Rollback.L (parented to Roll-Foot.L)
    # CTRL-Foot-Roll.L (parented to CTRL-IK-Foot.L

    bone_ik_toe = edit_bones['IK-Toe.L']
    bone_ik_foot = edit_bones['IK-Foot.L']
    bone_ctrl_ik_foot = edit_bones['CTRL-IK-Foot.L']

    create_bone(
        edit_bones=edit_bones,
        name='CTRL-Foot-Roll.L',
        custom_color=bright_blue,
        display_type='OCTAHEDRAL',
        parent=bone_ctrl_ik_foot,
        head=[bone_ik_foot.head[0], bone_ik_foot.head[1] + 0.05, bone_ik_foot.head[2]],
        tail=[bone_ik_foot.head[0], bone_ik_foot.head[1] + 0.075, bone_ik_foot.head[2]]
    )

    bone_roll_foot = create_bone(
        edit_bones=edit_bones,
        name='Roll-Foot.L',
        custom_color=bright_blue,
        display_type='OCTAHEDRAL',
        parent=bone_ctrl_ik_foot,
        head=bone_ik_foot.head,
        tail=[bone_ik_foot.head[0], -0.05 , bone_ik_foot.head[2]],
    )

    bone_mch_foot_rollback = create_bone(
        edit_bones=edit_bones,
        name='MCH-Foot-Rollback.L',
        custom_color=bright_blue,
        display_type='OCTAHEDRAL',
        parent=bone_roll_foot,
        head=[bone_ik_foot.head[0], bone_ik_foot.head[1], 0.025],
        tail=[bone_ik_foot.head[0], bone_ik_foot.head[1] - 0.025, 0.025]
    )

    bone_mch_roll_toe = create_bone(
        edit_bones=edit_bones,
        name='MCH-Roll-Toe.L',
        custom_color=bright_blue,
        display_type='OCTAHEDRAL',
        parent=bone_mch_foot_rollback,
        head=[bone_ik_toe.tail[0], bone_ik_toe.tail[1], 0],
        tail = bone_ik_toe.head
    )

    bone_mch_roll_foot = create_bone(
        edit_bones=edit_bones,
        name='MCH-Roll-Foot.L',
        custom_color=bright_blue,
        display_type='OCTAHEDRAL',
        parent=bone_mch_foot_rollback,
        head=bone_ik_foot.tail,
        tail= bone_ik_foot.head
    )

    # parent existing bones to new ones
    bone_ik_toe.parent = bone_mch_roll_toe
    bone_ik_foot.parent = bone_mch_roll_foot


def setup_collar_constraints(armature):
    # todo: refactor to use new method for adding damped track constraints
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


def add_limitrotation_constraint(pose_bone, euler_order='AUTO',
                                 max_x=0.0, max_y=0.0, max_z=0.0,
                                 min_x=0.0, min_y=0.0, min_z=0.0,
                                 use_limit_x=False, use_limit_y=False, use_limit_z=False,
                                 owner_space='LOCAL', target_space='LOCAL', influence = 1.0
                                 ):
    lr = pose_bone.constraints.new('LIMIT_ROTATION')
    lr.euler_order = euler_order
    lr.max_x = max_x
    lr.max_y = max_y
    lr.max_z = max_z
    lr.min_x = min_x
    lr.min_y = min_y
    lr.min_z = min_z
    lr.use_limit_x = use_limit_x
    lr.use_limit_y = use_limit_y
    lr.use_limit_z = use_limit_z
    lr.owner_space = owner_space
    lr.target_space = target_space
    lr.influence = influence

def add_copyrotation_constraint(pose_bone, target_bone, target_object,
                                name = 'Copy Rotation',
                                use_x = True, use_y = True, use_z = True,
                                invert_x = False, invert_y = False, invert_z = False,
                                mix_mode = 'REPLACE', use_offset = False, euler_order='AUTO',
                                owner_space='LOCAL', target_space='LOCAL',
                                influence = 1.0):
    cr = pose_bone.constraints.new('COPY_ROTATION')
    cr.name = name
    cr.target = target_object
    cr.subtarget = target_bone.name
    cr.use_x = use_x
    cr.use_y = use_y
    cr.use_z = use_z
    cr.invert_x = invert_x
    cr.invert_y = invert_y
    cr.invert_z = invert_z
    cr.mix_mode = mix_mode
    cr.use_offset = use_offset
    cr.euler_order = euler_order
    cr.owner_space = owner_space
    cr.target_space = target_space
    cr.influence = influence


def add_transformation_constraint(pose_bone, target_bone, target_object,
                                  from_max_x=0.0, from_max_x_rot=0.0, from_max_x_scale=0.0,
                                  from_max_y=0.0, from_max_y_rot=0.0, from_max_y_scale=0.0,
                                  from_max_z=0.0, from_max_z_rot=0.0, from_max_z_scale=0.0,
                                  from_min_x=0.0, from_min_x_rot=0.0, from_min_x_scale=0.0,
                                  from_min_y=0.0, from_min_y_rot=0.0, from_min_y_scale=0.0,
                                  from_min_z=0.0, from_min_z_rot=0.0, from_min_z_scale=0.0,
                                  from_rotation_mode='AUTO', map_from='LOCATION', map_to='LOCATION',
                                  map_to_x_from='X', map_to_y_from='Y', map_to_z_from='Z',
                                  mix_mode='ADD', mix_mode_rot='ADD', mix_mode_scale='REPLACE',
                                  to_max_x=0.0, to_max_x_rot=0.0, to_max_x_scale=0.0,
                                  to_max_y=0.0, to_max_y_rot=0.0, to_max_y_scale=0.0,
                                  to_max_z=0.0, to_max_z_rot=0.0, to_max_z_scale=0.0,
                                  to_min_x=0.0, to_min_x_rot=0.0, to_min_x_scale=0.0,
                                  to_min_y=0.0, to_min_y_rot=0.0, to_min_y_scale=0.0,
                                  to_min_z=0.0, to_min_z_rot=0.0, to_min_z_scale=0.0,
                                  to_euler_order = 'AUTO', name = 'Transformation',
                                  target_space = 'WORLD', owner_space = 'WORLD'):

    transform = pose_bone.constraints.new('TRANSFORM')
    transform.name = name
    transform.target = target_object
    transform.subtarget = target_bone.name
    transform.target_space = target_space
    transform.owner_space = owner_space
    transform.to_euler_order = to_euler_order
    transform.from_max_x = from_max_x
    transform.from_max_y = from_max_y
    transform.from_max_z = from_max_z
    transform.from_max_x_rot = math.radians(from_max_x_rot)
    transform.from_max_y_rot = math.radians(from_max_y_rot)
    transform.from_max_z_rot = math.radians(from_max_z_rot)
    transform.from_max_x_scale = from_max_x_scale
    transform.from_max_y_scale = from_max_y_scale
    transform.from_max_z_scale = from_max_z_scale
    transform.from_min_x = from_min_x
    transform.from_min_y = from_min_y
    transform.from_min_z = from_min_z
    transform.from_min_x_rot = math.radians(from_min_x_rot)
    transform.from_min_y_rot = math.radians(from_min_y_rot)
    transform.from_min_z_rot = math.radians(from_min_z_rot)
    transform.from_min_x_scale = from_min_x_scale
    transform.from_min_y_scale = from_min_y_scale
    transform.from_min_z_scale = from_min_z_scale
    transform.from_rotation_mode = from_rotation_mode
    transform.map_to = map_to
    transform.map_to_x_from = map_to_x_from
    transform.map_to_y_from = map_to_y_from
    transform.map_to_z_from = map_to_z_from
    transform.map_from = map_from
    transform.mix_mode = mix_mode
    transform.mix_mode_rot = mix_mode_rot
    transform.mix_mode_scale = mix_mode_scale
    transform.to_max_x = to_max_x
    transform.to_max_y = to_max_y
    transform.to_max_z = to_max_z
    transform.to_max_x_rot = math.radians(to_max_x_rot)
    transform.to_max_y_rot = math.radians(to_max_y_rot)
    transform.to_max_z_rot = math.radians(to_max_z_rot)
    transform.to_max_x_scale = to_max_x_scale
    transform.to_max_y_scale = to_max_y_scale
    transform.to_max_z_scale = to_max_z_scale
    transform.to_min_x = to_min_x
    transform.to_min_y = to_min_y
    transform.to_min_z = to_min_z
    transform.to_min_x_rot = math.radians(to_min_x_rot)
    transform.to_min_y_rot = math.radians(to_min_y_rot)
    transform.to_min_z_rot = math.radians(to_min_z_rot)
    transform.to_min_x_scale = to_min_x_scale
    transform.to_min_y_scale = to_min_y_scale
    transform.to_min_z_scale = to_min_z_scale


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


def create_ik_control_bones(edit_bones, chain: list[LiteralString], side ='.L', pole_name = 'Elbow', y_axis_position = 0.625,
                            control_color: Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"] = 'THEME01',
                            pole_color: Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"] = 'THEME09'):

    ctrl_prefix = 'CTRL'
    prefix = 'IK'
    ik_control_bone_name = ctrl_prefix + '-' + prefix + '-' + chain[0] + side
    first_bone = edit_bones[prefix + '-' + chain[0] + side]
    ik_control_bone = create_bone(
        edit_bones=edit_bones,
        name=ik_control_bone_name,
        head=first_bone.head,
        tail=first_bone.tail,
        bbone_size=first_bone.bbone_x * 2,
        palette=control_color,
        length=first_bone.length - 0.01
    )

    # create a pole target bone based off second bone in chain, but rotate 90 degrees and move on Y-axis
    ik_pole_bone_name = ctrl_prefix + '-' + prefix + '-Pole-' + pole_name + side
    ik_pole_position_bone = edit_bones[prefix + '-' + chain[1] + side]
    create_bone(
        edit_bones=edit_bones,
        name=ik_pole_bone_name,
        head=[ik_pole_position_bone.head[0], y_axis_position - 0.125, ik_pole_position_bone.head[2]],
        tail=[ik_pole_position_bone.head[0], y_axis_position, ik_pole_position_bone.head[2]],
        bbone_size=ik_pole_position_bone.bbone_x * 2,
        parent=ik_control_bone,
        palette=pole_color,
    )



def add_ik_constraints(armature, ik_target_name, chain: list[LiteralString], side:str = '.L', pole_name:str ='Elbow', pole_angle:float = 180):
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
    create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'IK', '', 'THEME09', 0.004)
    create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'FK', '', 'THEME04', 0.002)


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


def create_fkik_chains(edit_bones: ArmatureEditBones, bone_chains:list[str], parent:str = '', prefix:str = 'IK', suffix:str ='.L',
                       palette:Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"] = 'THEME01',
                       bone_size:float = 0.002) -> list[EditBone]:
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
        # parenting
        if 0 == i:
            fkik_bone_parent = edit_bones[parent]
        else:
            fkik_bone_parent = edit_bones[fkik_chains[i - 1]]

        deform_bone_name = fkik_chain_item.replace(prefix, 'DEF')
        fkik_bone = create_bone(
            edit_bones=edit_bones,
            name=fkik_chain_item,
            parent=fkik_bone_parent,
            palette=palette,
            head=edit_bones[deform_bone_name].head,
            tail=edit_bones[deform_bone_name].tail,
            bbone_size=bone_size,
        )

        completed_fkik_chains.append(fkik_bone)

    return completed_fkik_chains


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
