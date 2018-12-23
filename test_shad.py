class TestShad:

    def test_stress(self, solutions, input_generator, estimator, log):
        for idx, input in enumerate(input_generator()):
            times, mems, outputs = [], [], []
            for solution in solutions:
                output, time, mem = estimator(solution, input)
                outputs.append(output)
                mems.append(mem)
                times.append(time)

            log.error('[{}]input: {}, outputs: {}'.format(idx, input, outputs))
            self._check_all_outputs_are_the_same(input, outputs, solutions, times, mems, log)

    def _check_all_outputs_are_the_same(self, input, outputs, solutions, times, mems, log):
        if [outputs[0]] * len(outputs) == outputs:
            # log.info("Solutions have the same outputs!")
            # log.info("Input: {}\n".format(input))
            # log.info("Output: {}\n".format(outputs[0]))
            log.info("Resources:\n")
            for sol, time, mem in zip(solutions, times, mems):
                pass
                # log.info("\t{sol}[{time}s, {mem}]".format(sol=sol, time=time, mem=mem))

            return True

        log.error("Solutions have different outputs.\n")
        log.error("Input: {}\n".format(input))
        log.error("Outputs:\n")
        for sol, time, mem, output in zip(solutions, times, mems, outputs):
            log.error("\t{sol}[{time}s, {mem}]:\n{output}\n".format(sol=sol, time=time, mem=mem, output=output))

        raise ValueError
