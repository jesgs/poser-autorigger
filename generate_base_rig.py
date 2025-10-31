from typing import LiteralString, Sequence, Literal
from bpy.types import BoneCollections
from .helpers import rename_all_bones, create_bone, move_bone_along_local_axis, align_bone_to_source
from .colorscheme import assign_custom_color, bright_red, bright_orange, bright_yellow, bright_blue, bright_green
from .create_base import *
from .create_eye_controls import create_eye_control_bones, setup_eye_tracking_constraints
from .footroll import *
import bpy



def setup_poser_figure(objects):
    # Before deselecting everything, apply scale/rotation
    # Poser's scale is 1/100 smaller than Blender, plus rotation is different as well
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'

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

            setup_collections(armature.data.collections)


            # fix some issues with bones coming from Poser
            edit_bones = armature.data.edit_bones

            fix_bones(edit_bones)
            create_root(edit_bones)
            create_lower_abdomen_bone(edit_bones)
            #create_pelvis_bones()
            rename_all_bones(edit_bones, 'DEF-')

            rigging_collection = armature.data.collections['Rigging']
            deform_collection = rigging_collection.children['Deform']
            deform_spine_collection = deform_collection.children['DEF Spine']

            for bone in ['DEF-Hip', 'DEF-LowerAbdomen', 'DEF-Abdomen', 'DEF-Chest', 'DEF-Neck', 'DEF-Head']:
                deform_spine_collection.assign(edit_bones.get(bone))


            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')

            create_spine_fkik_chains(edit_bones, armature.data.collections)
            create_arm_fkik_chains(edit_bones, armature.data.collections)
            create_leg_fkik_chains(edit_bones, armature.data.collections)
            create_finger_fkik_chains(edit_bones, armature.data.collections)
            create_ik_control_bones(edit_bones, ['Hand', 'Forearm', 'Shoulder',])
            create_ik_control_bones(edit_bones, ['Foot', 'Shin', 'Thigh',], '.L', 'Knee', -0.625)
            create_ik_control_bones(edit_bones, ['LowerAbdomen', 'Hip',], '', 'Hip')
            create_ik_control_bones(edit_bones, ['Chest', 'Abdomen', ], '', 'Chest')
            create_ik_control_bones(edit_bones, ['Head', 'Neck',], '', 'Head', 0.5)
            create_mch_shoulder_bones_and_controls(edit_bones, armature.data.collections)
            create_spine_control_bones(edit_bones)
            create_finger_control_bones(edit_bones)
            create_foot_roll_control_bones(edit_bones)
            create_eye_control_bones(edit_bones)

            misc_bone_creation_cleanup(edit_bones)

            properties_bone = create_properties_bone(edit_bones)
            root = armature.data.collections.get('Root')
            root.assign(properties_bone)
            root.assign(edit_bones['root'])

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
            add_ik_constraints(armature, 'CTRL-IK-Head', ['Head', 'Neck'], '', 'Head', 90)
            # fingers
            add_ik_constraints(armature, 'CTRL-IK-Thumb-Joint', ['Thumb_1'], '.L', None)
            add_ik_constraints(armature, 'CTRL-IK-Thumb', ['Thumb_3', 'Thumb_2'], '.L', None)
            add_ik_constraints(armature, 'CTRL-IK-Index', ['Index_3', 'Index_2', 'Index_1'], '.L', None)
            add_ik_constraints(armature, 'CTRL-IK-Mid', ['Mid_3', 'Mid_2', 'Mid_1'], '.L', None)
            add_ik_constraints(armature, 'CTRL-IK-Ring', ['Ring_3', 'Ring_2', 'Ring_1'], '.L', None)
            add_ik_constraints(armature, 'CTRL-IK-Pinky', ['Pinky_3', 'Pinky_2', 'Pinky_1'], '.L', None)
            setup_collar_constraints(armature)
            setup_foot_roll_constraints(armature)
            setup_eye_tracking_constraints(armature)

            bpy.ops.object.editmode_toggle()
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.symmetrize(direction="POSITIVE_X")
            bpy.ops.object.posemode_toggle()
            # bpy.ops.object.select_all(action='DESELECT')

    bpy.context.scene.transform_orientation_slots[0].type = 'GLOBAL'
    bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'


def setup_collections(collections: BoneCollections):
    # collections = armature.data.collections
    all_collections = [
        'Body',
        'Spine IK',
        'Spine FK',
        'Legs IK',
        'Legs FK',
        'Arms IK',
        'Arms FK',
        'Fingers IK',
        'Fingers FK',
        'MCH',
        'DEF'
    ]
    root_collection = collections.new('Root')
    root_collection.is_visible = False

    all_collections['Body'] = body_collection = collections.new('Body')
    spine_collection = collections.new('Spine', parent=body_collection)
    collections.new('Spine IK', parent=spine_collection)
    collections.new('Spine FK', parent=spine_collection)

    legs_collection = collections.new('Legs', parent=body_collection)
    collections.new('Legs IK', parent=legs_collection)
    collections.new('Legs FK', parent=legs_collection)

    arms_collection = collections.new('Arms', parent=body_collection)
    collections.new('Arms IK', parent=arms_collection)
    collections.new('Arms FK', parent=arms_collection)

    fingers_collection = collections.new('Fingers', parent=body_collection)
    collections.new('Fingers IK', parent=fingers_collection)
    collections.new('Fingers FK', parent=fingers_collection)

    rigging_collection = collections.new('Rigging')
    deform_collection = collections.new('DEF', parent=rigging_collection)
    collections.new('MCH', parent=rigging_collection)


