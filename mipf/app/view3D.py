from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout,SinglePageWithDrawerLayout
from trame.widgets import vuetify, html, trame, vtk as vtk_widgets
from trame.app.file_upload import ClientFile

from mipf.core.render_window import *
from mipf.core.data import *
from tkinter import filedialog, Tk
from vtkmodules.vtkFiltersGeneral import vtkExtractSelectedFrustum
from vtkmodules.vtkFiltersCore import vtkThreshold

server = get_server(client_type = "vue2")
ctrl = server.controller
state = server.state
state.update(
    {
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
        "coneVisibility": False,
        "pixel_ratio": 2,
        # Meshes
        "f1Visible": True,
    }
)

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


# -----------------------------------------------------------------------------
# mipf initialization
# -----------------------------------------------------------------------------
data_storage = DataStorage()

state.data_nodes = data_storage.data_nodes

def add_item(item):
    print(item)
    state.data_nodes['c']=3
    state.data_nodes['d']=4

# image_data = ImageData()
# image_data.read_data(r'E:\test_data\CTA\cta.mha')
# image_node = DataNode()
# image_node.set_data(image_data)
# data_storage.add_node(image_node)

surface_data = SurfaceData()
surface_data.read_data(r'E:\test_data\CTA\vessel_smooth.vtp')
surface_node = DataNode()
surface_node.properties["color"]=[1.0,1.0,1.0]
surface_node.set_data(surface_data)
data_storage.add_node(surface_node)

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
render_window =  RenderWindow(data_storage,ViewType.View3D)
render_window.setup()

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
                surface_data2.read_byte("vtp",bytes)
                surface_node2 = DataNode()
                surface_node2.properties["color"] = [1.0, 1.0, 1.0]
                surface_node2.set_data(surface_data2)
                data_storage.add_node(surface_node2)
            elif ".vti" in file.name:
                bytes = file.content
                image_data2 = SurfaceData()
                image_data2.read_byte("vti",bytes)
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
                "coneVisibility": False,
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

@state.change("image_visibility")
def update_image_visibility(image_visibility, **kwargs):
    for node in data_storage.nodes.values():
        if node.data.type == DataType.Image:
            node.properties["visible"] = image_visibility
    render_window_manager.request_update_all()
    ctrl.view_update()

@state.change("surface_visibility")
def update_surface_visibility(surface_visibility, **kwargs):
    for node in data_storage.nodes.values():
        if node.data.type == DataType.Surface:
            node.properties["visible"] = surface_visibility
    render_window_manager.request_update_all()
    ctrl.view_update()

@state.change("surface_color")
def update_surface_color(surface_color, **kwargs):
    for node in data_storage.nodes.values():
        if node.data.type == DataType.Surface:
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

@state.change("mesh_representation")
def update_mesh_representation(mesh_representation, **kwargs):
    for node in data_storage.nodes.values():
        if node.data.type == DataType.Surface:
            node.properties["representation"] = mesh_representation
    render_window_manager.request_update_all()
    ctrl.view_update()


with SinglePageWithDrawerLayout(server) as layout:
    # Toolbar
    with layout.toolbar:
        vuetify.VFileInput(
            multiple=True,
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("files", None),
            dense=True,
            hide_details=True,
            style="max-width: 300px;",
            accept=".vtp",
            __properties=["accept"],
        )
        vuetify.VSpacer()
        with vuetify.VBtnToggle(v_model=("pickingMode", "hover"), dense=True):
            with vuetify.VBtn(value=("item.value",), v_for="item, idx in modes"):
                vuetify.VIcon("{{item.icon}}")

        vuetify.VBtn("Reset Camera", click=ctrl.reset_camera)

        with vuetify.VMenu():
            with vuetify.Template(v_slot_activator="{ on, attrs }"):
                with vuetify.VBtn(text="Control",icon=True, v_bind="attrs", v_on="on"):
                    vuetify.VIcon("mdi-dots-vertical")
            with vuetify.VList():
                with vuetify.VListItem():
                    vuetify.VSwitch(label="Depth Peeling", v_model=("depth_peeling", True))


    with layout.drawer as drawer:
        # drawer components
        drawer.width = 325
        vuetify.VDivider(classes="mb-2")

        with vuetify.VList():
            with vuetify.VListItem(
                    v_for="(item, i) in data_nodes",
                    key="i",
                    value=["item"],
            ):
                vuetify.VBtn(
                    "{{ item.name }}",
                    click=(add_item, "[item]")
                )



        vuetify.VCheckbox(label="Image visible",v_model=("image_visibility", True))
        vuetify.VCheckbox(label="Surface visible",v_model=("surface_visibility", True))
        vuetify.VSelect(
            # Representation
            v_model=("mesh_representation", Representation.Surface),
            items=(
                "representations",
                [
                    {"text": "Points", "value": 0},
                    {"text": "Wireframe", "value": 1},
                    {"text": "Surface", "value": 2},
                    {"text": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        vuetify.VDivider(classes="mb-2")
        vuetify.VColorPicker(mode='rgba',v_model=("surface_color","#FFFFFFFF"))


    with layout.content:
        # Left-hand side: Data list
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            #html_view = vtk.VtkRemoteLocalView(render_window.get_vtk_render_window())
            # html_view = vtk.VtkRemoteView(render_window.get_vtk_render_window(),
            #                               picking_modes=("[pickingMode]",),
            #                               interactor_settings=("interactorSettings", VIEW_INTERACT),
            #                               click="pickData = $event",
            #                               hover="pickData = $event",
            #                               select="selectData = $event",)
            with vtk_widgets.VtkRemoteLocalView(render_window.get_vtk_render_window(),
                                          picking_modes=("[pickingMode]",),
                                          interactor_settings=("interactorSettings", VIEW_INTERACT),
                                          click="pickData = $event", ) as html_view:
                #html_view = vtk.VtkLocalView(render_window.get_vtk_render_window())
                ctrl.on_server_ready.add(html_view.update)
                ctrl.view_update = html_view.update
                ctrl.reset_camera = html_view.reset_camera
                with vtk_widgets.VtkGeometryRepresentation(
                    id="pointer",
                    property=("{ color: [1, 0, 0]}",),
                    actor=("{ visibility: coneVisibility }",),
                ):
                    vtk_widgets.VtkAlgorithm(
                        vtk_class="vtkConeSource",
                        state=("cone", {}),
                    )

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    server.start()

