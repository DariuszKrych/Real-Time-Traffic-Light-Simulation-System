from render import *


def main():
    window_dimensions, window, renderer = create_window()
    draw_junction(window_dimensions, window, renderer)


if __name__ == "__main__":
    main()