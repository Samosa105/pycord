"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

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
# mypy: implicit-reexport=True
import datetime
import random
from inspect import signature
from typing import TypeVar, Tuple, Any, Dict, Optional, Callable, Literal, Type, Union

import pytest

from discord.utils import (
    copy_doc,
    time_snowflake,
    snowflake_time,
    utcnow,
    MISSING,
    _cached_property,
    find,
    get,
    _unique,
    _parse_ratelimit_header,
    maybe_coroutine,
    async_all, get_or_fetch, basic_autocomplete, generate_snowflake, format_dt, resolve_annotation, evaluate_annotation,
    PY_310,
)
from discord import utils
from .helpers import coroutine, MockObject

A = TypeVar('A')
B = TypeVar('B')


def test_copy_doc() -> None:
    def foo(a: A, b: B) -> Tuple[A, B]:
        """
        This is a test function.
        """
        return a, b

    @copy_doc(foo)
    def bar(a, b):  # type: ignore[no-untyped-def]
        return a, b

    foo(1, 2)
    bar(1, 2)

    assert bar.__doc__ == foo.__doc__
    assert signature(bar) == signature(foo)


@pytest.mark.parametrize('func', (time_snowflake, generate_snowflake))
def test_snowflake(func: Callable[[datetime.datetime], int]) -> None:
    now = utcnow().replace(microsecond=0)
    snowflake = func(now)
    assert snowflake_time(snowflake) == now


def test_missing() -> None:
    assert MISSING != object()
    assert not MISSING
    assert repr(MISSING) == '...'


def test_cached_property() -> None:
    class Test:
        def __init__(self, x: int):
            self.x = x

        @_cached_property
        def foo(self) -> int:
            self.x += 1
            return self.x

    t = Test(0)
    assert isinstance(_cached_property.__get__(_cached_property(None), None, None), _cached_property)
    assert t.foo == 1
    assert t.foo == 1


def test_find_get() -> None:
    class Obj:
        def __init__(self, value: int):
            self.value = value
            self.deep = self

        def __eq__(self, other: Any) -> bool:
            return isinstance(other, self.__class__) and self.value == other.value

        def __repr__(self) -> str:
            return f'<Obj {self.value}>'

    repr(Obj(0))

    obj_list = [Obj(i) for i in range(10)]
    for i in range(11):
        for val in (
                find(lambda o: o.value == i, obj_list),
                get(obj_list, value=i),
                get(obj_list, deep__value=i),
                get(obj_list, value=i, deep__value=i),
        ):
            if i >= len(obj_list):
                assert val is None
            else:
                assert val == Obj(i)


def test_unique() -> None:
    values = [random.randint(0, 100) for _ in range(1000)]
    unique = _unique(values)
    unique.sort()
    assert unique == list(set(values))


@pytest.mark.parametrize('use_clock', (True, False))
@pytest.mark.parametrize('value', list(range(0, 100, random.randrange(5, 10))))
def test_parse_ratelimit_header(use_clock, value):  # type: ignore[no-untyped-def]
    class RatelimitRequest:
        def __init__(self, reset_after: int):
            self.headers = {
                'X-Ratelimit-Reset-After': reset_after,
                'X-Ratelimit-Reset': (utcnow() + datetime.timedelta(seconds=reset_after)).timestamp(),
            }

    assert round(_parse_ratelimit_header(RatelimitRequest(value), use_clock=use_clock)) == value


@pytest.mark.parametrize('value', range(5))
async def test_maybe_coroutine(value) -> None:  # type: ignore[no-untyped-def]
    assert value == await maybe_coroutine(lambda v: v, value)
    assert value == await maybe_coroutine(coroutine, value)


@pytest.mark.parametrize('size', list(range(10, 20)))
@pytest.mark.filterwarnings("ignore:coroutine 'coroutine' was never awaited")
async def test_async_all(size) -> None:  # type: ignore[no-untyped-def]
    values = []
    raw_values = []

    for i in range(size):
        value = random.choices((True, False), (size - 1, 1))[0]
        raw_values.append(value)
        values.append(coroutine(value) if random.choice((True, False)) else value)

    assert all(raw_values) == await async_all(values)


