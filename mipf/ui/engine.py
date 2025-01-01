from trame.app.file_upload import ClientFile
from tkinter import filedialog
from mipf.core.data import *
from mipf.core.render_window_manager import render_window_manager
from mipf.core.mapper_mananger import mapper_manager
from mipf.core.pipeline_manager import PipelineManager
from mipf.core.render_window import ViewType
from mipf.core.mapper import *

VIEW_INTERACT = [
    {"button": 1, "action": "Rotate"},
    {"button": 2, "action": "Pan"},
    {"button": 3, "action": "Zoom", "scrollEnabled": True},
    {"button": 1, "action": "Pan", "alt": True},
    {"button": 1, "action": "Zoom", "control": True},
    {"button": 1, "action": "Pan", "shift": True},
    {"button": 1, "action": "Roll", "alt": True, "shift": True},
]

VIEW_SELECT = [{"button": 1, "action": "Select"}]


def initialize_binding(server, data_storage,**kwargs):
    state, ctrl = server.state, server.controller
    plotter = kwargs.get("plotter")
    

    @state.change("files")
    def load_client_files(files, **kwargs):
        if files is None or len(files) == 0:
            return

        field = "solid"
        fields = {
            "solid": {"value": "solid", "text": "Solid color", "range": [0, 1]},
        }
        meshes = []
        filesOutput = []

        if files and len(files):
            if not files[0].get("content"):
                return

            for file in files:
                file = ClientFile(file)
                print(f"Load {file.name}")
                if ".vtp" in file.name:
                    bytes = file.content
                    surface_data = SurfaceData()
                    surface_data.read_byte("vtp", bytes)
                    surface_node = DataNode()
                    surface_node["color"] = [1.0, 1.0, 1.0]
                    surface_node["name"] = file.name
                    surface_node.set_data(surface_data)
                    data_storage.add_node(surface_node)
                elif ".vti" in file.name:
                    bytes = file.content
                    image_data = ImageData()
                    image_data.read_byte("vti", bytes)
                    image_node = DataNode()
                    image_node["color"] = [1.0, 1.0, 1.0]
                    image_node["name"] = file.name
                    image_node.set_data(image_data)
                    data_storage.add_node(image_node)          
            render_window_manager.request_update_all()
            ctrl.reset_camera()

    @ctrl.set("load_data")
    def load_data():
        kwargs = {
            "title": "Select File",
        }
        filepath = filedialog.askopenfilename(**kwargs)
        if not filepath:
            # User canceled.
            print("Canceled")
            return

        print("Selected file:", filepath)
        surface_data2 = SurfaceData()
        surface_data2.read_data(filepath)
        surface_node2 = DataNode()
        surface_node2["color"] = [1.0, 1.0, 1.0]
        surface_node2.set_data(surface_data2)
        data_storage.add_node(surface_node2)

        render_window_manager.request_update_all()
        ctrl.reset_camera()
        
    @ctrl.set("before_scene_loaded")
    def before_scene_loaded():
        print("before_scene_loaded")
        
    @ctrl.set("after_scene_loaded")
    def after_scene_loaded():
        print("after_scene_loaded")
        
    @ctrl.set("on_ready2")
    def on_ready2():
        print("on_ready2")
        
    @ctrl.set("captura_screen")
    def captura_screen(name,event):
        print("captura_screen")
       #utils.download(name, event)

    @state.change("pickingMode")
    def update_picking_mode(pickingMode, **kwargs):
        print("Pick model change to ", pickingMode)
        mode = pickingMode
        if mode is None:
            state.update(
                {
                    "tooltip": "",
                    "tooltipStyle": {"display": "none"},
                    "pointerVisibility": False,
                    "interactorSettings": VIEW_INTERACT,
                }
            )
        else:
            state.interactorSettings = VIEW_SELECT if mode == "select" else VIEW_INTERACT
            state.update(
                {
                    "frustrum": None,
                    "selection": None,
                    "selectData": None,
                }
            )

    @state.change("pickData")
    def update_tooltip(pickData, pixel_ratio, **kwargs):
        data = pickData
        if not data:
            return
        print(data)
        mode = data.get("mode")
        if mode == "remote":
            sp = data.get("position")
            if not sp:
                return
            for node in data_storage.nodes.values():
                if node.data.type == DataType.PointSet:
                    pointset_data = node.get_data()
                    render_window = render_window_manager.get_activate_renderwindow()
                    wp = render_window.pick(sp)
                    if wp:
                        if len(pointset_data.get_pointset())>0:
                            pointset_data.set_point(0,wp)
                        else:
                            pointset_data.add_point(wp)
                        if node.get("activate"):
                            state.points_info = pointset_data.to_list()
            render_window_manager.request_update_all()
            ctrl.view_update()
        elif mode == "local":
            wp = data.get("worldPosition")
            if not wp:
                return
            for node in data_storage.nodes.values():
                if node.data.type == DataType.PointSet:
                    pointset_data = node.get_data()
                    if len(pointset_data.get_pointset())>0:
                            pointset_data.set_point(0,wp)
                    else:
                        pointset_data.add_point(wp)
                    if node.get("activate"):
                        state.points_info = pointset_data.to_list()
            render_window_manager.request_update_all()
            ctrl.view_update()

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


    if plotter:
        @state.change("show_axes_widget")
        def toggle_axes_widget(show_axes_widget, **kwargs):
            if show_axes_widget:
                plotter.renderer.show_axes()
            else:
                plotter.renderer.hide_axes()
            ctrl.view_update()