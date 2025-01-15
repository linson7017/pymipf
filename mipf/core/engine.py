from mipf.core.data import *
from mipf.core.render_window_manager import render_window_manager
from mipf.core.mapper_mananger import mapper_manager
from mipf.core.pipeline_manager import PipelineManager
from mipf.core.render_window import ViewType
from mipf.core.mapper import *


def initialize_internal_binding(server, data_storage, **kwargs):
    state, ctrl = server.state, server.controller

    @state.change("surface_color")
    def update_surface_color(surface_color, **kwargs):
        for node in data_storage.nodes.values():
            if node.data.type == DataType.Surface and node.get("activate"):
                color = hex_to_float(surface_color)
                node["color"] = color
        render_window_manager.request_update_all()
        ctrl.view_update()

    @state.change("depth_peeling")
    def update_depth_peeling(depth_peeling, **kwargs):
        for render_window in render_window_manager.render_windows:
            if render_window.view_type == ViewType.View3D:
                render_window.set_depth_peeling(depth_peeling)
        render_window_manager.request_update_all()
        ctrl.view_update()

    @state.change("current_representation")
    def update_mesh_representation(current_representation, **kwargs):
        for node in data_storage.nodes.values():
            if node.data.type == DataType.Surface and node.get("activate"):
                node["representation"] = current_representation
        render_window_manager.request_update_all()
        ctrl.view_update()

    @state.change("image_level_window")
    def update_image_level_window(image_level_window, **kwargs):
        for node in data_storage.nodes.values():
            if node.data.type == DataType.Image and node.get("activate"):
                scalar_opacity = []
                scalar_opacity.append((image_level_window[0], 0.0))
                scalar_opacity.append((image_level_window[0]+50, 0.2))
                scalar_opacity.append((image_level_window[0]+100, 0.8))
                scalar_opacity.append((image_level_window[1], 1.0))
                node["scalar_opacity"] = scalar_opacity
        render_window_manager.request_update_all()
        ctrl.view_update()

    @state.change("pointsize")
    def update_pointsize(pointsize, **kwargs):
        for node in data_storage.nodes.values():
            node["pointsize"] = pointsize
        render_window_manager.request_update_all()
        ctrl.view_update()
        
    @state.change("data_storage")
    def update_data_storage(data_storage, **kwargs):
        print("DataStorage changed!")
