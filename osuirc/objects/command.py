from typing import Any, Coroutine, List


class Command:
    def __init__(self, func: Coroutine) -> None:
        self.func = func
    
    def __repr__(self) -> str:
        return f'<Command {self.func}>'
    
    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        await self.func(*args, **kwds)
        
        
class MsgCommand(Command):
    def __init__(self, func: Coroutine, users: List[str] = None) -> None:
        super().__init__(func)
        self.users = users
        
    def __repr__(self) -> str:
        return f'<MsgCommand {self.func}>'