#!/usr/bin/env blender
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

"""An example for performance profiling
"""

import os
import time
from random import randint
from math import pi, sin, cos
from pyw3d import project, objects, placement, export_to_blender

# First, create a W3DProject to hold everything else you'll create
my_project = project.W3DProject(
    call_directory=os.path.dirname(__file__),
    allow_movement=True)

shapes = objects.W3DShape.argument_validators['shape_type'].valid_options
lights = objects.W3DLight.argument_validators['light_type'].valid_options

theta_div = 10
phi_div = 10
radius = 10
for i in range(1, theta_div):
    for j in range(phi_div):
        theta = pi / theta_div * i
        phi = 2 * pi / phi_div * j

        my_object = objects.W3DObject(
            name="elem{}x{}".format(i, j),
            color=(randint(0, 255), randint(0, 255), randint(0, 255)),
            placement=placement.W3DPlacement(
                position=(
                    radius * sin(theta) * cos(phi),
                    radius * sin(theta) * sin(phi),
                    radius * cos(theta)
                ),
                rotation=placement.W3DRotation(
                    rotation_mode="LookAt",
                    rotation_vector=(0, 0, 0)
                )
            ),
            content=objects.W3DText(
                text="W3D"
            ),
        )

        my_project["objects"].append(my_object)

        my_object = objects.W3DObject(
            name="shape{}x{}".format(i, j),
            content=objects.W3DShape(
                shape_type=shapes[(i + j) % len(shapes)]
            ),
            placement=placement.W3DPlacement(
                rotation=placement.W3DRotation(
                    rotation_mode="LookAt",
                    rotation_vector=(0, 0, 0)
                ),
                position=(
                    (radius - 2) * sin(theta) * cos(phi),
                    (radius - 2) * sin(theta) * sin(phi),
                    (radius - 2) * cos(theta)
                ),
            ),
            visible=True,
        )
        my_project["objects"].append(my_object)

        my_object = objects.W3DObject(
            name="image{}x{}".format(i, j),
            content=objects.W3DImage(
                filename="obama.jpg"
            ),
            placement=placement.W3DPlacement(
                rotation=placement.W3DRotation(
                    rotation_mode="LookAt",
                    rotation_vector=(0, 0, 0)
                ),
                position=(
                    (radius - 3) * sin(theta) * cos(phi),
                    (radius - 3) * sin(theta) * sin(phi),
                    (radius - 3) * cos(theta)
                ),
            ),
            visible=True,
        )
        my_project["objects"].append(my_object)

theta_div = 10
phi_div = 10
radius = 10
for i in range(1, theta_div):
    for j in range(phi_div):

        my_object = objects.W3DObject(
            name="room{}x{}".format(i, j),
            content=objects.W3DModel(
                filename="models/bathroom2.obj"
            ),
            placement=placement.W3DPlacement(
                rotation=placement.W3DRotation(
                    rotation_mode="LookAt",
                    rotation_vector=(0, 0, 0)
                ),
                position=(
                    (radius + 5) * sin(theta) * cos(phi),
                    (radius + 5) * sin(theta) * sin(phi),
                    (radius + 5) * cos(theta)
                ),
            ),
            visible=True,
        )
        my_project["objects"].append(my_object)

        my_object = objects.W3DObject(
            name="light{}x{}".format(i, j),
            content=objects.W3DLight(
                light_type=lights[(i + j) % len(lights)]
            ),
            placement=placement.W3DPlacement(
                rotation=placement.W3DRotation(
                    rotation_mode="LookAt",
                    rotation_vector=(0, 0, 0)
                ),
                position=(
                    (radius - 2) * sin(theta) * cos(phi),
                    (radius - 2) * sin(theta) * sin(phi),
                    (radius - 2) * cos(theta)
                ),
            ),
            visible=True,
        )
        my_project["objects"].append(my_object)

my_project["profile"] = True
my_project["debug"] = True

start_time = time.time()
export_to_blender(
    my_project, filename="performance_sample.blend", display=False,
    fullscreen=True
)
print("Approximate wall time: {}".format(time.time() - start_time))
