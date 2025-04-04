from abc import ABC, abstractmethod
from mipf.core.data import *
from mipf.core.local_storage import *
from vtkmodules.vtkRenderingCore import (
    vtkPolyDataMapper,
    vtkActor,
    vtkVolumeProperty,
    vtkColorTransferFunction,
    vtkVolume,
    vtkPropAssembly,
    vtkImageActor,
    vtkProperty
)
from vtkmodules.vtkCommonMath import (
    vtkMatrix4x4,
)
from vtkmodules.vtkCommonTransforms import vtkTransform

from vtkmodules.vtkFiltersSources import (
    vtkSphereSource
)

from vtkmodules.vtkFiltersCore import (
    vtkAppendPolyData,
    vtkPolyDataNormals,
    vtkCutter,
    vtkStripper
)

from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
from vtkmodules.vtkCommonDataModel import (
    vtkPiecewiseFunction,
    vtkPlane
)


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


class ResliceMatrix:
    Axial_Matrix = [
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1]

    Coronal_Matrix = [
        1, 0, 0, 0,
        0, 0, -1, 0,
        0, 1, 0, 0,
        0, 0, 0, 1]

    Sagittal_Matrix = [
        0, 0, 1, 0,
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 0, 1]


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

    def set_node(self, node):
        self.node = node

    @abstractmethod
    def get_prop(sel, renderer):
        return None

    @abstractmethod
    def initialize_mapper(self, renderer):
        pass

    @abstractmethod
    def generate_data_for_renderer(self, renderer):
        pass

    def _apply_actor_properties(self, renderer):
        if self.node and self.get_prop(renderer):
            visbile = self.node.get("visible")
            if visbile:
                self.get_prop(renderer).SetVisibility(visbile)


