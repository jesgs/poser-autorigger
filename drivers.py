import bpy

def create_and_add_drivers():
    # fk/ik switching
    # driver needs to link the fk/ik property on the PROPERTIES bone to the
    # COPY_ROTATION constraint on the relevant bone
    # pose.bones["PROPERTIES"]["FK/IK Spine"]

    armature = bpy.context.object
    pose_bones = armature.pose.bones

    # full fk/ik chain
    arm_bone_chain = ['FK-Hand', 'FK-Forearm', 'FK-Shoulder', 'FK-Collar']
    for b in arm_bone_chain:
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
                    # if is_left:
                    #     target.data_path = 'pose.bones["PROPERTIES"]["arms_fkik"][0]'  # Custom property path
                    # else:
                    #     target.data_path = 'pose.bones["PROPERTIES"]["arms_fkik"][1]'  # Custom property path

                    # Set driver expression
                    driver.expression = 'fkik_switch'
                    driver.use_self=False
