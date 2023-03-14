
#   _____        _
#  / ____|      | |
# | |      ___  | |  ___   _ __
# | |     / _ \ | | / _ \ | '__|
# | |____| (_) || || (_) || |
#  \_____|\___/ |_| \___/ |_|


"""
Everything Is Better With Color
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

color.py adds simple addition of color to the builtin print and input functions

It is often easier to view data when color is used to allow quick analysis of fast moving logs

"""

__title__ = 'color'
__description__ = "Simple addition of color to the builtin print and input functions"
__version__ = '1.0.0'
__author__ = 'CodingYuno'

named_colors = {
    'black': 0,
    'maroon': 1,
    'green': 46,
    'olive': 3,
    'navy': 4,
    'purple': 5,
    'plum': 219,
    'gold': 178,
    'pink': 13,
    'slate': 99,
    'magenta': 201,
    'orange': 214,
    'purple (system)': 129,
    'teal': 6,
    'silver': 7,
    'grey': 8,
    'red': 9,
    'lime': 10,
    'yellow': 11,
    'blue': 12,
    'fuchsia': 13,
    'aqua': 14,
    'white': 15,
    'grey0': 16,
    'navyblue': 17,
    'darkblue': 18,
    'blue3': 20,
    'blue1': 21,
    'darkgreen': 22,
    'deepskyblue4': 25,
    'dodgerblue3': 26,
    'dodgerblue2': 27,
    'green4': 28,
    'springgreen4': 29,
    'turquoise4': 30,
    'deepskyblue3': 32,
    'dodgerblue1': 33,
    'green3': 40,
    'springgreen3': 41,
    'darkcyan': 36,
    'lightseagreen': 37,
    'deepskyblue2': 38,
    'deepskyblue1': 39,
    'springgreen2': 47,
    'cyan3': 43,
    'darkturquoise': 44,
    'turquoise2': 45,
    'green1': 2,
    'springgreen1': 48,
    'mediumspringgreen': 49,
    'cyan2': 50,
    'cyan1': 51,
     'cyan': 51,
    'darkred': 88,
    'deeppink4': 125,
    'purple4': 55,
    'purple3': 56,
    'blueviolet': 57,
    'orange4': 94,
    'grey37': 59,
    'mediumpurple4': 60,
    'slateblue3': 62,
    'royalblue1': 63,
    'chartreuse4': 64,
    'darkseagreen4': 71,
    'paleturquoise4': 66,
    'steelblue': 67,
    'steelblue3': 68,
    'cornflowerblue': 69,
    'chartreuse3': 76,
    'cadetblue': 73,
    'skyblue3': 74,
    'steelblue1': 81,
    'palegreen3': 114,
    'seagreen3': 78,
    'aquamarine3': 79,
    'mediumturquoise': 80,
    'chartreuse2': 112,
    'seagreen2': 83,
    'seagreen1': 85,
    'aquamarine1': 122,
    'darkslategray2': 87,
    'darkmagenta': 91,
    'darkviolet': 128,
    'lightpink4': 95,
    'plum4': 96,
    'mediumpurple3': 98,
    'slateblue1': 99,
    'yellow4': 106,
    'wheat4': 101,
    'grey53': 102,
    'lightslategrey': 103,
    'mediumpurple': 104,
    'lightslateblue': 105,
    'darkolivegreen3': 149,
    'darkseagreen': 108,
    'lightskyblue3': 110,
    'skyblue2': 111,
    'darkseagreen3': 150,
    'darkslategray3': 116,
    'skyblue1': 117,
    'chartreuse1': 118,
    'lightgreen': 120,
    'palegreen1': 156,
    'darkslategray1': 123,
    'red3': 160,
    'mediumvioletred': 126,
    'magenta3': 164,
    'darkorange3': 166,
    'indianred': 167,
    'hotpink3': 168,
    'mediumorchid3': 133,
    'mediumorchid': 134,
    'mediumpurple2': 140,
    'darkgoldenrod': 136,
    'lightsalmon3': 173,
    'rosybrown': 138,
    'brown': 138,
    'grey63': 139,
    'mediumpurple1': 141,
    'gold3': 178,
    'darkkhaki': 143,
    'navajowhite3': 144,
    'grey69': 145,
    'lightsteelblue3': 146,
    'lightsteelblue': 147,
    'yellow3': 184,
    'darkseagreen2': 157,
    'lightcyan3': 152,
    'lightskyblue1': 153,
    'greenyellow': 154,
    'darkolivegreen2': 155,
    'darkseagreen1': 193,
    'paleturquoise1': 159,
    'deeppink3': 162,
    'magenta2': 200,
    'hotpink2': 169,
    'orchid': 170,
    'mediumorchid1': 207,
    'orange3': 172,
    'lightpink3': 174,
    'pink3': 175,
    'plum3': 176,
    'violet': 177,
    'lightgoldenrod3': 179,
    'tan': 180,
    'mistyrose3': 181,
    'thistle3': 182,
    'plum2': 183,
    'khaki3': 185,
    'lightgoldenrod2': 222,
    'lightyellow3': 187,
    'grey84': 188,
    'lightsteelblue1': 189,
    'yellow2': 190,
    'darkolivegreen1': 192,
    'honeydew2': 194,
    'lightcyan1': 195,
    'red1': 196,
    'deeppink2': 197,
    'deeppink1': 199,
    'magenta1': 201,
    'orangered1': 202,
    'indianred1': 204,
    'hotpink': 206,
    'darkorange': 208,
    'salmon1': 209,
    'lightcoral': 210,
    'palevioletred1': 211,
    'orchid2': 212,
    'orchid1': 213,
    'orange1': 214,
    'sandybrown': 215,
    'lightsalmon1': 216,
    'lightpink1': 217,
    'pink1': 218,
    'plum1': 219,
    'gold1': 220,
    'navajowhite1': 223,
    'mistyrose1': 224,
    'thistle1': 225,
    'yellow1': 226,
    'lightgoldenrod1': 227,
    'khaki1': 228,
    'wheat1': 229,
    'cornsilk1': 230,
    'grey100': 231,
    'grey3': 232,
    'grey7': 233,
    'grey11': 234,
    'grey15': 235,
    'grey19': 236,
    'grey23': 237,
    'grey27': 238,
    'grey30': 239,
    'grey35': 240,
    'grey39': 241,
    'grey42': 242,
    'grey46': 243,
    'grey50': 244,
    'grey54': 245,
    'grey58': 246,
    'grey62': 247,
    'grey66': 248,
    'grey70': 249,
    'grey74': 250,
    'grey78': 251,
    'grey82': 252,
    'grey85': 253,
    'grey89': 254,
    'grey93': 255
}


