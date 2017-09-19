class TestShad:

    def test_stress(self, solutions, input_generator, estimator, log):
        for input in input_generator():
            times, mems, outputs = [], [], []
            for solution in solutions:
                time, mem, output = estimator(solution, input)
                outputs.append(output)
                mems.append(mem)
                times.append(time)

            self._check_all_outputs_are_the_same(input, outputs, solutions, times, mems, log)

    def _check_all_outputs_are_the_same(self, input, outputs, solutions, times, mems, log):
        if [outputs[0]] * len(outputs) == outputs:
            msg = "Solutions have the same outputs!"
            msg += "Input: {}\n".format(input)
            msg += "Output: {}\n".format(outputs[0])
            msg += "Resources:\n"
            for sol, time, mem in zip(solutions, times, mems):
                msg += "\t{sol}[{time}s, {mem}]".format(sol=sol, time=time, mem=mem)

            log.info(msg)
            return True

        msg = "Solutions have different outputs.\n"
        msg += "Input: {}\n".format(input)
        msg += "Outputs:\n"
        for sol, time, mem, output in zip(solutions, times, mems, outputs):
            msg += "\t{sol}[{time}s, {mem}]: {output}\n".format(sol=sol, time=time, mem=mem, output=output)

        log.error(msg)
        raise ValueError
