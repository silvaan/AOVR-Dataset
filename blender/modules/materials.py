import bpy


class Materials:
    def __init__(self, types, colors):
        self.types = types
        self.colors = colors
        self.materials = []

    def generate(self):
        for mat_type, mat_props in self.types.items():
            for color_name, color_value in self.colors.items():
                mat_name = f'{mat_type}_{color_name}'
                mat = bpy.data.materials.get(mat_name)

                if mat is None:
                    mat = bpy.data.materials.new(mat_name)
                    mat.use_nodes = True

                    bsdf_node = mat.node_tree.nodes['Principled BSDF']

                    bsdf_node.inputs['Specular'].default_value = mat_props['specular']
                    bsdf_node.inputs['Roughness'].default_value = mat_props['roughness']
                    bsdf_node.inputs['Transmission'].default_value = mat_props['transmission']
                    bsdf_node.inputs['Metallic'].default_value = mat_props['metallic']
                    bsdf_node.inputs['Base Color'].default_value = color_value

                self.materials.append(mat)