def color_conversion(color):
    return named_colors[color.lower()] if str(color).lower() in named_colors.keys() else color


def color_string(color):
    return '\x1b[38;2;{};{};{}m'.format(*tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))) if "#" in str(color) else f'\033[38;5;{color}m'


def color_print(*args, sep: str = " ", end: str = "\n", color: int | str = "#FFFFFF", **kwargs) -> None:
    """
    end is added to the core string if end == \n making color_print a threadsafe line print

    :argument color:
    - Can be hex e.g. #FFFFFF
    - Can be terminal number code e.g. 0 is black
    - Can be any of the following colors:
        "black", "maroon", "green", "olive", "navy", "purple", "plum", "gold", "pink", "slate", "magenta", "orange",
        "purple (system)", "teal", "silver", "grey", "red", "lime", "yellow", "blue", "fuchsia", "aqua", "white",
        "grey0", "navyblue", "darkblue", "blue3", "blue1", "darkgreen", "deepskyblue4", "dodgerblue3", "dodgerblue2",
        "green4", "springgreen4", "turquoise4", "deepskyblue3", "dodgerblue1", "green3", "springgreen3", "darkcyan",
        "lightseagreen", "deepskyblue2", "deepskyblue1", "springgreen2", "cyan3", "darkturquoise", "turquoise2",
        "green1", "springgreen1", "mediumspringgreen", "cyan2", "cyan1", "darkred", "deeppink4", "purple4",
        "purple3", "blueviolet", "orange4", "grey37", "mediumpurple4", "slateblue3", "royalblue1", "chartreuse4",
        "darkseagreen4", "paleturquoise4", "steelblue", "steelblue3", "cornflowerblue", "chartreuse3", "cadetblue",
        "skyblue3", "steelblue1", "palegreen3", "seagreen3", "aquamarine3", "mediumturquoise", "chartreuse2",
        "seagreen2", "seagreen1", "aquamarine1", "darkslategray2", "darkmagenta", "darkviolet", "lightpink4",
        "plum4", "mediumpurple3", "slateblue1", "yellow4", "wheat4", "grey53", "lightslategrey", "mediumpurple",
        "lightslateblue", "darkolivegreen3", "darkseagreen", "lightskyblue3", "skyblue2", "darkseagreen3",
        "darkslategray3", "skyblue1", "chartreuse1", "lightgreen", "palegreen1", "darkslategray1", "red3",
        "mediumvioletred", "magenta3", "darkorange3", "indianred", "hotpink3", "mediumorchid3", "mediumorchid",
        "mediumpurple2", "darkgoldenrod", "lightsalmon3", "rosybrown", "grey63", "mediumpurple1", "gold3", "darkkhaki",
        "navajowhite3", "grey69", "lightsteelblue3", "lightsteelblue", "yellow3", "darkseagreen2", "lightcyan3",
        "lightskyblue1", "greenyellow", "darkolivegreen2", "darkseagreen1", "paleturquoise1", "deeppink3", "magenta2",
        "hotpink2", "orchid", "mediumorchid1", "orange3", "lightpink3", "pink3", "plum3", "violet", "lightgoldenrod3",
        "tan", "mistyrose3", "thistle3", "plum2", "khaki3", "lightgoldenrod2", "lightyellow3", "grey84",
        "lightsteelblue1", "yellow2", "darkolivegreen1", "honeydew2", "lightcyan1", "red1", "deeppink2", "deeppink1",
        "magenta1", "orangered1", "indianred1", "hotpink", "darkorange", "salmon1", "lightcoral", "palevioletred1",
        "orchid2", "orchid1", "orange1", "sandybrown", "brown", "lightsalmon1", "lightpink1", "pink1", "plum1", "gold1",
        "navajowhite1", "mistyrose1", "thistle1", "yellow1", "lightgoldenrod1", "khaki1", "wheat1", "cornsilk1",
        "grey100", "grey3", "grey7", "grey11", "grey15", "grey19", "grey23", "grey27", "grey30", "grey35", "grey39",
        "grey42", "grey46", "grey50", "grey54", "grey58", "grey62", "grey66", "grey70", "grey74", "grey78", "grey82",
        "grey85", "grey89", "grey93"'

    - swaps: green: 2 -> 46
             green1: 46 -> 2
             purple: 129 -> 5
             purple (system): 5 -> 129
    - extra: plum: 219
             gold: 178
             slate: 99
             magenta: 201
             orange: 214
             pink: 13
             brown: 138

    :argument sep:   string inserted between values, default a space.
    :argument end:   string appended after the last value, default a newline.
    """
    print(f'{color_string(color_conversion(color))}{sep.join([str(arg) for arg in args])}\x1b[0m{end}', sep=sep, end=end if end != "\n" else "", **kwargs)


