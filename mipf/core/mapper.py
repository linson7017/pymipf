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
    vtkAppendPolyData,
    vtkPolyDataNormals
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
            visbile = self.node.get("visible")
            if visbile:
                self.get_prop().SetVisibility(visbile)               


class SurfaceMapper3D(MapperBase):
    def __init__(self):
        MapperBase.__init__(self)

    def get_prop(self):
        return self.actor
    
    def set_node(self,node):
        MapperBase.set_node(self,node)
        node["representation"] = Representation.Surface

    def initialize_mapper(self):
        self.mapper = vtkPolyDataMapper()
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        opacity = self.node.get("opacity")
        if opacity:
            self.get_prop().GetProperty().SetOpacity(
                opacity)
            
        color = self.node.get("color")
        if color:
            self.get_prop().GetProperty().SetColor(
                color[0], color[1], color[2])
            if len(color) == 4:
                self.get_prop().GetProperty().SetOpacity(color[3])
 
        if "representation" in self.node.properties:
            update_representation(self.get_prop(), self.node.get("representation"))

    def generate_data_for_renderer(self, renderer=None):
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop().VisibilityOff()
            return
        else:
            self.get_prop().VisibilityOn()
        data = self.node.get_data()
        if data and data.type == DataType.Surface:
            if self.mapper.GetInput() != data.get_polydata():
                #normals = vtkPolyDataNormals()
                #normals.SetInputData(data.get_polydata())
                #self.mapper.SetInputConnection(normals)
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
        self.volume

    def set_scalar_range(self, range):
        opacity_function = self.volume_property.GetScalarOpacity()
        opacity_function.RemoveAllPoints()

        opacity_function.AddPoint(range[0], 0.0)
        opacity_function.AddPoint(range[0]+50, 0.2)
        opacity_function.AddPoint(range[0]+100, 0.8)
        opacity_function.AddPoint(range[1], 1.0)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        color_function = self.node.get("color_function")
        if color_function:
            self.volume_property.SetColor(color_function)
            
        opacity_function = self.node.get("opacity_function")
        if opacity_function:
            self.volume_property.SetScalarOpacity(opacity_function)

    def generate_data_for_renderer(self, renderer=None):
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop().VisibilityOff()
            return
        else:
            self.get_prop().VisibilityOn()
            
        scalar_opacity = self.node.get("scalar_opacity")
        if scalar_opacity:
            opacity_function = self.volume_property.GetScalarOpacity()
            opacity_function.RemoveAllPoints()
            for scalar,opacity in scalar_opacity:
                opacity_function.AddPoint(scalar, opacity)
        
        colors = self.node.get("colors")
        if colors:
            color_function = vtkColorTransferFunction()
            for color in colors:
                color_function.AddRGBPoint(color[0], color[1], color[2], color[3])    
            self.volume_property.SetColor(color_function) 

        data = self.node.get_data()
        if data and data.type == DataType.Image:
            if self.mapper.GetInput() != data.get_image():
                self.mapper.SetInputData(data.get_image())
            self._apply_actor_properties()


class PointSetMapper3D(MapperBase):
    def __init__(self):
        MapperBase.__init__(self)

    def get_prop(self):
        data = self.node.get_data()
        if len(data.pointset)>0:
            return self.assembly
        else:
            return None
        
    def set_node(self,node):
        MapperBase.set_node(self,node)
        node["pointsize"] = 2.0

    def initialize_mapper(self):
        self.assembly = vtkPropAssembly()
        self.mapper = vtkPolyDataMapper()
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)
        self.assembly.AddPart(self.actor)

    def _apply_actor_properties(self):
        MapperBase._apply_actor_properties(self)
        opacity = self.node.get("opacity")
        if opacity:
            self.actor.GetProperty().SetOpacity(
                opacity)
            
        unselectedcolor = self.node.get("unselectedcolor")
        if not unselectedcolor:
            unselectedcolor = [1.0,1.0,0.0,1.0]
        self.actor.GetProperty().SetColor(
            unselectedcolor[0], unselectedcolor[1], unselectedcolor[2])
        if len(unselectedcolor) == 4:
            self.actor.GetProperty().SetOpacity(unselectedcolor[3])
              
        representation = self.node.get("representation")
        if representation:
            update_representation(self.actor, representation)

    def generate_data_for_renderer(self, renderer=None):
        if not self.node:
            return
        
        data = self.node.get_data()
        if len(data.get_pointset())==0:
            return
        
        if not self.node.get("visible"):
            self.actor.VisibilityOff()
            return
        else:
            self.actor.VisibilityOn()
     
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
                   # appender.AddInputConnection(sphere_source.GetOutputPort())
                    self.mapper.SetInputConnection(sphere_source.GetOutputPort())
                #self.mapper.SetInputConnection(appender.GetOutputPort())
            self._apply_actor_properties()
    
