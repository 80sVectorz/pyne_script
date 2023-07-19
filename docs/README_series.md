# Pyne Script series.py

`series.py` is a Pyne Script sub-module that adds a Series class, which allows for time-series data to be accessed and manipulated in close to completely the same ways as in Pine Script.

## Usage

```python
from pyne_script.series import Series

series = Series(
    key_value_pairs_int={"a": list(range(0, 6))},
    track_history_mode=2,
    initial_update=True,
)

# "a" should look like this : past<-[0,1,2,3,4,5,.]->future
#                                              ^ ^
#                                              | |-After update the head moves here
#                                              |- Head is currently here. Update would finalize this value
#

print(series.a)  # should be 5
print(series.a[1])  # should be 4
series.a = 6
series.update()
print(series.a)  # should be 6
print(series.a[1])  # should be 5

```
First you create a master Series object which will store all time-series data. You have to declare the keys you want to use up-front. Here we create an integer series with name "a". We enable initial_update which will push the last value onto the series. We use `track_history_mode = 2` which is the hybrid mode. The series stores a fixed window NumPy array which is used for data queries that are inside the bounds. But it also keeps track of history in an unbounded list. It is recommended to use `track_history_mode = 0` in production and only use unbounded history while debugging or developing.

You can access each series using one of the following formats:
```python
series_object_a.series_b
series_object_a["series_b"]
```
