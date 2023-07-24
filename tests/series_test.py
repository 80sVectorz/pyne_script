from pyne_script.series import Series

def test_series_short():
    for history_mode in [0,1,2]:

        print("History_mode:",history_mode)
        for key in ["a","b"]:
            series = Series(
                key_value_pairs_int={"a": list(range(0, 6)),"b":list(range(0,6))},
                track_history_mode=history_mode,
                initial_update=True,
                window_size=10
            )
            print("Key:",key)

            assert series[key] == 5
            assert series[key][1] == 4

            series["a"] = 6
            series["b"] = 6
            series.update()
            assert series[key] == 6
            assert series[key][1] == 5

            assert list(series[key][:]) == [0,1,2,3,4,5,6]
            assert list(series[key][3:]) == [4,5,6]

def test_series_long():
    for history_mode in [0,1,2]:
        series = Series(
            key_value_pairs_int={"a": list(range(0, 20))},
            track_history_mode=history_mode,
            initial_update=True,
            window_size=10
        )
        print("History_mode:",history_mode)


        assert series.a == 19
        assert series.a[1] == 18

        series.a = 20
        series.update()
        assert series.a == 20
        assert series.a[1] == 19

        if history_mode ==0:
            assert list(series.a[:]) == [11,12,13,14,15,16,17,18,19,20]
        assert list(series.a[3:]) == [18,19,20]
