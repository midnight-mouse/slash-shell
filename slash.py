# Slash.py - A python implementation of a Unix-like shell.


""" ÖNSKELISTA

* CHECKA ALLA FUNKTIONER
* redirects
* piping
* subprocess?
* autocomplete
* shell scripts

"""

########################################
# IMPORTS
########################################
import os                      # for system functions

from termcolor import colored  # for coloring shell output
import socket                  # for reading host name
from datetime import datetime  # for parsing time
import pyfiglet                # for banner
import re                      # for grep command

########################################
# UTILITIES
########################################

def print_error(message):
    print(colored(message, "red", attrs=["underline"]))

def argparse(argstring):
    arglist = argstring.strip().split()
    return arglist

def check_exists(item):
    if not os.path.exists(item):
        print_error("No such file or directory")
        return False
    else:
        return True

def check_if_file(item, cwd):
    return (os.path.isfile(item) or os.path.isfile(cwd + "\\" + item))

# Checks that the number of supplied user arguments matches that of the called function.
def check_argument_count(arglist, count, usage_str=""):

    if len(arglist) > count:
        print_error(f"Too many arguments. {usage_str}")
        return False
    
    if len(arglist) < count:
        print_error(f"Too few arguments. {usage_str}")
        return False

    return True

def clear_screen():
    if os.name == "posix": 
        os.system("clear")
        return
    else:
        os.system("cls")

########################################
# COMMANDS
########################################

# echos back what the user entered. Supports multiline statements
def echo(arglist):
    if len(arglist) < 1:
        print_error("Usage: echo <message>")
        return

    # if " in echo, let user enter a multiline string
    if arglist[0].startswith("\"") and not arglist[-1].endswith("\""):
        # get XXX from after echo "XXX
        total_message = []
        total_message.append(" ".join(arglist)[1:])

        # prompt user for next line in string
        next_input = input(">> ")
        total_message.append(next_input)

        while not next_input.endswith("\""):
            next_input = input(">> ")
            total_message.append(next_input)

        total_message[-1] = total_message[-1][:-1]
        return "\n".join(total_message)

    # otherwise, just return everything after echo
    return " ".join(arglist)


def cd(arglist):
    if len(arglist) > 1:
        print_error("Too many arguments. Usage: cd <directory>")
    elif len(arglist) == 0:
        # go to home directory
        os.chdir("/")
    else:
        os.chdir(arglist[0])

# lists files and directories in current directory
def ls(arglist):
    
    # too many arguments and no flags
    if len(arglist) > 0 and '-' not in "".join(arglist):
        print_error("Too many arguments. Usage: ls <optional: flag>")
        return

    # check for flags
    for arg in arglist:
        if arg not in ["-l"]:
            print_error("Invalid argument. Usage: ls <optional: flag>")
            return

    # Get files and directories in current directory
    cwd = os.getcwd()
    ls_out = os.listdir(cwd)
    output = ""

    # Determine if file or directory
    contents = [(item, 'file') if check_if_file(item, cwd) else (item, 'dir') for item in ls_out]

    # check for flags
    if "-l" in arglist: # long list
        for item in contents:
            stat = os.stat(item[0])

            # Attributes
            item_type = item[1][0]
            size = stat.st_size
            modified = str(datetime.fromtimestamp(os.path.getmtime(item[0])))[:-7]
            item_format = item[0] if item_type == "f" else colored(item[0], "red")

            # Put together format
            output += f"{item_type} {str(size).rjust(11)} {modified} {item_format}\n"
    else:
        # list with spaces between 
        listing = [item[0] if item[1] == "file" else colored(item[0], "red") for item in contents]
        output = "   ".join(listing)

    return output.strip()

# shows current working directory
def pwd(arglist):
    if arglist > 0:
        print_error("Too many arguments. Usage: pwd")
        return

    cwd = os.getcwd()
    return cwd

# Shows help string for specified command
def man(arglist):
    if not check_argument_count(arglist, 1, "Usage: man <command>"): return
    
    # Get command and get its man statement
    command = arglist[0]

    if command in man_dict:
        outmsg = man_dict[command]
        return outmsg
    else:
        print_error("Command not found.")

# get contents of file
def cat(arglist):
    if not check_argument_count(arglist, 1, "Usage: cat <filename>"): return

    # Get contents of file
    filename = arglist[0]
    with open(filename, "r")as f:
        contents = f.read()

    return contents

