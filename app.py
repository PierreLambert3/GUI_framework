from engine.app_bases import Base_Application
from pages.enter_page.page import Example_Page
import multiprocessing

class Example_App(Base_Application):
    def __init__(self, title="Example Application", width=1024, height=768):
        super().__init__(width, height)
        self.current_page = Example_Page(self.screen)

    def update(self):
        return super().update()

if __name__ == "__main__":
    app = Example_App()
    app.run()
