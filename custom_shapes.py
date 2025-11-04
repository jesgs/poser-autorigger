from bpy.types import PoseBone, Object
from pathlib import Path
import bpy

def assign_all_custom_shapes(armature):
    pose_bones = armature.pose.bones
    shape_collection_name = 'WGTS-' + armature.name
    shape_collection = bpy.data.collections[shape_collection_name]
    override_bones = {
        'CTRL-IK-Thumb.L' : 'IK-Thumb_3.L',
        'CTRL-IK-Index.L' : 'IK-Index_3.L',
        'CTRL-IK-Mid.L' : 'IK-Mid_3.L',
        'CTRL-IK-Ring.L' : 'IK-Ring_3.L',
        'CTRL-IK-Pinky.L' : 'IK-Pinky_3.L',
        'CTRL-IK-Thumb.R' : 'IK-Thumb_3.R',
        'CTRL-IK-Index.R' : 'IK-Index_3.R',
        'CTRL-IK-Mid.R' : 'IK-Mid_3.R',
        'CTRL-IK-Ring.R' : 'IK-Ring_3.R',
        'CTRL-IK-Pinky.R' : 'IK-Pinky_3.R',
    }

    for bone in pose_bones:
        if 'DEF' in bone.name or 'MCH' in bone.name:
            continue

        shape_name = 'WGT-' + bone.name
        found = shape_collection.all_objects.find(shape_name)

        if found != -1:
            override_bone = None
            if bone.name in override_bones:
                override_bone = pose_bones[override_bones[bone.name]]

            assign_custom_shape(bone, shape_collection.all_objects[found], override_bone)


def assign_custom_shape(pose_bone: PoseBone, shape: Object|None, override_transform: PoseBone = None):
    pose_bone.custom_shape = shape
    pose_bone.custom_shape_transform = override_transform


def import_custom_shapes(collection_name:str):
    blend_path = Path(__file__).with_name("WGTS.blend")
    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
        data_to.collections = ["WGTS"]

    # Link into the scene tree so it’s visible
    coll = bpy.data.collections.get("WGTS")
    coll.name = "WGTS-" + collection_name # rename collection to match armature
    if coll and coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    coll.hide_viewport = True
