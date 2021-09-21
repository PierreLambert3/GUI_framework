from engine.screen_managers.manager import Manager
from engine.gui.listener import Listener
from engine.gui.event_ids import *
from utils import random_colors
import threading
import numpy as np
from engine.screens.main_screen import Main_screen

class Main_manager(Manager):
    def __init__(self, config, main_window, theme, uid_generator):
        super(Main_manager, self).__init__("main", initial_state=True)
        # self.type_identifier = "main manger"
        self.active  = True
        self.deleted = False
        self.theme = theme
        self.main_window        = main_window
        self.main_window.awaiting_key_press.append(self)
        self.uid_generator      = uid_generator
        self.screen             = Main_screen(theme, main_window, self)
        self.lock = threading.Lock()

    def wake_up(self, prev_manager):
        super(Main_manager, self).wake_up(prev_manager)

    def get_notified(self, event_class, id, value, to_redraw = []):
        with self.lock:
            if event_class == "this_event" and not self.ctrl_pressed:
                print("event")

    def on_awaited_key_press(self, to_redraw, pressed_keys, pressed_special_keys):
        if pressed_keys[0] == 'o':
            print("pressed o")
        return False