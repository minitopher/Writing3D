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

from .objects_utility import *

LOGGER = logging.getLogger("pyw3d")
try:
    import bpy
    import mathutils
    from _bpy import ops as ops_module
    BPY_OPS_CALL = ops_module.call
except ImportError:
    LOGGER.debug(
        "Module bpy not found. Loading pyw3d.objects as standalone")
		
class W3DLink(W3DFeature):
    """Store data on a clickable link

    :param bool enabled: Is link enabled?
    :param bool remain_enabled: Should link remain enabled after activation?
    :param tuple enabled_color: RGB color when link is enabled
    :param tuple selected_color: RGB color when link is selected
    :param actions: Dictionary mapping number of clicks to W3DActions
        (negative for any click)
    :param int reset: Number of clicks after which to reset link (negative
        value to never reset)"""

    argument_validators = {
        "enabled": IsBoolean(),
        "remain_enabled": IsBoolean(),
        "enabled_color": ListValidator(
            IsInteger(min_value=0, max_value=255), required_length=3),
        "selected_color": ListValidator(
            IsInteger(min_value=0, max_value=255), required_length=3),
        "actions": DictValidator(
            IsInteger(), ListValidator(FeatureValidator(W3DAction)),
            help_string="Must be a dictionary mapping integers to lists of "
            "W3DActions"
        ),
        "reset": IsInteger()
    }

    default_arguments = {
        "enabled": True,
        "remain_enabled": True,
        "enabled_color": (0, 128, 255),
        "selected_color": (255, 0, 0),
        "reset": -1
    }

    def __init__(self, *args, **kwargs):
        super(W3DLink, self).__init__(*args, **kwargs)
        if "actions" not in self:
            self["actions"] = defaultdict(list)
        self.num_clicks = 0

    def toXML(self, object_root):
        """Store W3DLink as LinkRoot node within Object node

        :param :py:class:xml.etree.ElementTree.Element object_root
        """
        linkroot_node = ET.SubElement(object_root, "LinkRoot")
        link_node = ET.SubElement(linkroot_node, "Link")

        node = ET.SubElement(link_node, "Enabled")
        node.text = bool2text(self["enabled"])
        node = ET.SubElement(link_node, "RemainEnabled")
        node.text = bool2text(self["remain_enabled"])
        node = ET.SubElement(link_node, "EnabledColor")
        node.text = "{},{},{}".format(*self["enabled_color"])
        node = ET.SubElement(link_node, "SelectedColor")
        node.text = "{},{},{}".format(*self["selected_color"])

        for clicks, action_list in self["actions"].items():
            for current_action in action_list:
                actions_node = ET.SubElement(link_node, "Actions")
                current_action.toXML(actions_node)
                clicks_node = ET.SubElement(actions_node, "Clicks")
                if clicks < 0:
                    ET.SubElement(clicks_node, "Any")
                else:
                    ET.SubElement(
                        clicks_node,
                        "NumClicks",
                        attrib={
                            "num_clicks": str(clicks),
                            "reset": bool2text(self["reset"] == clicks)
                        }
                    )

        return linkroot_node

    @classmethod
    def fromXML(link_class, link_root):
        """Create W3DLink from LinkRoot node

        :param :py:class:xml.etree.ElementTree.Element link_root
        """
        link = link_class()
        link_node = link_root.find("Link")
        if link_node is None:
            raise BadW3DXML("LinkRoot element has no Link subelement")
        link["enabled"] = text2bool(find_xml_text(link_node, "Enabled"))
        link["remain_enabled"] = text2bool(
            find_xml_text(link_node, "RemainEnabled"))
        node = link_node.find("EnabledColor")
        if node is not None:
            link["enabled_color"] = text2tuple(node.text, evaluator=int)
        node = link_node.find("SelectedColor")
        if node is not None:
            link["selected_color"] = text2tuple(node.text, evaluator=int)
        for actions_node in link_node.findall("Actions"):
            num_clicks = -1
            clicks_node = actions_node.find("Clicks")
            if clicks_node is not None:
                num_clicks_node = clicks_node.find("NumClicks")
                if num_clicks_node is not None:
                    try:
                        num_clicks = int(
                            num_clicks_node.attrib["num_clicks"]
                        )
                    except (KeyError, ValueError):
                        raise BadW3DXML(
                            "num_clicks attribute not set to an integer in"
                            "NumClicks node"
                        )
                    try:
                        if text2bool(num_clicks_node.attrib["reset"]):
                            if (
                                    num_clicks < link["reset"] or
                                    link["reset"] == -1):
                                link["reset"] = num_clicks
                    except KeyError:
                        pass
            for child in actions_node:
                if child.tag != "Clicks":
                    link["actions"][num_clicks].append(
                        W3DAction.fromXML(child))

        return link

    def blend(self, object_name):
        """Create Blender object to implement W3DLink

        :param str object_name: The name of the object to which link is
        assigned"""
        self.activator = BlenderClickTrigger(
            object_name, self["actions"], object_name,
            enable_immediately=self["enabled"],
            remain_enabled=self["remain_enabled"],
            select_color=self["selected_color"],
            enable_color=self["enabled_color"],
            reset_clicks=self['reset']
        )
        self.activator.create_blender_objects()
        return self.activator.base_object

    def link_blender_logic(self):
        """Link BGE logic bricks for this W3DLink"""
        try:
            self.activator.link_logic_bricks()
        except AttributeError:
            raise EBKAC(
                "blend() must be called before link_blender_logic()")

    def write_blender_logic(self):
        """Write any necessary game engine logic for this W3DTimeline"""
        try:
            self.activator.write_python_logic()
        except AttributeError:
            raise EBKAC(
                "blend() must be called before write_blender_logic()")