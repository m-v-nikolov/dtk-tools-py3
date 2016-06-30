import logging
import math
import re

logger = logging.getLogger(__name__)


class ProgressAnalyzer():
    def __init__(self, simIds=None):
        self.filenames = ['StdOut.txt', 'status.txt']
        self.simIds = simIds

    @staticmethod
    def getFormattedTime(seconds):
        flooredSeconds = int(math.floor(seconds))
        decimal = 100 * (round(seconds, 2) - float(flooredSeconds))

        m, s = divmod(flooredSeconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        return '%d:%02d:%02d:%02d.%02d' % (d, h, m, s, decimal)

    def filter(self, sim_metadata):
        return lambda x: True

    def apply(self, parser):

        # Ff this experiment has not started, set the values and return.
        if not self.filenames[0] in parser.raw_data:
            parser.timeElapsed = 0
            parser.progress = 0
            return

        lastLineOfStdOut = [i for i in parser.raw_data[self.filenames[0]].split('\n') if i != ''][-1]
        timeCapture = re.match('(\d*):(\d*):(\d*)', lastLineOfStdOut)
        if timeCapture:
            parser.timeElapsed = (60 ** 2) * float(timeCapture.group(1)) + 60 * float(timeCapture.group(2)) + float(
                timeCapture.group(3))
        else:
            parser.timeElapsed = 0

        lastLineOfStatus = [i for i in parser.raw_data[self.filenames[1]].split('\n') if i != ''][-1]
        if 'Done' in lastLineOfStatus:
            parser.progress = 100
        elif 'steps complete' in lastLineOfStatus:
            statusCapture = re.match('(\d*) of (\d*) steps complete.', lastLineOfStatus)
            parser.progress = 100.0 * (float(statusCapture.group(1)) / float(statusCapture.group(2)))
        else:
            parser.progress = 0

    def combine(self, parsers):
        self.data = '\n'

        if self.simIds:
            try:
                selected = {k: parsers.get(k) for k in self.simIds}
            except:
                logger.error('Bad simulation id(s).')
                raise Exception('Bad simulation id(s).')
        else:
            selected = parsers

        # Loop over all simulations and print the progress.
        totalProgress = 0
        totalTimeElapsed = 0
        for k in selected:
            progress = parsers.get(k).progress
            timeElapsed = parsers.get(k).timeElapsed

            totalProgress += progress
            totalTimeElapsed += timeElapsed

            if progress != 0:
                timeRemaining = timeElapsed * ((100.0 / progress) - 1)
            else:
                timeRemaining = None

            self.data += 'Simulation ' + str(k) + ':\n'
            self.data += '    ' + '{0:.2f}'.format(
                round(progress, 2)) + '% complete in ' + ProgressAnalyzer.getFormattedTime(timeElapsed) + '.\n'
            if timeRemaining:
                self.data += '    Approximately ' + ProgressAnalyzer.getFormattedTime(timeRemaining) + ' remaining.\n'

        # Compute and print the total progress.
        averageProgress = totalProgress / len(selected)
        averageTimeElapsed = totalTimeElapsed / len(selected)
        if totalProgress != 0:
            averageTimeRemaining = averageTimeElapsed * ((100.0 / averageProgress) - 1)
        else:
            averageTimeRemaining = None

        self.data += 'Overall:\n'
        self.data += '    ' + '{0:.2f}'.format(
            round(averageProgress, 2)) + '% complete in ' + ProgressAnalyzer.getFormattedTime(
            timeElapsed) + ' (on average).\n'
        if averageTimeRemaining:
            self.data += '    Approximately ' + ProgressAnalyzer.getFormattedTime(
                averageTimeRemaining) + ' remaining.\n'

    def finalize(self):
        print self.data
