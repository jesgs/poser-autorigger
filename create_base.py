from bpy.types import ArmatureEditBones, EditBone


def create_properties_bone(edit_bones: ArmatureEditBones) -> EditBone:
    # create new properties bone
    properties_bone = edit_bones.new('PROPERTIES')
    properties_bone.parent = edit_bones['root']
    properties_bone.head = [0, 0, 0]
    properties_bone.tail = [0, 0.25, 0]
    properties_bone.use_deform = False

    properties_bone.color.palette = 'THEME03'
    properties_bone.bbone_z = 0.01
    properties_bone.bbone_x = 0.01

    return properties_bone


def create_root(edit_bones: ArmatureEditBones) -> EditBone:
    # rename Body to root, disconnect, and drop to 0
    edit_bones['Hip'].use_connect = False
    edit_bones['Body'].use_deform = False
    edit_bones['Body'].head = [0, 0, 0]
    edit_bones['Body'].tail = [0, 0.5, 0]
    edit_bones['Body'].color.palette = 'THEME09'
    edit_bones['Body'].name = 'root'

    return edit_bones['root']
