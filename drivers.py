import bpy
# todo - deduplicate code
def create_limb_fkik_switch_drivers(chain:list[str], prop_name:str):
    # fk/ik switching
    # driver needs to link the fk/ik property on the PROPERTIES bone to the
    # COPY_ROTATION constraint on the relevant bone
    # pose.bones["PROPERTIES"]["FK/IK Spine"]

    armature = bpy.context.object
    pose_bones = armature.pose.bones

    # full fk/ik chain
    for b in chain:
        for bone in pose_bones:
            if b not in bone.name:
                continue

            is_left = bone.name.find('.L') != -1

            pose_bone_constraints  = bone.constraints
            for constraint in pose_bone_constraints:
                if 'IK' in constraint.name and constraint.type == 'COPY_TRANSFORMS':
                    fcurve = constraint.driver_add("influence")
                    driver = fcurve.driver
                    driver.type = 'SCRIPTED'
                    driver.use_self=True
                    var = driver.variables.new()
                    var.name = 'fkik_switch'
                    var.type = 'SINGLE_PROP'
                    target = var.targets[0]
                    target.id_type = 'OBJECT'
                    target.id = armature
                    if is_left:
                        target.data_path = 'pose.bones["PROPERTIES"]["' + prop_name + '"][0]'  # Custom property path
                    else:
                        target.data_path = 'pose.bones["PROPERTIES"]["' + prop_name + '"][1]'  # Custom property path

                    # Set driver expression
                    driver.expression = 'fkik_switch'
                    driver.use_self=False


def create_spine_fkik_switch_drivers(chain:list[str], prop_name:str):
    armature = bpy.context.object
    pose_bones = armature.pose.bones

    # full fk/ik chain
    for b in chain:
        for bone in pose_bones:
            if b not in bone.name:
                continue

            pose_bone_constraints  = bone.constraints
            for constraint in pose_bone_constraints:
                if 'IK' in constraint.name and constraint.type == 'COPY_TRANSFORMS':
                    fcurve = constraint.driver_add("influence")
                    driver = fcurve.driver
                    driver.type = 'SCRIPTED'
                    driver.use_self=True
                    var = driver.variables.new()
                    var.name = 'fkik_switch'
                    var.type = 'SINGLE_PROP'
                    target = var.targets[0]
                    target.id_type = 'OBJECT'
                    target.id = armature
                    target.data_path = 'pose.bones["PROPERTIES"]["' + prop_name + '"]'  # Custom property path
                    # Set driver expression
                    driver.expression = 'fkik_switch'
                    driver.use_self=False


def create_finger_fkik_switch_drivers(prop_name:str):
    armature = bpy.context.object
    pose_bones = armature.pose.bones

    # todo - figure out a better way of handling finger chains
    thumb_fkik_chain = [
        'FK-Thumb_1',
        'FK-Thumb_2',
        'FK-Thumb_3',
    ]
    index_fkik_chain = [
        'FK-Index_1',
        'FK-Index_2',
        'FK-Index_3',
    ]
    mid_fkik_chain = [
        'FK-Mid_1',
        'FK-Mid_2',
        'FK-Mid_3',
    ]
    ring_fkik_chain = [
        'FK-Ring_1',
        'FK-Ring_2',
        'FK-Ring_3',
    ]
    pinky_fkik_chain = [
        'FK-Pinky_1',
        'FK-Pinky_2',
        'FK-Pinky_3',
    ]

    chain = thumb_fkik_chain + index_fkik_chain + mid_fkik_chain + ring_fkik_chain + pinky_fkik_chain
    chain_name = ['Thumb', 'Index', 'Mid', 'Ring', 'Pinky']
    # full fk/ik chain
    for b in chain:
        for bone in pose_bones:
            if b not in bone.name:
                continue


            is_left = '.L' in bone.name

            if is_left:
                prop_name_loop = prop_name + '_l'
            else:
                prop_name_loop = prop_name + '_r'

            for i,finger in enumerate(chain_name):
                if finger not in bone.name:
                    continue

                pose_bone_constraints  = bone.constraints
                for constraint in pose_bone_constraints:
                    if 'IK' in constraint.name and constraint.type == 'COPY_TRANSFORMS':
                        fcurve = constraint.driver_add("influence")
                        driver = fcurve.driver
                        driver.type = 'SCRIPTED'
                        driver.use_self=True
                        var = driver.variables.new()
                        var.name = 'fkik_switch'
                        var.type = 'SINGLE_PROP'
                        target = var.targets[0]
                        target.id_type = 'OBJECT'
                        target.id = armature
                        target.data_path = 'pose.bones["PROPERTIES"]["' + prop_name_loop + '"][' + str(i) + ']'  # Custom property path
                        # Set driver expression
                        driver.expression = 'fkik_switch'
                        driver.use_self=False
