import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import math
from .errors import BadW3DXML, InvalidArgument, EBKAC
from .xml_tools import find_xml_text, text2bool, text2tuple, bool2text
from .features import W3DFeature
from .actions import W3DAction, ObjectAction, GroupAction, TimelineAction,\
    SoundAction, EventTriggerAction, MoveVRAction, W3DResetAction
from .placement import W3DPlacement
from .validators import OptionValidator, IsNumeric, ListValidator, IsInteger,\
    ValidPyString, IsBoolean, FeatureValidator, DictValidator,\
    TextValidator, ValidFile, ValidFontFile, ReferenceValidator
from .names import generate_blender_object_name,\
    generate_blender_material_name, generate_blender_sound_name,\
    generate_light_object_name, generate_paction_name, generate_group_name, \
    generate_blender_particle_name, generate_blender_curve_name
from .metaclasses import SubRegisteredClass
from .activators import BlenderClickTrigger
from .sounds import audio_playback_object
import logging
LOGGER = logging.getLogger("pyw3d")
try:
    import bpy
    import mathutils
    from _bpy import ops as ops_module
    BPY_OPS_CALL = ops_module.call
except ImportError:
    LOGGER.debug(
        "Module bpy not found. Loading pyw3d.objects as standalone")

def line_count(string):
    """Count lines in string"""
    return string.count('\n') + 1


def add_text_object(name, text):
    font_curve = bpy.data.curves.new(
        type="FONT", name=generate_blender_curve_name(name)
    )
    new_object = bpy.data.objects.new(name, font_curve)
    new_object.data.body = text
    new_object.data.space_line = 0.6
    return new_object


def apply_euler_rotation(blender_object, x, y, z):
    """Apply euler rotation (radians) to object"""
    blender_object.data.transform(
        mathutils.Euler((x, y, z), 'XYZ').to_matrix().to_4x4()
    )


def find_object_midpoint(blender_object):
    midpoint = mathutils.Vector((0, 0, 0))
    for vert in blender_object.data.vertices:
        midpoint += vert.co
    return (
        midpoint / len(blender_object.data.vertices)
    )


def set_object_center(blender_object, center_vec):
    blender_object.data.transform(
        mathutils.Matrix.Translation(
            blender_object.matrix_world.translation - center_vec
        )
    )


def duplicate_object(original):
    """Duplicate given object"""
    new = original.copy()
    if original.data is not None:
        new.data = original.data.copy()
    new.animation_data_clear()
    bpy.context.scene.objects.link(new)
    return new


def generate_object_from_model(filename):
    """Generate Blender object from model file"""
    try:
        return duplicate_object(
            generate_object_from_model._models[filename]
        )
    except AttributeError:
        generate_object_from_model._models = {}
    except KeyError:
        BPY_OPS_CALL(
            "import_scene.obj", None,
            {'filepath': filename}
        )
        model_pieces = bpy.context.selected_objects
        for piece in model_pieces:
            bpy.context.scene.objects.active = piece
            BPY_OPS_CALL(
                "object.convert", None,
                {'target': 'MESH', 'keep_original': False}
            )
        BPY_OPS_CALL("object.join", None, {})
        new_model = bpy.context.object
        generate_object_from_model._models[filename] = new_model

        return new_model

    return generate_object_from_model(filename)


def _alpha_prep(slot, material):
    """Allow transparency in texture slot"""
    slot.use_map_alpha = True
    material.use_transparency = True
    material.transparency_method = "Z_TRANSPARENCY"
    material.alpha = 0


def generate_material_from_image(filename, double_sided=True):
    """Generate Blender material from image for texturing"""
    try:
        return generate_material_from_image._materials[
            filename][double_sided]
    except AttributeError:
        generate_material_from_image._materials = {}
    except KeyError:
        material_name = bpy.path.display_name_from_filepath(filename)

        material_single = bpy.data.materials.new(
            name="{}{}".format(material_name, 0)
        )
        material_double = bpy.data.materials.new(
            name="{}{}".format(material_name, 1)
        )
        texture_slot_single = material_single.texture_slots.add()
        texture_slot_double = material_double.texture_slots.add()

        texture_name = '_'.join(
            (os.path.splitext(os.path.basename(filename))[0],
             "image_texture")
        )
        image_texture = bpy.data.textures.new(name=texture_name, type="IMAGE")
        image_texture.image = bpy.data.images.load(filename)
        # NOTE: The above already raises a sensible RuntimeError if file is not
        # found
        image_texture.image.use_alpha = True
        _alpha_prep(texture_slot_single, material_single)
        _alpha_prep(texture_slot_double, material_double)

        texture_slot_single.texture = image_texture
        texture_slot_double.texture = image_texture
        texture_slot_single.texture_coords = 'UV'
        texture_slot_double.texture_coords = 'UV'

        # material.alpha = 0.0
        # material.specular_alpha = 0.0
        # texture_slot.use_map_alpha
        # material.use_transparency = True
        material_single.game_settings.use_backface_culling = True
        material_double.game_settings.use_backface_culling = False

        generate_material_from_image._materials[filename] = (
            material_single, material_double
        )

    return generate_material_from_image(
        filename, double_sided=double_sided)

