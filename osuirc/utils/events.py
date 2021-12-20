from asyncio import Event

class Events:
    def __init__(self, loop) -> None:
        self.loop = loop
    
        self.welcome = Event(loop=self.loop)
        self.motd_start = Event(loop=self.loop)
        self.motd_end = Event(loop=self.loop)