# Process head or tail command
def process_head_or_tail(arglist, cmd_type):
    usage = f"Usage: {cmd_type} <filename> <optional: number of lines>"

    # Check argument count
    if len(arglist) == 0:
        print_error(f"Too few arguments. {usage}")
        return
    if len(arglist) > 2:
        print_error(f"Too many arguments. {usage}")
        return

    filename = arglist[0]
    if not check_exists(filename):
        print_error(f"File does not exist. {usage}")
        return

    if not check_if_file(filename, os.getcwd()):
        print_error(f"Not a file. {usage}")
        return
    
    # If user supplied row count, try to convert to int and use it
    if len(arglist) == 2:
        try:
            rows = int(arglist[1])
        except:
            print_error(f"Not a valid line number. {usage}")
            return
    else:
        # otherwise, default to 10 lines
        rows = 10

    # read contents
    with open(filename, "r") as f:
        contents = f.read().split("\n")

    return contents, rows

# show the first XX rows of a file
def head(arglist):
    contents, rows = process_head_or_tail(arglist, cmd_type="head")
    return "\n".join(contents[:rows])

# show the last XX rows of a file
def tail(arglist):
    contents, rows = process_head_or_tail(arglist, cmd_type="tail")
    return "\n".join(contents[-rows:])


# Creates a new empty file
def touch(arglist):
    if not check_argument_count(arglist, 1, "Usage: touch <filename>"): return

    filename = arglist[0]
    if os.path.exists(filename):
        print_error("File already exist.")
        return

    f = open(filename, "x")
    f.close()

# creates a directory
def mkdir(arglist):
    if not check_argument_count(arglist, 1, "Usage: mkdir <dirname>"): return

    dirname = arglist[0]
    if os.path.exists(dirname):
        print_error("Name already in use.")
        return

    # Create a new directory
    os.makedirs(dirname)

# removes a file
def rm(arglist):
    if not check_argument_count(arglist, 1, "Usage: rm <filename>"): return

    filename = arglist[0]
    if not os.path.exists(filename):
        print_error("File does not exist.")
        return

    if not check_if_file(filename, os.getcwd()):
        print_error(f"Not a file. Usage: rm <filename>")
        return

    os.remove(filename)

# removes a directory
def rmdir(arglist):
    if not check_argument_count(arglist, 1, "Usage: rmdir <dirname>"): return

    dirname = arglist[0]
    if not os.path.exists(dirname):
        print_error("Directory does not exist.")
        return

    if check_if_file(dirname, os.getcwd()):
        print_error(f"Not a directory. Usage: rmdir <dirname>")
        return

    os.rmdir(dirname)


# Copies a file from source to destination
def cp(arglist):
    if not check_argument_count(arglist, 2, "Usage: cp <source> <destination>"): return

    filesrc, filedst = arglist[0:2]

    # get source content
    with open(filesrc, "rb") as f:
        filebuffer = f.read()

    # create dest file
    f = open(filedst, "x")
    f.close()
    
    # fill with source content
    with open(filedst, "wb") as f:
        f.write(filebuffer)
    

# moves a file from a source to destination
def mv(arglist):
    if not check_argument_count(arglist, 2, "Usage: mv <source> <destination>"): return

    # Copy file to destination
    cp(arglist)
    
    # remove file source
    rm(arglist[:1])

# edit <filename>: opens up file in notepad
def edit(arglist):
    if not check_argument_count(arglist, 1, "Usage: edit <filename>"): return

    filename = arglist[0]
    if not os.path.exists(filename):
        print_error("File does not exist.")
        return

    if os.name == "posix":
        os.popen(f"gedit {filename}")
    else:
        os.popen(f"notepad.exe {filename}")

# redirects output to file. 
# w = write to new file/replace file contents
# a = append to file
def redirect_output(output, mode, filename):

    if not os.path.exists(filename):
        f = open(filename, "x")
        f.close()

    if mode == "a": output = "\n" + output

    with open(filename, mode) as f:
        f.write(output)

