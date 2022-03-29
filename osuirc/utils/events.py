from asyncio import Event

class ClientEvents:
    def __init__(self, loop) -> None:
        self.loop = loop
    
        self.welcome = Event()
        self.motd_start = Event()
        self.motd_end = Event()