def color_input(prompt: str, color: int | str = "#FFFFFF") -> str:
    """
    :param prompt: The prompt string, if given, is printed to standard output without a
    trailing newline before reading input.

    If the user hits EOF (*nix: Ctrl-D, Windows: Ctrl-Z+Return), raise EOFError.
    On *nix systems, readline is used if available.

    :param color:
    - Can be hex e.g. #FFFFFF
    - Can be terminal number code e.g. 0 is black
    - Can be any of the following colors:
        "black", "maroon", "green", "olive", "navy", "purple", "plum", "gold", "pink", "slate", "magenta", "orange",
        "purple (system)", "teal", "silver", "grey", "red", "lime", "yellow", "blue", "fuchsia", "aqua", "white",
        "grey0", "navyblue", "darkblue", "blue3", "blue1", "darkgreen", "deepskyblue4", "dodgerblue3", "dodgerblue2",
        "green4", "springgreen4", "turquoise4", "deepskyblue3", "dodgerblue1", "green3", "springgreen3", "darkcyan",
        "lightseagreen", "deepskyblue2", "deepskyblue1", "springgreen2", "cyan3", "darkturquoise", "turquoise2",
        "green1", "springgreen1", "mediumspringgreen", "cyan2", "cyan1", "darkred", "deeppink4", "purple4",
        "purple3", "blueviolet", "orange4", "grey37", "mediumpurple4", "slateblue3", "royalblue1", "chartreuse4",
        "darkseagreen4", "paleturquoise4", "steelblue", "steelblue3", "cornflowerblue", "chartreuse3", "cadetblue",
        "skyblue3", "steelblue1", "palegreen3", "seagreen3", "aquamarine3", "mediumturquoise", "chartreuse2",
        "seagreen2", "seagreen1", "aquamarine1", "darkslategray2", "darkmagenta", "darkviolet", "lightpink4",
        "plum4", "mediumpurple3", "slateblue1", "yellow4", "wheat4", "grey53", "lightslategrey", "mediumpurple",
        "lightslateblue", "darkolivegreen3", "darkseagreen", "lightskyblue3", "skyblue2", "darkseagreen3",
        "darkslategray3", "skyblue1", "chartreuse1", "lightgreen", "palegreen1", "darkslategray1", "red3",
        "mediumvioletred", "magenta3", "darkorange3", "indianred", "hotpink3", "mediumorchid3", "mediumorchid",
        "mediumpurple2", "darkgoldenrod", "lightsalmon3", "rosybrown", "grey63", "mediumpurple1", "gold3", "darkkhaki",
        "navajowhite3", "grey69", "lightsteelblue3", "lightsteelblue", "yellow3", "darkseagreen2", "lightcyan3",
        "lightskyblue1", "greenyellow", "darkolivegreen2", "darkseagreen1", "paleturquoise1", "deeppink3", "magenta2",
        "hotpink2", "orchid", "mediumorchid1", "orange3", "lightpink3", "pink3", "plum3", "violet", "lightgoldenrod3",
        "tan", "mistyrose3", "thistle3", "plum2", "khaki3", "lightgoldenrod2", "lightyellow3", "grey84",
        "lightsteelblue1", "yellow2", "darkolivegreen1", "honeydew2", "lightcyan1", "red1", "deeppink2", "deeppink1",
        "magenta1", "orangered1", "indianred1", "hotpink", "darkorange", "salmon1", "lightcoral", "palevioletred1",
        "orchid2", "orchid1", "orange1", "sandybrown", "brown", "lightsalmon1", "lightpink1", "pink1", "plum1", "gold1",
        "navajowhite1", "mistyrose1", "thistle1", "yellow1", "lightgoldenrod1", "khaki1", "wheat1", "cornsilk1",
        "grey100", "grey3", "grey7", "grey11", "grey15", "grey19", "grey23", "grey27", "grey30", "grey35", "grey39",
        "grey42", "grey46", "grey50", "grey54", "grey58", "grey62", "grey66", "grey70", "grey74", "grey78", "grey82",
        "grey85", "grey89", "grey93"'

    - swaps: green: 2 -> 46
             green1: 46 -> 2
             purple: 129 -> 5
             purple (system): 5 -> 129
    - extra: plum: 219
             gold: 178
             slate: 99
             magenta: 201
             orange: 214
             pink: 13
             brown: 138
    """
    return input(f"{color_string(color_conversion(color))}{prompt}\x1b[0m")


