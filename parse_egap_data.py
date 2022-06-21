""" 
    Parse atmosphere-ocean scattering data from:

    "Testbed results for scalar and vector radiative transfer computations
    of light in atmosphere-ocean systems." Chowdhary, Jacek et al. JQSRT. 2020. 

    https://doi.org/10.1016/j.jqsrt.2019.106717

    Retrieve the data as a multi-level dictionary.
"""

import math
import argparse
import numpy as np

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

grammar = Grammar(
    r"""
    expr            = (text / empty)+
    text            = ws? file_header data_row+

    file_header     = (~"25") ws?
    data_row        = number ws? number ws? number ws? number ws? number ws? number ws? number ws? number ws?

    number          = (number_sci / number_base)
    number_sci      = number_base (~"D[-\+]?\d\d")
    number_base     = ~"[-\+]?\d*\.?\d+"

    ws              = ~"\s*"
    empty           = ws+
    """
)

class PrintVisitor(NodeVisitor):
    def visit_expr(self, node, visited_children):
        """ Returns the overall output. """
        
        # There should be only one non-None child (text)
        for child in visited_children:
            if child[0] is not None:
                return child[0]

        return 0

    def visit_text(self, node, visited_children):
        _, _, data_rows = visited_children

        return np.array(data_rows)

    def visit_data_row(self, node, visited_children):
        mu_, _, r_i_, _, r_q_, _, r_u_, *_ = node.children

        mu  = self._str_to_num(mu_.text.strip())
        r_i = self._str_to_num(r_i_.text.strip())
        r_q = self._str_to_num(r_q_.text.strip())
        r_u = self._str_to_num(r_u_.text.strip())

        return mu, r_i, r_q, r_u

    def visit_empty(self, node, visited_children):
        return None

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

    def _str_to_num(self, num_str):
        """ Converts number-matched string to an int or float. """
        try:
            return float(num_str)
        except ValueError:
            D_idx = num_str.find("D")

            sig = float(num_str[:D_idx])
            exp = float(num_str[D_idx + 1:])

            val = sig * math.pow(10.0, exp)
            
            # Avoid some floating point awkwardness
            # We can assume that values in this format are whole-number angles
            return round(val, 1)


def parse_text(text):
    # Parse the text into AST
    tree = grammar.parse(text)

    # Convert AST to dictionary
    pv = PrintVisitor()
    output = pv.visit(tree)

    return output

def parse_file(filename):
    with open(filename, 'r') as f:
        output = parse_text(f.read())

    return output

def get_data(dir_prefix, name, theta_sun, phi, wavelength):
    sun_str = 'sun' + str(int(theta_sun)).zfill(3)
    phi_str = 'phi' + (str(int(phi)) if phi < 90.0 else str(int(phi - 180.0))).zfill(3) # Assumes phi is one of [0, 60, 180, 240]
    wav_str = str(int(wavelength)).zfill(4)

    filename = dir_prefix + '/' + name + '/RAW_DATA_' + name + '_TOA_' + sun_str + '_' + phi_str + '_' + wav_str + 'x'

    data = parse_file(filename)
    n_rows = data.shape[0]

    # Take only the first or second half corresponding to this phi
    data = np.flip(data[:n_rows//2+1, :], axis=0) if phi < 90.0 else data[n_rows//2:, :]

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", 
                        help='File name (including directory)',
                        type=str)
    args = parser.parse_args()

    parse_file(args.file)

