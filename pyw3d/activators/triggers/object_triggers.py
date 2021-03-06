# Copyright (C) 2016 William Hicks
#
# This file is part of Writing3D.
#
# Writing3D is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""A Blender implementation of triggers based on the state of objects in
virtual space
"""
import logging
LOGGER = logging.getLogger("pyw3d")
from pyw3d.errors import EBKAC
from .triggers import BlenderTrigger
try:
    import bpy
    from _bpy import ops as ops_module
    BPY_OPS_CALL = ops_module.call
except ImportError:
    LOGGER.debug(
        "Module bpy not found. Loading "
        "pyw3d.activators.triggers.object_triggers as standalone")


class BlenderObjectPositionTrigger(BlenderTrigger):
    """Activator based on position of objects in virtual space

    :param str objects_string: A string containing either a
    Python-formatted list of names of Blender objects or a single valid
    group name (e.g. "['object_myobj1', 'object_myobj2']" or "group_mygrp"
    :param bool detect_any: True if trigger should activate when any
    specified object passes the box's boundaries as specified, False if
    trigger should activate when ALL specified objects have done so
    """

    def create_enabled_sensor(self):
        """Add a sensor to fire continuously while trigger is enabled"""
        self.select_base_object()
        BPY_OPS_CALL(
            "logic.sensor_add", None,
            {
                'type': 'PROPERTY', 'object': self.name,
                'name': 'enabled_sensor'
            }
        )
        self.base_object.game.sensors[-1].name = "enabled_sensor"
        enable_sensor = self.base_object.game.sensors["enabled_sensor"]
        enable_sensor.use_pulse_true_level = True
        enable_sensor.tick_skip = 0
        enable_sensor.property = "enabled"
        enable_sensor.value = "True"
        self.enable_sensor = enable_sensor

        return enable_sensor

    def create_detection_controller(self):
        """Add a controller for detecting specified event"""

        BPY_OPS_CALL(
            "logic.controller_add", None,
            {
                'type': 'PYTHON', 'object': self.name,
                'name': 'detect'
            }
        )
        controller = self.base_object.game.controllers["detect"]
        controller.mode = "MODULE"
        controller.module = "{}.detect_event".format(self.name)
        self.detect_controller = controller
        return controller

    def link_detection_bricks(self):
        """Link necessary logic bricks for event detection

        :raises EBKAC: if controller or sensor does not exist"""
        try:
            self.detect_controller.link(sensor=self.enable_sensor)
        except AttributeError:
            raise EBKAC(
                "Detection sensor and controller must be created before they "
                "can be linked")
        return self.detect_controller

    def generate_detection_logic(self):
        """Add a function to Python control script to detect user position
        """

        detection_logic = [
            "\ndef detect_event(cont):",
            "    scene = bge.logic.getCurrentScene()",
            "    own = cont.owner",
            "    corners = {}".format(
                zip(self["box"]["corner1"], self["box"]["corner2"])),
            "    all_objects = {}".format(self.objects_string),
            "    all_objects = ["
            "scene.objects[object_name] for object_name in all_objects]",
            "    in_region = {}".format(not self.detect_any),
            "    for object_ in all_objects:",
            "        position = object_.position",
            "        in_region = (in_region {}".format(
                ("or", "and")[not self.detect_any]),
            "            {}(position[i] < min(corners[i]) or".format(
                ("", "not ")[self.box["direction"] == "Inside"]),
            "               position[i] > max(corners[i])))",
            "    if (",
            "            in_region and own['enabled'] and",
            "            own['status'] == 'Stop'):",
            "        own['status'] = 'Start'"
        ]
        detection_logic = "\n".join(detection_logic)
        return detection_logic

    def create_blender_objects(self):
        super(BlenderObjectPositionTrigger, self).create_blender_objects()
        self.create_enabled_sensor()
        self.create_detection_controller()

    def link_logic_bricks(self):
        super(BlenderObjectPositionTrigger, self).link_logic_bricks()
        self.link_detection_bricks()

    def __init__(
            self, name, actions, box, objects_string, duration=0,
            enable_immediately=True, remain_enabled=True, detect_any=True):
        super(BlenderObjectPositionTrigger, self).__init__(
            name, actions, enable_imediately=enable_immediately,
            remain_enabled=remain_enabled)
        self.box = box
        self.objects_string = objects_string
        self.detect_any = detect_any
