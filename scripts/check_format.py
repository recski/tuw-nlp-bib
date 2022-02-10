from bibliography import read_entries
from itertools import combinations
from argparse import ArgumentParser

import logging
logging.basicConfig(level=logging.DEBUG, filename='check_log.txt', filemode='w',
                    format='%(levelname)s - %(message)s')


def check_id_format(bib_entry):
    if bib_entry.year is None:
        logging.warning(f"The bib entry {bib_entry.id} does not specify the year.")
    elif bib_entry.year not in bib_entry.id:
        logging.warning(f"The bib entry {bib_entry.id} id does not contain the year {bib_entry.year} from the entry.")
    if len(bib_entry.authors) == 0:
        logging.warning(f"The bib entry {bib_entry.id} does not specify the authors.")
    else:
        first_author_last_name = bib_entry.authors_ascii[0].split(' ')[-1]
        if first_author_last_name not in bib_entry.id.lower() and \
                first_author_last_name.split('-')[0] not in bib_entry.id.lower():
            logging.warning(f"The bib entry {bib_entry.id} id does not contain the last name of the first author "
                            f"{' '.join(a.capitalize() for a in bib_entry.authors_ascii[0].split(' '))} "
                            f"from the entry.")
    if not bib_entry.id.isascii():
        logging.warning(f"The bib id {bib_entry.id} contains non-ascii characters.")


def check_unique(entry, other_entry):
    if entry == other_entry:
        logging.error(f"Duplication of bib ids: {entry.id}: {entry.title} by {', '.join(entry.authors)},"
                      f"and {other_entry.id}: {other_entry.title} by {', '.join(other_entry.authors)}")
    elif entry.bib_similarity(other_entry):
        logging.warning(f"Possible duplication of bib entries: {entry.id}, {other_entry.id}")


def check_format(bib_file):
    checked = set()
    bib_entries = read_entries(bib_file)
    for entry, other_entry in combinations(bib_entries, 2):
        check_unique(entry, other_entry)
        if entry not in checked:
            check_id_format(entry)
            checked.add(entry)


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument('-b', '--bib', help='The bib file to check', required=True)
    args = arg_parser.parse_args()
    if args.bib is None:
        raise Exception('No bibliography file given.')
    check_format(args.bib)
