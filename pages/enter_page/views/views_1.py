from engine.app_bases import Base_View
from engine.elements.scatterplot import Scatterplot
from engine.elements.container import Container

class Example_View(Base_View):
    def __init__(self, page, view_name, W_px=None, H_px=None):
        super().__init__(page, view_name, W_px, H_px)

        buttons_container     = Container(0.0, 0.0, 1.0, 0.1, self)
        scatterplot_container = Container(0.0, 0.1, 1.0, 0.9, self)
