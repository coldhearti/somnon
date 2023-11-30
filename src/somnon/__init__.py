from __future__ import annotations

from typing import Callable, Generic, Tuple, Type, TypeVar

"""
* Option and Result monad implementation,
* Influence from Rust std::option and std::result
"""

T = TypeVar("T")
U = TypeVar("U")
R = TypeVar("R")


class UnwrapException(Exception):
    ...


class TransposeException(Exception):
    ...


class __Maybe(Generic[T]):
    def __init__(self, ok: Type[_Ok[T | U]], nok: Type[_NoOk[T | U]]) -> None:
        self._value: T
        self._ok = ok
        self._nok = nok

    def __repr__(self) -> str:
        return str(self._value)

    def expect(self, panic_msg) -> T:
        try:
            return self.unwrap()

        except UnwrapException:
            raise UnwrapException(panic_msg)

    def unwrap(self) -> T:
        if self._value is None:
            raise UnwrapException()
        return self._value

    def unwrap_or(self, default: U) -> T | U:
        try:
            return self.unwrap()

        except UnwrapException:
            return default

    def unwrap_or_else(self, else_func: Callable[[], T]) -> T:
        try:
            return self.unwrap()

        except UnwrapException:
            return else_func()

    def map(self, func: Callable[[T], U]) -> __Maybe[U] | __Maybe[T]:
        match self:
            case self._ok():
                return self._ok(func(self._value), self._ok, self._nok)
            case self._nok():
                ...
        return self

    def map_or(self, func: Callable[[T], U], default: U) -> U:
        match self:
            case self._ok():
                return func(self._value)
            case self._nok():
                ...
        return default

    def map_or_else(self, func: Callable[[T], U], default: Callable[[], U]) -> U:
        match self:
            case self._ok():
                return func(self._value)
            case self._nok():
                ...
        return default()


class _Ok(Generic[T], __Maybe[T]):
    def __init__(self, value: T, ok: type[_Ok[T]], nok: type[_NoOk[T]]) -> None:
        super().__init__(ok, nok)
        self._value = value


class _NoOk(Generic[T], __Maybe[T]):
    def __init__(self, ok: type[_Ok[T]], nok: type[_NoOk[T]]) -> None:
        super().__init__(ok, nok)


class Result(Generic[T], __Maybe[T]):
    def __init__(self, value: T) -> None:
        super().__init__(Ok, Err)
        self._value = value

    def is_ok(self):
        return isinstance(self, Ok)

    def is_err(self):
        return isinstance(self, Err)


class Ok(Result[T], _Ok[T]):
    def __init__(self, value: T) -> None:
        super(Result, self).__init__(value, Ok, Err)
        super(_Ok, self).__init__(Ok, Err)


class Err(Result[T], _NoOk[T]):
    def __init__(self, err: T) -> None:
        super(Result, self).__init__(Ok, Err)
        super(_NoOk, self).__init__(Ok, Err)
        self._value = err


class Option(Generic[T], __Maybe[T]):
    def __init__(self) -> None:
        super().__init__(Som, Non)

    def is_som(self) -> bool:
        return isinstance(self, Som)

    def is_non(self) -> bool:
        return isinstance(self, Non)

    def ok_or(self, err: U) -> Result[T | U]:
        try:
            return Ok(self.unwrap())

        except UnwrapException:
            return Err(err)

    def ok_or_else(self, err_func: Callable[[], U]) -> Result[T | U]:
        return self.ok_or(err_func())

    def transpose(self) -> Result[Som[T] | Non | T]:
        match self:
            case Som():
                match self._value:
                    case Ok():
                        return Ok(Som(self._value._value))

                    case Err():
                        return Err(self._value._value)
            case Non():
                return Ok(Non())
        raise TransposeException

    def filter(self, pred: Callable[[T], bool]) -> Option[T]:
        match self:
            case Som():
                if pred(self._value):
                    return self
                return Non()
            case Non():
                ...
        return Non()

    def flatten(self) -> Option[T]:
        if isinstance(self._value, Option):
            return self._value
        return self

    def o_zip(self, optb: Option[U]) -> Option[Tuple[T, U]]:
        match self:
            case Som():
                match optb:
                    case Som():
                        return Som((self._value, optb._value))
                    case Non():
                        ...
            case Non():
                ...
        return Non()

    def o_zip_with(self, optb: Option[U], func: Callable[[T, U], R]) -> Option[R]:
        match self:
            case Som():
                match optb:
                    case Som():
                        return Som(func(self._value, optb._value))
                    case Non():
                        ...
            case Non():
                ...
        return Non()

    def o_and(self, optb: Option[U]) -> Option[T] | Option[U]:
        match self:
            case Som():
                match optb:
                    case Som():
                        return optb
                    case Non():
                        ...
            case Non():
                ...
        return Non()

    def o_or(self, optb: Option[U]) -> Option[T] | Option[U]:
        match self:
            case Som():
                return self
            case Non():
                match optb:
                    case Som():
                        return optb
                    case Non():
                        ...
        return Non()

    def o_xor(self, optb: Option[U]) -> Option[T] | Option[U]:
        match self:
            case Som():
                match optb:
                    case Som():
                        ...
                    case Non():
                        return self
            case Non():
                match optb:
                    case Som():
                        return optb
                    case Non():
                        ...
        return Non()

    def o_and_then(self, func: Callable[[T], Option[U]]) -> Option[T] | Option[U]:
        match self:
            case Som():
                return self.o_and(func(self._value))
            case Non():
                ...
        return Non()

    def o_or_else(self, func: Callable[[], Option[U]]) -> Option[T] | Option[U]:
        match self:
            case Som():
                return self
            case Non():
                ...
        return func()


class Som(Option[T], _Ok[T]):
    def __init__(self, value: T) -> None:
        super(Option, self).__init__(value, Som, Non)
        super(_Ok, self).__init__(Som, Non)
        self._value = value


class Non(Option[T], _NoOk[T]):
    def __init__(self) -> None:
        super(Option, self).__init__(Som, Non)
        super(_NoOk, self).__init__(Som, Non)
