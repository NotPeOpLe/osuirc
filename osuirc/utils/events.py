from asyncio import Event


class ClientEvents:
    def __init__(self) -> None:
        self.welcome = Event()
        self.motd_start = Event()
        self.motd_end = Event()