class Color:
    """
    Usage:

    >>> print(Color(1, 2, 3, color="green"), "\t", Color("hello", color="orange"), "\t", Color([{}, ()], color="blue"))

    1 2 3   hello   [{}, ()]
      ^       ^        ^
      |       |        |__ blue
      |       |__ orange
      |__ green

    """
    def __init__(self, *args, color: int | str = "#FFFFFF", sep: str = " ", end: str = ""):
        """
            end is added to the core string if end == \n making color_print a threadsafe line print

            :argument color:
            - Can be hex e.g. #FFFFFF
            - Can be terminal number code e.g. 0 is black
            - Can be any of the following colors:
                "black", "maroon", "green", "olive", "navy", "purple", "plum", "gold", "pink", "slate", "magenta", "orange",
                "purple (system)", "teal", "silver", "grey", "red", "lime", "yellow", "blue", "fuchsia", "aqua", "white",
                "grey0", "navyblue", "darkblue", "blue3", "blue1", "darkgreen", "deepskyblue4", "dodgerblue3", "dodgerblue2",
                "green4", "springgreen4", "turquoise4", "deepskyblue3", "dodgerblue1", "green3", "springgreen3", "darkcyan",
                "lightseagreen", "deepskyblue2", "deepskyblue1", "springgreen2", "cyan3", "darkturquoise", "turquoise2",
                "green1", "springgreen1", "mediumspringgreen", "cyan2", "cyan1", "darkred", "deeppink4", "purple4",
                "purple3", "blueviolet", "orange4", "grey37", "mediumpurple4", "slateblue3", "royalblue1", "chartreuse4",
                "darkseagreen4", "paleturquoise4", "steelblue", "steelblue3", "cornflowerblue", "chartreuse3", "cadetblue",
                "skyblue3", "steelblue1", "palegreen3", "seagreen3", "aquamarine3", "mediumturquoise", "chartreuse2",
                "seagreen2", "seagreen1", "aquamarine1", "darkslategray2", "darkmagenta", "darkviolet", "lightpink4",
                "plum4", "mediumpurple3", "slateblue1", "yellow4", "wheat4", "grey53", "lightslategrey", "mediumpurple",
                "lightslateblue", "darkolivegreen3", "darkseagreen", "lightskyblue3", "skyblue2", "darkseagreen3",
                "darkslategray3", "skyblue1", "chartreuse1", "lightgreen", "palegreen1", "darkslategray1", "red3",
                "mediumvioletred", "magenta3", "darkorange3", "indianred", "hotpink3", "mediumorchid3", "mediumorchid",
                "mediumpurple2", "darkgoldenrod", "lightsalmon3", "rosybrown", "grey63", "mediumpurple1", "gold3", "darkkhaki",
                "navajowhite3", "grey69", "lightsteelblue3", "lightsteelblue", "yellow3", "darkseagreen2", "lightcyan3",
                "lightskyblue1", "greenyellow", "darkolivegreen2", "darkseagreen1", "paleturquoise1", "deeppink3", "magenta2",
                "hotpink2", "orchid", "mediumorchid1", "orange3", "lightpink3", "pink3", "plum3", "violet", "lightgoldenrod3",
                "tan", "mistyrose3", "thistle3", "plum2", "khaki3", "lightgoldenrod2", "lightyellow3", "grey84",
                "lightsteelblue1", "yellow2", "darkolivegreen1", "honeydew2", "lightcyan1", "red1", "deeppink2", "deeppink1",
                "magenta1", "orangered1", "indianred1", "hotpink", "darkorange", "salmon1", "lightcoral", "palevioletred1",
                "orchid2", "orchid1", "orange1", "sandybrown", "brown", "lightsalmon1", "lightpink1", "pink1", "plum1", "gold1",
                "navajowhite1", "mistyrose1", "thistle1", "yellow1", "lightgoldenrod1", "khaki1", "wheat1", "cornsilk1",
                "grey100", "grey3", "grey7", "grey11", "grey15", "grey19", "grey23", "grey27", "grey30", "grey35", "grey39",
                "grey42", "grey46", "grey50", "grey54", "grey58", "grey62", "grey66", "grey70", "grey74", "grey78", "grey82",
                "grey85", "grey89", "grey93"'

            - swaps: green: 2 -> 46
                     green1: 46 -> 2
                     purple: 129 -> 5
                     purple (system): 5 -> 129
            - extra: plum: 219
                     gold: 178
                     slate: 99
                     magenta: 201
                     orange: 214
                     pink: 13
                     brown: 138

            :argument sep:   string inserted between values, default a space.
            :argument end:   string appended after the last value, default "".
            """
        self.string = f'{color_string(color_conversion(color))}{sep.join([str(arg) for arg in args])}\x1b[0m{end}'

    def __repr__(self) -> str:
        return self.string
