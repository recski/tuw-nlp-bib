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

        self.title = None
        self.title_text = None
        self.authors = []
        self.authors_ascii = []
        self.author_text = None
        self.year_text = None
        self.year = None
        self.find_title()
        self.find_author()
        self.find_year()

    def find_closing(self):
        opened = 0
        for i, c in enumerate(self.title_text):
            if c == '{':
                opened += 1
            elif c == '}' and opened != 0:
                opened -= 1
            elif c == '}' and opened == 0:
                self.title_text = self.title_text[:i]
                break

    def find_title(self):
        self.title_text = re.findall(
            r'^\s*(title|TITLE|Title)\s*.*\s*=\s*'
            r'["{]'
            r'([\{\}\(\)\[\]<>\s\w,.?!:;_/\\\'’=+^%~$—–\-@0-9{\"o}{\"a}{\"u}“”`´‘ü]*)'
            r'[}"]',
            self.text, re.MULTILINE)
        if len(self.title_text) > 0:
            self.title_text = self.title_text[0][1]
            self.find_closing()
            self._clean_title()

    def find_author(self):
        self.author_text = re.findall(
            r'^\s*(author|AUTHOR|Author)\s*=\s*'
            r'["{]'
            r'([\{\}\s\w,/\\\'^.\-~&`´‘’${\\i}{\"o}{\"a}{\"u}ü]*)'
            r'[}"]',
            self.text, re.MULTILINE)
        if len(self.author_text) > 0:
            self.author_text = self.author_text[0][1]
            self._clean_author()

    def find_year(self):
        self.year_text = re.findall(r'^\s*(year|YEAR|Year)\s*=\s*["{]*[A-Za-z\s]*([0-9]+)[}"]*', self.text, re.MULTILINE)
        if len(self.year_text) > 0:
            self.year = self.year_text[0][1]

    def _clean_author(self):
        if self.author_text is not None:
            self.authors = re.split(r'\sand\s|\sAND|\\&\s', self.author_text)
            self.authors = [" ".join(reversed(author.strip().split(','))).strip() for author in self.authors]
            replace_dict = {'\\\'': '', '\\\"': '', '\\v': '', '\\H': '', '\\': '', '{': '', '}': '', '\'': '', '^': '',
                            'á': 'a', 'ä': 'a', 'ǎ': 'a',
                            'é': 'e',
                            'í': 'i',
                            'ó': 'o', 'ö': 'o', 'ő': 'o', 'ø': 'o', 'ò': 'o',
                            'ú': 'u', 'ü': 'u', 'ű': 'u',
                            'ß': 'ss',
                            'ğ': 'g',
                            'ć': 'c', 'ç': 'c',
                            'š': 's', 'ş': 's',
                            'ř': 'r',
                            'ý': 'y',
                            'ž': 'z'}
            for author in self.authors:
                author_ascii = author.lower()
                for character, replacement in replace_dict.items():
                    author_ascii = author_ascii.replace(character, replacement)
                self.authors_ascii.append(author_ascii)

    def _clean_title(self):
        if self.title_text is not None:
            self.title = self.title_text.replace('{', '').replace('}', '').replace('\n', '').replace('\t', '')

    def bib_similarity(self, other):
        if (self.title is not None and other.title is not None and self.title.lower() == other.title.lower()) \
                and set(self.authors) == set(other.authors):
            return True
        return False

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

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.text


def find_citations(tex_file, is_latex=True):
    citations = set()
    with open(tex_file) as tex:
        tex_string = tex.read()
        if is_latex:
            # If cite is in newcommand, it will think it's a citation, but won't find it in the bibs.
            cites = re.findall(r'\\cite[^{}]*{([^}]*)}', tex_string)
        else:
            cites = re.findall(r'\\citation{([^}]*)}', tex_string)
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
    cits = set()
    bibs = []
    for tex in args.tex:
        cits = cits.union(find_citations(tex, is_latex=True))
    for aux in args.aux:
        cits = cits.union(find_citations(aux, is_latex=False))
    for bib in args.bib:
        bibs += read_entries(bib)
    bibs = list(set(bibs))
    citations = find_entries(bibs, cits)
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
    arg_parser.add_argument('-a', '--aux', nargs='+', help='List the aux files you want '
                                                           'to gather the citations from')
    arg_parser.add_argument('-b', '--bib', nargs='+', help='The bib files to check for the citations')
    arg_parser.add_argument('-o', '--out', help='The output bib file. '
                                                'The bib file can be non-empty and it will be '
                                                'checked for existing citations.')
    args = arg_parser.parse_args()
    if args.tex is None or len(args.tex) < 1 or args.aux is None or len(args.aux) < 1:
        raise Exception('No tex or aux files given. At least one tex file is needed to add the citations from it.')
    if args.bib is None or len(args.bib) < 1:
        raise Exception('No original bibliography files given to find the citations in.')
    if args.out is None:
        args.out = 'mybib.bib'
    main(args)
