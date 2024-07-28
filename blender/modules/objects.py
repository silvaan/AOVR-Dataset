import bpy
import random
from math import radians
from mathutils import Vector
from modules.utils import *


class Objects():
    def __init__(
            self,
            types,
            ground,
            num_objects,
            materials,
            sizes,
            angle_range,
            margin
        ):
        self.collection_name = 'Objects'
        self.types = types
        self.base_objects = [bpy.data.objects.get(obj_name) for obj_name in types]
        self.ground = ground
        self.container = ground.name.split('_Ground')[0].lower()
        self.num_objects = num_objects
        self.materials = materials
        self.sizes = sizes
        self.angle_range = angle_range
        self.margin = margin


    def randomize_object_transform(self, obj):
        # Randomize orientation
        random_rotation_z = radians(random.uniform(self.angle_range[0], self.angle_range[1]))
        obj.rotation_euler = (0, 0, random_rotation_z)

        # Randomize scale
        size = random.choice(list(self.sizes.keys()))
        scale = self.sizes[size]
        obj.scale = (scale, scale, scale)
        
        # Assign random material
        random_material = random.choice(self.materials)
        # get color and texture from material name
        mat_type, mat_color = random_material.name.split('_')

        if len(obj.material_slots) == 0:
            bpy.ops.object.material_slot_add({"object": obj})
        obj.material_slots[0].material = random_material

        info = {
            'material': mat_type,
            'color': mat_color,
            'size': size,
        }

        return info


    # def randomize_object_transform(self, obj):
    #     # Randomize orientation
    #     random_rotation_z = radians(random.uniform(self.angle_range[0], self.angle_range[1]))
    #     obj.rotation_euler = (0, 0, random_rotation_z)

    #     # Randomize scale
    #     random_scale = random.uniform(self.scale_range[0], self.scale_range[1])
    #     random_scale = random.choice(self.scale_range)
    #     obj.scale = (random_scale, random_scale, random_scale)
        
    #     # Assign random material
    #     random_material = random.choice(self.materials)

    #     if len(obj.material_slots) == 0:
    #         bpy.ops.object.material_slot_add({"object": obj})

    #     obj.material_slots[0].material = random_material


    def random_point_above_ground(self, obj, height=0.0):
        bpy.context.view_layer.update()
        
        # Calculate ground's bounds
        ground_bounds = [self.ground.matrix_world @ v.co for v in self.ground.data.vertices]
        min_x = min(v.x for v in ground_bounds)
        max_x = max(v.x for v in ground_bounds)
        min_y = min(v.y for v in ground_bounds)
        max_y = max(v.y for v in ground_bounds)
        max_z = max(v.z for v in ground_bounds)

        # Calculate object's radius
        obj_radius = max((obj.dimensions.x, obj.dimensions.y)) / 2

        # Adjust the min and max ranges to account for the object's radius
        min_x += obj_radius
        max_x -= obj_radius
        min_y += obj_radius
        max_y -= obj_radius
        
        # Randomly select a point within the ground's bounds
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        # z = self.ground.location.z + height
        z = max_z + height

        return x, y, z


    def generate_random_object(self):
        obj_type = random.choice(self.types)
        obj = bpy.data.objects.get(obj_type)

        # Create a copy of the object
        obj_copy = obj.copy()
        obj_copy.data = obj.data.copy()
        obj_copy.animation_data_clear()
        obj_copy.hide_render = False

        # Add the copied object to the current collection
        bpy.context.collection.objects.link(obj_copy)
        
        # Randomize object
        info = self.randomize_object_transform(obj_copy)
        info['shape'] = obj_type.lower()

        # Generate random location above the ground object
        obj_copy.location = self.random_point_above_ground(obj_copy)
        info['location'] = [obj_copy.location.x, obj_copy.location.y, obj_copy.location.z]

        return obj_copy, info
    

    def do_objects_collide(self, obj1, obj2, margin=0.0):
        # Update the scene to get accurate bounding box data
        bpy.context.view_layer.update()

        # Get the world coordinates of the bounding boxes
        bounding_box1_world = [obj1.matrix_world @ Vector(v[:]) for v in obj1.bound_box]
        bounding_box2_world = [obj2.matrix_world @ Vector(v[:]) for v in obj2.bound_box]

        # Find the minimum and maximum coordinates for each bounding box
        bbox1_min = [min([v[i] for v in bounding_box1_world]) for i in range(3)]
        bbox1_max = [max([v[i] for v in bounding_box1_world]) for i in range(3)]
        bbox2_min = [min([v[i] for v in bounding_box2_world]) for i in range(3)]
        bbox2_max = [max([v[i] for v in bounding_box2_world]) for i in range(3)]

        # Add a small margin to the bounding boxes
        bbox1_min = [v - margin for v in bbox1_min]
        bbox1_max = [v + margin for v in bbox1_max]
        bbox2_min = [v - margin for v in bbox2_min]
        bbox2_max = [v + margin for v in bbox2_max]

        # Check for intersection
        for i in range(3):
            if bbox1_min[i] > bbox2_max[i] or bbox1_max[i] < bbox2_min[i]:
                return False

        return True


    def generate(self, max_tries=5):
        self.generated_objects = []
        self.infos = []
        
        # Get or create the "Generated" collection
        generated_collection = bpy.data.collections.get(self.collection_name)
        if generated_collection is None:
            generated_collection = bpy.data.collections.new(self.collection_name)
            bpy.context.scene.collection.children.link(generated_collection)
        
        for i in range(self.num_objects):
            tries = 0
            while tries < max_tries:
                tries += 1
                # print(f'Generating object {i+1}/{self.num_objects} (try {tries}/{max_tries})')
                obj_copy, info = self.generate_random_object()
                
                collision = False
                for gen_obj in self.generated_objects:
                    if self.do_objects_collide(gen_obj, obj_copy, self.margin):
                        collision = True
                        break

                if collision:
                    bpy.data.objects.remove(obj_copy)
                    continue
                else:
                    self.generated_objects.append(obj_copy)
                    info['container'] = self.container
                    info['bounding_box'] = camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, obj_copy)
                    self.infos.append(info)
                    bpy.context.collection.objects.unlink(obj_copy)
                    generated_collection.objects.link(obj_copy)
                    break


# floor_generator = Objects(
#     num_objects=32,
#     types=['Cube', 'Sphere', 'Cylinder'],
#     self.groundect='Plane',
# )

# floor_generator.generate()