# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import io
from .errors import InvalidArgument
from . import utils

VALID_STATIC_FORMATS = {"jpeg", "jpg", "webp", "png"}
VALID_AVATAR_FORMATS = VALID_STATIC_FORMATS | {"gif"}

class Asset:
    """Represents a CDN asset on Discord.

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the CDN asset.
    """
    __slots__ = ('_state', '_url')

    def __init__(self, state, url=None):
        self._state = state
        self._url = url

    @classmethod
    def from_avatar(cls, user, state, *, format=None, static_format='webp', size=1024):
        """Creates a :class:`.Asset` from an avatar."""
        if not utils.valid_icon_size(size):
            raise InvalidArgument("size must be a power of 2 between 16 and 1024")
        if format is not None and format not in VALID_AVATAR_FORMATS:
            raise InvalidArgument("format must be None or one of {}".format(VALID_AVATAR_FORMATS))
        if format == "gif" and not user.is_avatar_animated():
            raise InvalidArgument("non animated avatars do not support gif format")
        if static_format not in VALID_STATIC_FORMATS:
            raise InvalidArgument("static_format must be one of {}".format(VALID_STATIC_FORMATS))

        if user.avatar is None:
            return user.default_avatar_url

        if format is None:
            if user.is_avatar_animated():
                format = 'gif'
            else:
                format = static_format

        return cls(state, 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.{1}?size={2}'.format(user, format, size))

    @classmethod
    def from_guild_image(cls, guild, state, image_type, *, format='webp', size=1024):
        """Creates a :class:`.Asset` from the requested guild image."""
        if not utils.valid_icon_size(size):
            raise InvalidArgument("size must be a power of 2 between 16 and 4096")
        if format not in VALID_STATIC_FORMATS:
            raise InvalidArgument("format must be one of {}".format(VALID_STATIC_FORMATS))

        if getattr(guild, image_type) is None:
            return ''

        if image_type == 'splash':
            suffix = "es"
        else:
            suffix = "s"

        return cls(state, 'https://cdn.discordapp.com/{0}/{1.id}/{1.icon}.{2}?size={3}'.format(image_type+suffix, guild, format, size))

    def __str__(self):
        return self._url

    def __repr__(self):
        return '<Asset url={0._url!r}>'.format(self)

    async def save(self, fp, *, seek_begin=True):
        """|coro|

        Saves this asset into a file-like object.

        Parameters
        -----------
        fp: Union[BinaryIO, :class:`os.PathLike`]
            Same as in :meth:`Attachment.save`.
        seek_begin: :class:`bool`
            Same as in :meth:`Attachment.save`.

        Raises
        --------
        HTTPException
            Saving the asset failed.
        NotFound
            The asset was deleted.

        Returns
        --------
        :class:`int`
            The number of bytes written.
        """
        data = await self._state.http.get_from_cdn(self._url)
        if isinstance(fp, io.IOBase) and fp.writable():
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)
