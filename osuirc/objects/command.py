from typing import Any, Coroutine, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..objects.message import Message


class Command:
    def __init__(self, func: Coroutine, allow_users: List[str] = None) -> None:
        self.func = func
        self.allow_users = list(*map(lambda u: u.lower(), allow_users))
    
    def __repr__(self) -> str:
        return f'<Command {self.func}>'
    
    async def __call__(self, ctx: 'Message', *args: Any, **kwds: Any) -> Any:
        if ctx.author.lower() not in self.allow_users:
            return
        await self.func(ctx, *args, **kwds)
        
        
class MsgCommand(Command):
    def __init__(self, func: Coroutine, allow_users: List[str] = None) -> None:
        super().__init__(func, allow_users)
        
    def __repr__(self) -> str:
        return f'<MsgCommand {self.func}>'