"""
run with "python -m app"
"""
from engine.app_bases import Base_Front_End, Base_Back_End, Event, Listener
from pages.enter_page.page import Example_Page
import multiprocessing
import time

class Front_End(Base_Front_End):
    def __init__(self, multiprocessing_context, title="Example Application", width=1024, height=768):
        super().__init__(multiprocessing_context, title, width, height)
        self.current_page = Example_Page(self.screen)

    def update(self):
        return super().update()

class Back_End(Base_Back_End):
    def __init__(self, multiprocessing_context):
        super().__init__(multiprocessing_context)

    def run(self):
        super().run()


def _back_end_process(front_end):
    back_end = Back_End()
    back_end.run()

    # Event(listener_to_notify=front_end.listeners["worker initialised"]).trigger()


if __name__ == "__main__":
    
    # Set up multiprocessing context
    ctx = multiprocessing.get_context("spawn")
    ctx.freeze_support()

    # Create the front-end 
    front_end = Front_End(multiprocessing_context = ctx)

    # Launch back-end worker process
    back_end = Back_End(multiprocessing_context = ctx)

    back_end.join() 