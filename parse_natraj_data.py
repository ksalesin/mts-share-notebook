""" 
    Parse Rayleigh scattering data from:

    "Rayleigh scattering in planetary atmospheres: corrected tables
    through accurate computation of x and y functions." Natraj, Vijay,
    Li, King-Fai, and Yung, Yuk L. Astro. J. 2009. 

    http://web.gps.caltech.edu/~vijay/Rayleigh_Scattering_Tables/CDS/

    Retrieve the data as a multi-level dictionary.
"""

import math
import argparse

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

grammar = Grammar(
    r"""
    expr            = (text / empty)+
    text            = ws? file_header data_chunk+

    file_header     = tline pair tline col_headers
    col_headers     = word ws? word ws? pair+
    data_chunk      = tline pair tline data_row+
    data_row        = number ws? number ws? number ws? number ws? number ws? number ws? number ws? number ws? number ws?

    pair            = word equal number ws?

    number          = ~"[-\+]?\d*\.?\d+"
    word            = ~"[\w]+ 0?"
    equal           = ws? "=" ws?
    tline           = (~"\~+") ws?

    ws              = ~"\s*"
    empty           = ws+
    """
)

class PrintVisitor(NodeVisitor):
    def visit_expr(self, node, visited_children):
        """ Returns the overall output. """
        output = {}

        for child in visited_children:
            if child[0]:
                output.update(child[0])

        return output

    def visit_text(self, node, visited_children):
        _, tau, data_chunks = visited_children

        output = {}
        for chunk in data_chunks:
            output.update(chunk)

        return {tau[1]: output}

    def visit_file_header(self, node, visited_children):
        _, tau, _, _ = visited_children
        return tau

    def visit_data_chunk(self, node, visited_children):
        _, albedo, _, data_rows = visited_children

        output = {}
        for row in data_rows:
            for mu0 in row.keys():
                if mu0 in output.keys():
                    output[mu0].update(row[mu0])
                else:
                    output[mu0] = row[mu0]

        return {albedo[1]: output}

    def visit_data_row(self, node, visited_children):
        mu0_, _, mu_, _, phi0_, _, phi30_, _, phi60_, _, phi90_, _, phi120_, _, phi150_, _, phi180_, _ = visited_children

        mu0    = self._str_to_num(mu0_.text.strip())
        mu     = self._str_to_num(mu_.text.strip())
        phi0   = self._str_to_num(phi0_.text.strip())
        phi30  = self._str_to_num(phi30_.text.strip())
        phi60  = self._str_to_num(phi60_.text.strip())
        phi90  = self._str_to_num(phi90_.text.strip())
        phi120 = self._str_to_num(phi120_.text.strip())
        phi150 = self._str_to_num(phi150_.text.strip())
        phi180 = self._str_to_num(phi180_.text.strip())

        return {mu0: {mu: {0.0: phi0, 30.0: phi30, 60.0: phi60, 90.0: phi90, 120.0: phi120, 150.0: phi150, 180.0: phi180}}}

    def visit_pair(self, node, visited_children):
        """ Gets each key/value pair, returns a tuple. """
        key_, _, value_, *_ = node.children

        key   = key_.text.strip()
        value = self._str_to_num(value_.text.strip())

        return key, value

    def visit_empty(self, node, visited_children):
        return None

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

    def _str_to_num(self, num_str):
        """ Converts number-matched string to a float. """
        return float(num_str)


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", 
                        help='File name (including directory)',
                        type=str)
    args = parser.parse_args()

    parse_file(args.file)

