import random
from string import ascii_lowercase


def rand_str(alphabet, length):
    return ''.join([random.choice(alphabet) for _ in range(length)])


def user_input_generator(iterations):
    """
        Function for input generation
        iterations: int
            number of iterations, specified by --iterations flag

        return: generator object or list
    """
    def _generator():
        def generate_call():
            hour = random.randint(0, 23)
            if hour < 10:
                hour = '0' + str(hour)

            minute = random.randint(0, 59)
            if minute < 10:
                minute = '0' + str(minute)

            def generate_point():
                return random.randint(1, 200), random.randint(1, 200)

            start = generate_point()
            finish = generate_point()
            return '{}:{} {} {} {} {}'\
                .format(hour, minute, start[0], start[1], finish[0], finish[1])

        for _ in range(iterations):
            n = random.randint(1, 500)

            calls = []
            for _ in range(n):
                calls.append(generate_call())

            calls.sort()

            yield '\n'.join([str(n)] + calls)

    return _generator

