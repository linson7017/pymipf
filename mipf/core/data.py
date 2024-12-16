from mipf.core.geometry import *
from abc import ABC, abstractmethod
from mipf.core.utils import *
from typing import Dict
from enum import Enum
import uuid
from collections import defaultdict
from mipf.core.data_manager import data_manager


class DataType(Enum):
    Image = 1
    Surface = 2
    PointSet = 3


class BaseData(ABC):
    def __init__(self):
        self.type: DataType = None
        self.name = ""
        self.geometry: Geometry = None

    def get_geometry(self):
        return self.geometry

    @abstractmethod
    def read_data(self, filename: str):
        pass


class ImageData(BaseData):
    def __init__(self):
        self.type = DataType.Image
        self.geometry = Geometry()
        self.image = None

    def read_data(self, filename: str):
        self.image = load_image(filename)

    def read_byte(self, type, intput):
        if type == "vti":
            reader = vtkXMLImageDataReader()
            reader.SetInputString(intput)
            reader.SetReadFromInputString(True)
            reader.Update()
            self.image = reader.GetOutput()

    def get_image(self):
        return self.image


class SurfaceData(BaseData):
    def __init__(self):
        self.type = DataType.Surface
        self.geometry = Geometry()
        self.polydata = None

    def read_data(self, filename: str):
        self.polydata = load_surface(filename)

    def read_byte(self, type, intput):
        if type == "vtp":
            reader = vtkXMLPolyDataReader()
            reader.SetInputString(intput)
            reader.SetReadFromInputString(True)
            reader.Update()
            self.polydata = reader.GetOutput()

    def get_polydata(self):
        return self.polydata
    
class PointSetData(BaseData):
    def __init__(self):
        self.type = DataType.PointSet
        self.geometry = Geometry()
        self.pointset = []

    def read_data(self, filename: str):
        pass

    def read_byte(self, type, intput):
        pass

    def get_pointset(self):
        return self.pointset


class DataNode:
    def __init__(self, name="undefined"):
        self.name = name
        self.id = uuid.uuid4().hex
        self.properties = {
            "visible": True,
            "color": [1, 1, 1],
            "opacity": 1.0,
            "activate": False,
            "name": self.name,
            "id": self.id
        }
        self.parent = None
        self.mappers = {}

    def set_data(self, data: BaseData):
        self.data = data
        data_manager.add_data(data,self.id)

    def get_data(self):
        return data_manager.get_data(self.id)
    
    def __getitem__(self,key):
        return self.properties.get(key)
    
    def __setitem__(self,key,value):
        self.properties[key] = value
        
    def __delitem__(self,key):
        del self.properties[key]
        
    def get(self,key,default=None):
        return self.properties.get(key,default)
    
    def pop(self,key,default=None):
        self.pop(key,default)


class DataStorage:
    def __init__(self):
        self.nodes: Dict[uuid.UUID, DataNode] = {}
        self.children_map = defaultdict(set)
        
    def update(self):
        pass

    def add_node(self, node: DataNode, parent_node=None, **item_keys):
        _id = node.id
        _parent_id = "0"
        if parent_node:
            _parent_id = parent_node.id
        node.properties={
            **node.properties,
            "parent": _parent_id,
            **item_keys,
        }
        node.parent = parent_node
        self.nodes[_id] = node
        self._update_hierarchy()
        return _id
        
            
    def get_node(self, _id):
        return self.nodes.get(f"{_id}")

    def get_named_node(self, name: str):
        for node in self.nodes.values():
            if node.name == name:
                return node
            
    def _update_hierarchy(self):
        self.children_map.clear()
        for node in self.nodes.values():
            _parent_id = "0"
            if node.parent:
                _parent_id = node.parent.id
            self.children_map[_parent_id].add(node.id)
        
    

def import_image_file(filename, data_storage, node_name="undefined"):
    image_data = ImageData()
    image_data.read_data(filename)
    image_node = DataNode(node_name)
    image_node.set_data(image_data)
    data_storage.add_node(image_node)


def import_surface_file(filename, data_storage, node_name="undefined", color=[1.0, 1.0, 1.0]):
    surface_data = SurfaceData()
    surface_data.read_data(filename)
    surface_node = DataNode(node_name)
    surface_node.properties["color"] = [1.0, 1.0, 1.0]
    surface_node.set_data(surface_data)
    data_storage.add_node(surface_node)