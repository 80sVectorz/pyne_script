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
