#!/usr/bin/env python3

import sys
import os
import re
from Process import Process

pid = os.getpid()
global close_these_fds
close_these_fds = []
global prompt
prompt = 'shelly $ '

def read_():
    '''
    Handle user input
    '''
    # get the commands
    global prompt
    global close_these_fds

    close_these_fds = [] # reset pipefds that need to be closed
    processes = []
    if 'PS1' in os.environ:
        prompt = os.environ['PS1']
    input_ = input(prompt)
    input_ = str.strip(input_)
    if not input_:
        return
    if '|' in input_: # TIME TO PIPE!
        commands = re.split('\|', str.strip(input_))  # TODO rename commands to chain? chain and link?
        pipefds = (None, None)
        for index, command in enumerate(commands):
            pread = None
            pwrite = None
            # do I need to read from a pipe? (was one made before me?)
            if pipefds[0]:
               pread = pipefds[0]
            # do I need to make a new pipe?
            if not index == len(commands) - 1: # if last one, can't be another pipe to write to
               pipefds = os.pipe()
               for f in pipefds:
                   os.set_inheritable(f, True)
                   close_these_fds.append(f)
               print("pipefds: %s, %s" % (pipefds[0], pipefds[1])) # do some more testing to be sure, but take this out
               pwrite = pipefds[1]
            args = re.split(' ', str.strip(command))
            if args[0] == 'exit':
                sys.exit(0)
            p = prep_subprocess(args=args, pipe_read=pread, pipe_write=pwrite)
            if not p:
                paranoid_pipefd_close()
                return
            processes.append(p)
    else: # prep like normal
        args = re.split(' ', str.strip(input_))
        if args[0] == 'exit':
            sys.exit(0)
        p = prep_subprocess(args=args)
        if not p:
            paranoid_pipefd_close()
            return
        processes.append(p)

    # start execing stuff!
    for index, p in enumerate(processes):
        if index == len(processes) - 1: # when last one, wait
            exec_(args=p.args, in_fd=p.input, out_fd=p.output)
        else:
            exec_(args=p.args, in_fd=p.input, out_fd=p.output, parent_wait=False)

    paranoid_pipefd_close()
 
def paranoid_pipefd_close(): # should only be called from the parent
    ''' Close all fds in 'close_these_fds list.'''
    global close_these_fds
    for fd in close_these_fds:
        try:
            os.close(fd)
        except OSError: # already closed
            pass

def prep_subprocess(args=[], pipe_read=None, pipe_write=None):
    ''' Return a process object that read can execute.'''
    p = Process()
    new_in_fpath = None
    new_out_fpath = None
    
    try: # check for < > file redirection
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == '<':
                if pipe_read:
                    raise IndexError # TODO Multiple redirection error
                new_in_fpath = args[index + 1]
                index += 2
            elif arg == '>':
                if pipe_write:
                    raise IndexError # TODO Multiple redirection error
                new_out_fpath = args[index + 1]
                index += 2
            else:
                p.args.append(arg)
                index += 1
 
    except IndexError:
        os.write(2, ("Shelly: Unexpected redirection %s \n" % args).encode())
        return None

    if new_in_fpath:
        p.input= os.open(new_in_fpath, os.O_RDONLY)
        os.set_inheritable(p.input, True)
    else:
        p.input = pipe_read

    if new_out_fpath:
        p.output = os.open(new_out_fpath, os.O_WRONLY | os.O_CREAT)
        os.set_inheritable(p.output, True)
    else:
        p.output = pipe_write

    return p


def exec_(args=[], in_fd=None, out_fd=None, parent_wait=True):
    '''
    Forks a child process and execs args.
        args: list of agruments to be passed to os.execve()
        in_fd: integer of new input file descriptor
        out_fd: integer of new output file descriptor
        parent_wait: if True, then parent waits for child process to terminate
    '''
    global close_these_fds

    rc = os.fork()

    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)

    elif rc == 0:                   # child
        child_pid = os.getpid()

        # change stdin/out fds if given
        if in_fd:
            os.close(0)
            fd = os.dup(in_fd)
            os.set_inheritable(fd, True)
            os.close(in_fd)
        if out_fd:
            os.close(1)
            fd = os.dup(out_fd)
            os.set_inheritable(fd, True)
            os.close(out_fd)

        for fd in close_these_fds:
            try:
                os.close(fd)
            except OSError:
                pass

        for dir in re.split(":", os.environ['PATH']):
            # try each directory in the path
            program = "%s/%s" % (dir, args[0])
            try:
                os.execve(program, args, os.environ) # try to exec program
            except FileNotFoundError:             # ...expected
                pass                              # ...fail quietly

        os.write(2, ("Child: pid=%d Could not exec %s\n" %
                     (child_pid, args[0])).encode())
        sys.exit(1)                 # terminate with error

    else:                           # parent (forked ok)
        if in_fd:
            os.close(in_fd)
        if out_fd:
            os.close(out_fd)

        while parent_wait:
            try:
                childPidCode = os.wait()
                if childPidCode[0] == rc:
                    break
            except ChildProcessError:
                os.write(2, ("child processes already terminated").encode())
                break
                pass
            


while True:
    read_()
    
