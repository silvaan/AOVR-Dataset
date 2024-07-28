import random
import bpy


class Containers:
    def __init__(self, types, spacing):
        self.collection_name = 'Containers'
        self.types = types
        self.space_between_containers = spacing
        
    def clear_collection(self):
        # Remove all objects from the collection
        containers_collection = bpy.data.collections.get(self.collection_name)
        if containers_collection:
            for obj in containers_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(containers_collection)
            
    def copy_object_with_children(self, obj, new_location):
        # Create a copy of the object
        new_obj = obj.copy()

        # Add a suffix to the copied object's name
        new_obj.name = obj.name + "_Container"
        new_obj.hide_render = False

        # Link the new object to the active scene and place it in a collection
        containers_collection = bpy.data.collections.get(self.collection_name)
        if not containers_collection:
            containers_collection = bpy.data.collections.new(self.collection_name)
            bpy.context.scene.collection.children.link(containers_collection)
        containers_collection.objects.link(new_obj)

        # Copy all the child objects and link them to the new parent
        for child in obj.children:
            new_child = child.copy()
            new_child.parent = new_obj
            containers_collection.objects.link(new_child)

            if not 'Ground' in new_child.name:
                new_child.hide_render = False

        # Compute the transformation matrix for the new parent object
        old_matrix = obj.matrix_world
        new_matrix = new_obj.matrix_world
        delta_matrix = new_matrix @ old_matrix.inverted()

        # Set the new location for the object and its children
        new_obj.location = (new_location[0], 0, obj.location.z)
        for child in new_obj.children:
            child.matrix_world = delta_matrix @ child.matrix_world
            child.name = child.name.split('.')[0]
        
        new_obj.name = new_obj.name.split('.')[0]
        # print(f'{new_obj.name} generated')

        return new_obj
    
    def set_floor_ground(self):
        # Set the ground of the floor if is not already set
        if bpy.data.objects.get('Floor_Ground'):
            return
        floor_ground_base = bpy.data.objects.get('Floor_Ground')
        floor_ground = floor_ground_base.copy()
        floor_ground.location = (0, -12, floor_ground_base.location.z)
    
    def generate(self, grounds):
        self.set_floor_ground()
        # Select two containers randomly
        container_1, container_2 = random.sample(self.types, k=2)
        container_1 = bpy.data.objects.get(container_1)
        container_2 = bpy.data.objects.get(container_2)

        # Create copies of the selected containers and place them side by side with a margin
        location = (0, 0, 0)
        copy_1 = self.copy_object_with_children(container_1, location)
        copy_2 = self.copy_object_with_children(container_2, location)
        width_1, length_1, _ = copy_1.dimensions
        width_2, length_2, _ = copy_2.dimensions
        center_distance = (width_1 + width_2) / 2 + self.space_between_containers
        x_1 = -center_distance + width_1 / 2
        x_2 = center_distance - width_2 / 2
        copy_1.location = (x_1, 0, copy_1.location.z)
        copy_2.location = (x_2, 0, copy_2.location.z)

        grounds = self.get_grounds(grounds)
        return grounds
        
    def get_grounds(self, grounds):
        object_grounds = [{
            **grounds['Floor_Ground'],
            'object': bpy.data.objects.get('Floor_Ground'),
        }]

        # Get all the grounds in the scene
        containers_collection = bpy.data.collections.get(self.collection_name)

        # Get the ground of each object
        for obj in containers_collection.all_objects:
            if '_Ground' in obj.name:
                object_grounds.append({
                    **grounds[obj.name],
                    'object': obj,
                })

        return object_grounds



# containers = Containers()
# containers.clear_collection()
# containers.generate()
# print(containers.get_grounds())