class SurfaceMapper3D(MapperBase):
    class LocalStorage:
        def __init__(self):
            self.mapper = vtkPolyDataMapper()
            self.actor = vtkActor()
            self.actor.SetMapper(self.mapper)

    def __init__(self):
        MapperBase.__init__(self)
        self.lsh = LocalStroageHandler(SurfaceMapper3D.LocalStorage)

    def get_prop(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        return ls.actor

    def set_node(self, node):
        MapperBase.set_node(self, node)
        node["representation"] = Representation.Surface

    def initialize_mapper(self, renderer):
        pass

    def _apply_actor_properties(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        MapperBase._apply_actor_properties(self, renderer)
        opacity = self.node.get("opacity")
        if opacity:
            self.get_prop(renderer).GetProperty().SetOpacity(
                opacity)

        color = self.node.get("color")
        if color:
            self.get_prop(renderer).GetProperty().SetColor(
                color[0], color[1], color[2])
            if len(color) == 4:
                self.get_prop(renderer).GetProperty().SetOpacity(color[3])

        if "representation" in self.node.properties:
            update_representation(
                self.get_prop(renderer), self.node.get("representation"))
            
        # self.get_prop(renderer).GetProperty().SetInterpolationToPBR()
        # self.get_prop(renderer).GetProperty().SetMetallic(0.5)
        # self.get_prop(renderer).GetProperty().SetRoughness(0.0)

    def generate_data_for_renderer(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop(renderer).VisibilityOff()
            return
        else:
            self.get_prop(renderer).VisibilityOn()
        data = self.node.get_data()
        if data and data.type == DataType.Surface:
            if ls.mapper.GetInput() != data.get_polydata():
                # normals = vtkPolyDataNormals()
                # normals.SetInputData(data.get_polydata())
                # self.mapper.SetInputConnection(normals)
                ls.mapper.SetInputData(data.get_polydata())
            self._apply_actor_properties(renderer)


class ImageMapper3D(MapperBase):
    class LocalStorage:
        def __init__(self):
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

    def __init__(self):
        MapperBase.__init__(self)
        self.lsh = LocalStroageHandler(ImageMapper3D.LocalStorage)

    def get_prop(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        return ls.volume
    
    vtkImageData.GetDirectionMatrix

    def initialize_mapper(self, renderer):
        pass

    def _apply_actor_properties(self, renderer):
        MapperBase._apply_actor_properties(self, renderer)
        ls = self.lsh.get_local_storage(renderer)
        color_function = self.node.get("color_function")
        if color_function:
            ls.volume_property.SetColor(color_function)

        opacity_function = self.node.get("opacity_function")
        if opacity_function:
            ls.volume_property.SetScalarOpacity(opacity_function)

    def generate_data_for_renderer(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop(renderer).VisibilityOff()
            return
        else:
            self.get_prop(renderer).VisibilityOn()

        scalar_opacity = self.node.get("scalar_opacity")
        if scalar_opacity:
            opacity_function = ls.volume_property.GetScalarOpacity()
            opacity_function.RemoveAllPoints()
            for scalar, opacity in scalar_opacity:
                opacity_function.AddPoint(scalar, opacity)

        colors = self.node.get("colors")
        if colors:
            color_function = vtkColorTransferFunction()
            for color in colors:
                color_function.AddRGBPoint(
                    color[0], color[1], color[2], color[3])
            ls.volume_property.SetColor(color_function)

        data = self.node.get_data()
        if data and data.type == DataType.Image:
            if ls.mapper.GetInput() != data.get_image():
                ls.mapper.SetInputData(data.get_image())
            self._apply_actor_properties(renderer)


class PointSetMapper3D(MapperBase):
    class LocalStorage:
        def __init__(self):
            self.assembly = vtkPropAssembly()
            self.mapper = vtkPolyDataMapper()
            self.actor = vtkActor()
            self.actor.SetMapper(self.mapper)
            self.assembly.AddPart(self.actor)

    def __init__(self):
        MapperBase.__init__(self)
        self.lsh = LocalStroageHandler(PointSetMapper3D.LocalStorage)

    def get_prop(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        data = self.node.get_data()
        if len(data) > 0:
            return ls.assembly
        else:
            return None

    def set_node(self, node):
        MapperBase.set_node(self, node)
        node["pointsize"] = 2.0

    def initialize_mapper(self, renderer):
        pass

    def _apply_actor_properties(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        MapperBase._apply_actor_properties(self, renderer)
        opacity = self.node.get("opacity")
        if opacity:
            ls.actor.GetProperty().SetOpacity(
                opacity)

        unselectedcolor = self.node.get("unselectedcolor")
        if not unselectedcolor:
            unselectedcolor = [1.0, 1.0, 0.0, 1.0]
        ls.actor.GetProperty().SetColor(
            unselectedcolor[0], unselectedcolor[1], unselectedcolor[2])
        if len(unselectedcolor) == 4:
            ls.actor.GetProperty().SetOpacity(unselectedcolor[3])

        representation = self.node.get("representation")
        if representation:
            update_representation(ls.actor, representation)

    def generate_data_for_renderer(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        if not self.node:
            return

        data = self.node.get_data()
        if len(data) == 0:
            return

        if not self.node.get("visible"):
            ls.actor.VisibilityOff()
            return
        else:
            ls.actor.VisibilityOn()

        if data and data.type == DataType.PointSet:
            if ls.mapper.GetInput() != data.get_pointset():
                radius = self.node.get("pointsize")
                if not radius:
                    radius = 2.0
                appender = vtkAppendPolyData()
                for point in data.get_points_array():
                    sphere_source = vtkSphereSource()
                    sphere_source.SetCenter(point[0], point[1], point[2])
                    sphere_source.SetRadius(radius)
                   # appender.AddInputConnection(sphere_source.GetOutputPort())
                    ls.mapper.SetInputConnection(
                        sphere_source.GetOutputPort())
                # self.mapper.SetInputConnection(appender.GetOutputPort())
            self._apply_actor_properties(renderer)


class ImageMapper2D(MapperBase):
    class LocalStorage:
        def __init__(self):
            self.image_actor = vtkImageActor()
            self.reslice = vtkImageReslice()
            self.matrix = vtkMatrix4x4()

    def __init__(self):
        MapperBase.__init__(self)
        self.current_image = None
        self.lsh = LocalStroageHandler(ImageMapper2D.LocalStorage)

    def get_prop(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        return ls.image_actor

    def set_reslice_matrix(self, matrix, renderer):
        ls = self.lsh.get_local_storage(renderer)
        ls.matrix.SetData(matrix)

    def initialize_mapper(self, renderer):
        pass

    def generate_data_for_renderer(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop(renderer).VisibilityOff()
            return
        else:
            self.get_prop(renderer).VisibilityOn()

        data = self.node.get_data()
        if data and data.type == DataType.Image:
            image = data.get_image()
            ls.reslice.SetInputData(image)
            ls.reslice.SetOutputDimensionality(2)
            ls.reslice.SetResliceAxes(ls.matrix)
            ls.reslice.SetInterpolationModeToLinear()
            ls.reslice.Update()

            # from mipf.core.utils import save_image
            # save_image(ls.reslice.GetOutput(),f"D:/slice.mha")

            ls.image_actor.SetInputData(ls.reslice.GetOutput())
            
            trans = vtkTransform()
            matrix = ls.reslice.GetResliceAxes()
            trans.SetMatrix(matrix)
            ls.image_actor.SetUserTransform(trans)        

            self._apply_actor_properties(renderer)


class SurfaceMapper2D(MapperBase):
    class LocalStorage:
        def __init__(self):
            self.mapper = vtkPolyDataMapper()
            self.actor = vtkActor()
            self.actor.GetProperty().SetLighting(False)
            self.actor.SetMapper(self.mapper)
            self.matrix = vtkMatrix4x4()
            self.plane = vtkPlane()
            self.cutter = vtkCutter()
            self.cutter.SetCutFunction(self.plane)
            self.mapper.SetInputConnection(self.cutter.GetOutputPort())
            

    def __init__(self):
        MapperBase.__init__(self)
        self.lsh = LocalStroageHandler(SurfaceMapper2D.LocalStorage)

    def set_reslice_matrix(self, matrix, renderer):
        ls = self.lsh.get_local_storage(renderer)
        ls.matrix.SetData(matrix)

    def get_prop(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        return ls.actor

    def set_node(self, node):
        MapperBase.set_node(self, node)

    def initialize_mapper(self, renderer):
        pass

    def _apply_actor_properties(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        MapperBase._apply_actor_properties(self, renderer)
        opacity = self.node.get("opacity")
        if opacity:
            self.get_prop(renderer).GetProperty().SetOpacity(
                opacity)

        color = self.node.get("color")
        if color:
            self.get_prop(renderer).GetProperty().SetColor(
                color[0], color[1], color[2])
            if len(color) == 4:
                self.get_prop(renderer).GetProperty().SetOpacity(color[3])
        
        line_width = self.node.get("line_width")
        if line_width:  
            self.get_prop(renderer).GetProperty().SetLineWidth(line_width)
        else:
            self.get_prop(renderer).GetProperty().SetLineWidth(2)

    def generate_data_for_renderer(self, renderer):
        ls = self.lsh.get_local_storage(renderer)
        if not self.node:
            return
        if not self.node.get("visible"):
            self.get_prop(renderer).VisibilityOff()
            return
        else:
            self.get_prop(renderer).VisibilityOn()
        data = self.node.get_data()
        if data and data.type == DataType.Surface:
            if ls.mapper.GetInput() != data.get_polydata():      
                ls.plane.SetOrigin(
                    ls.matrix.GetElement(0, 3),
                    ls.matrix.GetElement(1, 3),
                    ls.matrix.GetElement(2, 3)
                )
                ls.plane.SetNormal(
                    ls.matrix.GetElement(0, 2),
                    ls.matrix.GetElement(1, 2),
                    ls.matrix.GetElement(2, 2)
                )
                ls.cutter.SetInputData(data.get_polydata())
                
            self._apply_actor_properties(renderer)
