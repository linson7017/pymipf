from vtkmodules.vtkInteractionStyle import (
    vtkInteractorStyleTrackballCamera,
    vtkInteractorStyleImage
)
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkPropPicker,
    vtkCellPicker,
    vtkCamera
)

from mipf.core.mapper import *
from mipf.core.data import DataStorage
from mipf.core.render_window_manager import render_window_manager
from mipf.core.mapper_mananger import mapper_manager
from mipf.core.settings import *


class ViewDirection(Enum):
    Axial = 1
    Sagittal = 2
    Coronal = 3


class ViewType(Enum):
    View2D = 1
    View3D = 2


class ImageInteractor2D(vtkInteractorStyleImage):
    def __init__(self, orientation, render_window):
        self.orientation = orientation
        self.render_window = render_window
        self.actions = {}
        self.actions["Slicing"] = 0
        self.step_size = 1.0
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)

    def on_scroll_forward(self, obj, event):
        self.update_slice(self.orientation, 1)

    def on_scroll_backward(self, obj, event):
        self.update_slice(self.orientation, -1)

    def update_slice(self, orientation, step):
        if self.orientation == ViewDirection.Axial:
            self.render_window.shift[2] += step*self.step_size
        elif self.orientation == ViewDirection.Sagittal:
            self.render_window.shift[0] += step*self.step_size
        elif self.orientation == ViewDirection.Coronal:
            self.render_window.shift[1] += step*self.step_size

        self.render_window.update()


