from typing import LiteralString
import math
import bpy


def add_damped_track_constraint(pose_bone, target_bone, target_object, head_tail=0.0, track_axis='TRACK_X'):
    dt = pose_bone.constraints.new('DAMPED_TRACK')
    dt.subtarget = target_bone
    dt.target = target_object
    dt.head_tail = head_tail
    dt.track_axis = track_axis

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



def add_ik_constraints(ik_target_name, chain: list[LiteralString], side:str = '.L', pole_name:str = None, pole_angle:float = 180):
    armature = bpy.context.object
    bones = armature.pose.bones

    chain_length = len(chain)
    ik_target_bone = bones.get(ik_target_name + side)
    ik_constraint_bone_name = 'IK-' + chain[0] + side

    ik_constraint = bones[ik_constraint_bone_name].constraints.new('IK')
    ik_constraint.target = armature
    ik_constraint.subtarget = ik_target_bone.name
    ik_constraint.chain_count = chain_length

    if pole_name is not None:
        ik_pole_bone = bones.get('CTRL-IK-Pole-' + pole_name + side)
        ik_constraint.pole_target = armature
        ik_constraint.pole_angle = math.radians(pole_angle)
        ik_constraint.pole_subtarget = ik_pole_bone.name

    ik_constraint.enabled = True


def add_copy_constraints(prefix_target, prefix_constraint):
    armature = bpy.context.object
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
