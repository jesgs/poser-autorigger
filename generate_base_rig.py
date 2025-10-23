import bpy

def rename_all_bones(armature, prefix = ''):
    bones = armature.data.bones

    for bone in bones:
        new_name = rename_bone(bone.name)
        if new_name != "":
            armature.data.bones[bone.name].name = prefix + new_name


def rename_bone(name):
    if "root" in name:
        return ""

    if name.find('Left_') != -1:
        return name[5:] + '.L'

    if name.find('Right_') != -1:
        return name[6:] + '.R'

    if name.find('l', 0, 1) != -1:
        name = name[1:] + '.L'
    elif name.find('r', 0, 1) != -1:
        name = name[1:] + '.R'

    return name


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

            obj = bpy.context.object
            # fix some issues with bones coming from Poser
            edit_bones = obj.data.edit_bones
            # head and neck bone are off-center, let's fix
            create_root(edit_bones)
            create_lower_abdomen_bone(edit_bones)
            properties_bone = create_properties_bone(edit_bones)

            arm_ik_bone_chains = [
                'Hand',
                'Forearm',
                'Shoulder',
                'Collar'
            ]

            leg_ik_bone_chains = [
                ''
            ]

            # change bone-roll to Global +Z to prevent issues later on
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')

            # separate_armatures(figure_name, obj)
            # strip_trailing_digits_from_bones(obj)
            rename_all_bones(obj, 'DEF-')

            bpy.ops.object.editmode_toggle()  # we're done here

        bpy.ops.object.select_all(action='DESELECT')


def create_properties_bone(edit_bones):
    # create new properties bone
    properties_bone = edit_bones.new('PROPERTIES')
    properties_bone.parent = edit_bones['root']
    properties_bone.head[0] = 0
    properties_bone.head[1] = 0
    properties_bone.head[2] = 0
    properties_bone.tail[0] = 0
    properties_bone.tail[1] = 0.25
    properties_bone.tail[2] = 0
    properties_bone.use_deform = False

    properties_bone.color.palette = 'THEME03'
    properties_bone.bbone_z = 0.01
    properties_bone.bbone_x = 0.01

    return properties_bone


def create_lower_abdomen_bone(edit_bones):
    # create new LowerAbdomen bone, move to between hip and abdomen, make hip its parent,
    # then parent abdomen to new bone
    bone_lower_abdomen = edit_bones.new('LowerAbdomen')

    bone_lower_abdomen.head[0] = edit_bones['Hip'].tail[0]
    bone_lower_abdomen.head[1] = edit_bones['Hip'].tail[1]
    bone_lower_abdomen.head[2] = edit_bones['Hip'].tail[2]
    bone_lower_abdomen.tail[0] = edit_bones['Abdomen'].head[0]
    bone_lower_abdomen.tail[1] = edit_bones['Abdomen'].head[1]
    bone_lower_abdomen.tail[2] = edit_bones['Abdomen'].head[2]

    bone_lower_abdomen.parent = edit_bones['Hip']
    edit_bones['Abdomen'].parent = bone_lower_abdomen
    bone_lower_abdomen.bbone_z = 0.001
    bone_lower_abdomen.bbone_x = 0.001


def create_root(edit_bones):
    edit_bones['Head'].head[0] = 0  # this should also move the tail of the neck bone since they're connected

    # rename Body to root, disconnect, and drop to 0
    edit_bones['Hip'].use_connect = False
    edit_bones['Body'].use_deform = False
    edit_bones['Body'].head[0] = 0
    edit_bones['Body'].head[1] = 0
    edit_bones['Body'].head[2] = 0
    edit_bones['Body'].tail[0] = 0
    edit_bones['Body'].tail[1] = 0.5
    edit_bones['Body'].tail[2] = 0
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

class RigPoserArmature_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Poser"
    bl_category = "Rig Poser"

    def draw(self, context):
        layout = self.layout
        op_row = layout.row(align=True)
        op_row.scale_y = 1.5

        op_row.operator("poser.generate_base_rig", icon="POSE_HLT")

classes = [RigPoserArmature_Panel, GenerateBaseRig_Operator]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()