import __future__
from typing import Any
import copy
import numpy as np


class SeriesHeadObject:
    value: float | int
    key: str | int
    track_history_mode: int
    window_size: int | None
    values: np.ndarray | None
    history: list[int | float] | None

    def __init__(
        self,
        value: float | int,
        key: str | int,
        track_history_mode: int,
        window_size: int | None = 200,
        values: np.ndarray | None = None,
        history: None | list[int | float] = None,
    ) -> None:
        self.value = value
        self.key = key
        self.track_history_mode = track_history_mode
        self.window_size = window_size
        self.values = values
        self.history = history

    def __setitem__(self, *_) -> None:
        raise SeriesCannotMutateHistory()

    def index(self, i: int, error: bool = False) -> tuple[int, bool, bool]:
        overflow_window = False
        overflow_full = False
        if self.track_history_mode in [0, 2] and i > self.window_size - 1:  # type: ignore
            overflow_window = True
        elif self.track_history_mode in [1, 2] and i > len(self.history):  # type: ignore
            if error:
                raise SeriesIndexOutOfRange(self.key, i)
            overflow_full = True
        if not overflow_window:
            return i, overflow_window, overflow_full
        else:
            if self.track_history_mode == 0:
                if error:
                    raise SeriesIndexOutOfRange(self.key, i)
                return self.window_size - 1, overflow_window, overflow_full  # type: ignore
            else:
                return i, overflow_window, overflow_full

    def __getitem__(
        self, items: list[int | slice] | int | slice
    ) -> int | float | slice | list[float | int | list[float | int]]:
        if not isinstance(items, list):
            indices = [items]
        else:
            indices = items

        out = []
        for index in indices:  # type: ignore
            match index:
                case int():
                    index_checked = self.index(index, error=True)
                    overflow_window = index_checked[1]
                    if self.track_history_mode == 1:
                        values = self.history
                    if self.track_history_mode in [0, 2] and not overflow_window:
                        values = self.values
                    else:
                        values = self.history

                    out.append(values[-index])  # type: ignore
                    break
                case slice():
                    values = None
                    for slice_index in [index.start, index.stop]:
                        index_checked = self.index(slice_index, error=True)
                        overflow_window = index_checked[1]
                        if self.track_history_mode == 1:
                            values = self.history
                        if (
                            values != self.history
                            and self.track_history_mode in [0, 2]
                            and not overflow_window
                        ):
                            values = self.values
                        else:
                            values = self.history

                    if index.step:
                        try:
                            out.append(
                                values[-index.start : -index.stop : index.step]  # type: ignore
                            )
                        except:
                            raise SeriesIndexError(self.key)
                    else:
                        try:
                            out.append(values[-index.start : -index.stop])  # type: ignore
                        except:
                            raise SeriesIndexError(self.key)

                    break
                case _:
                    raise InvalidSeriesIndex(self.key)

        if len(out) == 1:
            return out[0]
        return out


class SeriesHeadObjectFloat(float, SeriesHeadObject):
    def __new__(
        cls,
        val: float,
        key: str | int,
        track_history_mode: int,
        window_size: int | None = 200,
        values: np.ndarray | None = None,
        history: None | list[int | float] = None,
    ) -> float:
        i = float.__new__(SeriesHeadObjectFloat, val)
        i.values = values
        i.key = key
        i.track_history_mode = track_history_mode
        i.window_size = window_size
        i.values = values
        i.history = history
        return i

    def __init__(
        self,
        val: float,
        key: str | int,
        track_history_mode: int,
        window_size: int | None = 200,
        values: np.ndarray | None = None,
        history: None | list[int | float] = None,
    ) -> None:
        self.val = val
        self.key = key
        self.track_history_mode = track_history_mode
        self.window_size = window_size
        self.values = values
        self.history = history
        super().__init__(val, key, track_history_mode, window_size, values, history)

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.__str__()


class SeriesHeadObjectInteger(int, SeriesHeadObject):
    def __new__(
        cls,
        val: int,
        key: str | int,
        track_history_mode: int,
        window_size: int | None = 200,
        values: np.ndarray | None = None,
        history: None | list[int | float] = None,
    ) -> int:
        i = int.__new__(SeriesHeadObjectInteger, val)
        i.values = values
        i.key = key
        i.track_history_mode = track_history_mode
        i.window_size = window_size
        i.values = values
        i.history = history
        return i

    def __init__(
        self,
        val: int,
        key: str | int,
        track_history_mode: int,
        window_size: int | None = 200,
        values: np.ndarray | None = None,
        history: None | list[int | float] = None,
    ) -> None:
        self.val = val
        self.key = key
        self.track_history_mode = track_history_mode
        self.window_size = window_size
        self.values = values
        self.history = history
        super().__init__(val, key, track_history_mode, window_size, values, history)

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.__str__()


