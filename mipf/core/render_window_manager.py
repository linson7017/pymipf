class RenderWindowManager:
    """
    Render window manager.
    """

    def __init__(self):
        self.render_windows = set()

    def add_renderwindow(self, render_window):
        self.render_windows.add(render_window)

    def request_update_all(self):
        for render_window in self.render_windows:
            render_window.update()


render_window_manager = RenderWindowManager()
