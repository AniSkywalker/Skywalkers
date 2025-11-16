"""
Clones in your skywalk
"""


class Clone:
    def __init__(self, communicator=None):
        self.communicator = communicator

    def run(self):
        raise NotImplementedError
