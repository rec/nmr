from . _type import Type


class Hex(Type):
    @staticmethod
    def type_to_int(s: str):
        s = s.lower()
        if s.startswith('0x'):
            return int(s[2:], 16)
        if s.startswith('-0x'):
            return -int(s[2:], 16)

    int_to_type = staticmethod(hex)
