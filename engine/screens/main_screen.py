from engine.gui.container import Container
from engine.gui.scatterplot import Scatterplot, Heatmap
from engine.gui.window import Window
from engine.gui.selector import  Button, Mutex_with_title, String_selector, Number_selector, Mutex_choice, Scrollable_bundle
from engine.gui.listener import Listener
from engine.gui.event_ids import *
from utils import random_colors
from utils import luminosity_change
import numpy as np

class Main_screen():
    def __init__(self, theme, window, manager):
        self.manager = manager
        self.color = theme["color"]; self.background_color = theme["background"]
        self.eight_colors = random_colors(8)
        self.main_view   = Container((0,0), (0.745, 0.75), "main_area", window, manager.uid_generator, color=theme["color"], background_color=theme["background"], filled=True)
        window.add_container(self.main_view)

    def schedule_draw(self, to_redraw, all = False):
        if all:
            self.main_view.schedule_draw(to_redraw)

    def ctrl_press(self, dataset_name):
        print("ctrl press in Main_screen() class")

    def ctrl_unpress(self, dataset_name):
        print("ctrl unpress in Main_screen() class")