def create_finger_control_bones(edit_bones: ArmatureEditBones):
    # eventually, we'll want to "DRY" this out, but this will do for now
    # finger/thumb curl bones
    # these are the bones to use for naming and positioning
    ctrl_bones = ['Thumb_1', 'Index_1', 'Mid_1', 'Ring_1', 'Pinky_1']
    fk_control_parent = edit_bones['FK-Hand.L']
    ik_control_parent = edit_bones['IK-Hand.L'] # eventually, we'll need a separate parent for the IK controls
    bpy.ops.armature.select_all(action='DESELECT')
    for bone in ctrl_bones:
        name = bone.replace('_1', '')
        fk_finger_bone = edit_bones['FK-' + bone + '.L']
        ik_finger_bone = edit_bones['IK-' + name + '_3.L']

        fk_ctrl_bone = create_bone(
            edit_bones=edit_bones,
            name='CTRL-FK-' + name + '.L',
            head=fk_finger_bone.head,
            tail=fk_finger_bone.tail,
            length=0.025,
            bbone_size=fk_finger_bone.bbone_x * 3,
            palette='THEME09',
            parent=fk_control_parent
        )
        ik_ctrl_bone = create_bone(
            edit_bones=edit_bones,
            name='CTRL-IK-' + name + '.L',
            head=ik_finger_bone.head,
            tail=ik_finger_bone.tail,
            length=0.025,
            bbone_size=fk_finger_bone.bbone_x * 3,
            palette='THEME09',
            parent=ik_control_parent
        )

        move_bone_along_local_axis(fk_ctrl_bone, -0.025)
        move_bone_along_local_axis(ik_ctrl_bone, 0.025)
        ik_ctrl_bone.head = ik_finger_bone.tail # we want the heads and tails to align
        ik_ctrl_bone.length = 0.025 # make sure length stays the same, though

    # need to do the same thing for thumb_1, because IKs are a bit different here
    thumb_bone = edit_bones['IK-Thumb_1.L']
    ik_thumb_bone = create_bone(
        edit_bones=edit_bones,
        name='CTRL-IK-Thumb-Joint.L',
        head=thumb_bone.tail,
        tail=thumb_bone.head,
        length=0.025,
        bbone_size=0.002,
        palette='THEME09'
    )
    align_bone_to_source(ik_thumb_bone, thumb_bone)


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
    assign_custom_color(edit_bones['CTRL-IK-Pole-Head'], bright_blue)


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


def create_mch_shoulder_bones_and_controls(edit_bones, collections:BoneCollections):
    # what we need:
    # IK-Collar (both sides)
    # X/Y axis of Hand tail
    # grab existing bones for coordinates and alignment
    bpy.ops.armature.select_all(action='DESELECT')
    rigging_collection = collections.get('Rigging')
    mch_collection = rigging_collection.children['MCH']
    mch_shoulder_collection = collections.new('MCH Shoulder')
    mch_shoulder_collection.parent=mch_collection

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


def create_spine_control_bones(edit_bones: ArmatureEditBones):
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


def create_ik_control_bones(edit_bones: ArmatureEditBones, chain: list[LiteralString], side ='.L', pole_name = 'Elbow', y_axis_position = 0.625,
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
        head=[ik_pole_position_bone.tail[0], y_axis_position - 0.125, ik_pole_position_bone.tail[2]],
        tail=[ik_pole_position_bone.tail[0], y_axis_position, ik_pole_position_bone.tail[2]],
        bbone_size=ik_pole_position_bone.bbone_x * 2,
        parent=ik_control_bone,
        palette=pole_color,
    )


def create_leg_fkik_chains(edit_bones, collections: BoneCollections):
    body_collection = collections.get('Body')
    legs_collection = body_collection.children.get('Legs')
    legs_ik_collection = legs_collection.children.get('Legs IK')
    legs_fk_collection = legs_collection.children.get('Legs FK')

    # leg chains
    leg_fkik_bone_chain = [
        'Buttock',
        'Thigh',
        'Shin',
        'Foot',
        'Toe',
    ]

    ik_chain = create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'IK-Hip', 'IK', '.L', 'THEME01', 0.004)
    fk_chain = create_fkik_chains(edit_bones, leg_fkik_bone_chain, 'FK-Hip', 'FK', '.L', 'THEME03', 0.002)

    for ik_bone in ik_chain:
        legs_ik_collection.assign(ik_bone)

    for fk_bone in fk_chain:
        legs_fk_collection.assign(fk_bone)


