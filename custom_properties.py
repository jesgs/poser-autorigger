from bpy.props import FloatVectorProperty
from bpy.types import PoseBone
import bpy
def create_custom_properties():
    properties_bone = bpy.context.object.pose.bones['PROPERTIES']
    # ik/fk switching
    properties_bone['head_tracking'] = False
    properties_bone['arms_fkik'] = [1.0, 1.0]
    properties_bone['legs_fkik'] = [1.0, 1.0]
    properties_bone['spine_fkik'] = [1.0, 1.0]
    properties_bone['fingers_fkik_l'] = [1.0, 1.0, 1.0, 1.0, 1.0]
    properties_bone['fingers_fkik_r'] = [1.0, 1.0, 1.0, 1.0, 1.0]

    properties_bone.property_overridable_library_set(f'["head_tracking"]', True)
    properties_bone.id_properties_ui('head_tracking')

    properties_bone.property_overridable_library_set(f'["arms_fkik"]', True)
    arms_fkik_ui = properties_bone.id_properties_ui('arms_fkik')
    arms_fkik_ui.update(
        min=0.0,
        max=1.0,
    )
    properties_bone.property_overridable_library_set(f'["legs_fkik"]', True)
    legs_fkik_ui = properties_bone.id_properties_ui('legs_fkik')
    legs_fkik_ui.update(
        min=0.0,
        max=1.0,
    )
    properties_bone.property_overridable_library_set(f'["spine_fkik"]', True)
    spine_fkik_ui = properties_bone.id_properties_ui('spine_fkik')
    spine_fkik_ui.update(
        min=0.0,
        max=1.0,
    )
    properties_bone.property_overridable_library_set(f'["fingers_fkik_l"]', True)
    fingers_fkik_l_ui = properties_bone.id_properties_ui('fingers_fkik_l')
    fingers_fkik_l_ui.update(
        min=0.0,
        max=1.0,
    )
    properties_bone.property_overridable_library_set(f'["fingers_fkik_r"]', True)
    fingers_fkik_r_ui = properties_bone.id_properties_ui('fingers_fkik_r')
    fingers_fkik_r_ui.update(
        min=0.0,
        max=1.0,
    )
