from engine.app_bases import Base_Page
from pages.enter_page.views.views_1 import Example_View

class Example_Page(Base_Page):
    def __init__(self, screen):
        super().__init__(screen)
        self.add_view(Example_View(self, "main view"))