def create_arm_fkik_chains(edit_bones, collections: BoneCollections):
    body_collection = collections.get('Body')
    arms_collection = body_collection.children.get('Arms')
    arms_ik_collection = arms_collection.children.get('Arms IK')
    arms_fk_collection = arms_collection.children.get('Arms FK')

    # arm chains
    arm_fkik_bone_chain = [
        'Collar',
        'Shoulder',
        'Forearm',
        'Hand',
    ]
    ik_chain = create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'IK-Chest', 'IK', '.L', 'THEME01', 0.004)
    fk_chain = create_fkik_chains(edit_bones, arm_fkik_bone_chain, 'FK-Chest', 'FK', '.L', 'THEME03', 0.002)

    for ik_bone in ik_chain:
        arms_ik_collection.assign(ik_bone)

    for fk_bone in fk_chain:
        arms_fk_collection.assign(fk_bone)


def create_spine_fkik_chains(edit_bones, collections: BoneCollections):
    body_collection = collections.get('Body')
    spine_collection = body_collection.children.get('Spine')
    spine_ik_collection = spine_collection.children.get('Spine IK')
    spine_fk_collection = spine_collection.children.get('Spine FK')

    # handle all fk/ik chains
    spine_fkik_bone_chain = [
        'Hip',
        'LowerAbdomen',
        'Abdomen',
        'Chest',
        'Neck',
        'Head'
    ]
    ik_chain = create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'IK', '', 'THEME09', 0.004)
    fk_chain = create_fkik_chains(edit_bones, spine_fkik_bone_chain, 'root', 'FK', '', 'THEME04', 0.002)

    for ik_bone in ik_chain:
        spine_ik_collection.assign(ik_bone)

    for fk_bone in fk_chain:
        spine_fk_collection.assign(fk_bone)


def create_finger_fkik_chains(edit_bones, collections: BoneCollections):
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

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004, True)
    create_fkik_chains(edit_bones, index_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004, True)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004, True)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004, True)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'IK-Hand.L', 'IK', '.L', 'THEME01', 0.004, True)

    create_fkik_chains(edit_bones, thumb_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, index_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, mid_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, ring_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)
    create_fkik_chains(edit_bones, pinky_fkik_chain, 'FK-Hand.L', 'FK', '.L', 'THEME03', 0.002)

    # adjust position of middle joints in IK finger change
    for bone in edit_bones:
        if bone.name in ['IK-Thumb_2.L', 'IK-Index_2.L', 'IK-Mid_2.L', 'IK-Ring_2.L', 'IK-Pinky_2.L']:
            if bone.name == 'IK-Thumb_2.L':
                head_y_axis = bone.head[1]
                tail_y_axis = bone.tail[1]
                tail_z_axis = bone.tail[2]
                bone.head[1] = head_y_axis - 0.005
                bone.tail[1] = tail_y_axis - 0.005
                bone.tail[2] = tail_z_axis + 0.005
            else:
                head_z_axis = bone.head[2]
                tail_z_axis = bone.tail[2]
                bone.head[2] = head_z_axis + 0.005
                bone.tail[2] = tail_z_axis + 0.005


def fix_bones(edit_bones: ArmatureEditBones):
    # head and neck bone are off-center, let's fix
    edit_bones['Head'].head.x = 0  # this should also move the tail of the neck bone since they're connected

    # let's also align tail of chest bone with head of neck bone
    # move the z and y axi, but we need to find the center
    chest_tail_y = edit_bones['Chest'].tail.y
    chest_tail_z = edit_bones['Chest'].tail.z
    neck_head_y = edit_bones['Neck'].head.y
    neck_head_z = edit_bones['Neck'].head.z
    center_y = (neck_head_y + chest_tail_y) / 2
    center_z = (neck_head_z + chest_tail_z) / 2

    edit_bones['Neck'].head.y = center_y
    edit_bones['Neck'].head.z = center_z
    edit_bones['Chest'].tail.y = center_y
    edit_bones['Chest'].tail.z = center_z

    # fix eyes and toe bones as well
    eye_y = edit_bones['Left_Eye'].tail.y
    edit_bones['Left_Eye'].tail.y = eye_y - -0.1
    edit_bones['Right_Eye'].tail.y = eye_y - -0.1

    toe_y = edit_bones['Left_Toe'].tail.y
    edit_bones['Left_Toe'].tail.y = toe_y - -0.1
    edit_bones['Right_Toe'].tail.y = toe_y - -0.1


def create_fkik_chains(edit_bones: ArmatureEditBones, bone_chains:list[str], parent:str = '', prefix:str = 'IK', suffix:str ='.L',
                       palette:Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"] = 'THEME01',
                       bone_size:float = 0.002, use_connect:bool = False) -> list[EditBone]:
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

        connect_bone = use_connect and 0 != i
        deform_bone_name = fkik_chain_item.replace(prefix, 'DEF')
        fkik_bone = create_bone(
            edit_bones=edit_bones,
            name=fkik_chain_item,
            parent=fkik_bone_parent,
            palette=palette,
            head=edit_bones[deform_bone_name].head,
            tail=edit_bones[deform_bone_name].tail,
            bbone_size=bone_size,
            use_connect=connect_bone,
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

