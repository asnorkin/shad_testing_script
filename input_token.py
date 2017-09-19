import random
import re


LEFT_LIMIT = r"[\[\(]-?\d+\.?\d*"
RIGHT_LIMIT = r"-?\d+\.?\d*[\]\)]"
RANGE_TOKEN = LEFT_LIMIT + ", " + RIGHT_LIMIT
INT_TOKEN = r"[\[\(]-?\d+, -?\d+[\]\)]"
FLOAT_TOKEN = r"[\[\(]-?\d+\.\d*, -?\d+\.\d*[\]\)]"
SET_TOKEN = r"{.+}"
# TODO: make this inside one regexp
SEQ_OF_RANGE_TOKEN = r"\[" + RANGE_TOKEN + r", len=" + INT_TOKEN + r"\]"
SEQ_OF_SET_TOKEN = r"\[" + SET_TOKEN + r", len=" + INT_TOKEN + r"\]"
SEQ_LENGTH = r"len=" + INT_TOKEN


TOKEN_PATTERNS = {
    "range_token": re.compile(RANGE_TOKEN),
    "int_token": re.compile(INT_TOKEN),
    "float_token": re.compile(FLOAT_TOKEN),
    "left_limit": re.compile(LEFT_LIMIT),
    "right_limit": re.compile(RIGHT_LIMIT),

    "set_token": re.compile(SET_TOKEN),

    "seq_of_range_token": re.compile(SEQ_OF_RANGE_TOKEN),
    "seq_of_set_token": re.compile(SEQ_OF_SET_TOKEN),
    "seq_length": re.compile(SEQ_LENGTH),
}


def get_token_generator(token):
    if TOKEN_PATTERNS["int_token"].fullmatch(token):
        return IntToken(token).get_generator()
    elif TOKEN_PATTERNS["float_token"].fullmatch(token):
        return FloatToken(token).get_generator()
    elif TOKEN_PATTERNS["set_token"].fullmatch(token):
        return SetToken(token).get_generator()
    elif TOKEN_PATTERNS["seq_of_range_token"].fullmatch(token) \
            or TOKEN_PATTERNS["seq_of_set_token"].fullmatch(token):
        return SeqToken(token).get_generator()
    else:
        raise ValueError("Wrong input pattern")


class BaseToken:
    def __init__(self, token_str):
        self.token_str = token_str


class ValueToken(BaseToken):
    pass


class RangeToken(ValueToken):
    def __init__(self, token_str):
        super().__init__(token_str)
        self.left_limit = self.__get_left_limit()
        self.right_limit = self.__get_right_limit()

    def __get_left_limit(self):
        left_limit_bracket = TOKEN_PATTERNS["left_limit"].findall(self.token_str)[0][0]
        left_limit_str = TOKEN_PATTERNS["left_limit"].findall(self.token_str)[0][1:]

        if "." in left_limit_str:
            return float(left_limit_str)
        else:
            if left_limit_bracket == "[":
                return int(left_limit_str)
            else:
                return int(left_limit_str) + 1

    def __get_right_limit(self):
        right_limit_bracket = TOKEN_PATTERNS["right_limit"].findall(self.token_str)[0][-1]
        right_limit_str = TOKEN_PATTERNS["right_limit"].findall(self.token_str)[0][:-1]

        if "." in right_limit_str:
            return float(right_limit_str)
        else:
            if right_limit_bracket == "]":
                return int(right_limit_str)
            else:
                return int(right_limit_str) - 1


class SetToken(ValueToken):
    def __init__(self, token_str):
        super().__init__(token_str)
        self.set = self.__get_set_of_values()

    def get_generator(self):
        def _generator():
            while True:
                yield random.sample(self.set, 1)[0]

        return _generator

    def __get_set_of_values(self):
        return set(self.token_str.strip("{}").split(", "))


class IntToken(RangeToken):
    def get_generator(self):
        def _generator():
            while True:
                yield str(random.randint(self.left_limit, self.right_limit))

        return _generator


class FloatToken(RangeToken):
    def get_generator(self):
        def _generator():
            while True:
                yield str(random.random() * (self.right_limit - self.left_limit) + self.left_limit)

        return _generator


class SeqToken(BaseToken):
    def __init__(self, token_str):
        super().__init__(token_str)
        self.length_generator = self.__get_length_generator()
        self.element_generator = self.__get_elemet_generator()

    def get_generator(self):
        def _generator():
            length = int(next(self.length_generator()))
            seq = [next(self.element_generator()) for _ in range(length)]
            yield " ".join(seq)

        return _generator

    def __get_length_generator(self):
        length_str = TOKEN_PATTERNS["seq_length"].findall(self.token_str)[0][4:]
        return IntToken(length_str).get_generator()

    def __get_elemet_generator(self):
        if TOKEN_PATTERNS["seq_of_range_token"].fullmatch(self.token_str):
            element_str = TOKEN_PATTERNS["range_token"].findall(self.token_str)[0]
        else:
            element_str = TOKEN_PATTERNS["set_token"].findall(self.token_str)[0]

        return get_token_generator(element_str)
