#!/usr/bin/env python3

class Process:
    def __init__(self):
        '''
        args: list of args for execve, where args[0] is the program name
        input: int of an fd for input redirection
        output: int of an fd for output redirection
        '''
        self.args = []
        self.input = None
        self.output = None

    def __str__(self):
        return ("args: %s\ninput: %s\noutput: %s\n" % (self.args, self.input, self.output))
