#!/usr/bin/env python3

import sys
import os
import re

pid = os.getpid()

def read_():
    '''
    Handle user input
    '''
    # get the command
    args = re.split(' ', str.strip(input('shelly $ ')))
    if args[0] == 'exit':
        sys.exit(0)

    # print(args)

    # check for redirection
    in_ = None
    out = None
    new_in_fpath = None
    new_out_fpath = None
    new_in_fd = None
    new_out_fd = None
    try:
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == '<':
                in_ = index
                new_in_fpath = args[index + 1]
                del args[index]
                del args[index]
            elif arg == '>':
                out = index
                new_out_fpath = args[index + 1]
                del args[index]
                del args[index]
            else:
                index += 1
        if in_:
            new_in_fd = os.open(new_in_fpath, os.O_RDONLY)
            # new_in_fd = open(new_in_fpath, 'r').fileno()
            os.set_inheritable(new_in_fd, True)
            print("fpath: %s at index: %d fd: %d" % (new_in_fpath, in_, new_in_fd))
        if out:
            new_out_fd = os.open(new_out_fpath, os.O_WRONLY)
            # new_out_fd = open(new_out_fpath, 'w').fileno()
            os.set_inheritable(new_out_fd, True)
            print("fpath: %s at index: %d fd: %d" % (new_out_fpath, out, new_out_fd))
        print(args)
        exec_(args=args, in_fd=new_in_fd, out_fd=new_out_fd)
    except IndexError:
        print("Your redirection looks a little funny, try again")
    

def exec_(args=[], in_fd=None, out_fd=None):
    '''
    Forks a child process and execs args.
        args: list of agruments to be passed to os.execve()
        in_fd: integer of new input file descriptor
        out_fd: integer of new output file descriptor
    '''
    os.write(1, ("Command read...About to fork (pid:%d)\n" % pid).encode())

    rc = os.fork()

    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)

    elif rc == 0:                   # child
        os.write(1, ("Child: My pid=%d.  Parent's pid=%d\n" % 
                    (os.getpid(), pid)).encode())

        # change stdin/out fds if given
        if in_fd:
            os.write(2, ("Child: given in_fd: %d\n" % in_fd).encode())
            os.close(0)
            os.dup(in_fd)
            os.close(in_fd)
            fd = sys.stdin.fileno()
            os.write(2, ("Child: using fd=%d for reading\n" % fd).encode())
        if out_fd:
            os.write(2, ("Child: given out_fd: %d\n" % out_fd).encode())
            os.close(1)
            os.dup(out_fd)
            os.close(out_fd)
            fd = sys.stdout.fileno()
            os.write(2, ("Child: using fd=%d for writing\n" % fd).encode())

        for dir in re.split(":", os.environ['PATH']): # try each directory in the path
            program = "%s/%s" % (dir, args[0])
            os.write(1, ("Child:  ...trying to exec %s\n" % program).encode())
            try:
                os.execve(program, args, os.environ) # try to exec program
            except FileNotFoundError:             # ...expected
                pass                              # ...fail quietly

        os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                 # terminate with error

    else:                           # parent (forked ok)
        os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" % 
                    (pid, rc)).encode())
        childPidCode = os.wait()
        os.write(1, ("Parent: Child %d terminated with exit code %d\n" % 
                    childPidCode).encode())


while True:
    read_()
    
