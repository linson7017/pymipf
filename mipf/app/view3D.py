from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout, SinglePageWithDrawerLayout, VAppLayout
from trame.widgets import vuetify, html, trame, vtk as vtk_widgets


from mipf.core.render_window import *
from mipf.core.data import *
from mipf.core.utils import *
from mipf.ui.data import *
from mipf.ui.engine import *

server = get_server(client_type="vue2")


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
        elif filename.endswith('vtp') or filename.endswith('stl'):
            node = import_surface_file(filename, name)
            self.data_storage.add_node(node)
            render_window_manager.request_update_all()
            self.ctrl.reset_camera()
        else:
            print("Not a supported file ",filename)

    def setupui(self):
        self.render_window = RenderWindow(self.data_storage, ViewType.View3D)
        self.render_window.setup()
        initialize_binding(server, self.data_storage)
        state= server.state

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
                vuetify.VSpacer()
                with vuetify.VBtnToggle(v_model=("pickingMode", "hover"), dense=True):
                    with vuetify.VBtn(value=("item.value",), v_for="item, idx in modes"):
                        vuetify.VIcon("{{item.icon}}")

                vuetify.VBtn("Reset Camera", click=self.ctrl.reset_camera)

                with vuetify.VMenu():
                    with vuetify.Template(v_slot_activator="{ on, attrs }"):
                        with vuetify.VBtn(text="Control", icon=True, v_bind="attrs", v_on="on"):
                            vuetify.VIcon("mdi-dots-vertical")
                    with vuetify.VList():
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
                    with vtk_widgets.VtkRemoteLocalView(self.render_window.get_vtk_render_window(),
                                                        picking_modes=(
                        "[pickingMode]",),
                        interactor_settings=(
                        "interactorSettings", VIEW_INTERACT),
                        click="pickData = $event",
                    ) as html_view:
                        #     # html_view = vtk.VtkLocalView(render_window.get_vtk_render_window())
                        self.ctrl.on_server_ready.add(html_view.update)
                        self.ctrl.view_update = html_view.update
                        self.ctrl.reset_camera = html_view.reset_camera


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
