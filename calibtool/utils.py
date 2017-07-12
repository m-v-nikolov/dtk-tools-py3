from enum import Enum

class StatusPoint(Enum):
    iteration_start = 0
    commission = 1
    running = 2
    analyze = 3
    plot = 4
    next_point = 5