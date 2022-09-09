""" 
    Parse Pengwang Zhai's successive orders of scattering data.

    Manually deleted file headers up to "DETECTOR" since it is not relevant
    (and made the parsing extremely difficult for some reason).

    Retrieve the data as a multi-level dictionary.
"""

import math
import argparse
import numpy as np

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

# Parameter values
λ_ch       = np.array([350., 450., 550., 650.])
θp_ch      = np.array([60.0, 30.0]) # Flipped since this is the natural order of this data
θs_ch      = np.linspace(0.0, 60.0, 13)
φ_ch       = np.array([0.0, 60.0, 180.0, 240.0])

grammar = Grammar(
    r"""
    expr            = (text / empty)+
    text            = ws? detector_section+

    detector_section  = (~"DETECTOR") ws? number ws? mu_section+
    mu_section      = (~"SOLAR MU0=") ws? number ws? irradiances column_headers ws? data_row+
    irradiances     = (~"DOWNWELLING IRRADIANCE=") ws? number ws? (~"UPWELLING IRRADIANCE=") ws? number ws?
    column_headers  = word ws? word ws? word ws? word ws? word ws? word ws?
    data_row        = number ws? number ws? number ws? number ws? number ws? number ws?
    
    number          = (number_sci / number_base)
    number_sci      = number_base (~"E[-\+]?\d\d")
    number_base     = ~"[-\+]?\d*\.?\d+"

    word            = (~"[,\w]+") ws?
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
        _, detector_sections = visited_children

        return np.vstack(detector_sections)

    def visit_detector_section(self, node, visited_children):
        _, _, detector_no, _, _ = node.children
        _, _, _, _, mu_sections = visited_children

        return np.vstack(mu_sections)

    def visit_mu_section(self, node, visited_children):
        _, _, mu_photon_, _, _, _, _, _ = node.children
        _, _, _, _, _, _, _, data_rows  = visited_children

        mu_photon  = self._str_to_num(mu_photon_.text.strip())

        if mu_photon == -0.5:
            theta_photon = 60.0
        elif mu_photon == -0.866025:
            theta_photon = 30.0
        else:
            pass

        data = np.zeros((13*4, 6))
        data[:, 1:] = np.array(data_rows)
        data[:, 0]  = theta_photon

        return data

    def visit_data_row(self, node, visited_children):
        theta_, _, phi_, _, r_i_, _, r_q_, _, r_u_, *_ = node.children

        theta  = self._str_to_num(theta_.text.strip())
        phi    = self._str_to_num(phi_.text.strip())
        r_i    = self._str_to_num(r_i_.text.strip())
        r_q    = self._str_to_num(r_q_.text.strip())
        r_u    = self._str_to_num(r_u_.text.strip())

        return theta, phi, r_i, r_q, r_u

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
            E_idx = num_str.find("E")

            sig = float(num_str[:E_idx])
            exp = float(num_str[E_idx + 1:])

            val = sig * math.pow(10.0, exp)

            return val
            
            # Avoid some floating point awkwardness
            # We can assume that values in this format are whole-number angles
            # return round(val, 1)


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

def get_data(dir_prefix, name, theta_photon, phi, wavelength):
    """ Returns array of theta_sensor values in [0-60] for given parameters. """
    wav_str = str(int(wavelength)).zfill(3)

    filename = dir_prefix + '/vSOS_PACE_Bench_AOS_III_W0_' + wav_str

    data = parse_file(filename)
    
    tp = np.where(theta_photon == θp_ch)[0][0]
    p  = np.where(phi == φ_ch)[0][0]

    row_start = tp * len(θs_ch) * len(φ_ch) + p * len(θs_ch)
    row_end   = row_start + len(θs_ch)

    # Top of atmosphere data (vs. at surface)
    data_new = data[row_start:row_end, 3:]

    return data_new


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", 
                        help='File name (including directory)',
                        type=str)
    args = parser.parse_args()

    output = parse_file(args.file)
    # print(output)

    # print(get_data('sos_data/', 'AOS_3', 30.0, 240.0, 350.0))

