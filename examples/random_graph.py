import random
import time
from pyne_script.series import Series

from rich import print as rich_print
from rich.traceback import install

install(show_locals=True)


def draw(series: Series, clear=False) -> None:
    def clear_screen():
        print("\u001b[?1049h", sep="")  # enable alternate screen buffer

    def blit(buffer):
        print("\u001b[H", sep="")
        rich_print(buffer, sep="")

    def to_screen(value) -> int:
        return range(window_height)[
            round((value - hist_min) / full_range * (window_height - 1))
        ]

    hist_min = 0
    hist_max = 0

    for i in range(window_width):
        hist_min = min(hist_min, series.low[i])
        hist_max = max(hist_max, series.high[i])

    full_range = hist_max - hist_min

    zero_line = to_screen(0)

    buffer = ""
    for line in range(window_height):
        line = window_height - line
        line_buffer = ""
        for collumn in range(window_width):
            character = " "

            direction = series.direction[window_width - collumn]
            open_point = to_screen(series.open[window_width - collumn])
            close_point = to_screen(series.close[window_width - collumn])
            high_point = to_screen(series.high[window_width - collumn])
            low_point = to_screen(series.low[window_width - collumn])
            body_range = list(
                range(min([open_point, close_point]), max([open_point, close_point]))
            )
            wick_range = list(range(low_point, high_point))

            if line in body_range:
                if direction > 0:
                    character = "[green]\u2588[/]"
                if direction < 0:
                    character = "[red]\u2588[/]"
            elif line in wick_range:
                character = "[bold white]\u2502[/]"
            if line == zero_line:
                character = f"[strike]{character}[/]"
            line_buffer += character

        if line != window_height - 1:
            line_buffer += "\n"
        buffer += line_buffer

    if clear:
        clear_screen()

    blit(buffer)


length = 500
delay = 0.25
window_width = 160
window_height = 49


symbol = Series(
    key_value_pairs_float={
        "open": [0, 0],
        "close": [0, 0],
        "low": [0, 0],
        "high": [0, 0],
        "direction": [0, 0],
    },
    window_size=window_width + 1,
    track_history_mode=0,
    initial_update=True,
)

for i in range(length):
    symbol.open = symbol.close
    symbol.close = symbol.open + random.uniform(-1, 1)
    symbol.direction = 1
    if symbol.open > symbol.close:
        symbol.direction = -1

    candle_size = abs(symbol.close - symbol.open)
    candle_bottom = min([symbol.open, symbol.close])
    candle_top = max([symbol.open, symbol.close])

    symbol.low = candle_bottom - candle_size * random.uniform(0, 1)
    symbol.high = candle_top + candle_size * random.uniform(0, 1)
    symbol.update()

    if i > window_width:
        draw(symbol, i == window_width + 1)
        time.sleep(delay)
