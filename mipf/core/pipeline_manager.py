from mipf.core.data import DataNode, DataStorage


class PipelineManager:
    DEFAULT_NODE = {
        "collapsed": 0,
        "actions": ["delete"]
    }

    def __init__(self, state, name, data_storage):
        self._state = state
        self._name = name
        self.data_storage = data_storage
        self.update()

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
        node.properties.update(
            append_keys
        )
        self.update()
        return node["id"]

    def remove_node(self, _id):
        self.update()
        
    def modified_node(self, _id):
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
