import bpy
from typing import Sequence, Literal
from mathutils import Vector, Matrix
from bpy.types import ArmatureEditBones, EditBone, BoneCollection
from .colorscheme import assign_custom_color


def rename_all_bones(prefix = ''):
    edit_bones = bpy.context.object.data.edit_bones
    for bone in edit_bones:
        new_name = rename_bone(bone.name, prefix)
        if new_name != "":
            edit_bones[bone.name].name = new_name


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


def create_bone(edit_bones: ArmatureEditBones, name:str, bbone_size:float=0.001, head:Vector|Sequence[float]=0.0, tail:Vector|Sequence[float]=0.0, length:float=None, parent:EditBone=None, display_type:Literal["ARMATURE_DEFINED", "OCTAHEDRAL", "STICK", "BBONE", "ENVELOPE", "WIRE"]="ARMATURE_DEFINED", use_deform=False, use_connect=False,
                palette:Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"]='CUSTOM',
                custom_color: dict[str, tuple[float, float, float]] = None,
                collection:BoneCollection = None) -> EditBone:
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

    if collection is not None:
        collection.assign(new_bone)

    return new_bone

def align_bone_to_source(source_bone:EditBone, target_bone:EditBone):
    target_dir = target_bone.tail - target_bone.head
    source_dir = source_bone.tail - source_bone.head

    rotation_q = source_dir.rotation_difference(target_dir)

    location, rotation, scale = source_bone.matrix.decompose()
    new_rotation = rotation_q @ rotation
    source_bone.matrix = Matrix.LocRotScale(location, new_rotation, scale)


def move_bone_along_local_axis(bone: EditBone, distance:float):
    normal = (bone.tail - bone.head).normalized()

    # Calculate the new head and tail positions
    translation_vector = normal * distance

    bone.head += translation_vector
    bone.tail += translation_vector


def create_fkik_chains(bone_chains:list[str], parent:str = '', prefix:str = 'IK', suffix:str ='.L',
                       palette:Literal["DEFAULT", "THEME01", "THEME02", "THEME03", "THEME04", "THEME05", "THEME06", "THEME07", "THEME08", "THEME09", "THEME10", "THEME11", "THEME12", "THEME13", "THEME14", "THEME15", "THEME16", "THEME17", "THEME18", "THEME19", "THEME20", "CUSTOM"] = 'THEME01',
                       bone_size:float = 0.002, use_connect:bool = False) -> list[EditBone]:
    edit_bones = bpy.context.object.data.edit_bones

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
