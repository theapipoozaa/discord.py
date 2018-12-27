from .user import User, Profile, ClientUser
from .invite import Invite
from .object import Object
from .guild import Guild
from .enums import Status, VoiceRegion
from .emoji import Emoji
from .gateway import *
from .activity import Activity, Game, Streaming, Spotify
from .voice_client import VoiceClient
from .webhook import Webhook
from .member import Member
from .channel import TextChannel, VoiceChannel, CategoryChannel, DMChannel, GroupChannel

import asyncio
import aiohttp

from typing import Any, Union, Optional, List, Callable, Iterator, Coroutine, TypeVar, NamedTuple

_FuncType = Callable[..., Coroutine[Any, Any, Any]]
_F = TypeVar('_F', bound=_FuncType)

class AppInfo(NamedTuple):
    id: int
    name: str
    description: str
    icon: str
    owner: User

    @property
    def icon_url(self) -> str: ...

class Client:
    ws: Optional[DiscordWebSocket]
    loop: asyncio.AbstractEventLoop

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = ...,
                 shard_id: Optional[int] = ..., shard_count: Optional[int] = ...,
                 connector: aiohttp.BaseConnector = ..., proxy: Optional[str] = ...,
                 proxy_auth: Optional[aiohttp.BasicAuth] = ..., max_messages: Optional[int] = ...,
                 fetch_offline_members: bool = ..., status: Optional[Status] = ...,
                 activity: Optional[Union[Activity, Game, Streaming]] = ...,
                 heartbeat_timeout: float = ..., **options: Any) -> None: ...

    @property
    def latency(self) -> float: ...

    # NOTE: user is actually Optional[ClientUser] because it's None when logged out, but the vast
    # majority of uses will be while logged in. Because of this fact, it is typed as ClientUser to
    # prevent false positives
    @property
    def user(self) -> ClientUser: ...

    @property
    def guilds(self) -> List[Guild]: ...

    @property
    def emojis(self) -> List[Emoji]: ...

    @property
    def private_channels(self) -> List[Union[DMChannel, GroupChannel]]: ...

    @property
    def voice_clients(self) -> List[VoiceClient]: ...

    def is_ready(self) -> bool: ...

    def dispatch(self, event: str, *args: Any, **kwargs: Any) -> None: ...

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None: ...

    async def request_offline_members(self, *guilds: Guild) -> None: ...

    async def login(self, token: str, *, bot: bool = ...) -> None: ...

    async def logout(self) -> None: ...

    async def connect(self, *, reconnect: bool = ...) -> None: ...

    async def close(self) -> None: ...

    def clear(self) -> None: ...

    async def start(self, token: str, *, bot: bool = ..., reconnect: bool = ...) -> None: ...

    def run(self, token: str, *, bot: bool = ..., reconnect: bool = ...) -> None: ...

    def is_closed(self) -> bool: ...

    activity: Union[Activity, Game, Streaming, Spotify]

    @property
    def users(self) -> List[User]: ...

    def get_channel(self, id: int) -> Optional[Union[TextChannel, VoiceChannel, CategoryChannel, DMChannel, GroupChannel]]: ...

    def get_guild(self, id: int) -> Optional[Guild]: ...

    def get_user(self, id: int) -> Optional[User]: ...

    def get_emoji(self, id: int) -> Optional[Emoji]: ...

    def get_all_channels(self) -> Iterator[Union[TextChannel, VoiceChannel, CategoryChannel]]: ...

    def get_all_members(self) -> Iterator[Member]: ...

    async def wait_until_ready(self) -> None: ...

    def wait_for(self, event: str, *, check: Optional[Callable[..., bool]] = ..., timeout: Optional[float] = ...) -> Any: ...

    def event(self, coro: _F) -> _F: ...

    async def change_presence(self, *, activity: Optional[Union[Activity, Game, Streaming, Spotify]] = ...,
                              status: Optional[Status] = ..., afk: bool = ...) -> None: ...

    async def create_guild(self, name: str, region: Optional[VoiceRegion] = ..., icon: Optional[bytes] = ...) -> Guild: ...

    async def get_invite(self, url: str) -> Invite: ...

    async def delete_invite(self, invite: Union[Invite, str]) -> None: ...

    async def application_info(self) -> AppInfo: ...

    async def get_user_info(self, user_id: int) -> User: ...

    async def get_user_profile(self, user_id: int) -> Profile: ...

    async def get_webhook_info(self, webhook_id: int) -> Webhook: ...
