from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout, SinglePageWithDrawerLayout, VAppLayout
from trame.widgets import vuetify, html, trame, vtk as vtk_widgets


from mipf.core.render_window import *
from mipf.core.data import *
from mipf.core.utils import *
from mipf.ui.data import *
from mipf.ui.engine import *
from mipf.ui.app import AppBase
import threading
import asyncio
import os
import tkinter as tk
from tkinter import filedialog

server = get_server(client_type="vue2")
state = server.state


class Workbench(AppBase):
    def __init__(self, server, app_name="Undefined"):
        super().__init__(server, app_name)
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
                # 4D CTA controls
                "is_playing": False,
                "playback_progress": 0,
                "playback_speed": 1.0,
                "current_vessel": 0,
                "vessel_number": 0,
                # CTP parameters
                "active_tab": "playback",
                "cbv_value": 0,
                "cbf_value": 0,
                "mtt_value": 0,
                "ttp_value": 0,
            }
        )
        self.playback_task = None
        self._setup_playback_controls()
        
    def init_scene(self):
        # 计算血管数量
        number = 0
        for node in self.data_storage.nodes.values():
            if "vessel" in node['name']:
                number += 1
        self.state.vessel_number = number-1
        self.state.current_vessel = 0
        self.state.playback_progress = 0
        
    def _setup_playback_controls(self):
        @self.state.change("is_playing")
        def toggle_playback(is_playing, **kwargs):
            if is_playing:
                self.start_playback()
            else:
                self.stop_playback()

        @self.state.change("playback_progress")
        def update_playback_progress(playback_progress, **kwargs):
            # 在这里更新4D CTA的显示状态
            print(f"update_playback_progress: {playback_progress}")
            self.state.current_vessel = int(playback_progress*self.state.vessel_number)
            for node in self.data_storage.nodes.values():
                if "vessel_" in node['name']:
                    index = node["name"].split("_")[1]
                    index = index.split(".")[0]
                    if index.isdigit():
                        if self.state.current_vessel == int(index):
                            node['visible'] = True
                        else:
                            node['visible'] = False
            self.data_storage.modefied(0)
            render_window_manager.request_update_all()
            self.ctrl.view_update()

    async def _playback_loop(self):
        while self.state.is_playing:
            self.update_progress()
            await asyncio.sleep(0.1)

    def start_playback(self):
        if self.playback_task is None:
            self.playback_task = asyncio.create_task(self._playback_loop())

    def stop_playback(self):
        if self.playback_task is not None:
            self.playback_task.cancel()
            self.playback_task = None

    def update_progress(self):
        if self.state.is_playing:
            step = 0.01 * self.state.playback_speed
            self.state.playback_progress = (self.state.playback_progress + step) % 1.0
            self.state.flush()
            self.ctrl.view_update()

    def setupui(self):
        use_plotter = False
        self.render_window = RenderWindow(self.data_storage,
                                          ViewType.View3D, use_plotter=use_plotter)
        self.render_window.setup()
                
        

        initialize_binding(server, self.data_storage,
                           plotter=self.render_window.get_plotter())
            
        @state.change("vtk_files")
        def load_files(vtk_files, **kwargs):
            if vtk_files is None or len(vtk_files) == 0:
                return
                
            # 显示进度条
            self.state.loading = True
            self.state.loading_progress = 0
            self.state.loading_text = "正在加载文件..."
            
            # 计算总文件数
            total_files = len(vtk_files)
            
            # 加载所有文件
            nodes = load_client_files(files=vtk_files, data_storage=self.data_storage)
            
            for node in nodes:
                node["helper object"] = True
                
            self.data_storage.modefied(0)
            
            # 更新进度
            self.state.loading_progress = 100
            self.state.loading_text = "文件加载完成"
            
            self.init_scene()
            self.ctrl.reset_camera()

        @state.change("tf_files")
        def load_tf_files(tf_files, **kwargs):
            if tf_files is None or len(tf_files) == 0:
                return

            if tf_files and len(tf_files):
                if not tf_files[0].get("content"):
                    return
                for file in tf_files:
                    file = ClientFile(file)
                    print(f"Load {file.name}")
                    scalar_opacity, gradient_opacity, color = extract_tf(
                        file.content)

                    for node in self.data_storage.nodes.values():
                        if node.data.type == DataType.Image and node.get("activate"):
                            node["scalar_opacity"] = scalar_opacity
                            node["gradient_opacity"] = gradient_opacity
                            node["colors"] = color
                    render_window_manager.request_update_all()
                    self.ctrl.view_update()

        with SinglePageWithDrawerLayout(server) as layout:
            # Toolbar
            layout.title.set_text(self.app_name)
            layout.footer.hide()
            with layout.toolbar as toolbar:
                vuetify.VSpacer()
                vuetify.VFileInput(
                    multiple=True,
                    v_model=("vtk_files", None),
                    accept=".vtp,.vti",
                    __properties=["accept"],
                    style="max-width: 300px;",
                    id="hidden_file_input",
                    hide_details=True,
                    dense=True,
                    small_chips=True,
                    truncate_length=0
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
                vuetify.VBtn("重置视角", click=self.ctrl.reset_camera)
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
                
                # CTP参数显示
                with vuetify.VCard(classes="mb-4"):
                    with vuetify.VCardTitle("CTP参数"):
                        vuetify.VSpacer()
                    
                    with vuetify.VCardText():
                        vuetify.VTextField(
                            label="CBV",
                            v_model=("cbv_value", 0),
                            type="number",
                            hide_details=True,
                            class_="mb-2",
                        )
                        vuetify.VTextField(
                            label="CBF",
                            v_model=("cbf_value", 0),
                            type="number",
                            hide_details=True,
                            class_="mb-2",
                        )
                        vuetify.VTextField(
                            label="MTT",
                            v_model=("mtt_value", 0),
                            type="number",
                            hide_details=True,
                            class_="mb-2",
                        )
                        vuetify.VTextField(
                            label="TTP",
                            v_model=("ttp_value", 0),
                            type="number",
                            hide_details=True,
                            class_="mb-2",
                        )

                vuetify.VDivider(classes="mb-2")
                DataPropertyCard(
                    self.state, self.ctrl, self.data_storage)

            with layout.content:
                with vuetify.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    with vuetify.VRow(classes="fill-height"):
                        # 左侧视图
                        with vuetify.VCol(cols=9):
                            with vtk_widgets.VtkRemoteView(self.render_window.get_vtk_render_window(),
                                                           picking_modes=(
                                "[pickingMode]",),
                                interactor_settings=(
                                "interactorSettings", VIEW_INTERACT),
                                click="pickData = $event",
                                on_remote_image_capture="utils.download('remote.png', $event)",
                                on_local_image_capture=(
                                    self.ctrl.captura_screen, "['local.png', $event]"),
                                on_ready=self.ctrl.on_ready2,
                            ) as html_view:
                                self.ctrl.on_server_ready.add(html_view.update)
                                self.ctrl.view_update = html_view.update
                                self.ctrl.reset_camera = html_view.reset_camera
                                self.ctrl.view_capture_image = html_view.capture_image

                                if use_plotter:
                                    self.ctrl.view_widgets_set = html_view.set_widgets
                                    html_view.set_widgets(
                                        [self.render_window.plotter.renderer.axes_widget])
                                
                                vuetify.VProgressLinear(
                                    model=("loading_progress", 0),
                                    indeterminate=True,
                                    color="primary",
                                    width=2,
                                    height=2,
                                )
                        
                        # 右侧播放控件
                        with vuetify.VCol(cols=3):
                            with vuetify.VCard(classes="mb-4"):
                                with vuetify.VCardTitle("4D CTA"):
                                    vuetify.VSpacer()
                                    with vuetify.VBtn(icon=True, click=(self.toggle_playback,)):
                                        vuetify.VIcon("{{ is_playing ? 'mdi-pause' : 'mdi-play' }}")
                                
                                with vuetify.VCardText():
                                    vuetify.VSlider(
                                        v_model=("playback_progress", 0),
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        hide_details=True,
                                        input=("is_playing = false; state.flush()",),
                                        change=("is_playing = false; state.flush()",)
                                    )
                                    vuetify.VSlider(
                                        v_model=("playback_speed", 1.0),
                                        min=0.1,
                                        max=2.0,
                                        step=0.1,
                                        label="速度",
                                        hide_details=True,
                                    )

    def toggle_playback(self):
        self.state.is_playing = not self.state.is_playing
        self.state.flush()


def main(server=None, **kwargs):
    # Get or create server
    if server is None:
        server = get_server()

    if isinstance(server, str):
        server = get_server(server)

    # Set client type
    server.client_type = "vue2"

    # Init application
    app = Workbench(server, "UnionStrong")
    app.setupui()
    
    #app.load(r'E:\test_data\CTA\cta.mha', "cta_image")
    # app.load(r'E:\test_data\CTA\vessel_smooth.vtp', "vessel_surface")
    # pointset = PointSetData()
    # pointset_node = DataNode("pointset")
    # pointset_node.set_data(pointset)
    # app.data_storage.add_node(pointset_node)

    # Start server
    server.start(**kwargs)


if __name__ == "__main__":
    main()
