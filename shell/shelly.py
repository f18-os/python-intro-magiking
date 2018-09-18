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
    print("input: %s" % input_)
    if not input_:
        return
    if '|' in input_: # TIME TO PIPE!
        commands = re.split('\|', str.strip(input_))  # TODO rename commands to chain? chain and link?
        # print("read_() commands: %s" % commands)
        pipefds = (None, None)
        for index, command in enumerate(commands):
            # print("read_() command: %s" % command)
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
               print("pipefds: %s, %s" % (pipefds[0], pipefds[1]))
               pwrite = pipefds[1]
            args = re.split(' ', str.strip(command))
            # print("read_() args: %s" % args)
            if args[0] == 'exit':
                sys.exit(0)
            p = prep_subprocess(args=args, pipe_read=pread, pipe_write=pwrite)
            # print("read_() create p, id of p: %d" % id(p))
            # print(p)
            if not p:
                paranoid_pipefd_close()
                return
            processes.append(p)
    else: # prep like normal
        args = re.split(' ', str.strip(input_))
        if args[0] == 'exit':
            sys.exit(0)
        p = prep_subprocess(args=args)
        # print("read_() created p, id of p: %d" % id(p))
        # print(p)
        if not p:
            paranoid_pipefd_close()
            return
        processes.append(p)

    print("before execing. close_these_fds: %s" % close_these_fds)
    # start execing stuff!
    for index, p in enumerate(processes):
        # print("read_() exec p, id of p: %d" % id(p))
        # print(p)
        if index == len(processes) - 1: # when last one, wait
            exec_(args=p.args, in_fd=p.input, out_fd=p.output)
        else:
            exec_(args=p.args, in_fd=p.input, out_fd=p.output, parent_wait=False)

    paranoid_pipefd_close()
 
def paranoid_pipefd_close():
    global close_these_fds
    for fd in close_these_fds:
        try:
            print("parent read_() closing fd: %d" % fd)
            os.close(fd)
        except OSError:
            print("looks like this one was already closed")
            pass

def prep_subprocess(args=[], pipe_read=None, pipe_write=None):
    ''' Return a process object that read can execute.'''
    p = Process()
    # print("prep: id of p: %d" % id(p))
    # print("prep: given args: %s" % args)
    # print("prep: id of p.args %d" % id(p.args))
    new_in_fpath = None
    new_out_fpath = None
    
    # print("prep: p before try %s" % p)
    try:
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

        if new_in_fpath:
            p.input= os.open(new_in_fpath, os.O_RDONLY)
            os.set_inheritable(p.input, True)
            print("fpath: %s fd: %d" % (new_in_fpath, p.input))
        else:
            p.input = pipe_read

        if new_out_fpath:
            p.output = os.open(new_out_fpath, os.O_WRONLY | os.O_CREAT)
            os.set_inheritable(p.output, True)
            print("fpath: %s fd: %d" % (new_out_fpath, p.output))
        else:
            p.output = pipe_write
 
    except IndexError:
        # TODO check to make sure nothing tries to run using this p if there is an error
        print("Your redirection looks a little funny, try again")
        return None

    # print("prep: returning %s" % p)
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
    os.write(1, ("Command %s read wait= %s \nAbout to fork (pid:%d)\n" % (args[0], parent_wait, pid)).encode())

    rc = os.fork()

    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)

    elif rc == 0:                   # child
        child_pid = os.getpid()
        os.write(1, ("Child: My pid=%d.  Parent's pid=%d\n" % 
                    (child_pid, pid)).encode())

        # change stdin/out fds if given
        if in_fd:
            os.write(2, ("Child: pid=%d given in_fd: %d\n" %
                         (child_pid, in_fd)).encode())
            os.close(0)
            fd = os.dup(in_fd)
            os.set_inheritable(fd, True)
            os.close(in_fd)
            os.write(2, ("Child: pid=%d stdin 0 -> %d\n" %
                         (child_pid, in_fd)).encode())
        if out_fd:
            os.write(2, ("Child: pid=%d given out_fd: %d\n" %
                         (child_pid, out_fd)).encode())
            os.close(1)
            fd = os.dup(out_fd)
            os.set_inheritable(fd, True)
            os.close(out_fd)
            os.write(2, ("Child: pid=%d stdout 1 -> %d\n" %
                         (child_pid, out_fd)).encode())

        for fd in close_these_fds:
            try:
                os.write(2, ("Child: pid=%d " % (child_pid)).encode())
                os.write(2, ("child: closing fd: %d \n" % fd).encode())
                os.close(fd)
            except OSError:
                pass

        for dir in re.split(":", os.environ['PATH']):
            # try each directory in the path
            program = "%s/%s" % (dir, args[0])
            os.write(1, ("Child: pid=%d  ...trying to exec %s\n" %
                         (child_pid, program)).encode())
            try:
                os.execve(program, args, os.environ) # try to exec program
            except FileNotFoundError:             # ...expected
                pass                              # ...fail quietly

        os.write(2, ("Child: pid=%d Could not exec %s\n" %
                     (child_pid, args[0])).encode())
        sys.exit(1)                 # terminate with error

    else:                           # parent (forked ok)
        os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" % 
                    (pid, rc)).encode())
        if in_fd:
            os.write(1, ("Parent: My pid=%d " % 
                        (pid)).encode())
            os.write(1, ("closing fd: %d \n" % in_fd).encode())
            os.close(in_fd)
        if out_fd:
            os.write(1, ("Parent: My pid=%d " % 
                        (pid)).encode())
            os.write(1, ("closing fd: %d \n" % out_fd).encode())
            os.close(out_fd)

        while parent_wait:
            os.write(1, ("Waiting Parent: My pid=%d.  Child's pid=%d\n" % 
                        (pid, rc)).encode())
            try:
                childPidCode = os.wait()
                os.write(1, ("Parent: Child %d terminated with exit code %d\n" % 
                            childPidCode).encode())
                if childPidCode[0] == rc:
                    break
            except ChildProcessError:
                print("child processes already terminated")
                break
                pass
            


while True:
    read_()
    
