#!/usr/bin/python

from __future__ import print_function
import argparse
import serialization_tools as st

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-o', '--output', default='output.dtk')

    args = parser.parse_args()
    st.zero_infections(args.filename, args.output)
