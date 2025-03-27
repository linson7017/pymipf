from mipf.core.render_window import *
from mipf.core.data import *
from mipf.core.utils import *
from mipf.core.settings import *
from mipf.ui.data import *
from mipf.ui.engine import *
from abc import ABC, abstractmethod

class AppBase(ABC):
    def __init__(self, server, app_name="Undefined"):
        self.server = server
        self.app_name = app_name
        self.data_storage = DataStorage()
    
    @abstractmethod
    def setupui(self):
        pass

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller
    
    def load(self, filename: str, name="undefined"):
        if filename.endswith('nii') or filename.endswith('nii.gz') or \
                filename.endswith('vti') or filename.endswith('mha') or \
                filename.endswith('nrrd'):
            node = import_image_file(filename, name)
            self.data_storage.add_node(node)
            render_window_manager.request_update_all()
            if self.server.protocol:
                self.ctrl.reset_camera()
                self.ctrl.view_update()
        elif filename.endswith('vtp') or filename.endswith('stl'):
            node = import_surface_file(filename, name)
            self.data_storage.add_node(node)
            render_window_manager.request_update_all()
            if self.server.protocol:
                self.ctrl.reset_camera()
                self.ctrl.view_update()
        else:
            print("Not a supported file ",filename)