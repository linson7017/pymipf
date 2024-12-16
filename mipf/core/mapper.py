from abc import ABC, abstractmethod
from mipf.core.data import *
from vtkmodules.vtkRenderingCore import (
    vtkPolyDataMapper,
    vtkActor,
    vtkVolumeProperty,
    vtkColorTransferFunction,
    vtkVolume,
    vtkPropAssembly
)
from vtkmodules.vtkFiltersSources import (
    vtkSphereSource
)

from vtkmodules.vtkFiltersCore import (
    vtkAppendPolyData
)

from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction


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

    def set_node(self, node):
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
            self.get_prop().GetProperty().SetOpacity(
                self.node.properties["opacity"])
        if "color" in self.node.properties:
            color = self.node.properties["color"]
            self.get_prop().GetProperty().SetColor(
                color[0], color[1], color[2])
            if len(color) == 4:
                self.get_prop().GetProperty().SetOpacity(color[3])
        if "representation" in self.node.properties:
            representation = self.node.properties["representation"]
            update_representation(self.get_prop(), representation)

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
        color_function.AddRGBPoint(-2000, 0.0, 0.0, 0.0)
        color_function.AddRGBPoint(0, 1.0, 0.5, 0.3)
        color_function.AddRGBPoint(500, 1.0, 1.0, 0.6)
        color_function.AddRGBPoint(2000, 1.0, 1.0, 0.9)
        self.volume_property.SetColor(color_function)

        opacity_function = vtkPiecewiseFunction()
        opacity_function.AddPoint(100, 0.0)
        opacity_function.AddPoint(150, 0.3)
        opacity_function.AddPoint(200, 0.8)
        opacity_function.AddPoint(1000, 1.0)

        self.volume_property.SetScalarOpacity(opacity_function)
        self.volume = vtkVolume()
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volume_property)

    def set_scalar_range(self, range):
        opacity_function = self.volume_property.GetScalarOpacity()
        opacity_function.RemoveAllPoints()

        opacity_function.AddPoint(range[0], 0.0)
        opacity_function.AddPoint(range[0]+50, 0.2)
        opacity_function.AddPoint(range[0]+100, 0.8)
        opacity_function.AddPoint(range[1], 1.0)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        if "color_function" in self.node.properties:
            self.volume_property.SetColor(
                self.node.properties["color_function"])
        if "opacity_function" in self.node.properties:
            self.volume_property.SetScalarOpacity(
                self.node.properties["opacity_function"])

    def generate_data_for_renderer(self, renderer=None):
        if self.node:
            data = self.node.get_data()
            if data and data.type == DataType.Image:
                if self.mapper.GetInput() != data.get_image():
                    self.mapper.SetInputData(data.get_image())
                self._apply_actor_properties()


class PointSetMapper3D(MapperBase):
    def __init__(self):
        MapperBase.__init__(self)

    def get_prop(self):
        return self.assembly

    def initialize_mapper(self):
        self.assembly = vtkPropAssembly()
        self.mapper = vtkPolyDataMapper()
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)
        self.assembly.AddPart(self.actor)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        if "opacity" in self.node.properties:
            self.actor.GetProperty().SetOpacity(
                self.node.properties["opacity"])
        unselectedcolor = [1.0, 1.0, 0.0,1.0]
        if "unselectedcolor" in self.node.properties:
            unselectedcolor = self.node.properties["unselectedcolor"]
        self.actor.GetProperty().SetColor(
            unselectedcolor[0], unselectedcolor[1], unselectedcolor[2])
        if len(unselectedcolor) == 4:
            self.actor.GetProperty().SetOpacity(unselectedcolor[3])
        if "representation" in self.node.properties:
            representation = self.node.properties["representation"]
            update_representation(self.actor, representation)

    def generate_data_for_renderer(self, renderer=None):
        if self.node:
            data = self.node.get_data()
            if data and data.type == DataType.PointSet:
                if self.mapper.GetInput() != data.get_pointset():
                    radius = self.node.get("pointsize")
                    if not radius:
                        radius = 2.0
                    appender = vtkAppendPolyData()
                    for point in data.get_pointset():
                        sphere_source = vtkSphereSource()
                        sphere_source.SetCenter(point[0], point[1], point[2])
                        sphere_source.SetRadius(radius)
                        sphere_source.Update()
                        appender.AddInputData(sphere_source.GetOutput())
                    appender.Update()
                    self.mapper.SetInputData(appender.GetOutput())
                self._apply_actor_properties()
