"""
Keeps track of all registered events.
"""
class Event_Manager:

    """ Singleton creation """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Event_Manager, cls).__new__(cls)
        else:
            print("Warning: Event_Manager is a singleton class. Returning the existing instance.")
        return cls._instance
    
    def __init__(self):
        self._events = []
        self._event_ids = []
        self._event_counter = 0
        self._uuid = 0

    def register(self, event):
        self._events.append(event)
        self._event_counter += 1
        event.set_id(self._uuid)
        self._uuid += 1
    
    def unregister(self, event):
        self._events.remove(event)
        self._event_counter -= 1

    @property
    def events(self):
        return self._events

"""
An Event: sends a notification to its listeners when triggered.
On instanciation, registers itself to the Event_Manager singleton.
"""
class Base_Event:

    """
    to_notify: list of Listeners to notify when the event is triggered
    """
    def __init__(self, listeners_to_notify=None):
        if listeners_to_notify is None:
            listeners_to_notify = []
        self.to_notify = listeners_to_notify
        self._id = None
        Event_Manager().register(self)

    def add_listener(self, listener):
        self.to_notify.append(listener)
    
    # ex: event.trigger(arg1='thing', arg2=42)
    def trigger(self, **kwargs):
        for listener in self.to_notify:
            listener.notify(self, **kwargs)

"""
A Listener: listens to Events and reacts when notified.
"""
class Base_Listener:

    def __init__(self, callback):
        self.callback = callback

    def notify(self, event, **kwargs):
        self.callback(event, **kwargs)