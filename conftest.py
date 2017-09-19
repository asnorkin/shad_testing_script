import functools
import pytest
import time
import types
from logging import getLogger
from subprocess import Popen, PIPE
from input_token import get_token_generator
from input_generation import user_input_generator


DELIMITER = "; "


def get_input_generator_from_list(lst):
    def _generator():
        for line in lst:
            yield line

    return _generator


def get_input_generator(request, iterations):
    input = request.config.getoption("--input")
    if not input:
        input = user_input_generator(iterations)
        if not input:
            raise ValueError("No input data expression or file or user defined function specified")

        if isinstance(input, types.GeneratorType):
            return input
        elif isinstance(input, list):
            return get_input_generator_from_list(input)
        else:
            raise TypeError("User defined functions has wrong return value type: {type}."
                            "Expected: generator or list".format(type=type(input)))

    # File input
    if input[0] not in ["[", "{", "("]:
        with open(input, "r") as fin:
            input = fin.readlines()
        return get_input_generator_from_list(input)

    tokens = input.split(DELIMITER)
    token_generators = []
    for token in tokens:
        token_generator = get_token_generator(token)
        token_generators.append(token_generator)

    def _input_generator():
        for _ in range(iterations):
            input = []
            for gen in token_generators:
                s = next(gen())
                input.append(s)

            yield " ".join(input)

    return _input_generator


@pytest.fixture()
def log(request):
    log_level = request.config.getoption("--log")
    _log = getLogger()
    _log.setLevel(log_level)
    return _log


@pytest.fixture()
def iterations(request):
    return int(request.config.getoption("--iterations"))


@pytest.fixture()
def input_generator(request, iterations):
    return get_input_generator(request, iterations)


@pytest.fixture()
def solutions(request):
    return request.config.getoption("--solutions").split()


@pytest.fixture()
def estimator(request, log):
    timeout = request.config.getoption("--timeout")
    memory_limit = request.config.getoption("--memory_limit")
    return get_estimator(timeout=timeout, memory_limit=memory_limit, log=log)


def get_estimator(timeout, memory_limit, log):
    def _estimator(solution, input):
        # TODO: memory check
        start_memory = 0
        start_time = time.time()
        output = run_process(solution, input)
        delta_time = time.time() - start_time
        delta_memory = 0 - start_memory
        if delta_time > timeout:
            log.warning("Timout exceeded: {time}s > {timeout}s\n"
                        "Solution: {solution}\n"
                        "Input: {input}"
                        .format(time=delta_time, timeout=timeout,
                                solution=solution, input=input))
        if delta_memory > memory_limit:
            pass
        return round(delta_time, 3), delta_memory, output

    return _estimator


def run_process(solution, input):
    proc = Popen("./" + solution, stdin=PIPE, stdout=PIPE)
    proc.stdin.write(bytes(input + "\n", "utf-8"))
    proc.stdin.flush()
    return str(proc.stdout.read())


def pytest_addoption(parser):
    parser.addoption("--iterations", help="Number of tests run", default=float("inf"))
    parser.addoption("--solutions", help="Filename of solution")
    parser.addoption("--input", help="Input parameters")
    parser.addoption("--timeout", help="Timeout in seconds", default=1)
    parser.addoption("--memory_limit", help="Memory limit", default=1)
    parser.addoption("--log", help="Log level", default="INFO")

