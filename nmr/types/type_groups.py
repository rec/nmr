from enum import IntEnum, auto


class Group(IntEnum):
    math = auto()
    science = auto()
    music = auto()
    place = auto()
    time = auto()
    network = auto()
    game = auto()
    commercial = auto()
    other = auto()


class Math(IntEnum):
    integer = auto()
    fraction = auto()


class Science(IntEnum):
    element = auto()
    unit = auto()


class Music(IntEnum):
    rhythm = auto()
    melody = auto()


class Place(IntEnum):
    lat_long = auto()


class Network(IntEnum):
    ip_address = auto()
    sem_ver = auto()
    uuid = auto()


class Game(IntEnum):
    backgammon = auto()
    cards = auto()
    chess = auto()
    go = auto()


class Commercial(IntEnum):
    isbn = auto()
    upc = auto()
