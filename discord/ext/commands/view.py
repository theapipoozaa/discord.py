"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from __future__ import annotations

from typing import List, Optional, Set, Tuple, Union, overload
from .errors import UnexpectedQuoteError, InvalidEndOfQuotedStringError, ExpectedClosingQuoteError

__all__ = (
    'Separator',
    'Quotation'
)

# map from opening quotes to closing quotes
_quotes = {
    '"': '"',
    "‘": "’",
    "‚": "‛",
    "“": "”",
    "„": "‟",
    "⹂": "⹂",
    "「": "」",
    "『": "』",
    "〝": "〞",
    "﹁": "﹂",
    "﹃": "﹄",
    "＂": "＂",
    "｢": "｣",
    "«": "»",
    "‹": "›",
    "《": "》",
    "〈": "〉",
}
_all_quotes = set(_quotes.keys()) | set(_quotes.values())


class Separator:
    """An argument qualifier, which acts as the delimiter for arguments.

    .. versionadded:: 2.0

    .. code-block:: python3

        @bot.command(qualifier=Separator(','))
        async def foo(ctx, *c):
            await ctx.send(', '.join(c))

        # ?foo a b, c, d, e

        # -> "a b,c,d,e"
        # trailing whitespace is stripped by default.

        @bot.command(separator=Separator('|', strip_ws=False))
        async def bar(ctx, *c):
            await ctx.send(','.join(c))

        # ?bar a b test | c |  e  | f
        # -> " a b test , c ,  e  , f"

    Attributes
    -----------
    key: Optional[:class:`str`]
        The key that separates each argument. By default, it is a space.
    strip_ws: :class:`bool`
        Whether or not to strip whitespace from the arguments. By default,
        it is ``True``.
    """

    __slots__ = ('key', 'strip_ws')

    def __init__(self, key: Optional[str] = None, *, strip_ws: bool = True) -> None:
        if key == '':
            raise ValueError('The separator must be a non-empty string or None.')
        self.key: Optional[str] = key
        self.strip_ws: bool = strip_ws

    def __repr__(self) -> str:
        return '<Separator key={0.key!r} strip_ws={0.strip_ws}>'.format(self)


class Quotation:
    r"""An argument qualifier, which acts as a drop-in replacement for quotes.

    .. versionadded:: 2.0

    .. code-block:: python3

        @bot.command(quotation=Quotation('-'))
        async def foo(ctx, *c):
            await ctx.send(','.join(c))

        # ?foo -a b c- b
        # -> "a b c,b"

        @bot.command(quotation=Quotation('(', ')'))
        async def bar(ctx, *c):
            await ctx.send(','.join(c))

        # ?bar a b (c d e) f g
        # -> "a,b,c d e,f,g"

    Parameters
    -----------
    start: :class:`str`
        The starting key that represents the first quote character.
    end: Optional[:class:`str`]
        The ending key that represents the last quote character. If ``None``\,
        it will be set as the same key as ``start``.
    """

    __slots__ = ('_keys', '_all_keys', '_initial_quotations')

    @overload
    def __init__(self, start: str) -> None:
        ...

    @overload
    def __init__(self, start: str, end: str) -> None:
        ...

    def __init__(self, start: str, end: Optional[str] = None):
        self._keys = {start: end or start}
        self._all_keys = None

        for s, e in self._keys.items():
            if not s or not e:
                raise ValueError('Quotations must be a non-empty string.')

        self._initial_quotations = (start, end or start)

    @property
    def all_keys(self) -> Set[str]:
        if not self._all_keys:
            self._all_keys = set(self._keys.keys()) | set(self._keys.values())
        return self._all_keys

    @classmethod
    def from_pairs(cls, *pairs: Union[Tuple[str, str], List[str]]) -> Quotation:
        """Creates a Quotation that can accept pairs of quotes as tuples or lists.

        .. code-block:: python3

            @bot.command(quotation=Quotation.from_pairs(('(', ')'), ('[', ']'), ('{', '}')))
            async def foo(ctx, *c):
                await ctx.send(','.join(c))
        """
        if not pairs:
            raise ValueError('at least one pair must be provided.')

        self = None
        for s, e in pairs:
            if self is None:
                self = cls(s, e)
            else:
                if not s or not e:
                    raise ValueError('quotations must be a non-empty string.')

                self._keys[s] = e
        return self  # type: ignore

    def get(self, key) -> Optional[str]:
        return self._keys.get(key)

    def __contains__(self, item) -> bool:
        return item in self._all_keys

    def __repr__(self) -> str:
        return '<Quotation keys={0!r}>'.format(self._all_keys)


class StringView:
    def __init__(self, buffer):
        self.index = 0
        self.buffer = buffer
        self.end = len(buffer)
        self.previous = 0
        self.separator = Separator()
        self.quotation = None

    @property
    def current(self):
        return None if self.eof else self.buffer[self.index]

    @property
    def eof(self):
        return self.index >= self.end

    def is_separator(self, c):
        key = self.separator.key
        if key is None:
            return c.isspace()
        return c == key

    def is_space(self, c):
        key = self.separator.key
        if key is None:
            return c.isspace()
        if self.separator.strip_ws:
            return c.isspace() or c == key
        return c == key

    def undo(self):
        self.index = self.previous

    def skip_ws(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if not self.is_space(current):
                    break
                pos += 1
            except IndexError:
                break

        self.previous = self.index
        self.index += pos
        return self.previous != self.index

    def skip_string(self, string):
        strlen = len(string)
        if self.buffer[self.index:self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def read_rest(self):
        result = self.buffer[self.index:]
        self.previous = self.index
        self.index = self.end
        return result

    def read(self, n):
        result = self.buffer[self.index:self.index + n]
        self.previous = self.index
        self.index += n
        return result

    def get(self):
        try:
            result = self.buffer[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1
        return result

    def get_word(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if self.is_separator(current):
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index:self.index + pos]
        self.index += pos
        return result

    def get_quoted_word(self):
        current = self.current
        if current is None:
            return None

        quotation = self.quotation or _quotes
        close_quote = quotation.get(current)

        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            _escaped_quotes = _all_quotes

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise ExpectedClosingQuoteError(close_quote)

                r = ''.join(result)
                if self.separator.strip_ws:
                    r = r.strip()
                return r

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            # separator characters (either a white space character or
            # a custom separator string) can also be escaped : hello\ world
            if current == '\\':
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise ExpectedClosingQuoteError(close_quote)
                    # if we aren't then we just let it through
                    return ''.join(result)

                if next_char in _escaped_quotes:
                    # escaped separator or quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            allowed_quotes = self.quotation or _all_quotes
            if not is_quoted and current in _quotes:
                # we aren't quoted
                raise UnexpectedQuoteError(current)

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or self.is_separator(next_char)
                if not valid_eof:
                    raise InvalidEndOfQuotedStringError(next_char)

                # we're quoted so it's okay
                return ''.join(result)

            if self.is_separator(current) and not is_quoted:
                # end of word found
                r = ''.join(result)
                if self.separator.strip_ws:
                    r = r.strip()

                return r

            result.append(current)


    def __repr__(self):
        return f'<StringView pos: {self.index} prev: {self.previous} end: {self.end} eof: {self.eof}>'
