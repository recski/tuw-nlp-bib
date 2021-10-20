import os
import re
import warnings
from argparse import ArgumentParser


class BibEntry:
    def __init__(self, text):
        self.needed = False
        self.type = re.findall(r'@([^{]*)', text)[0].strip()
        try:
            self.id = re.findall(r'{(.*),', text)[0].strip()
        except IndexError:
            if self.type == 'String':
                self.needed = True
            self.id = re.findall(r'{(.*)', text)[0].strip()
        self.text = text

    def __eq__(self, other):
        return self.id == other
    
    def __lt__(self, other):
        if self.needed:
            return True
        if other.needed:
            return False
        return self.id < other.id
    
    def __le__(self, other):
        if self.needed:
            return True
        if other.needed:
            return False
        return self.id <= other.id
    
    def __gt__(self, other):
        if self.needed:
            return False
        if other.needed:
            return True
        return self.id > other.id
    
    def __le__(self, other):
        if self.needed:
            return False
        if other.needed:
            return True
        return self.id >= other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.text


def find_citations(tex_file):
    citations = set()
    with open(tex_file) as tex:
        tex_string = tex.read()
        cites = re.findall(r'\\cite{([^}]*)}', tex_string)
        for cite in cites:
            individual_cites = cite.split(',')
            for individual_cite in individual_cites:
                citations.add(individual_cite.strip())
    return citations


def read_entries(bib_file):
    with open(bib_file) as bib:
        bib_string = bib.read()
        entries = re.split(r'\n@', bib_string)
        bib_entries = []
        for entry in entries:
            entry = f'@{entry}' if not entry.startswith('@') else entry
            bib_entries.append(BibEntry(entry))
    return bib_entries


def find_entries(bib_entries, citation_set):
    citation_list = list(citation_set)
    citations = [cit for cit in bib_entries if cit.needed]
    for cite in citation_list:
        try:
            citations.append(bib_entries[bib_entries.index(cite)])
        except ValueError:
            warnings.warn(f'{cite} not found')
    return citations


def main(args):
    cit = find_citations(args.tex[0])
    bib = read_entries(args.bib)
    citations = find_entries(bib, cit)
    mode = 'w'
    if os.path.exists(args.out):
        out_bib = read_entries(args.out)
        citations = list(set(citations).union(set(out_bib)))
    elif not os.path.exists(os.path.dirname(args.out)) and os.path.dirname(args.out) != '':
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, mode) as output:
        citations.sort()
        for citation in citations:
            output.write(f'{citation}\n\n')


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('-t', '--tex', nargs='+', help='List the latex files you want '
                                                           'to gather the citations from')
    arg_parser.add_argument('-b', '--bib', help='The bib files to check for the citations')
    arg_parser.add_argument('-o', '--out', help='The output bib file. '
                                                'The bib file can be non-empty and it will be '
                                                'checked for existing citations.')
    args = arg_parser.parse_args()
    if args.tex is None or len(args.tex) < 1:
        raise Exception('No tex files given. At least one tex file is needed to add the citations from it.')
    if args.bib is None:
        raise Exception('No original bibliograpy file given to find the citations in.')
    if args.out is None:
        args.out = 'mybib.bib'
    main(args)