class Series:
    keys: set
    key_mappings: dict[str | int, int]
    values: dict[type, np.ndarray | None]
    heads: dict[type, np.ndarray | None]
    head_positions: int
    window_size: int
    heads_assigned: set[int | str]
    series_types: dict[str | int, type]

    track_history_mode: int
    history: dict[str | int, list[int | float]] | None

    def __init__(
        self,
        key_value_pairs_int: dict[str | int, list[int]] = {},
        key_value_pairs_float: dict[str | int, list[float]] = {},
        track_history_mode: int = 0,
        window_size: int = 200,
        initial_update: bool = False,
        dtypes: dict[type, type] = {int: np.int64, float: np.float32},
    ) -> None:
        """
        Args:
        - key_value_pairs_[type]: Initial values for each series.
          Formated as a dict[string or int, numeric list of corrosponding type]
          with each list having equal length with at least length 1.
          Last value in each list is used as current head value.

        - (default:0) track_history_mode: one of [0, 1 ,2].
          (*WARNING*: track history will grow the list untill there is no memory left)
          0: track no history only use rolling window numpy array of window size.
          1: track history and dont use rolling window numpy array at all.
          2: Hybrid mode track history but use the numpy array for regular access if within window size.

        - (default:200) window_size: The size of the rolling window when using track_history_modes 0 or 2.

        - (default: int:int64 float:float128) dtypes: dtypes for np arrays of different source types.
        """
        self.keys = set()
        self.key_mappings = {}
        self.series_types = {}
        self.values = {}
        self.heads = {}
        self.track_history_mode = track_history_mode
        self.window_size = window_size

        if self.track_history_mode not in [0, 1, 2]:
            pass

        length_ticker = -1
        series_type_pairs = {int: key_value_pairs_int, float: key_value_pairs_float}

        for series_type in series_type_pairs.keys():
            key_value_pairs = series_type_pairs[series_type]
            for i, key in enumerate(key_value_pairs.keys()):
                if key in self.keys:
                    raise SeriesInvalidKeyValuePairs_Duplicate(key)

                if not isinstance(key, str | int):
                    raise SeriesInvalidKeyValuePairs_Format()

                self.keys.add(key)
                self.key_mappings[key] = i

                data = key_value_pairs[key]

                if not isinstance(data, list):
                    raise SeriesInvalidKeyValuePairs_Format()
                elif len(data) == 0:
                    raise SeriesInvalidKeyValuePairs_Zero()
                if length_ticker == -1:
                    length_ticker = len(data)
                elif len(data) != length_ticker:
                    raise SeriesInvalidKeyValuePairs_Length()
                for element in data:
                    if not isinstance(element, int | float):
                        raise SeriesInvalidKeyValuePairs_Numeric(key)

                self.series_types[key] = series_type

                if series_type == int:
                    self.heads[int] = np.zeros(
                        len(key_value_pairs.values()), dtype=dtypes[int]
                    )
                else:
                    self.heads[float] = np.zeros(
                        len(key_value_pairs.values()), dtype=dtypes[float]
                    )

                self.heads_assigned = set(key_value_pairs.keys())
                self.head_positions = length_ticker - 1

                if self.track_history_mode in [1, 2]:  # use unbounded history tracking
                    self.history = {}
                    for key in self.key_mappings.keys():
                        self.history[key] = []
                        if length_ticker != 1:
                            self.history[key] += copy.deepcopy(
                                key_value_pairs[key][:-1]
                            )

                        self.heads[series_type][self.key_mappings[key]] = copy.copy(
                            key_value_pairs[key][-1]
                        )

                if self.track_history_mode in [
                    0,
                    2,
                ]:  # use bounded rolling window tracking
                    if series_type == int:
                        self.values[int] = np.zeros(
                            (len(key_value_pairs.values()), window_size),
                            dtype=dtypes[int],
                        )
                    else:
                        self.values[float] = np.zeros(
                            (len(key_value_pairs.values()), window_size),
                            dtype=dtypes[float],
                        )

                    if length_ticker > 2:
                        self.values[series_type][ #type: ignore
                            i, -min([window_size, length_ticker - 2]) :
                        ] = np.array(key_value_pairs[key])[
                            -min([window_size, length_ticker - 1]) : -1]  # type: ignore

        if initial_update:
            self.update()

    def index(
        self, i: int, error: bool = False, key: str | None = None
    ) -> tuple[int, bool, bool]:
        overflow_window = False
        overflow_full = False
        if self.track_history_mode in [0, 2] and i > self.window_size - 1:  # type: ignore
            overflow_window = True
        elif self.track_history_mode in [1, 2] and i > len(tuple(self.history.values())[0]):  # type: ignore
            if error:
                raise SeriesIndexOutOfRange(key, i)
            overflow_full = True
        if not overflow_window:
            return i, overflow_window, overflow_full
        else:
            if self.track_history_mode == 0:
                if error:
                    raise SeriesIndexOutOfRange(key, i)
                return self.window_size - 1, overflow_window, overflow_full  # type: ignore
            else:
                return i, overflow_window, overflow_full

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

        index = self.index(self.head_positions + 1)
        self.head_positions = index[0]
        if self.track_history_mode in [0, 2]:
            if self.track_history_mode in [0, 2]:
                if int in self.values.keys():
                    self.values[int] = np.roll(self.values[int], (0, -1))  # type: ignore
                    self.values[int][:, -1] = self.heads[int]  # type: ignore
                if float in self.values.keys():
                    self.values[float] = np.roll(self.values[float], (0, -1))  # type: ignore
                    self.values[float][:, -1] = self.heads[float]  # type: ignore

        if self.track_history_mode in [1, 2]:
            for key in self.keys:
                self.history[key].append(self.heads[self.series_types[key]][self.key_mappings[key]])  # type: ignore

    def __getitem__(
        self, key: int | str
    ) -> SeriesHeadObjectFloat | SeriesHeadObjectInteger:
        if isinstance(key, list | tuple):
            raise InvalidSeriesIndex()

        if isinstance(key, str | int):
            if key in self.keys:
                if self.head_positions > 0:
                    values = None
                    history = None
                    if self.track_history_mode in [0, 2]:
                        values = self.values[self.series_types[key]][self.key_mappings[key]][:-1]  # type: ignore
                    if self.track_history_mode in [1, 2]:
                        history = self.history[key][:-1]  # type: ignore
                    if self.series_types[key] == int:
                        return SeriesHeadObjectInteger(
                            val=int(self.heads[int][self.key_mappings[key]]),
                            key=key,
                            track_history_mode=self.track_history_mode,
                            window_size=self.window_size,
                            values=values,
                            history=history,
                        )
                    else:
                        return SeriesHeadObjectFloat(
                            self.heads[float][self.key_mappings[key]],
                            key=key,
                            track_history_mode=self.track_history_mode,
                            window_size=self.window_size,
                            values=values,
                            history=history,
                        )
                else:
                    raise UnAssignedHead(key)
            else:
                raise NonExistentHead(key, "get")
        else:
            raise InvalidSeriesIndex()

    def __getattribute__(self, __name: str) -> Any:
        keys = None
        try:
            keys = object.__getattribute__(self,"keys")
        except:
            pass
        if keys and __name in keys:
            return self.__getitem__(__name)
        return object.__getattribute__(self,__name)

    def __setitem__(self, key: str | int, value: int | float) -> None:
        if isinstance(key, list | tuple):
            raise InvalidSeriesIndex

        if isinstance(key, str | int):
            if key in self.keys:
                self.heads[self.series_types[key]][self.key_mappings[key]] = self.series_types[key](value)
                self.heads_assigned.add(key)
            else:
                raise NonExistentHead(key, "set")
        else:
            raise InvalidSeriesIndex()

    def __setattr__(self, __name: str, __value: Any) -> None:
        keys = None
        try:
            keys = object.__getattribute__(self,"keys")
        except:
            pass
        if keys and __name in keys:
            self.__setitem__(__name,__value)
            return
        object.__setattr__(self,__name,__value)


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
            return "Series object received invalid indexing. Expected singular string or int series id as key"


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
        msg = f"Invalid index when indexing head object: {self.args[0]} ."
        return msg


