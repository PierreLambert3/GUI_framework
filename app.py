"""
run with "python -m app"
"""
from engine.app_bases import Base_Front_End, Base_Back_End, Listener
from pages.enter_page.page import Example_Page
import multiprocessing
import time

class Front_End(Base_Front_End):
    def __init__(self, multiprocessing_context, title="Example Application", width=1024, height=768):
        super().__init__(multiprocessing_context, title, width, height)
        self.add_page(Example_Page(self.screen, "entry page"))

    def update(self):
        return super().update()

class Back_End(Base_Back_End):
    def __init__(self, multiprocessing_context, to_frontend, from_frontend):
        super().__init__(multiprocessing_context, to_frontend, from_frontend)
        
        # Launch the back end process
        self.worker = multiprocessing_context.Process(
            target=self.launch_process,
            args=(42,),
            name="ExampleWorker",
            daemon=False,
        )
        self.worker.start()

    def page_dispatcher(self):
        while 1:
            self.send("pagename request")
            pagename_received = False
            while not pagename_received:
                time.sleep(0.1)
                print("waiting for page name")
                while not self.from_frontend.empty():
                    msg, data = self.from_frontend.get()
                    if msg == "pagename received":
                        pagename_received = True
                    else: # re-iterate the demand (in case the request was dropped, should not be happening)
                        if self.to_frontend.empty():
                            self.send("pagename request")
                    self.listeners[msg](data)
            
            if self.pagename_now == "entry page":
                self.loop_entry_page()
            else:
                self._exit_program("received an unknown page name from front end: " + str(self.pagename_now))

    def loop_entry_page(self):
        print("entering entry page")
        page_changed = False
        while not page_changed:
            ... # work here
            while not self.to_frontend.empty():
                msg, data = self.from_frontend.get()
                self.listeners[msg]()

    def launch_process(self, *args):
        # 1. This verifies that the front-end is initialised and ready
        front_end_ready = super().launch_process()
        if not front_end_ready:
            return

        # 2. initialise things in the back-end
        time.sleep(0.1)

        # 3. signal front-end that the back end is ready
        self.send("back-end initialised")
        print("send : back-end initialised")

        # 4. wait for front-end acknowledgement of loop launching
        waiting_length = 0.0
        while self.from_frontend.empty():
            time.sleep(0.1)
            waiting_length += 0.1
            if waiting_length > 5.0:
                self._exit_program()
                return
        msg, data = self.from_frontend.get()
        assert self.from_frontend.empty(), "front end posted multiple messages when only waiting for 'front-end main loop launching'"
        assert msg == "front-end main loop launching", "expected message from front end: 'front-end main loop launching' but received: " + str(msg)

        # 5. launch main loop
        self.pagename_now = "entry page"
        self.page_dispatcher()

if __name__ == "__main__":
    
    # Set up multiprocessing context
    ctx = multiprocessing.get_context("spawn")
    ctx.freeze_support()

    # Create the front-end 
    front_end = Front_End(multiprocessing_context = ctx)

    # Launch back-end worker process
    back_end  = Back_End(multiprocessing_context = ctx, to_frontend=front_end.from_backend, from_frontend=front_end.to_backend)

    front_end.wait_for_backend_ready()
    back_end.join() 