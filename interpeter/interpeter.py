from enum import StrEnum
import os
from operator import index


class Variable:
    def __init__(self , var_type , name , value_stack_index , var_id):
        self.name = name
        self.value_stack_index = value_stack_index
        self.type = var_type
        self.var_id = var_id
        
class VOVNode:
    def __init__(self , left_value , right_value , operator):
        self.left_value: VOVNode | str = left_value
        self.right_value: VOVNode | str= right_value
        self.operator: str = operator

class InterpeterActions(StrEnum):
    Run = "run"
    Parse = "parse"
    Done = "done"

class Interpreter:
    def __init__(self):
        self.error = False
        self.value_stack = []
        self.value_type_stack = []
        self.variables = []
        self.variable_names_to_id = {}
        self.next_var_id = 0
    
    def run_code(self):
        langauge_is_running = True
        while langauge_is_running:
            command = input("What file to run:")
            command_lst = command.split()
            action = command_lst[0]
            if action != InterpeterActions.Done.value:
                file_use = command_lst[1]
                if action == InterpeterActions.Parse.value:
                    self.parse_code(file_use)
                elif action == InterpeterActions.Run.value:
                    if os.path.isfile(f"file_use.run"):
                        self.interpret_code(file_use)
                    else:
                        self.parse_code(file_use)
                        self.interpret_code(file_use)
                else:
                    print("unknown command")
            elif action == InterpeterActions.Done.value:
                return
            else:
                print("unknown command")
    @staticmethod
    def parse_code(lines_of_code: str):
        code_lines = [] #for the return code lines
        read_lines = []
        with open(F"{lines_of_code}.code", "r") as code_file:
            for line in code_file:
                read_lines.append(line)
        for line in read_lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(";")
            for p in parts:
                p = p.strip()
                if p:
                    code_lines.append(p)
        
        for index , expression in enumerate(code_lines):
            if expression.startswith("print("):
                expression = expression.replace("(" , " ")
                expression = expression.replace(")" , " ")
                code_lines[index] = expression
        
        with open(f"{lines_of_code}.run", "w") as run_ready_file:
            for line in code_lines:
                run_ready_file.write(f"{line}\n")
    
    def interpret_code(self, file):
        file_for_run = f"{file}.run"
        with open(file_for_run , "r") as code_file:
            read_lines = []
            for line in code_file:
                read_lines.append(line)
            for line in read_lines:
                if not self.error:
                    if line.startswith("dec"):
                        line = line.split()
                        if line[3] != "=":
                            self.send_error("Syntax Error")
                            break
                        self.dec_variable(line[1] , line[2] , line[4:])
                    elif line.startswith("set"):
                        line = line.split()
                        if line[3] != "=":
                            self.send_error()
                            break
                        check = self.set_variable(line[1],line[2], line[4:])
                        if check is None:
                            self.send_error()
                            break
                    elif line.startswith("print"):
                        line = line[len("print"):].strip()
                        check = self.print_expression(line)
                        if check is None:
                            self.send_error("Syntax Error")
                            break
                    else:
                        self.send_error("Syntax Error")
                        break
                else:
                    self.reset_interpeter()
                    break
    
    def pop_value(self):
        value_type = self.value_type_stack.pop()
        var = self.value_stack.pop()
        return value_type , var
    
    def push_value(self , value_type , value):
        self.value_type_stack.append(value_type)
        self.value_stack.append(value)
    
    def get_value(self , value_stack_index: int):
        value = self.value_stack[value_stack_index]
        value_type = self.value_type_stack[value_stack_index]
        return value_type , value
    
    def set_value(self , value_stack_index: int , value_type , value):
        if value_type != self.value_type_stack[value_stack_index]:
            self.send_error("Type Error")
            return None
        self.value_stack[value_stack_index] = value
        return True
    
    def dec_variable(self , value_type , name , value):
        var: Variable = Variable(value_type , name , len(self.value_stack) , self.next_var_id)
        self.next_var_id += 1
        check = self.solve_expression(value)
        if check is None:
            self.send_error()
            return None
        self.variables.append(var)
        self.variable_names_to_id[name] = var.var_id
        value = self.pop_value()
        self.push_value(value_type , value[1])
    
    def get_variable(self , value_type: str , name: str):
        var_id = self.variable_names_to_id.get(name)
        if var_id is None:
            self.send_error(f"Variable {name} not found")
            return None
        var = self.variables[var_id]
        if var.type != value_type:
            self.send_error(f"Type Error: Expected {value_type}, got {var.type}")
            return None
        return var
    
    def set_variable(self, value_type, name, expression):
        error = False
        var: Variable = self.get_variable(value_type,name)
        if var is None:
            error = True
            return None
        check = self.solve_expression(expression)
        if check is None:
            error = True
            return None
        set_value = self.pop_value()[1]
        self.set_value(var.value_stack_index, name, set_value)
        if error:
            return None
        else:
            return True
    
    def print_expression(self , expression):
        error: bool = False
        expression = expression.split()
        check = self.solve_expression(expression)
        if check is None:
            error = True
            return None
        if error:
            return None
        else:
            print(self.pop_value()[1])
            return True
    
    def solve_expression(self , expression):
        error: bool = False
        possible_opperators = ["+" , "-" , "*" , "/" , "%" , ">>" , "<<"]
        opperator_stack = []
        value_stack_opp = []
        if 1 == len(expression):
            if expression[0].lstrip("-").isdigit():
                self.push_value("int" , expression[0])
            elif expression[0] in self.variable_names_to_id:
                var = self.get_variable("int" , expression[0])
                if var is not None:
                    var_value = self.get_value(var.value_stack_index)
                    var_value = var_value[1]
                    self.push_value("int" , var_value)
                else:
                    error = True
                    return None
        else:
            for value in expression:
                if value in possible_opperators:
                    opperator_stack.append(value)
                elif value.lstrip("-").isdigit():
                    value_stack_opp.append(value)
                elif value in self.variable_names_to_id:
                    var = self.get_variable("int" , value)
                    if var is not None:
                        var_value = self.get_value(var.value_stack_index)
                        var_value = var_value[1]
                        self.push_value("int" , var_value)
                    else:
                        error = True
                        break
                else:
                    error = True
                    break
            if not error:
                opperator_stack.reverse()
                value_stack_opp.reverse()
                for value in value_stack_opp:
                    self.push_value("int", value)
                precedence = self.build_vov_tree(opperator_stack)
                val_first = self.pop_value()[1]
                result: int = int(val_first)
                result_str:str = ""
                while len(opperator_stack) > 0:
                    opperator = opperator_stack.pop()
                    val = self.pop_value()[1]
                    val = int(val)
                    result = self.solve_vov_expression(int(result),opperator,int(val))
                    result_str:str = str(result)
                self.push_value("int",result_str)
        if error:
            return None
        else:
            return True
        
    def build_vov_tree(self,opp_stack):
        opp_precedence_indecies: list[int] = []
        opp_stack = opp_stack
        while not all(x is None for x in opp_stack):
            index = self.find_highest_opp_index(opp_stack)
            opp_stack[index] = None
            opp_precedence_indecies.append(index)
        return  opp_precedence_indecies
    
    @staticmethod
    def solve_vov_expression(value1, opp, value2):
        if opp == "+":
            result = value1 + value2
        elif opp == "-":
            result = value1 - value2
        elif opp == "*":
            result = value1 * value2
        elif opp == "/":
            result = value1 // value2
        elif opp == "%":
            result = value1 % value2
        elif opp == ">>":
            result = value1 >> value2
        elif opp == "<<":
            result = value1 << value2
        else:
            result = None
        return result
    
    @staticmethod
    def find_highest_opp_index(opp_stack):
        index = 0
        for index,i in enumerate(opp_stack):
            if i == "*" or i == "/":
                break
            elif not ("*" in opp_stack or "/" in opp_stack):
                if i is None:
                    continue
                break
        return index
        
        
    def send_error(self , error_message: str | None = None):
        self.error = True
        if error_message:
            print(error_message)
        else:
            print("An error has occurred")
            
    def reset_interpeter(self):
        self.error = False
        self.value_stack = []
        self.value_type_stack = []
        self.variables = []
        self.variable_names_to_id = {}
        self.next_var_id = 0
            
interpreter_run = Interpreter()
interpreter_run.run_code()
