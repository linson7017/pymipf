import time
from pathlib import Path
from trame.assets.local import LocalFileManager
from trame.widgets import html,vuetify, trame, vtk
from trame.assets.local import LocalFileManager

from mipf.core.render_window import RenderWindow,ViewType,ViewDirection
from mipf.core.data import DataType

    

class SliceNavigatorSlider:
    def __init__(self, state, ctrl, render_window:RenderWindow):
        if self.render_window.view_type != ViewType.View2D:
            raise ValueError("SliceNavigatorSlider can only binded to 2D renderwindow!")
            return  
        self.state = state
        self.ctrl = ctrl
        self.current_index = 0
        self.name = id(render_window)
        self.ui = self._setup_ui()
        self.render_window = render_window
        ctrl.data_storage_changed.add(self._update)

    def __call__(self, *args, **kwds):
        return self.ui
    
    def _update(self):
        node = self.render_window.data_storage.get_top_node(DataType.Image)
        if node:
            image = node.get_data().get_image()
            dimensions = image.GetDimensions()
            if self.orientation == ViewDirection.Axial:
                self.state[f"slice_number_{self.name}"] = dimensions[2]
            elif self.orientation == ViewDirection.Sagittal:
                self.state[f"slice_number_{self.name}"] = dimensions[0]     
            elif self.orientation == ViewDirection.Coronal:
                self.state[f"slice_number_{self.name}"] = dimensions[1]    
                

    def _setup_ui(self):
        @self.state(f"current_{self.name}_slice")
        def current_slice_changed():
            # if self.orientation == ViewDirection.Axial:
            #     self.render_window.shift[2] = 1*self.step_size
            # elif self.orientation == ViewDirection.Sagittal:
            #     self.render_window.shift[0] = 1*self.step_size
            # elif self.orientation == ViewDirection.Coronal:
            #     self.render_window.shift[1] = 1*self.step_size
            
            # self.render_window.update()
        
            vuetify.VSlider(hide_details=True,
                        v_model=(f"current_{self.name}_slice", 0),
                        max=(f"slice_number_{self.name}", 0),
                        min=0,
                        step=1,)
        
        
        