class RenderWindow:
    """
    Render window for data rendering in 2D and 3D
    """

    def __init__(self,
                 data_storage: DataStorage,
                 view_type: ViewType = ViewType.View3D,
                 direction: ViewDirection = ViewDirection.Axial,
                 use_plotter: bool = False,
                 ):
        if not use_plotter:
            self.vtk_render_window = vtkRenderWindow()
            self.renderer = vtkRenderer()
            self.vtk_render_window.AddRenderer(self.renderer)
            self.vtk_render_window.OffScreenRenderingOn()
            self.plotter = None
        else:
            import pyvista as pv
            self.plotter = pv.Plotter(off_screen=True)
            self.vtk_render_window = self.plotter.render_window
            self.renderer = self.plotter.renderer
            self.plotter.add_axes()
            # self.plotter.add_box_axes()
            
        if view_type == ViewType.View3D:
            self.set_background_color(general_settings.background_color_3d)
        else:
            self.set_background_color(general_settings.background_color_2d)
        
        # self.picker = vtkPropPicker()
        self.picker = vtkCellPicker()
        self.view_type = view_type
        self.direction = direction
        self.data_storage = data_storage
        self.shift = [0, 0, 0]
        self.interactor_style = None

        render_window_manager.add_renderwindow(self)

    def get_renderer(self) -> vtkRenderer:
        return self.renderer

    def set_depth_peeling(self, flag):
        self.renderer.SetUseDepthPeeling(flag)

    def get_vtk_render_window(self) -> vtkRenderWindow:
        return self.vtk_render_window

    def get_active_camera(self) -> vtkCamera:
        return self.renderer.GetActiveCamera()

    def get_plotter(self):
        return self.plotter

    def set_view_direction(self, view_direction: ViewDirection):
        self.direction = view_direction

    def set_view_type(self, view_type: ViewType):
        self.view_type = view_type

    def set_background_color(self, color):
        if not self.plotter:
            self.renderer.SetBackground(color[0], color[1], color[1])
        else:
            self.renderer.set_background(color)

    def pick(self, position):
        ret = self.picker.Pick(position.get(
            "x"), position.get("y"), 0, self.renderer)
        if ret != 0:
            return self.picker.GetPickPosition()
        else:
            return None

    def _get_direction_matrix(self):
        matrix = None
        if self.direction == ViewDirection.Axial:
            matrix = ResliceMatrix.Axial_Matrix
        elif self.direction == ViewDirection.Sagittal:
            matrix = ResliceMatrix.Sagittal_Matrix
        elif self.direction == ViewDirection.Coronal:
            matrix = ResliceMatrix.Coronal_Matrix
        else:
            raise ValueError(f"Invalid direction {self.direction}!")

        matrix[3] = self.shift[0]
        matrix[7] = self.shift[1]
        matrix[11] = self.shift[2]
        return matrix

    def _get_default_mapper3D(self, node):
        data = node.get_data()
        if data.type.value == DataType.Surface.value:
            return SurfaceMapper3D()
        elif data.type.value == DataType.Image.value:
            return ImageMapper3D()
        elif data.type.value == DataType.PointSet.value:
            return PointSetMapper3D()
        else:
            raise TypeError(
                "There is not valid mapper for node ", node.get("name"))

    def _get_default_mapper2D(self, node):
        data = node.get_data()
        if data.type.value == DataType.Surface.value:
            return SurfaceMapper2D()  # not support yet
        elif data.type.value == DataType.Image.value:
            return ImageMapper2D()
        elif data.type.value == DataType.PointSet.value:
            return None  # not support yet
        else:
            raise TypeError(
                "There is not valid mapper for node ", node.get("name"))

    def test(self):
        print("test")

    def reset_camera(self, node=None):
        if self.view_type == ViewType.View3D:
            self.renderer.ResetCamera()
            self.vtk_render_window.Render()
        else:
            camera = self.get_active_camera()
            bounds = self.data_storage.get_bounds()
            center = self.data_storage.get_center()
            self.renderer.ResetCamera()

            camera.SetFocalPoint(center)
            camera.SetClippingRange(0.1, 1000000);
            if self.direction == ViewDirection.Axial:
                camera.SetParallelScale((bounds[3] - bounds[2]) / 2)
                camera.SetViewUp(0,-1,0)
                camera.SetPosition(center[0], center[1], -100000)
                self.shift[2] = center[2]
            elif self.direction == ViewDirection.Sagittal:
                camera.SetParallelScale((bounds[5] - bounds[4]) / 2)
                camera.SetViewUp(0,0,1)
                camera.SetPosition(100000,center[1],center[2])
                self.shift[0] = center[0]
            elif self.direction == ViewDirection.Coronal:
                camera.SetParallelScale((bounds[5] - bounds[4]) / 2)
                camera.SetViewUp(0,0,1)
                camera.SetPosition(center[0],-100000,center[2])
                self.shift[1] = center[1]
                
            #self.renderer.ResetCameraClippingRange()
            self.update()

    def update(self):
        for key, node in self.data_storage.nodes.items():
            if self.view_type == ViewType.View3D:
                mapper = mapper_manager.get_mapper(node, MapperType.Mapper_3D)
                if not mapper:
                    mapper = self._get_default_mapper3D(node)
                    if mapper:
                        mapper_manager.set_mapper(
                            node, mapper, MapperType.Mapper_3D)
                if mapper:
                    mapper.generate_data_for_renderer(self.renderer)
                    self.renderer.AddViewProp(mapper.get_prop(self.renderer))
            elif self.view_type == ViewType.View2D:
                mapper = mapper_manager.get_mapper(node, MapperType.Mapper_2D)
                if not mapper:
                    mapper = self._get_default_mapper2D(node)
                    if mapper:
                        mapper_manager.set_mapper(
                            node, mapper, MapperType.Mapper_2D)
                if mapper:
                    mapper.set_reslice_matrix(
                        self._get_direction_matrix(), self.renderer)
                    mapper.generate_data_for_renderer(self.renderer)
                    self.renderer.AddViewProp(mapper.get_prop(self.renderer))
        self.vtk_render_window.Render()

    def setup(self):
        if self.view_type == ViewType.View2D:
            self.interactor_style = ImageInteractor2D(self.direction, self)
            interactor = vtkRenderWindowInteractor()
            interactor.SetRenderWindow(self.vtk_render_window)
            interactor.SetInteractorStyle(self.interactor_style)
            self.get_active_camera().ParallelProjectionOn()
            self.renderer.ResetCamera()
            self.update()
        else:
            self.interactor_style = vtkInteractorStyleTrackballCamera()
            interactor = vtkRenderWindowInteractor()
            interactor.SetRenderWindow(self.vtk_render_window)
            interactor.SetInteractorStyle(self.interactor_style)
            self.renderer.ResetCamera()
            self.update()
