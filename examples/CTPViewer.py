from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout, SinglePageWithDrawerLayout, VAppLayout
from trame.widgets import vuetify, html, trame, vtk as vtk_widgets


from mipf.core.render_window import *
from mipf.core.data import *
from mipf.core.utils import *
from mipf.ui.data import *
from mipf.ui.engine import *


from trame_vtk.modules.vtk.widget import WidgetManager
from vtkmodules.vtkInteractionWidgets import vtkImplicitPlaneWidget2

server = get_server(client_type="vue2")
state = server.state


def init_scene(*args, **kwargs):
    print("exec_function", args, kwargs)


class Workbench:
    def __init__(self, server, app_name="Undefined"):
        self.server = server
        self.app_name = app_name
        self.data_storage = DataStorage()
        self.state.update(
            {
                "active_node_type": None,
                "current_representation": Representation.Surface,
                "surface_color": "#FFFFFFFF",
                "current_opacity": 1.0,
                # picking controls
                "modes": [
                    {"value": "hover", "icon": "mdi-magnify"},
                    {"value": "click", "icon": "mdi-cursor-default-click-outline"},
                    {"value": "select", "icon": "mdi-select-drag"},
                ],
                # Picking feedback
                "pickData": None,
                "selectData": None,
                "tooltip": "",
                "pixel_ratio": 2,
            }
        )

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    def load(self, filename: str, name="undefined"):
        if filename.endswith('nii') or filename.endswith('nii.gz') or \
                filename.endswith('vti') or filename.endswith('mha') or \
                filename.endswith('nrrd'):
            node = import_image_file(filename, name)
            self.data_storage.add_node(node)
            render_window_manager.request_update_all()
            self.ctrl.reset_camera()
            self.ctrl.view_update()
        elif filename.endswith('vtp') or filename.endswith('stl'):
            node = import_surface_file(filename, name)
            self.data_storage.add_node(node)
            render_window_manager.request_update_all()
            self.ctrl.reset_camera()
            self.ctrl.view_update()
        else:
            print("Not a supported file ", filename)

    def setupui(self):
        use_plotter = False
        self.render_window = RenderWindow(self.data_storage,
                                          ViewType.View3D, use_plotter=use_plotter)
        self.render_window.setup()
                
        

        initialize_binding(server, self.data_storage,
                           plotter=self.render_window.get_plotter())
        state = server.state
        ctrl = server.controller
        data_storage = self.data_storage

        @state.change("current_vessel")
        def update_current_vessel(current_vessel, **kwargs):
            for node in data_storage.nodes.values():
                if "vessel_" in node['name']:
                    index = node["name"].split("_")[1]
                    index = index.split(".")[0]
                    if index.isdigit():
                        if current_vessel == int(index):
                            node['visible'] = True
                        else:
                            node['visible'] = False
            data_storage.modefied(0)
            render_window_manager.request_update_all()
            ctrl.view_update()

        @ctrl.set("init_scene")
        def init_scene():
            number = 0
            for node in data_storage.nodes.values():
                if "vessel" in node['name']:
                    number += 1
            state.vessel_number = number-1
            state.current_vessel = 0

        @state.change("tf_files")
        def load_tf_files(tf_files, **kwargs):
            if tf_files is None or len(tf_files) == 0:
                return

            field = "solid"
            fields = {
                "solid": {"value": "solid", "text": "Solid color", "range": [0, 1]},
            }
            meshes = []
            filesOutput = []
            if tf_files and len(tf_files):
                if not tf_files[0].get("content"):
                    return
                for file in tf_files:
                    file = ClientFile(file)
                    print(f"Load {file.name}")
                    scalar_opacity, gradient_opacity, color = extract_tf(
                        file.content)

                    for node in data_storage.nodes.values():
                        if node.data.type == DataType.Image and node.get("activate"):
                            node["scalar_opacity"] = scalar_opacity
                            node["gradient_opacity"] = gradient_opacity
                            node["colors"] = color
                    render_window_manager.request_update_all()
                    ctrl.view_update()

        with SinglePageWithDrawerLayout(server) as layout:
            # Toolbar
            layout.title.set_text(self.app_name)
            with layout.toolbar as toolbar:
                vuetify.VSpacer()
                vuetify.VFileInput(
                    multiple=True,
                    show_size=True,
                    small_chips=True,
                    truncate_length=25,
                    v_model=("files", None),
                    dense=True,
                    hide_details=True,
                    style="max-width: 300px;",
                    accept=".vtp,.vti",
                    __properties=["accept"],
                )

                vuetify.VFileInput(
                    multiple=True,
                    show_size=True,
                    small_chips=True,
                    truncate_length=25,
                    v_model=("tf_files", None),
                    dense=True,
                    hide_details=True,
                    style="max-width: 300px;",
                    accept=".xml",
                    __properties=["accept"],
                )

                vuetify.VSpacer()
                with vuetify.VBtn(icon=True, click=self.ctrl.view_capture_image):
                    vuetify.VIcon("mdi-camera-outline")
                vuetify.VSpacer()
                with vuetify.VBtnToggle(v_model=("pickingMode", "hover"), dense=True):
                    with vuetify.VBtn(value=("item.value",), v_for="item, idx in modes"):
                        vuetify.VIcon("{{item.icon}}")
                vuetify.VSpacer()
                vuetify.VBtn("Reset Camera", click=self.ctrl.reset_camera)
                vuetify.VSpacer()
                with vuetify.VMenu():
                    with vuetify.Template(v_slot_activator="{ on, attrs }"):
                        with vuetify.VBtn(text="Control", icon=True, v_bind="attrs", v_on="on"):
                            vuetify.VIcon("mdi-dots-vertical")
                    with vuetify.VList():
                        with vuetify.VListItem():
                            vuetify.VSwitch(
                                label="Dark Theme",
                                v_model="$vuetify.theme.dark",
                            )
                        with vuetify.VListItem():
                            vuetify.VSwitch(label="Axes",
                                            v_model=("show_axes_widget", True),
                                            )
                        with vuetify.VListItem():
                            vuetify.VSwitch(label="Depth Peeling",
                                            v_model=("depth_peeling", True))
                        with vuetify.VListItem():
                            vuetify.VSwitch(label="Remote Rendering",
                                            v_model=("viewMode", "remote"),
                                            false_value="local",
                                            true_value="remote")

            with layout.drawer as drawer:
                # drawer components
                drawer.width = 325
                vuetify.VDivider(classes="mb-2")
                DataNodesTree(self.state, self.ctrl, self.data_storage)
                vuetify.VDivider(classes="mb-2")
                vuetify.VBtn(
                    "Init",
                    click=init_scene
                )
                vuetify.VSlider(
                    hide_details=True,
                    v_model=("current_vessel", 0),
                    max=("vessel_number", 0),
                    min=0,
                    step=1,
                    style="max-width: 300px;",
                )
                vuetify.VDivider(classes="mb-2")
                DataPropertyCard(
                    self.state, self.ctrl, self.data_storage)

            with layout.content:
                with vuetify.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    # html_view = vtk.VtkRemoteLocalView(self.render_window.get_vtk_render_window())
                    # html_view = vtk.VtkRemoteView(render_window.get_vtk_render_window(),
                    #                               picking_modes=("[pickingMode]",),
                    #                               interactor_settings=("interactorSettings", VIEW_INTERACT),
                    #                               click="pickData = $event",
                    #                               hover="pickData = $event",
                    #                               select="selectData = $event",)
                    with vtk_widgets.VtkRemoteView(self.render_window.get_vtk_render_window(),
                                                   picking_modes=(
                        "[pickingMode]",),
                        interactor_settings=(
                        "interactorSettings", VIEW_INTERACT),
                        click="pickData = $event",
                        on_remote_image_capture="utils.download('remote.png', $event)",
                        on_local_image_capture=(
                            self.ctrl.captura_screen, "['local.png', $event]"),
                        # interactive_quality = 1.0,
                        # interactive_ratio = 1.0,
                        # still_ratio = 1.0,
                        # still_quality = 100,
                        on_ready=self.ctrl.on_ready2,

                    ) as html_view:
                        #     # html_view = vtk.VtkLocalView(render_window.get_vtk_render_window())
                        self.ctrl.on_server_ready.add(html_view.update)
                        self.ctrl.view_update = html_view.update
                        self.ctrl.reset_camera = html_view.reset_camera
                        self.ctrl.view_capture_image = html_view.capture_image

                        # self.ctrl.before_scene_loaded=html_view.before_scene_loaded
                        # self.ctrl.after_scene_loaded=html_view.after_scene_loaded
                        # self.state.viewMode = "local"

                        if use_plotter:
                            self.ctrl.view_widgets_set = html_view.set_widgets
                            html_view.set_widgets(
                                [self.render_window.plotter.renderer.axes_widget])


def main(server=None, **kwargs):
    # Get or create server
    if server is None:
        server = get_server()

    if isinstance(server, str):
        server = get_server(server)

    # Set client type
    server.client_type = "vue2"

    # Init application
    app = Workbench(server, "MIPF")
    app.setupui()
    
    #app.load(r'E:\test_data\CTA\cta.mha', "cta_image")
    app.load(r'E:\test_data\CTA\vessel_smooth.vtp', "vessel_surface")
    pointset = PointSetData()
    pointset_node = DataNode("pointset")
    pointset_node.set_data(pointset)
    app.data_storage.add_node(pointset_node)

    # Start server
    server.start(**kwargs)


if __name__ == "__main__":
    main()
