import bpy
import os
import json


def clear_collection(name):
    collection = bpy.data.collections.get(name)
    if collection:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)


def load_config():
    with open(os.path.join(bpy.path.abspath("//"), 'config.json'), 'r') as stream:
        try:
            config = json.load(stream)
        except json.JSONDecodeError as exc:
            print(exc)
    return config


def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))


def camera_view_bounds_2d(scene, cam_ob, me_ob):
    """
    Returns camera space bounding box of mesh object.

    Negative 'z' value means the point is behind the camera.

    Takes shift-x/y, lens angle and sensor size into account
    as well as perspective/ortho projections.

    :arg scene: Scene to use for frame size.
    :type scene: :class:`bpy.types.Scene`
    :arg obj: Camera object.
    :type obj: :class:`bpy.types.Object`
    :arg me: Untransformed Mesh.
    :type me: :class:`bpy.types.Mesh´
    :return: a Box object (call its to_tuple() method to get x, y, width and height)
    :rtype: :class:`Box`
    """
    mat = cam_ob.matrix_world.normalized().inverted()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh_eval = me_ob.evaluated_get(depsgraph)
    me = mesh_eval.to_mesh()
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp = camera.type != 'ORTHO'

    lx = []
    ly = []

    for v in me.vertices:
        co_local = v.co
        z = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)
            
            # if z <= 0.0:
            #     continue
            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = clamp(min(lx), 0.0, 1.0)
    max_x = clamp(max(lx), 0.0, 1.0)
    min_y = clamp(min(ly), 0.0, 1.0)
    max_y = clamp(max(ly), 0.0, 1.0)

    mesh_eval.to_mesh_clear()

    r = scene.render
    fac = r.resolution_percentage * 0.01
    dim_x = r.resolution_x * fac
    dim_y = r.resolution_y * fac

    # Sanity check
    if round((max_x - min_x) * dim_x) == 0 or round((max_y - min_y) * dim_y) == 0:
        return (0, 0, 0, 0)
    
    return [round(min_x*dim_x), round(dim_y - max_y * dim_y), round(max_x*dim_x), round(dim_y - min_y * dim_y)]

    # return (
    #     round(min_x * dim_x),            # X
    #     round(dim_y - max_y * dim_y),    # Y
    #     round((max_x - min_x) * dim_x),  # Width
    #     round((max_y - min_y) * dim_y)   # Height
    # )


def get_objs_bboxes():
    bboxes = []
    for obj in bpy.data.collections.get('Generated').objects:
        bboxes.append(camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, obj))
    return bboxes


def render(output_dir, data, filename):
    output_image = os.path.join(output_dir, f'{filename}.png')
    output_info = os.path.join(output_dir, f'{filename}.json')
    
    bpy.context.scene.render.filepath = output_image
    bpy.ops.render.render(write_still = True)

    with open(output_info, 'w') as f:
        json.dump(data, f)