from mipf.core.geometry import *
from abc import ABC, abstractmethod
from mipf.core.utils import *
from typing import Dict
from enum import Enum
import uuid


class DataType(Enum):
    Image = 1
    Surface = 2


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


class DataNode:
    def __init__(self, name="Unknow"):
        self.name = name
        self.properties = {
            "visible": True,
            "color": [1, 1, 1],
            "opacity": 1.0,
            "selected": False
        }
        self.data = None
        self.id = uuid.uuid4()
        self.mappers = {}

    def set_data(self, data: BaseData):
        self.data = data

    def get_data(self):
        return self.data

    def set_mapper(self, mapper, mapper_type):
        self.mappers[mapper_type] = mapper


class DataStorage:
    def __init__(self):
        self.nodes: Dict[uuid.UUID, DataNode] = {}
        self.data_nodes = {"a": 1, "b": 2}

    def add_node(self, node):
        if node.id in self.nodes:
            print("Node ", node.name, " with ", node.id, " has already exist in data storage!")
        else:
            self.nodes[node.id] = node

    def get_named_node(self, name: str):
        for node in self.nodes.values():
            if node.name == name:
                return node
