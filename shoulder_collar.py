from .constraints import add_damped_track_constraint, add_copylocation_constraint
from .colorscheme import assign_custom_color, bright_orange, bright_yellow
from .helpers import align_bone_to_source
import bpy

def setup_collar_constraints():
    # todo: refactor to use new method for adding damped track constraints
    armature = bpy.context.object
    bones = bpy.context.object.pose.bones

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


def create_mch_shoulder_bones_and_controls():
    edit_bones = bpy.context.object.data.edit_bones
    collections = bpy.context.object.data.collections
    all_collections = bpy.context.object.data.collections_all
    mch_collection = all_collections.get('MCH')
    mch_shoulder_collection = collections.new('MCH Shoulder', parent=mch_collection)

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
    mch_shoulder_collection.assign(bone_mch_collar_bone)

    bone_mch_collar__damped_track = edit_bones.new('MCH-Collar-DampedTrack.L')
    bone_mch_collar__damped_track.display_type = 'STICK'
    assign_custom_color(bone_mch_collar__damped_track, bright_yellow)
    bone_mch_collar__damped_track.select = True
    mch_shoulder_collection.assign(bone_mch_collar__damped_track)

    bone_mch_collar__target = edit_bones.new('MCH-Collar-Target.L')
    bone_mch_collar__target.display_type = 'OCTAHEDRAL'
    assign_custom_color(bone_mch_collar__target, bright_orange)
    bone_mch_collar__target.select = True
    mch_shoulder_collection.assign(bone_mch_collar__target)

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
