#!/usr/bin/env python3

import sys
import os
import re

pid = os.getpid()

def read_():
    # get the command
    args = re.split(' ', input('shelly $ '))
    if args[0] == 'exit':
        sys.exit(0)

    print(args)

    # check for redirection
    in_ = None
    out = None
    new_in = None
    new_out = None
    try:
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == '<':
                in_ = index
                new_in = args[index + 1]
                del args[index]
                del args[index]
            elif arg == '>':
                out = index
                new_out = args[index + 1]
                del args[index]
                del args[index]
            else:
                index += 1
        if in_:
            print("new_in: %s at index: %d " % (new_in, in_))
        if out:
            print("new_out: %s at index: %d " % (new_out, out))
        # TODO: assuming that input comes before output 
        print(args)
        exec_(args=args, in_redir=new_in, out_redir=new_out)
    except IndexError:
        print("Your redirection looks a little funny, try again")
    

def exec_(args=[], in_redir=None, out_redir=None):
    os.write(1, ("Command read...About to fork (pid:%d)\n" % pid).encode())

    rc = os.fork()

    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)

    elif rc == 0:                   # child
        os.write(1, ("Child: My pid=%d.  Parent's pid=%d\n" % 
                    (os.getpid(), pid)).encode())
        if in_redir:
            os.close(0)                 # redirect child's stdout
            sys.stdin = open(in_redir, "r")
            fd = sys.stdin.fileno() # os.open(in_redir, os.O_CREAT)
            os.set_inheritable(fd, True)
            os.write(2, ("Child: opened fd=%d for reading\n" % fd).encode())
        if out_redir:
            os.close(1)                 # redirect child's stdout
            sys.stdout = open(out_redir, "w")
            fd = sys.stdout.fileno() # os.open(out_redir, os.O_CREAT)
            os.set_inheritable(fd, True)
            os.write(2, ("Child: opened fd=%d for writing\n" % fd).encode())
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
    
