from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout, SinglePageWithDrawerLayout, VAppLayout
from trame.widgets import vuetify, html, trame, vtk as vtk_widgets


from mipf.core.render_window import *
from mipf.core.data import *
from mipf.core.utils import *
from mipf.ui.data import *
from mipf.ui.engine import *

server = get_server(client_type="vue2")
state = server.state


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
                #View Layouts
                "layouts":[
                    {"value":"FourViews","icon":"mdi-view-grid"},
                    {"value":"Axial","icon":"mdi-numeric-1-box"},
                    {"value":"Sagittal","icon":"mdi-numeric-2-box"},
                    {"value":"Coronal","icon":"mdi-numeric-3-box"},
                    {"value":"3D","icon":"mdi-numeric-4-box"},
                ],
                # Picking feedback
                "pickData": None,
                "selectData": None,
                "tooltip": "",
                "pixel_ratio": 2,
                "layout_style":"display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr;width: 100%;height: 100%;"
            }
        )
        self.render_windows = []

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
        self.rendow_rendows = {
            "Axial":RenderWindow(self.data_storage,ViewType.View2D,ViewDirection.Axial),
            "Sagittal":RenderWindow(self.data_storage,ViewType.View2D,ViewDirection.Sagittal),
            "Coronal":RenderWindow(self.data_storage,ViewType.View2D,ViewDirection.Coronal),
            "3D":RenderWindow(self.data_storage,ViewType.View3D)
        }  
        colors = {
            "Axial":"#FF0000",
            "Sagittal":"#00FF00",
            "Coronal":"#0000FF",
            "3D":"#FFFF00"
        }
        for render_window in self.rendow_rendows.values():
            render_window.setup()
                  

        initialize_binding(server, self.data_storage)
        state = server.state
        ctrl = server.controller
        data_storage = self.data_storage
        

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
                with vuetify.VBtnToggle(v_model=("viewLayout", "FourViews"), dense=True):
                    with vuetify.VBtn(value=("item.value",), v_for="item, idx in layouts"):
                        vuetify.VIcon("{{item.icon}}")
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
               
                vuetify.VDivider(classes="mb-2")
                DataPropertyCard(
                    self.state, self.ctrl, self.data_storage)

            with layout.content:
                with vuetify.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                    style=("layout_style",""),
                ):
                    for name,renderwindow in self.rendow_rendows.items():
                        with html.Div(
                            style=f"height:100%;width:100%;justify-self: stretch; border:2px solid; borderColor:{colors[name]};",
                            click=f"active_view = '{name}'",
                            v_show=f"viewLayout == '{name}' || viewLayout == 'FourViews'"
                        ) as renderwindow_container:
                            render_window = renderwindow.get_vtk_render_window()
                            with vtk_widgets.VtkRemoteLocalView(
                                render_window, ref=f"view_{name}",   
                                ) as html_view:
                                self.ctrl.on_server_ready.add(html_view.update)
                                self.ctrl[f"view_{name}_capture_image"].add(html_view.capture_image)
                                
                                self.ctrl.view_update.add(html_view.update)
                                #self.ctrl.reset_camera.add(html_view.reset_camera)
                                self.ctrl.reset_camera.add(renderwindow.reset_camera)
                                self.ctrl.reset_camera.add(html_view.update)
                                
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
    
    #app.load(r'D:\ncct.nii', "ncct")
    app.load(r'E:\test_data\CTA\cta.mha', "cta_image")
    # app.load(r'E:\test_data\CTA\vessel_smooth.vtp', "vessel_surface")
    # pointset = PointSetData()
    # pointset_node = DataNode("pointset")
    # pointset_node.set_data(pointset)
    # app.data_storage.add_node(pointset_node)

    # Start server
    server.start(**kwargs)


if __name__ == "__main__":
    main()
