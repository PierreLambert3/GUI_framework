import pygfx as gfx
from rendercanvas.auto import RenderCanvas, loop
from engine.elements.container import Container
from engine.ENGINE_CONSTANTS import FPS_FAST, FPS_SLOW, FPS_VSLOW

class Screen:

    def __init__(self, W_px, H_px, title="GUI Screen"):
        self.W_px = W_px
        self.H_px = H_px

        # pygfx core objects
        self.canvas   = RenderCanvas(title=title, size=(W_px, H_px),
                                    max_fps=FPS_FAST, # ignored: 'ondemand' mode
                                    update_mode='ondemand',
                                    vsync=False)
        self.renderer = gfx.renderers.WgpuRenderer(self.canvas)
        self.scene    = gfx.Scene()
        self.camera   = gfx.PerspectiveCamera(fov=90, aspect=W_px/H_px)
        self.reset_camera()

    def render(self):
        self.renderer.render(self.scene, self.camera)
    
    def reset_camera(self):
        self.camera.local.position = (0, 0, 5)


import time
"""
This class is inherited by the main application
This is where the engine interacts with the application
"""
class Base_Application:
    
    """ Singleton pattern """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Base_Application, cls).__new__(cls)
        return cls._instance

    def __init__(self, width=800, height=600):
        self.fps = FPS_FAST
        self.screen = Screen(width, height, title="GUI Application")
        self.existing_pages  = []
        self.active_page_idx = -1

        self.tic = time.time()

    def update(self):
        print("Override this for screen updates.")
    
    def _schedule_next_frame(self):
        loop.call_later(1.0 / max(1e-6, self.fps), self.screen.canvas.request_draw, self.animate)

    """ Internal animation loop - called before each render. """
    def animate(self):
        self.update()
        self.screen.render()
        self._schedule_next_frame()

    def run(self):
        """Start the main loop."""
        self._schedule_next_frame() # the first frame to kick things off
        loop.run()

    def set_fps(self, fps):
        self.fps = fps

"""
Contains views
"""
class Base_Page:
    def __init__(self, screen):
        self._screen = screen
        self._views = {}
    
    @property
    def size(self):
        return (self._screen.W_px, self._screen.H_px)
    
    @property
    def view(self, view_name):
        return self._views.get(view_name, None)

    def add_view(self, view):
        self._views[view.name] = view



"""
Contains elements
"""
class Base_View:
    def __init__(self, page, view_name, W_rel=1.0, H_rel=1.0):
        self._page = page
        self.name = view_name
        self.W_rel = W_rel
        self.H_rel = H_rel
        self.containers = Container(0.0, 0.0, 1.0, 1.0, self)

    @property
    def size(self):
        return (self.W_px, self.H_px)
    
    @property
    def W_px(self):
        return self._page.W_px * self.W_rel
    
    @property
    def H_px(self):
        return self._page.H_px * self.H_rel
    
    def add_container(self, container):
        self.containers.add_container(container)