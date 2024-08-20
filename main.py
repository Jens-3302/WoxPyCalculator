# -*- coding: utf-8 -*-

from math import *
import re as _re
import os as _os
import json as _json

try:
    import pyperclip
except:
    pyperclip = None

try:
    import numpy as np
except:
    pass

try:
    from scipy.special import *
    c = binom
except:
    pass

from builtins import *  # Required for division scipy, also allows for pow to be used with modulus

###########################
# Environment preparation #
###########################
  
sqr = lambda x: x ** 2
x = 0

varFilePath = _os.environ['TMP'] + _os.sep + "wox_pycalc_vars.json"
variables = ["pi", "e"]

if _os.path.exists(varFilePath):
    try:
        with open(varFilePath, "r") as varFile:
            data = _json.load(varFile)
            for key in data:
                exec(f"{key} = {repr(data[key])}")
                variables.append(key)
    except:
        pass

def delete(variable):
    if not isinstance(variable, str):
        return "Surround with '"
    try:
        with open(varFilePath, "r") as varFile:
            data = _json.load(varFile)
            exists = data.get(variable) is not None
            del data[variable]
            with open(varFilePath, "w") as varFile:
                _json.dump(data, varFile)
                if exists:
                    return "Deleted"
                else:
                    return "Not Found"
    except:
        pass
    return "Didnt work"

def deleteVariables():
    try:
        with open(varFilePath, "w") as varFile:
            _json.dump({}, varFile)
            return "done"
    except:
        pass
        
delVars = deleteVariables

############################
# Pre-calculation handlers #
############################

def handle_trim_specials(query):
    return _re.sub(r'(^[*/=])|([+\-*/=(]$)', '', query) # Removes leading and trailing special chars
  
def handle_factorials(query):
    # Replace simple factorial
    query = _re.sub(r'(\b\d+\.?\d*\b)!',
                   lambda match: f'factorial({match.group(1)})', query)

    i = 2
    while i < len(query):
        if query[i] == "!" and query[i-1] == ")":
            j = i-1
            bracket_count = 1
            while bracket_count != 0 and j > 0:
                j -= 1
                if query[j] == ")":
                    bracket_count += 1
                elif query[j] == "(":
                    bracket_count -= 1
            query = query[:j] + f'factorial({query[j+1:i-1]})' +\
                    (query[i+1:] if i+1 < len(query) else "")
            i += 8  # 8 is the difference between factorial(...) and (...)!
        i += 1
    return query

def handle_pow_xor(query):
    return query.replace("^", "**").replace("²", "**2").replace("³", "**3").replace("xor", "^")

def handle_implied_multiplication(query):
    joinedVariables = "|".join(list(map(_re.escape, variables)))
    return _re.sub(r'(\.\d+|\b\d+\.\d*|\b\d+)\s*(' + joinedVariables + r')\b',
                  r'(\1*\2)', query)

def handle_missing_parentheses(query):
    parDiff = query.count('(') - query.count(')')
    if parDiff > 0:
        return query + ')'*parDiff
    if parDiff < 0:
        return '('*(-parDiff) + query
    return query
    
_variableName = 'x'

def handle_assign(query):
    global _variableName
    if query.count('=') != 1:
        return query
    equ = query.split('=', 1)
    if bool(_re.match(r'^[^\W0-9_]\w*\s*[\+\-\*\/]?$', equ[0])):
        if equ[0][-1] in '+-*/':
            equ[1] = equ[0]+equ[1]
            equ[0] = equ[0][:-1]
        _variableName = equ[0].strip()
        return equ[1]
    if bool(_re.match(r'^\s*[^\W0-9_]\w*$', equ[1])):
        if equ[0][-1] in '+-*/':
            equ[0] = equ[0]+equ[1]
        _variableName = equ[1].strip()
        return equ[0]
        
        

####################
# Post Calculation #
####################

def json_wox(title, subtitle, icon, action=None, action_params=None, action_keep=None):
    jsonObject = {
        'Title': title,
        'SubTitle': subtitle,
        'IcoPath': icon
    }
    if action and action_params and action_keep:
        jsonObject.update({
            'JsonRPCAction': {
                'method': action,
                'parameters': action_params,
                'dontHideAfterAction': action_keep
            }
        })
    return jsonObject

def copy_to_clipboard(text):
    if pyperclip is not None:
        pyperclip.copy(text)
    else:
        # Workaround
        cmd = 'echo ' + text.strip() + '| clip'
        _os.system(cmd)

def write_to_vars(result, variableName):
    if variableName in ['pi', 'e']:
        return # Maybe we should not allow the user to redefine pi
    try:
        if _os.path.exists(varFilePath):
            with open(varFilePath, "r") as varFile:
                data = _json.load(varFile)
                data[variableName] = result
                with open(varFilePath, "w") as varFile:
                    _json.dump(data, varFile)
        else:
            data = {}
            data[variableName] = result
            with open(varFilePath, "w") as varFile:
                _json.dump(data, varFile)
    except:
        pass

def format_result(result):
    if hasattr(result, '__call__'):
        # show docstring for other similar methods
        raise NameError
    if isinstance(result, str):
        return result
    if isinstance(result, int) or isinstance(result, float):
        if int(result) == float(result):
            return '{:,}'.format(int(result)).replace(',', ' ')
        else:
            return '{:,}'.format(round(float(result), 5)).replace(',', ' ')
    elif hasattr(result, '__iter__'):
        try:
            return '[' + ', '.join(list(map(format_result, list(result)))) + ']'
        except TypeError:
            # check if ndarray
            result = result.flatten()
            if len(result) > 1:
                return '[' + ', '.join(list(map(format_result, result.flatten()))) + ']'
            else:
                return format_result(np.asscalar(result))
    else:
        return str(result)
      
    
#################
# Main Function #
#################

def calculate(query):
    _results = []
    query = handle_trim_specials(query)
    query = handle_assign(query)
    query = handle_factorials(query)
    query = handle_pow_xor(query)
    query = handle_implied_multiplication(query)
    query = handle_missing_parentheses(query)
    
    try:
        _result = eval(query)
        formatted = format_result(_result)
        _results.append(json_wox(formatted,
                                '{} = {}'.format(query, _result),
                                'icons/app.png',
                                'change_query',
                                [_result, _variableName],
                                True))
    except NameError:
        # try to find docstrings for methods similar to query
        glob = set(filter(lambda x: 'Error' not in x and 'Warning' not in x and '_' not in x, globals()))
        help = list(sorted(filter(lambda x: query in x, glob)))[:6]
        for method in help:
            method_eval = eval(method)
            method_help = method_eval.__doc__.split('\n')[0] if method_eval.__doc__ else ''
            _results.append(json_wox(method,
                                    method_help,
                                    'icons/app.png',
                                    'change_query_method',
                                    [str(method)],
                                    True))
        if not help:
            # let Wox keep previous result
            raise NameError
    return _results

from wox import Wox, WoxAPI


class Calculator(Wox):
    def query(self, query):
        return calculate(query)

    def change_query(self, result, variableName):
        WoxAPI.change_query(str(result))
        write_to_vars(result, variableName)
        copy_to_clipboard(str(result))

    def change_query_method(self, query):
        WoxAPI.change_query(query + '(')


if __name__ == '__main__':
    Calculator()
