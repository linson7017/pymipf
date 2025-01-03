from mipf.core.geometry import *
from abc import ABC, abstractmethod
from mipf.core.utils import *
from typing import Dict
from enum import Enum
import uuid
from collections import defaultdict
from mipf.core.data_manager import data_manager

from vtkmodules.vtkCommonCore import (
    vtkPoints
)
from vtkmodules.vtkCommonDataModel import (
    vtkImageData,
    vtkPolyData,
    vtkPointSet
)


class DataType(Enum):
    Image = 1
    Surface = 2
    PointSet = 3


class BaseData(ABC):
    def __init__(self):
        self.type: DataType = None
        self.name = ""
        self._geometry: Geometry = None

    def get_geometry(self):
        return self._geometry

    @abstractmethod
    def get_bounds(self):
        pass

    @abstractmethod
    def read_data(self, filename: str):
        pass


class ImageData(BaseData):
    def __init__(self):
        self.type = DataType.Image
        self._geometry = Geometry()
        self._image: vtkImageData = None

    def read_data(self, filename: str):
        self._image = load_image(filename)

    def read_byte(self, type, intput):
        if type == "vti":
            reader = vtkXMLImageDataReader()
            reader.SetInputString(intput)
            reader.SetReadFromInputString(True)
            reader.Update()
            self._image = reader.GetOutput()

    def get_image(self):
        return self._image

    def get_bounds(self):
        return self._image.GetBounds()

    def get_center(self):
        return self._image.GetCenter()


class SurfaceData(BaseData):
    def __init__(self):
        self.type = DataType.Surface
        self._geometry = Geometry()
        self._polydata: vtkPolyData = None

    def read_data(self, filename: str):
        self._polydata = load_surface(filename)

    def get_bounds(self):
        return self._polydata.GetBounds()

    def get_center(self):
        return self._polydata.GetCenter()

    def read_byte(self, type, intput):
        if type == "vtp":
            reader = vtkXMLPolyDataReader()
            reader.SetInputString(intput)
            reader.SetReadFromInputString(True)
            reader.Update()
            self._polydata = reader.GetOutput()

    def get_polydata(self):
        return self._polydata


class PointSetData(BaseData):
    def __init__(self):
        self.type = DataType.PointSet
        self.geometry = Geometry()
        self._pointset: vtkPoints = vtkPoints()

    def read_data(self, filename: str):
        pass

    def read_byte(self, type, intput):
        pass

    def get_pointset(self):
        return self._pointset

    def get_point(self, index):
        if index < len(self._pointset.GetNumberOfPoints()):
            return self._pointset.GetPoint(index)
        raise ValueError("{} is out of range!".format(index))

    def set_point(self, index, point):
        if index < len(self._pointset):
            self._pointset.SetPoint(index, point)
        else:
            raise ValueError("{} is out of range!".format(index))

    def add_point(self, point):
        self._pointset.InsertNextPoint(point)

    def clear(self):
        self._pointset.Reset()

    def to_list(self):
        results = []
        for i in range(self._pointset.GetNumberOfPoints()):
            result = {}
            result["id"] = i
            p = self._pointset[i]
            result["position_x"] = p[0]
            result["position_y"] = p[1]
            result["position_z"] = p[2]
            result["position"] = p
            results.append(result)
        return results

    def get_bounds(self):
        return self._pointset.GetBounds()

    def get_center(self):
        bounds = self._pointset.GetBounds()
        return [(bounds[0]+bounds[1])*0.5,
                (bounds[2]+bounds[3])*0.5,
                (bounds[4]+bounds[5])*0.5,]


