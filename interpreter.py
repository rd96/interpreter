#!/usr/bin/env python
import sys
import re

def read_file(filename):
    with open(filename, 'r') as file:
        return file.readlines()

class InterpretException(Exception): pass

class Command:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.instructions = []

    def append(self, instruction):
        self.instructions.append(instruction)

    def extend(self, instructions):
        self.instructions.extend(instructions)

    def __str__(self):
        if len(self.instructions):
            return "{}({}){{\n{}\n}}".format(self.name, ", ".join(self.args), "\n".join([str(it) for it in self.instructions]))
        else:
            return "{}({})".format(self.name, ", ".join(self.args))

class Interpreter:
    def __init__(self):
        self.functions = {}
        self.context = [{}]

    def assert_args_length(command, length):
        if len(command.args) != length: raise InterpretException('Incorrect number of args for {}, expected {}'.format(command.args, length))

    def assert_register_has_value(self, register):
        if (register not in self.context[-1]): raise InterpretException('Register {} not present in registers'.format(register))

    def handle_def(self, name, args, instructions):
        command = Command(name, args)
        command.extend(instructions)
        self.functions[name] = command

    def handle_custom(self, command):
        custom_function = self.functions[command.name]
        Interpreter.assert_args_length(command, len(custom_function.args))
        # TODO: handle context stack correctly
        self.run(custom_function.instructions)

    def handle_zero(self, register):
        self.context[-1][register] = 0

    def handle_incr(self, register):
        self.assert_register_has_value(register)
        self.context[-1][register] += 1

    def handle_asgn(self, dest, source):
        self.assert_register_has_value(source)
        self.context[-1][dest] = self.context[-1][source]

    def handle_prnt(self, register):
        self.assert_register_has_value(register)
        print(self.context[-1][register])

    def handle_loop(self, register, commands):
        self.assert_register_has_value(register)
        for _ in range(self.context[-1][register]): self.run(commands)

    def run(self, instructions):
        for i in range(len(instructions)):
            try:
                command = instructions[i]

                if command.name == 'ZERO':
                    Interpreter.assert_args_length(command, 1)
                    self.handle_zero(command.args[0])
                elif command.name == 'INCR':
                    Interpreter.assert_args_length(command, 1)
                    self.handle_incr(command.args[0])
                elif command.name == 'ASGN':
                    Interpreter.assert_args_length(command, 2)
                    self.handle_asgn(command.args[0], command.args[1])
                elif command.name == 'PRNT':
                    Interpreter.assert_args_length(command, 1)
                    self.handle_prnt(command.args[0])
                elif command.name == 'LOOP':
                    Interpreter.assert_args_length(command, 1)
                    self.handle_loop(command.args[0], command.instructions)
                elif command.name == 'DEF':
                    self.handle_def(command.args[0], command.args[1:], command.instructions)
                elif command.name in self.functions:
                    self.handle_custom(command)
                else: raise InterpretException('No function found {}'.format(command.name))

            except InterpretException as e:
                # BUG: line numbers are broken in recursive run calls
                print('Error {}:'.format(i + 1), e.args[0])

def parse(lines):
    line_regex = re.compile('^\s*([A-Z0-9]+)\(([A-Z0-9,]*)\)({?)$')
    end_of_block_regex = re.compile('^\s*}\s*$')
    context = [Command('MAIN', [])]

    for l in lines:
        r = line_regex.match(l)

        if r is None:
            if end_of_block_regex.match(l):
                context[-2].append(context.pop())
        else:
            command = r.groups()[0]
            args = [] if len(r.groups()[1]) == 0 else r.groups()[1].split(',')
            is_block = r.groups()[2] == '{'

            if is_block:
                context.append(Command(command, args))
            else:
                context[-1].append(Command(command, args))

    return context[0].instructions

interpreter = Interpreter()

commands = parse(read_file(sys.argv[1]))

print("{}".format("\n".join([str(c) for c in commands])))

interpreter.run(commands)
