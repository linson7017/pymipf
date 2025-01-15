from trame.app.file_upload import ClientFile
from tkinter import filedialog
from mipf.core.data import *
from mipf.core.render_window_manager import render_window_manager
from mipf.core.mapper_mananger import mapper_manager
from mipf.core.pipeline_manager import PipelineManager
from mipf.core.render_window import ViewType
from mipf.core.mapper import *
from mipf.core.engine import *

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


def initialize_binding(server, data_storage, **kwargs):
    state, ctrl = server.state, server.controller
    plotter = kwargs.get("plotter")

    initialize_internal_binding(server, data_storage, **kwargs)

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
    def captura_screen(name, event):
        print("captura_screen")
       # utils.download(name, event)

    @state.change("viewLayout")
    def update_picking_mode(viewLayout, **kwargs):
        print("View Layout change to ", viewLayout)
        if viewLayout == "FourViews":
            state.layout_style = "display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr;width: 100%;height: 100%;"
        else:
            state.layout_style = "display:flex;align-items: center;justify-content: center;width: 100%;height: 100%;"

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
                        if len(pointset_data) > 0:
                            pointset_data.set_point(0, wp)
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
                    if len(pointset_data) > 0:
                        pointset_data.set_point(0, wp)
                    else:
                        pointset_data.add_point(wp)
                    if node.get("activate"):
                        state.points_info = pointset_data.to_list()
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
