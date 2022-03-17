from typing import Any, Coroutine, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..objects.message import Message


class Command:
    def __init__(self, func: Coroutine) -> None:
        self.func = func
    
    def __repr__(self) -> str:
        return f'<Command {self.func}>'
    
    async def __call__(self, ctx: 'Message', *args: Any, **kwds: Any) -> Any:
        await self.func(ctx, *args, **kwds)
        
        
class MsgCommand(Command):
    def __init__(self, func: Coroutine) -> None:
        super().__init__(func)
        
    def __repr__(self) -> str:
        return f'<MsgCommand {self.func}>'