class DataNode:
    def __init__(self, name="undefined"):
        self.properties = {
            "visible": True,
            "color": [1, 1, 1, 1],
            "opacity": 1.0,
            "activate": False,
            "name": name,
            "id": uuid.uuid4().hex
        }
        self.parent = None
        self.mappers = {}

    def set_data(self, data: BaseData):
        self.data = data
        data_manager.add_data(data, self.get("id"))

    def get_data(self):
        return data_manager.get_data(self.get("id"))

    def __getitem__(self, key):
        return self.properties.get(key)

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __delitem__(self, key):
        del self.properties[key]

    def update(self, items: Dict):
        self.properties.update(Dict)

    def get(self, key, default=None):
        return self.properties.get(key, default)

    def pop(self, key, default=None):
        self.pop(key, default)


class DataStorage:
    class DataStorageEvent(Enum):
        ADD_NODE = 0,
        REMOVE_NODE = 1,
        MODIFIED_NODE = 3

    def __init__(self):
        self.nodes: Dict[uuid.UUID, DataNode] = {}
        self.children_map = defaultdict(set)
        self._callbacks = {
            DataStorage.DataStorageEvent.ADD_NODE: [],
            DataStorage.DataStorageEvent.REMOVE_NODE: [],
            DataStorage.DataStorageEvent.MODIFIED_NODE: []
        }

    def trigger_callbacks(self, event_name, *args, **kwargs):
        if event_name in self._callbacks:
            for callback in self._callbacks[event_name]:
                callback(*args, **kwargs)

    def register_callback(self, callback, event_name):
        if event_name in self._callbacks:
            if callback not in self._callbacks[event_name]:
                self._callbacks[event_name].append(callback)
        else:
            print("Event {} is not in the callback list {}".format(
                event_name, self._callbacks.keys()))

    def remove_callback(self, callback):
        for event_callbacks in self._callbacks.values():
            if callback in event_callbacks:
                event_callbacks.remove(callback)

    def add_node(self, node: DataNode, parent_node=None, **item_keys):
        _id = node.get("id")
        _parent_id = "0"
        if parent_node:
            _parent_id = parent_node.get("id")
        node.properties.update(
            {
                "parent": _parent_id,
                **item_keys,
            }
        )
        node.parent = parent_node
        self.nodes[_id] = node
        self._update_hierarchy()
        self.trigger_callbacks(DataStorage.DataStorageEvent.ADD_NODE,
                               node, parent_node, **item_keys)
        return _id

    def remove_node(self, _id):
        for id in self.data_storage.children_map[_id]:
            self.remove_node(id)
        self.data_storage.nodes.pop(_id)
        self.data_storage._update_hierarchy()
        self.trigger_callbacks(DataStorage.DataStorageEvent.REMOVE_NODE, _id)

    def modefied(self, _id):
        self.trigger_callbacks(DataStorage.DataStorageEvent.MODIFIED_NODE, _id)

    def get_node(self, _id):
        return self.nodes.get(f"{_id}")

    def get_named_node(self, name: str):
        for node in self.nodes.values():
            if node.get("name") == name:
                return node

    def _update_hierarchy(self):
        self.children_map.clear()
        for node in self.nodes.values():
            _parent_id = "0"
            if node.parent:
                _parent_id = node.parent.id
            self.children_map[_parent_id].add(node.get("id"))

    def get_bounds(self):
        bounds_list = []
        for node in self.nodes.values():
            if node.get("visible"):
                bounds_list.append(node.get_data().get_bounds())
        return bounds_union(*bounds_list)    
    
    def get_center(self):
        bounds = self.get_bounds()
        center=[0,0,0]
        center[0] = (bounds[0]+bounds[1])*0.5
        center[1] = (bounds[2]+bounds[3])*0.5
        center[2] = (bounds[4]+bounds[5])*0.5
        return center     



def import_image_file(filename, node_name="undefined"):
    image_data = ImageData()
    image_data.read_data(filename)
    image_node = DataNode(node_name)
    image_node.set_data(image_data)
    return image_node


def import_surface_file(filename, node_name="undefined"):
    surface_data = SurfaceData()
    surface_data.read_data(filename)
    surface_node = DataNode(node_name)
    surface_node.set_data(surface_data)
    return surface_node
