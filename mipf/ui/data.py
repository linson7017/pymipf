from trame.widgets import vuetify, html, trame

from collections import defaultdict

from mipf.core.data import DataStorage, DataNode, DataType
from mipf.core.mapper import Representation
from mipf.core.render_window_manager import render_window_manager
from mipf.ui.common import *


class PipelineManager:
    DEFAULT_NODE = {"collapsed": 0}

    def __init__(self, state, name, data_storage):
        self._state = state
        self._name = name
        self.data_storage = data_storage

    def update(self):
        result = self._add_children([], "0")
        self._state[self._name] = result
        return result

    def _add_children(self, list_to_fill, node_id):
        for child_id in self.data_storage.children_map[node_id]:
            node = self.data_storage.nodes[child_id]
            list_to_fill.append(node.properties)
            if node.get("collapsed"):
                continue
            self._add_children(list_to_fill, node.get("id"))

        return list_to_fill

    def add_node(self, node: DataNode, parent_node=None, **item_keys):
        append_keys = {
            **PipelineManager.DEFAULT_NODE,
            **item_keys
        }
        _id = self.data_storage.add_node(node, parent_node, **append_keys)
        self.update()
        return _id

    def remove_node(self, _id):
        for id in self.data_storage.children_map[_id]:
            self.remove_node(id)
        self.data_storage.nodes.pop(_id)
        self.data_storage._update_hierarchy()
        self.update()

    def toggle_collapsed(self, _id, icons=["collapsed", "collapsible"]):
        node = self.get_node(_id)
        node["collapsed"] = not node["collapsed"]

        # Toggle matching action icon
        actions = node.get("actions", [])
        for i in range(len(actions)):
            action = actions[i]
            if action in icons:
                actions[i] = icons[(icons.index(action) + 1) % 2]

        self.update()
        return node["collapsed"]

    def toggle_visible(self, _id):
        node = self.data_storage.get_node(_id)
        node["visible"] = not node["visible"]
        self.update()
        return node["visible"]


class DataNodesTree:
    def __init__(self, state, ctrl, data_storage: DataStorage):
        self.pipeline = PipelineManager(state, "data_storage", data_storage)
        self.data_storage: DataStorage = data_storage
        self.state = state
        self.ctrl = ctrl
        self.update()
        self.ui = self._setup_ui()

    def __call__(self, *args, **kwds):
        return self.ui

    def update(self):
        for node in self.data_storage.nodes.values():
            color = node.properties["color"]
            self.pipeline.add_node(
                node, actions=["delete"]
            )
        self.pipeline.update()

    def _data_nodes_action(self, event):
        print("on_action", event)
        _id = event.get("id")
        _action = event.get("action")
        if _action.startswith("collap"):
            print(self.pipeline.toggle_collapsed(_id))
        if _action.startswith("delete"):
            self.pipeline.remove_node(_id)

    def _visiblity_changed(self, event):
        for node in self.data_storage.nodes.values():
            if node.id == event.get("id"):
                node.properties["visible"] = event.get("visible")
        render_window_manager.request_update_all()
        self.ctrl.view_update()

    def _actives_changed(self, event):
        for node in self.data_storage.nodes.values():
            if node.id in event:
                node.properties["activate"] = True
                if node.data.type == DataType.Surface:
                    self.state.active_node_type = "surface"
                elif node.data.type == DataType.Image:
                    self.state.active_node_type = "image"
                else:
                    self.state.active_node_type = None
            else:
                node.properties["activate"] = False

    def _setup_ui(self):
        return trame.GitTree(
            sources=("data_storage",),
            action_map=("icons", local_file_manager.assets),
            action_size=25,
            action=(self._data_nodes_action, "[$event]"),
            visibility_change=(self._visiblity_changed, "[$event]"),
            actives_change=(self._actives_changed, "[$event]"),
        )


class SurfaceDataPropertyCard:
    def __init__(self, state, ctrl, data_storage: DataStorage):
        self.data_storage: DataStorage = data_storage
        self.ctrl = ctrl
        self.ui = self._setup_ui()

    def __call__(self, *args, **kwds):
        return self.ui

    def _property_card_title(self, title, ui_icon):
        with vuetify.VCardTitle(
            classes="grey lighten-1 pa-0 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        ) as card_title:
            vuetify.VIcon(ui_icon, classes="mr-3", color="grey darken-3")
            html.Div(title)
        return card_title

    def _property_card_actions(self):
        vuetify.VSpacer()

    def _property_card_text(self):
            vuetify.VSelect(
                v_model=("current_representation", Representation.Surface),
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
            vuetify.VColorPicker(mode='rgba', v_model=(
                "surface_color", "#FFFFFFFF"))

    def _setup_ui(self):
        with ui_property_card("surface") as card:
            card_title = self._property_card_title(
                title="Properties",
                ui_icon="mdi-tools",
            )
            with ui_card_text() as card_text:
                self._property_card_text()
            with ui_card_actions() as card_actions:
                self._property_card_actions()
        with ui_property_card("image") as card:
            card_title = self._property_card_title(
                title="Properties",
                ui_icon="mdi-tools",
            )
            with ui_card_text() as card_text:
                vuetify.VRangeSlider(
                    thumb_size=16,
                    thumb_label="always",
                    label="Window",
                    v_model=("image_level_window", [100, 2000]),
                    min=("image_min", -2000),
                    max=("image_max", 4000),
                    dense=True,
                    hide_details=True,
                    step=1,
                    style="max-width: 400px",
                )
            return card


class DataDrawer:
    def __init__(self,
                 drawer,
                 state,
                 ctrl,
                 data_storage: DataStorage,
                 width=325):
        self.data_storage: DataStorage = data_storage
        self.ctrl = ctrl
        self.state = state
        self.drawer = drawer
        self.drawer.width = 325
        self.ui = self._setup_ui()

    def __call__(self, *args, **kwds):
        return self.ui

    def _setup_ui(self):
        DataNodesTree(self.state, self.ctrl, self.data_storage)
        vuetify.VDivider(classes="mb-2")
        # Pipeline Cards
        SurfaceDataPropertyCard(self.state, self.ctrl, self.data_storage)

        # property_card()
        # grid_card(self.ctrl)
        # topography_card(self.ctrl)
        # # Workflow Cards
        # stacks_card(self.ctrl)
        # surfaces_card(self.ctrl)
        # points_card(self.ctrl)
        # orientations_card(self.ctrl)
