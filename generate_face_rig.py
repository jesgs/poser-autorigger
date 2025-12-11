from typing import Literal, LiteralString
from bpy.types import BoneCollection, Object
import bpy

def setup_face_rig(armature: Object):
    # bpy.context.active_bone.bbone_segments = 15
    # bpy.context.active_bone.bbone_mapping_mode = 'CURVED'
    # bpy.context.active_bone.bbone_handle_type_start = 'TANGENT'

    # define bone chains
    # set to bendy bones (10 segments)
    # set each bendy bone to Curved, Tangent
    # create control bones
    bpy.ops.object.editmode_toggle()
    edit_bones = armature.data.edit_bones
    bone_chains = ['Lip_Upper', 'Lip_Lower', 'LipRing', 'Laughline', 'Nose', 'Cheek', 'UpperCheek', 'OuterCheek', 'EyeRing', 'Eyebrow', 'Temple', 'Jaw']

    for chain in bone_chains:
        for bone in edit_bones:
            if 'DEF' in bone.name:
                continue

            if '_TMP_' in bone.name:
                continue

            if chain in bone.name:
                print(bone.name)

    bpy.ops.object.editmode_toggle()

setup_face_rig(bpy.context.active_object)
