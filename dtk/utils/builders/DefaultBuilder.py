# a class to build a default experiment of a single simulation
class DefaultBuilder:

    def __init__(self):
        self.finished = False
        self.next_params = {}

    def next_sim(self, config_builder):
        self.finished = True