async def test_get_or_fetch() -> None:
    class Test:
        def __init__(self, values: Dict[int, int]):
            self.values = values
            self.allow_get = True

        def get_x(self, key: int) -> Optional[int]:
            if not self.allow_get:
                return None
            return self.values.get(key)

        async def fetch_x(self, key: int) -> int:
            return self.values[key]

        async def _fetch_x(self, key: int) -> int:
            return self.values[key]

    test = Test({i: random.randint(0, 100) for i in range(100)})

    while True:
        for k, v in test.values.items():
            assert v == await get_or_fetch(test, "x", k)
        if test.get_x(0) is not None:
            test.allow_get = False
        elif hasattr(Test, 'fetch_x'):
            del Test.fetch_x
        else:
            break


phrase_values = "test", "test2", "test3", "tests", "testing", "testing2", "tea"


@pytest.mark.parametrize('phrase', phrase_values)
@pytest.mark.parametrize('phrases', (phrase_values, lambda ctx: coroutine(phrase_values), lambda ctx: phrase_values))
async def test_basic_autocomplete(phrase, phrases) -> None:  # type: ignore[no-untyped-def]
    autocomplete = basic_autocomplete(phrases)

    class MockContext:
        def __init__(self, value: str):
            self.value = value

    for i in range(len(phrase)):
        assert phrase in await autocomplete(MockContext(phrase[:i]))


@pytest.mark.parametrize('style', ('t', 'T', 'd', "D", 'f', 'F', 'R', None))
def test_format_dt(style: Optional[Literal['f', 'F', 'd', 'D', 't', 'T', 'R']]) -> None:
    dt = utcnow()
    if style is None:
        formatted = f'<t:{int(dt.timestamp())}>'
    else:
        formatted = f'<t:{int(dt.timestamp())}:{style}>'
    assert formatted == format_dt(dt, style=style)


@pytest.mark.parametrize('annotation', (None, MockObject))
@pytest.mark.parametrize('use_str', (True, False))
def test_resolve_annotation(annotation: Optional[Type[object]], use_str: bool) -> None:
    annotation_type = annotation
    if annotation_type is None:
        annotation_type = type(None)
    if use_str:
        if annotation is None:
            return
        annotation = annotation.__name__
    assert issubclass(resolve_annotation(annotation, globals(), locals(), None), annotation_type)


test1 = type('test1', (object,), {'__args__': (MockObject,)})
test2 = type('test2', (test1,), {'__origin__': Union})
test3 = type('test3', (test2,), {'__args__': [type(None), MockObject]})
test4 = type('test4', (object,), {'__origin__': Literal, '__args__': ('a', 'b')})
test5 = type('test5', (test4,), {})
test6 = type('test6', (test5,), {'__args__': (MockObject,)})


@pytest.mark.parametrize('annotation', (
        None,
        MockObject,
        Optional[MockObject],
        test1,
        test2,
        test3,
        test4,
        test5,
        test6,
        "MockObject | None" if PY_310 else None,
))
@pytest.mark.parametrize('use_str', (True, False))
@pytest.mark.parametrize('use_cache', (True, False))
def test_evaluate_annotation(
        annotation: Optional[Type[object]],
        use_str: bool,
        use_cache: bool,
) -> None:
    reset_310 = False
    annotation_type = annotation
    if annotation_type == test5 and PY_310:
        reset_310 = True
        utils.PY_310 = False
    if annotation_type is None:
        annotation_type = type(None)
    if use_str and not isinstance(annotation, str):
        if annotation is None:
            if reset_310:
                utils.PY_310 = True
            return
        annotation = annotation.__name__
    if use_cache:
        cache = globals() | locals()
    else:
        cache = {}
    if annotation_type == test6:
        with pytest.raises(TypeError):
            evaluate_annotation(annotation, globals(), locals(), {})
        return
    result = evaluate_annotation(annotation, globals(), locals(), cache)
    if reset_310:
        utils.PY_310 = True
    if annotation is None:
        assert result is None
    elif type(annotation_type) is object:
        assert issubclass(result, annotation_type)