from vtkmodules.vtkInteractionStyle import (
    vtkInteractorStyleTrackballCamera,
    vtkInteractorStyleImage
)
from mipf.core.mapper import *

from mipf.core.render_window_manager import render_window_manager


class ViewDirection(Enum):
    Axial = 1
    Sagittal = 2
    Coronal = 3


class ViewType(Enum):
    View2D = 1
    View3D = 2


class SliceScrollInteractorStyle(vtkInteractorStyleImage):
    def __init__(self, orientation, actors):
        self.orientation = orientation
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)

    def on_scroll_forward(self, obj, event):
        # update_slice(self.orientation, 1)
        print("on_scroll_forward")

    def on_scroll_backward(self, obj, event):
        # update_slice(self.orientation, -1)
        print("on_scroll_backward")


class RenderWindow:
    """
    Render window for data rendering in 2D and 3D
    """

    def __init__(self,
                 data_storage: DataStorage,
                 view_type: ViewType = ViewType.View3D,
                 direction: ViewDirection = ViewDirection.Axial
                 ):
        self.vtk_render_window = vtkRenderWindow()
        self.vtk_render_window.OffScreenRenderingOn()
        self.renderer = vtkRenderer()
        self.vtk_render_window.AddRenderer(self.renderer)
        self.view_type = view_type
        self.direction = direction
        self.data_storage = data_storage

        render_window_manager.add_renderwindow(self)

    def get_renderer(self):
        return self.renderer

    def set_depth_peeling(self, flag):
        self.renderer.SetUseDepthPeeling(flag)

    def get_vtk_render_window(self):
        return self.vtk_render_window

    def get_active_camera(self):
        return self.renderer.GetActiveCamera()

    def set_view_direction(self, view_direction: ViewDirection):
        self.direction = view_direction

    def set_view_type(self, view_type: ViewType):
        self.view_type = view_type

    def set_background_color(self, color):
        self.renderer.SetBackground(color[0], color[1], color[1])

    def _get_direction_cosines(self):
        if self.direction == ViewDirection.Axial:
            return [1, 0, 0, 0, 1, 0, 0, 0, 1]
        elif self.direction == ViewDirection.Sagittal:
            return [0, 1, 0, 0, 0, 1, 1, 0, 0]
        elif self.direction == ViewDirection.Coronal:
            return [1, 0, 0, 0, 0, 1, 0, 1, 0]

    def _set_default_mapper3D(self, node):
        data = node.get_data()
        if data.type.value == DataType.Surface.value:
            return SurfaceMapper3D(node)
        elif data.type.value == DataType.Image.value:
            return ImageMapper3D(node)
        else:
            raise TypeError("There is not valid mapper for node ", node.name)

    def update(self):
        for key, node in self.data_storage.nodes.items():
            if self.view_type == ViewType.View3D:
                mapper = node.mappers.get(MapperType.Mapper_3D)
                if not mapper:
                    mapper = self._set_default_mapper3D(node)
                mapper.generate_data_for_renderer()
                self.renderer.AddViewProp(mapper.get_prop())
        self.vtk_render_window.Render()

    def setup(self):
        if self.view_type == ViewType.View2D:
            direction = [1, 0, 0, 0, 1, 0, 0, 0, 1]
            if self.direction == ViewDirection.Axial:
                direction = [1, 0, 0, 0, 1, 0, 0, 0, 1]
            elif self.direction == ViewDirection.Sagittal:
                direction = [0, 1, 0, 0, 0, 1, 1, 0, 0]
            elif self.direction == ViewDirection.Coronal:
                direction = [1, 0, 0, 0, 0, 1, 0, 1, 0]

            interactor = vtkRenderWindowInteractor()
            interactor.SetRenderWindow(self.vtk_render_window)
            # interactor_style = SliceScrollInteractorStyle(direction, renderer.GetActors())
            # interactor.SetInteractorStyle(interactor_style)
            self.renderer.ResetCamera()
        else:
            trackball_style = vtkInteractorStyleTrackballCamera()
            interactor_3d = vtkRenderWindowInteractor()
            interactor_3d.SetRenderWindow(self.vtk_render_window)
            interactor_3d.SetInteractorStyle(trackball_style)
            self.renderer.ResetCamera()

        self.update()
