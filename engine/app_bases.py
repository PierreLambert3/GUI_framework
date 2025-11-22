import multiprocessing
import queue
import pygfx as gfx
from rendercanvas.auto import RenderCanvas, loop
from engine.elements.container import Container
from engine.ENGINE_CONSTANTS import FPS_FAST, FPS_SLOW, FPS_VSLOW
import time

# """
# An Event: sends a notification to its listeners when triggered.
# """
# class Event:

#     """
#     to_notify: list of Listeners to notify when the event is triggered
#     """
#     def __init__(self, listener_to_notify=None, identifier=None):
#         self.to_notify  = [] if listener_to_notify is None else [listener_to_notify]
#         self.identifier = identifier

#     def add_listener(self, listener):
#         self.to_notify.append(listener)
    
#     # ex: event.trigger(arg1='thing', arg2=42)
#     def trigger(self, **kwargs):
#         for listener in self.to_notify:
#             listener.notify(self.identifier, **kwargs)

"""
A Listener: listens to Events and reacts when notified.
for the front end and the back end, the Liteners are expected to be srored in a dictionnary, so that the key can be used by the event maker
"""
class Listener:

    def __init__(self, callback):
        self.callback = callback

    def notify(self, *args):
        self.callback(*args)

    def __call__(self, *args):
        self.callback(*args)


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
        self.listeners    = {
            "back-end initialised": Listener(self._launch_main_loop),
            "exit program": Listener(self._exit_program),
            "pagename request": Listener(self._send_pagename)
            }

        # alive signal for the backend
        self.send("front-end alive")

    def add_page(self, page):
        self.existing_pages.append(page)
    
    def change_page(self, pagename):
        found_idx = -1
        for idx, page in enumerate(self.existing_pages):
            if page.name == pagename:
                found_idx = idx
        if found_idx < 0:
            self._exit_program("change page to a name that does not exist")
        self.active_page_idx = found_idx
    
    @property
    def pagename(self):
        if len(self.existing_pages) < 1:
            self._exit_program("current page querried but no pages exist")
        return self.existing_pages[self.active_page_idx].name

    def _exit_program(self, message="exiting program (no message)"):
        print(message)
        self.send("exit program")
        print("TODO: graceful close, front-end")
        1/0

    def update(self):
        # print("Override this for screen updates.")
        pass
    
    """ Internal animation loop - called before each render. """
    def one_frame(self):
        # 2. check & react to events
        while not self.from_backend.empty():
            msg, data = self.from_backend.get()
            self.listeners[msg]()

        # 2. update screen
        self.update()

        # 3. render & schedule next render
        self.screen.render()
        self._schedule_next_frame()

    def run(self):
        """Start the main loop."""
        self._schedule_next_frame() # the first frame to kick things off
        loop.run()

    def _schedule_next_frame(self):
        loop.call_later(1.0 / max(1e-6, self.fps), self.screen.canvas.request_draw, self.one_frame)

    def _launch_main_loop(self):
        del self.listeners["back-end initialised"]
        self.run()

    def wait_for_backend_ready(self):
        # 1. wait for back-end to be ready
        while self.from_backend.empty():
            time.sleep(0.1)
        msg, data = self.from_backend.get()
        assert self.from_backend.empty(), "back end sent multiple messages to front end when signaling init finished"
        assert msg == "back-end initialised", "expecting message: 'back-end initialised', but received: "+str(msg)
        # 2. Acknowledge receipt & indicate that front-end main loop is launching
        self.send("front-end main loop launching")
        # 3. Launch main loop
        self.listeners[msg]()

    def set_fps(self, fps):
        self.fps = fps

    def _send_pagename(self):
        self.send("pagename received", [self.pagename])

    def send(self, listener_key, parameters = []):
        self.to_backend.put((listener_key, parameters))

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
        self.pagename_now  = "no page"

        self.listeners    = {
            "exit program": Listener(self._exit_program),
            "pagename received": Listener(self._update_page_name)
            }

    def launch_process(self, *args):
        # verify that front-end is alive
        try:
            assert not self.from_frontend.empty(), "from_frontend queue is empty, but it shouldn't be."
            msg, data = self.from_frontend.get()
            assert self.from_frontend.empty(), "front end posted multiple messages when only waiting for 'front-end alive'"
            assert msg == "front-end alive", "front-end message is not the expected 'front-end alive' string"
        except:
            self.send("front end gave no sign of life: exiting program")
            return False
        return True

    def join(self):
        self.worker.join()

    def _exit_program(self, message="exiting program (no message)"):
        self.send("exit program")
        print(message)
        print("TODO: graceful close, front-end")
        1/0
    
    def _update_page_name(self, parameters):
        print("received page name : ", parameters[0])
        self.pagename_now = parameters[0]

    def send(self, listener_key, parameters = []):
        self.to_frontend.put((listener_key, parameters))
        
"""
Contains views
"""
class Base_Page:
    def __init__(self, screen, name):
        self._screen = screen
        self.name    = name
        self._views  = {}
    
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