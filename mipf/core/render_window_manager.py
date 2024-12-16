class RenderWindowManager:
    """
    Render window manager.
    """

    def __init__(self):
        self.render_windows = []

    def add_renderwindow(self, render_window):
        self.render_windows.append(render_window)
        
    def get_activate_renderwindow(self):
        if len(self.render_windows)>0:
            return self.render_windows[0]
        else:
            return None

    def request_update_all(self):
        for render_window in self.render_windows:
            render_window.update()


render_window_manager = RenderWindowManager()
