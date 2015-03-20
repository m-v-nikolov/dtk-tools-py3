# a class to build an experiment of simulations sweeping over Run_Number
class RunNumberSweepBuilder:

    def __init__(self, nsims):
        self.nsims = int(nsims)
        self.finished = False
        self.run_number = 0

    def next_sim(self, config_builder):
        self.next_params = {'Run_Number': self.run_number}
        config_builder.update_params(self.next_params)
        self.run_number += 1
        if self.run_number == self.nsims:
            self.finished = True