class SeriesIndexOutOfRange(PyneSeriesException):
    """When an index is out of range

    Args:
    0. Head id
    1. Index
    """

    def __str__(self) -> str:
        msg = f"Index: {self.args[1]} out of range for head object: {self.args[0]} ."
        return msg


class SeriesCannotMutateHistory(PyneSeriesException):
    """When an item assignment is tried on a head object."""

    def __str__(self) -> str:
        return "Tried to assign to head object. History is immutable."


class SeriesInvalidKeyValuePairs_Length(PyneSeriesException):
    """When Series init reveives invalid key value pairs with differing lengths"""

    def __str__(self) -> str:
        return "Series init recieved invalid key value pairs. Found differing entry lenghts."


class SeriesInvalidKeyValuePairs_Format(PyneSeriesException):
    """When Series init reveives invalid key value pairs with invalid key types"""

    def __str__(self) -> str:
        msg = """Series init recieved invalid key value pairs: Invalid format. Dictionary of string or int keys and equal length numeric list value pairs excpected."""
        return msg

class SeriesInvalidKeyValuePairs_Duplicate(PyneSeriesException):
    """When Series init reveives key value pairs with duplicate keys

    Args:
    0. Key
    """

    def __str__(self) -> str:
        msg = f"Series init recieved invalid key value pairs: Found duplicate key in key value pairs: {self.args[0]}."
        return msg


class SeriesInvalidKeyValuePairs_Numeric(PyneSeriesException):
    """When Series init reveives invalid key value pairs with non numeric list element

    Args:
    0.key
    """

    def __str__(self) -> str:
        msg = f"Series init recieved invalid key value pairs: Found non numeric element in list value with key: {self.args[0]}."
        return msg


class SeriesInvalidKeyValuePairs_Zero(PyneSeriesException):
    """When Series init reveives invalid key value pairs with list of length zero"""

    def __str__(self) -> str:
        return "Series init recieved invalid key value pairs: List values must have at least one element."
