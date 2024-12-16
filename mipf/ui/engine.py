from trame.app.file_upload import ClientFile
from tkinter import filedialog
from mipf.core.data import *
from mipf.core.render_window_manager import render_window_manager
from mipf.core.render_window import ViewType

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

def initialize_binding(server, data_storage):
    state, ctrl = server.state, server.controller

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
                    surface_data2 = SurfaceData()
                    surface_data2.read_byte("vtp", bytes)
                    surface_node2 = DataNode()
                    surface_node2.properties["color"] = [1.0, 1.0, 1.0]
                    surface_node2.set_data(surface_data2)
                    data_storage.add_node(surface_node2)
                elif ".vti" in file.name:
                    bytes = file.content
                    image_data2 = SurfaceData()
                    image_data2.read_byte("vti", bytes)
                    image_node2 = DataNode()
                    image_node2.properties["color"] = [1.0, 1.0, 1.0]
                    image_node2.set_data(image_data2)
                    data_storage.add_node(image_node2)

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
        surface_node2.properties["color"] = [1.0, 1.0, 1.0]
        surface_node2.set_data(surface_data2)
        data_storage.add_node(surface_node2)

        render_window_manager.request_update_all()
        ctrl.reset_camera()

    @state.change("pickingMode")
    def update_picking_mode(pickingMode, **kwargs):
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
        if data:
            print(data)

    @state.change("surface_color")
    def update_surface_color(surface_color, **kwargs):
        for node in data_storage.nodes.values():
            if node.data.type == DataType.Surface and node.get("activate"):
                color = hex_to_float(surface_color)
                node.properties["color"] = color
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
                node.properties["representation"] = current_representation
        render_window_manager.request_update_all()
        ctrl.view_update()
