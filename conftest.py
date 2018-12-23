import pytest
import sys
from inspect import isgeneratorfunction
from logging import getLogger
from subprocess import Popen, PIPE
from re import search
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

        if isgeneratorfunction(input):
            return input
        elif isinstance(input, list):
            return get_input_generator_from_list(input)
        else:
            raise TypeError("User defined functions has wrong return value type: {type}."
                            "Expected: generator or list".format(type=type(input)))

    # File input
    with open(input, "r") as fin:
        input = fin.readlines()
    return get_input_generator_from_list(input)


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
def solutions(request, log):
    _solutions = request.config.getoption("--solutions").split()
    for _idx, _sol in enumerate(_solutions):
        if _sol.rpartition(".")[-1] == "cpp":
            _solutions[_idx] = compile_solution(_sol, log)
            compile_solution(_sol, log, sanitizer=False)

    return _solutions


@pytest.fixture()
def estimator(request, log):
    timeout = float(request.config.getoption("--timeout"))
    memory_limit = float(request.config.getoption("--memory_limit"))
    return get_estimator(timeout=timeout, memory_limit=memory_limit, log=log)


def get_estimator(timeout, memory_limit, log):
    def _estimator(solution, input):
        if "__naive" in solution:
            solution_without_sanitizer = solution.rpartition(".")[0] + \
                                         "_without_sanitizer" + "." + \
                                         solution.rpartition(".")[-1]
            output = run_process(solution_without_sanitizer, input, log)
            return output.strip(), 0, 0

        _time = run_process_with_time_check(solution, input, log)
        if _time > timeout:
            log.warning("Timout exceeded: {time}s > {timeout}s\n".format(time=_time, timeout=timeout))
            log.warning("Solution: {solution}\n".format(solution=solution))
            log.warning("Input: {input}\n".format(input=input))
            log.warning("Trying to run without sanitizer..\n")

            solution_without_sanitizer = solution.rpartition(".")[0] + \
                                         "_without_sanitizer" + "." + \
                                         solution.rpartition(".")[-1]
            _time = run_process_with_time_check(solution_without_sanitizer, input, log)
            if _time > timeout:
                log.warning("Timeout exceeded without sanitizer: {time}s > {timeout}s\n"
                            .format(time=_time, timeout=timeout))
                log.warning("Solution: {solution}\n".format(solution=solution))
                log.warning("Input: {input}\n".format(input=input))
            else:
                log.warning("Without sanitizer time is ok: {time}s < {timeout}s\n"
                            .format(time=_time, timeout=timeout))

        _mem = run_process_with_memory_check(solution, input, log)
        if _mem > memory_limit:
            log.warning("Memory limit exceeded: {mem}kb > {mem_limit}kb".format(mem=_mem, mem_limit=memory_limit))
            log.warning("Solution: {solution}\n".format(solution=solution))
            log.warning("Input: {input}\n".format(input=input))
            log.warning("Trying to run without sanitizer..\n")

            solution_without_sanitizer = solution.rpartition(".")[0] + \
                                         "_without_sanitizer" + "." + \
                                         solution.rpartition(".")[-1]
            _mem = run_process_with_memory_check(solution_without_sanitizer, input, log)
            if _mem > memory_limit:
                log.warning("Memory limit exceeded without sanitizer: {mem}kb > {mem_limit}kb\n"
                            .format(mem=_mem, mem_limit=memory_limit))
                log.warning("Solution: {solution}\n".format(solution=solution))
                log.warning("Input: {input}\n".format(input=input))
            else:
                log.warning("Without sanitizer memory is ok: {mem}kb < {mem_limit}kb\n"
                            .format(mem=_mem, mem_limit=memory_limit))

        output = run_process(solution, input, log)
        return output.strip(), _time, _mem
    return _estimator


def compile_solution(solution, log, sanitizer=True):
    if solution.rpartition(".")[-1] == "cpp":
        sanitizer_suffix = "" if sanitizer else "_without_sanitizer"
        compiled_solution = solution.rpartition(".")[0] + sanitizer_suffix + ".out"

        args = ["g++",
                solution,
                "-fsanitize=address,undefined",
                "-x",
                "c++",
                "-std=c++14",
                "-O2",
                # "-Wall",
                # "-Werror",
                # "-Wsign-compare",
                "-o",
                compiled_solution]
        if not sanitizer:
            del args[2]

        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        compile_stdout, compile_stderr = proc.communicate()
        if compile_stdout or compile_stderr:
            err_msg = "Compilation error:\n" \
                      "Solution: {}\n" \
                      "STDOUT: {}\n" \
                      "STDERR: {}\n"\
                      .format(solution, str(compile_stdout.decode("utf-8")), str(compile_stderr.decode("utf-8")))
            log.error(err_msg)
            raise ValueError(err_msg)

    else:
        err_msg = "Trying to compile not .cpp file: {}".format(solution)
        log.error(err_msg)
        raise ValueError(err_msg)

    return compiled_solution


def run_process(solution, input, log):
    proc = Popen("./" + solution, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate(bytes(input + "\n", "utf-8"))
    if stderr:
        log.warning("Process' stderr is not empty after execution of {}:\n{}"
                    .format(solution, str(stderr.decode("utf-8"))))

    return str(stdout.decode("utf-8"))


def run_process_with_time_check(solution, input, log):
    if sys.platform == "linux":
        proc = Popen('/usr/bin/time -f "\ntime: %E" ./' + solution, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    elif sys.platform == "darwin":
        proc = Popen('gtime -f "\ntime: %E" ./' + solution, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    else:
        log.error("Unsupported platform: {}.\n".format(sys.platform))
        log.error("Expected linux or darwin")
        raise ValueError

    stdout, stderr = proc.communicate(bytes(input + "\n", "utf-8"))
    minutes, seconds = search(r"time: ([\d]+):([\d]+.[\d]+)", str(stderr.decode("utf-8"))).groups()
    return float(minutes) * 60 + float(seconds)


def run_process_with_memory_check(solution, input, log):
    if sys.platform == "linux":
        proc = Popen('/usr/bin/time -f "\nmem: %M" ./' + solution, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    elif sys.platform == "darwin":
        proc = Popen('gtime -f "\nmem: %M" ./' + solution, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    else:
        log.error("Unsupported platform: {}.\n".format(sys.platform))
        log.error("Expected linux or darwin")
        raise ValueError

    stdout, stderr = proc.communicate(bytes(input + "\n", "utf-8"))
    (mem, ) = search(r"mem: (\d+)", str(stderr.decode("utf-8"))).groups()
    return float(mem)


def pytest_addoption(parser):
    parser.addoption("--iterations", help="Number of tests run", default=float("inf"))
    parser.addoption("--solutions", help="Filename of solution")
    parser.addoption("--input", help="Input parameters")
    parser.addoption("--timeout", help="Timeout in seconds", default=1)
    parser.addoption("--memory_limit", help="Memory limit", default=1)
    parser.addoption("--log", help="Log level", default="INFO")
