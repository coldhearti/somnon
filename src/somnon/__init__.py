from __future__ import annotations

from types import NoneType
from typing import Any, Callable, Generic, Tuple, Type, TypeVar, cast

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


class ResultException(Exception):
    ...


class __Maybe(Generic[T, U]):
    def __init__(self, value: T | U, ok: Type[_Ok[T]], nok: Type[_NoOk[U]]) -> None:
        self._value = value
        self._ok = ok
        self._nok = nok

    def __repr__(self) -> str:
        try:
            return str(self.unwrap())
        except UnwrapException:
            return "None"
        except Exception as e:
            return e.__repr__()

    def __hash__(self) -> int:
        return hash(self._value)

    def __format__(self, __format_spec: str) -> str:
        try:
            return str(self.unwrap())
        except UnwrapException:
            return "None"
        except Exception as e:
            return e.__format__(__format_spec)

    def __str__(self) -> str:
        try:
            return str(self.unwrap())
        except UnwrapException:
            return "None"
        except Exception as e:
            return e.__str__()

    def __eq__(self, __value: object) -> bool:
        match type(self):
            case self._ok:
                if isinstance(__value, self._ok):
                    return __value._value == self._value
            case self._nok:
                if isinstance(__value, self._nok):
                    return True
        return False

    def expect(self, panic_msg) -> T | U:
        try:
            return self.unwrap()

        except UnwrapException:
            raise UnwrapException(panic_msg)

    def unwrap(self) -> T | U:
        val = self._value
        match self:
            case self._nok():
                match val:
                    case None:
                        raise UnwrapException()
                return val
            case self._ok():
                ...
        return val

    def unwrap_or(self, default: T | U) -> T | U:
        try:
            return self.unwrap()
        except Exception:
            return default

    def unwrap_or_else(self, else_func: Callable[[], T | U]) -> T | U:
        return self.unwrap_or(else_func())

    def map(self, func: Callable[[T], U]) -> __Maybe[T, U]:
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
            case self._nok:
                ...
        return default

    def map_or_else(self, func: Callable[[T], U], default: Callable[[], U]) -> U:
        match self:
            case self._ok():
                return func(self._value)
            case self._nok():
                ...
        return default()


class _Ok(__Maybe[T, NoneType]):
    def __init__(self, value: T, ok: type[_Ok[T]], nok: type[_NoOk[NoneType]]) -> None:
        super().__init__(value, ok, nok)


class _NoOk(__Maybe[NoneType, T]):
    def __init__(self, value: T, ok: type[_Ok[NoneType]], nok: type[_NoOk[T]]) -> None:
        super().__init__(value, ok, nok)


class Result(__Maybe[T, U]):
    def __init__(self, value: T) -> None:
        super().__init__(value, Ok, Err)

    def is_ok(self):
        return isinstance(self, Ok)

    def is_err(self):
        return isinstance(self, Err)


class Ok(Result[T, NoneType], _Ok[T]):
    def __init__(self, value: T) -> None:
        super(Result, self).__init__(value, Ok, Err)
        super(_Ok, self).__init__(value, Ok, Err)


class Err(Result[NoneType, T], _NoOk[T]):
    def __init__(self, err: T = "") -> None:
        super(Result, self).__init__(err, Ok, Err)
        super(_NoOk, self).__init__(err, Ok, Err)


class Option(__Maybe[T, NoneType]):
    def __init__(self) -> None:
        super().__init__(cast(T, None), Som, Non)

    def is_som(self) -> bool:
        return isinstance(self, Som)

    def is_non(self) -> bool:
        return isinstance(self, Non)

    def ok_or(self, err: U) -> Result[NoneType, U] | Result[T, NoneType]:
        try:
            return Ok(cast(T, self.unwrap()))
        except UnwrapException:
            return Err(err)

    def ok_or_else(self, err_func: Callable[[], U]) -> Result[NoneType, U] | Result[T, NoneType]:
        return self.ok_or(err_func())

    def transpose(self) -> Result[T | Som | Non, NoneType] | Result[NoneType, Any]:
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

    def filter(self, pred: Callable[[T], bool]) -> Option[T] | Option[NoneType]:
        match self:
            case Som():
                if pred(cast(T, self._value)):
                    return self
                return Non()
            case Non():
                ...
        return Non()

    def flatten(self) -> Option[T]:
        if isinstance(self._value, Option):
            return self._value
        return self

    def o_zip(self, optb: Option[U]) -> Option[Tuple[T, U]] | Option[NoneType]:
        match self:
            case Som():
                match optb:
                    case Som():
                        return Som((cast(T, self._value), cast(U, optb._value)))
                    case Non():
                        ...
            case Non():
                ...
        return Non()

    def o_zip_with(self, optb: Option[U], func: Callable[[T, U], R]) -> Option[R] | Option[NoneType]:
        match self:
            case Som():
                match optb:
                    case Som():
                        return Som(func(cast(T, self._value), cast(U, optb._value)))
                    case Non():
                        ...
            case Non():
                ...
        return Non()

    def o_and(self, optb: Option[U]) -> Option[T] | Option[U] | Option[NoneType]:
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

    def o_or(self, optb: Option[U]) -> Option[T] | Option[U] | Option[NoneType]:
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

    def o_xor(self, optb: Option[U]) -> Option[T] | Option[U] | Option[NoneType]:
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

    def o_and_then(self, func: Callable[[T], Option[U]]) -> Option[T] | Option[U] | Option[NoneType]:
        match self:
            case Som():
                return self.o_and(func(cast(T, self._value)))
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
        super(_Ok, self).__init__(value, Som, Non)


class Non(Option[NoneType], _NoOk[NoneType]):
    def __init__(self) -> None:
        super(Option, self).__init__(None, Som, Non)
        super(_NoOk, self).__init__(None, Som, Non)
