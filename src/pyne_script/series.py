from typing import Any, KeysView, Union
import numpy as np


class SeriesHeadObject:
    value: Union[float, int]
    values: np.ndarray
    name: str

    def __init__(self, value: Union[float, int], values: np.ndarray, name: str) -> None:
        self.value = value
        self.values = values
        self.name = name

    def __setitem__(self, key, value) -> None:
        raise SeriesCannotMutateHistory()

    def __getitem__(
        self, items: list[Union[int, slice]]
    ) -> Union[int, float, list[Union[int, float, slice]]]:
        if not isinstance(items, list):
            items = [items]

        out = []
        for index in items:
            match index:
                case int():
                    out.append(self.values[-index])  # type: ignore
                    break
                case slice():
                    if index.step:  # type: ignore
                        # type: ignore
                        try:
                            out.append(
                                self.values[-index.start: -index.end: index.step])
                        except:
                            raise SeriesIndexError(self.name)
                    else:
                        # type: ignore
                        try:
                            out.append(self.values[-index.start: -index.end])
                        except:
                            raise SeriesIndexError(self.name)

                    break
                case _:
                    raise InvalidSeriesIndex(self.name)

        if len(out) == 1:
            return out[0]
        return out


class SeriesHeadObjectFloat(float, SeriesHeadObject):
    def __new__(cls, val: float, values: np.ndarray, name: str) -> float:
        i = float.__new__(SeriesHeadObjectFloat, val)
        i.values = values
        i.name = name
        return i

    def __init__(self, val: float, values: np.ndarray, name: str) -> None:
        self.val = val
        self.value = values
        self.name = name
        super().__init__(val,values,name)

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.__str__()


class SeriesHeadObjectInteger(int, SeriesHeadObject):
    def __new__(cls, val: float, values: np.ndarray, name: str) -> int:
        i = int.__new__(SeriesHeadObjectInteger, val)
        i.values = values
        i.name = name
        return i

    def __init__(self, val: float, values: np.ndarray, name: str) -> None:
        self.val  = val
        self.value = values
        self.name = name
        super().__init__(val,values,name)

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.__str__()


class Series:
    keys: set
    key_mappings: dict[str, int]
    values: np.ndarray
    heads: np.ndarray
    head_positions: int
    window_size: int
    heads_assigned: set

    track_history: bool
    history: tuple[str,list[Union[float, int]]]

    def __init__(self, keys: list[str], window_size: int = 200, track_history: bool = False) -> None:
        self.keys = set()
        self.key_mappings = {}
        self.values = np.zeros((len(keys), window_size))
        self.heads = np.zeros(len(keys))
        self.heads_assigned = set()
        for i in range(len(keys)):
            key = keys[i]
            self.keys.add(key)
            self.key_mappings[key] = i

        self.head_positions = 0
        self.window_size = window_size

        self.track_history = track_history
        if track_history:
            self.history = {}
            for key in self.keys:
                self.history[key] = []

    def update(self) -> None:
        all_assigned = True
        unassigned_heads = []

        for key in self.keys:
            if key not in self.heads_assigned:
                all_assigned = False
                unassigned_heads.append(key)
            else:
                self.heads_assigned.remove(key)

        if not all_assigned:
            raise PrematureSeriesUpdate(unassigned_heads)

        if self.head_positions+1 > self.window_size-1:
            self.values = np.roll(self.values, (0, -1))
        else:
            self.head_positions += 1

        self.values[:, self.head_positions] = self.heads

        if self.track_history:
            for key in self.keys:
                self.history[key].append(self.heads[self.key_mappings[key]])

    def __getitem__(self, items: list[Union[int, slice]]) -> SeriesHeadObject:
        if not isinstance(items, list):
            items = [items]

        if isinstance(items[0], str) and len(items) == 1:
            name = items[0]
            if name in self.keys:
                if self.head_positions > 0:
                    if isinstance(self.heads[self.key_mappings[name]], int):
                        return SeriesHeadObjectInteger(
                            self.heads[self.key_mappings[name]],
                            self.values[self.key_mappings[name]],
                            name,
                        )
                    else:
                        return SeriesHeadObjectFloat(
                            self.heads[self.key_mappings[name]],
                            self.values[self.key_mappings[name]],
                            name,
                        )
                else:
                    raise UnAssignedHead(name)
            else:
                raise NonExistentHead(name, "get")
        else:
            raise InvalidSeriesIndex()

    def __setitem__(self, key, value) -> None:
        if isinstance(key, str):
            name = key
            if name in self.keys:
                self.heads[self.key_mappings[name]] = value
                self.heads_assigned.add(name)
            else:
                raise NonExistentHead(name, "set")
        else:
            raise InvalidSeriesIndex()


class PyneSeriesException(Exception):
    """The base class for any pyne script series related exceptions."""

    def __init__(self, *args) -> None:
        self.args = args
        super().__init__(*args)


class NonExistentHead(PyneSeriesException):
    """When a query is received for a non-existent head.

    Args:
    0. Head id
    1. Query type

    """

    def __str__(self) -> str:
        return f"Series received {self.args[1]} query for a non-existent head: {self.args[0]}"


class UnAssignedHead(PyneSeriesException):
    """When a query is received for a head that has not been assigned a value.

    Args:
    0. Head id

    """

    def __str__(self) -> str:
        return f"Series received query for a head with no currently assigned value: {self.args[0]}"


class InvalidSeriesIndex(PyneSeriesException):
    """When a head is indexed in an unexpected way.

    Args:
    0. Head id
    """

    def __str__(self) -> str:
        if len(self.args) == 1:
            return f"Invalid indexing for series: {self.args[0]}"
        else:
            return "Series object received invalid indexing. Expected single string series id as key"


class PrematureSeriesUpdate(PyneSeriesException):
    """When a series object is updated while still having unassigned heads

    Args:
    0. Unassigned head ids
    """

    def __str__(self) -> str:
        msg = "Premature Update recieved by Series object. Some heads were still unassigned:"
        for head in self.args[0]:
            msg += f"\n- {head}"
        return msg

class SeriesIndexError(PyneSeriesException):
    """When an index is invalid for a head

    Args:
    0. Head id
    """

    def __str__(self) -> str:
        msg = f"Invalid index when indexing head object: {self.args[0]}"
        return msg

class SeriesCannotMutateHistory(PyneSeriesException):
    """When an item assignment is tried on a head object."""

    def __str__(self) -> str:
        return "Tried to assign to head object. History is immutable"
