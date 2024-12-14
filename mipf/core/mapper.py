from abc import ABC, abstractmethod
from mipf.core.data import *
from vtkmodules.vtkRenderingCore import(
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkPolyDataMapper,
    vtkActor,
    vtkVolumeProperty,
    vtkColorTransferFunction,
    vtkVolume,
    vtkImageActor
)

from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction,vtkImageData

class MapperType(Enum):
    Unknow = 0
    Mapper_2D = 1
    Mapper_3D = 2

class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

# Representation Callbacks
def update_representation(actor, mode):
    property = actor.GetProperty()
    if mode == Representation.Points:
        property.SetRepresentationToPoints()
        property.SetPointSize(5)
        property.EdgeVisibilityOff()
    elif mode == Representation.Wireframe:
        property.SetRepresentationToWireframe()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.Surface:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.SurfaceWithEdges:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOn()

class MapperBase(ABC):
    def __init__(self):
        self.node = None
        self.initialize_mapper()
        
    def set_node(self,node):
        self.node = node

    @abstractmethod
    def get_prop(self):
        return None

    @abstractmethod
    def initialize_mapper(self):
        pass

    @abstractmethod
    def generate_data_for_renderer(self, renderer=None):
        pass

    def _apply_actor_properties(self):
        if self.node and self.get_prop():
            if "visible" in self.node.properties:
                self.get_prop().SetVisibility(self.node.properties["visible"])


class SurfaceMapper3D(MapperBase):
    def __init__(self):
        MapperBase.__init__(self)

    def get_prop(self):
        return self.actor

    def initialize_mapper(self):
        self.mapper = vtkPolyDataMapper()
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        if "opacity" in self.node.properties:
            self.get_prop().GetProperty().SetOpacity(self.node.properties["opacity"])
        if "color" in self.node.properties:
            color = self.node.properties["color"]
            self.get_prop().GetProperty().SetColor(color[0], color[1], color[2])
            if len(color)==4:
                self.get_prop().GetProperty().SetOpacity(color[3])
        if "representation" in self.node.properties:
            representation = self.node.properties["representation"]
            update_representation(self.get_prop(),representation)

    def generate_data_for_renderer(self, renderer=None):
        if self.node:
            data = self.node.get_data()
            if data and data.type == DataType.Surface:
                if self.mapper.GetInput() != data.get_polydata():
                    self.mapper.SetInputData(data.get_polydata())
                self._apply_actor_properties()

class ImageMapper3D(MapperBase):
    def __init__(self):
        MapperBase.__init__(self)

    def get_prop(self):
        return self.volume
    
    def initialize_mapper(self):
        self.mapper = vtkSmartVolumeMapper()
        self.volume_property = vtkVolumeProperty()
        self.volume_property.ShadeOn()
        self.volume_property.SetInterpolationTypeToLinear()

        color_function = vtkColorTransferFunction()
        color_function.AddRGBPoint(0, 0.0, 0.0, 0.0)
        color_function.AddRGBPoint(1000, 1.0, 1.0, 1.0)
        self.volume_property.SetColor(color_function)

        opacity_function = vtkPiecewiseFunction()
        opacity_function.AddPoint(0, 0.0)
        opacity_function.AddPoint(2000, 0.2)
        self.volume_property.SetScalarOpacity(opacity_function)
        self.volume = vtkVolume()
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volume_property)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        if "color_function" in self.node.properties:
            self.volume_property.SetColor(self.node.properties["color_function"])
        if "opacity_function" in self.node.properties:
            self.volume_property.SetScalarOpacity(self.node.properties["opacity_function"])

    def generate_data_for_renderer(self, renderer=None):
        if self.node:
            data = self.node.get_data()
            if data and data.type == DataType.Image:
                if self.mapper.GetInput() != data.get_image():
                    self.mapper.SetInputData(data.get_image())
                self._apply_actor_properties()