# finds word in file
def grep(arglist):
    if not check_argument_count(arglist, 2, "Usage: grep <keyword> <filename>"): return

    # get arguments
    grep_str = arglist[0]
    grep_file = arglist[1]

    if grep_file is not "*" and not os.path.exists(grep_file):
        print_error("File does not exist.")
        return

    # add support for * = try every file in directory
    if grep_file == "*":
        grep_files = os.listdir()
        grep_files = [f for f in grep_files if check_if_file(f, os.getcwd())]
    else:
        grep_files = [grep_file]

    for f in grep_files:

        # get one answer per line
        grep_line = "^.*" + grep_str + ".*$"

        try:
            file_str = open(f).readlines()
        except:
            # failed to load file, skip to next
            print_error(f"Could not read {f}")
            continue

        if grep_file == "*":
            print(colored(f"--- In {f} ---", "red"))

        # check for matches on every line
        for line in file_str:
            # ignore case
            real_line = re.findall(grep_line,line,re.IGNORECASE)

            # if found
            if len(real_line) > 0:
        
                # get complete line
                real_line = real_line[0].strip()

                # highlight keyword
                found = set().union(re.findall(grep_str,line,re.IGNORECASE))
                for find in found:
                    real_line = re.sub(find, colored(find, "red", attrs=["bold"]) ,real_line)

                print(real_line)

# Prints out the available commands
def help(arglist):
    print()
    print(colored("---- Available Commands ----", "red"))
    for k in command_list.keys():
        print(f"   * {k.ljust(9)} {man_dict.get(k, '')}")

    print()

# clears the shell
def clear(arglist):
    if not check_argument_count(arglist, 0, "Usage: clear"): return

    clear_screen()

# exists the shell
def exit(argstring):
    print(colored("Good Knight...", "red"))
    quit()


########################################
# SETUP
########################################

command_list = {
    "echo":     echo, 
    "pwd":      pwd, 
    "ls":       ls,
    "cd":       cd, 
    "man":      man, 
    "head":     head,
    "tail":     tail,
    "cat":      cat, 
    "touch":    touch, 
    "mkdir":    mkdir, 
    "rm":       rm,
    "rmdir":    rmdir,
    "cp":       cp, 
    "mv":       mv,
    "edit":     edit,
    "grep":     grep,
    "help":     help, 
    "clear":    clear, 
    "exit":     exit,
}

man_dict = {
    "echo":     "prints out the user input",
    "pwd":      "prints current directory",
    "ls":       "lists contents of current directory",
    "cd":       "change current directory",
    "man":      "prints manual for command",
    "head":     "prints first lines of a file",
    "tail":     "prints last lines of a file",
    "cat":      "prints contents of file",
    "touch":    "creates an empty file",
    "mkdir":    "creates a directory",
    "rm":       "removes file",
    "rmdir":    "removes a directory",
    "cp":       "copy file a to file b",
    "mv":       "copy file a to file b",
    "help":     "outputs a list of available commands",
    "clear":    "clears the screen",
    "edit":     "opens a file in notepad.exe for windows, gedit for linux",
    "not":      "dont do shit",
    "exit":     "exits the Slash shell"
}

########################################
# SHELL LOOP
########################################

clear_screen()
print(colored(pyfiglet.figlet_format("Slash Shell />"), "red"))

running = True
while running:

    # Get User Input
    print(colored(f"{socket.gethostname()} />", "red", attrs=["bold", "dark"]), end=" ")
    user_in = input()
    if user_in.strip() == "":
        continue
    
    # Get first part of user command
    user_command = user_in.split()[0]

    # Get args as a string from the user input of format <COMMAND> <ARG LIST>
    user_argstring = user_in[user_in.find(user_command) + len(user_command):].strip()
    redirect = False
    output_file = None

    # print("HELP:\n",user_in,"\n",user_command,"\n",user_argstring)
    if user_command in command_list.keys():
        try:

            # check for redirect
            if ">>" in user_argstring:
                user_argstring, output_file = user_argstring.split(">>")
                redirect = "a"
            elif ">" in user_argstring:
                user_argstring, output_file = user_argstring.split(">")
                redirect = "w"
            

            output = ""
            output = command_list[user_command](argparse(user_argstring))

            if output != "" and output != None:
                if redirect and output_file != "":
                    redirect_output(output, redirect, output_file.lstrip())
                else:
                    print(output)

        except Exception as E:
            print_error(E.args[-1])
    else:
        print_error(f"Command not found: {user_in}")