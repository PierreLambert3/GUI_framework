import multiprocessing
import queue
import pygfx as gfx
from rendercanvas.auto import RenderCanvas, loop
from engine.elements.container import Container
from engine.ENGINE_CONSTANTS import FPS_FAST, FPS_SLOW, FPS_VSLOW

"""
An Event: sends a notification to its listeners when triggered.
"""
class Event:

    """
    to_notify: list of Listeners to notify when the event is triggered
    """
    def __init__(self, listener_to_notify=None, identifier=None):
        self.to_notify  = [] if listener_to_notify is None else [listener_to_notify]
        self.identifier = identifier

    def add_listener(self, listener):
        self.to_notify.append(listener)
    
    # ex: event.trigger(arg1='thing', arg2=42)
    def trigger(self, **kwargs):
        for listener in self.to_notify:
            listener.notify(self.identifier, **kwargs)

"""
A Listener: listens to Events and reacts when notified.
"""
class Listener:

    def __init__(self, callback):
        self.callback = callback

    def notify(self, event_identifier, **kwargs):
        self.callback(event_identifier, **kwargs)

"""
A value that is safe to access from multiple threads/processes.
"""
class Shared_Variable:
    def __init__(self, ctx, initial_value=None, lock=None):
        self._value = initial_value
        self._lock  = lock if lock is not None else ctx.Lock()

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value):
        with self._lock:
            self._value = new_value


class Screen:

    """ Singleton """
    _instance = None
    def __new__(cls, W_px, H_px, title="GUI Screen"):
        if cls._instance is None:
            cls._instance = super(Screen, cls).__new__(cls)
        return cls._instance

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


"""
This class is inherited by the main application
This is where the engine interacts with the application
"""
class Base_Front_End:
    
    """ Singleton """
    _instance = None
    def __new__(cls, *args, **kwargs):  # accept incoming args/kwargs
        if cls._instance is None:
            cls._instance = super(Base_Front_End, cls).__new__(cls)
        return cls._instance

    def __init__(self, multiprocessing_context, title, width, height):
        self.ctx = multiprocessing_context
        
        # App internals
        self.fps = FPS_FAST
        self.screen = Screen(width, height, title=title)
        self.existing_pages  = []
        self.active_page_idx = -1

        # communications with the back-end process
        self.from_backend = self.ctx.Queue()
        self.to_backend   = self.ctx.Queue()
        self.listeners    = {"worker initialised": Listener(self._launch_front_end_loop)}

        # give the listeners to the back-end process
        # self.to_backend.put(("frontend listeners", self.listeners))
        import numpy as np
        self.to_backend.put(("frontend listeners", np.random.uniform(size=(10,))))

    def _launch_front_end_loop(self, listener_program_closed):
        self.listeners["program closed"] = listener_program_closed
        self.run()

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

class Base_Back_End:

    """ Singleton """
    _instance = None
    def __new__(cls, *args, **kwargs):  # accept incoming args/kwargs
        if cls._instance is None:
            cls._instance = super(Base_Back_End, cls).__new__(cls)
        return cls._instance

    def __init__(self, multiprocessing_context, to_frontend, from_frontend):
        # communications with the front-end process
        self.to_frontend   = to_frontend
        self.from_frontend = from_frontend

        self.worker = multiprocessing_context.Process(
            target=self.run,
            args=(42,),
            name="ExampleWorker",
            daemon=False,
        )
        self.worker.start()

    def run(self, *args):
        # need to notify the front end that the worker is ready
        assert not self.from_frontend.empty(), "from_frontend queue is empty, but it shouldn't be."
        msg, data = self.from_frontend.get()
        print(f"Back_End received message from front end: {msg} with data: {data}")



    def join(self):
        self.worker.join()
            
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
    def W_px(self):
        return self._screen.W_px

    @property
    def H_px(self):
        return self._screen.H_px
    
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