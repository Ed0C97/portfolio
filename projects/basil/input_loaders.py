# Portfolio excerpt, adapted. Input layer from a CLI crossword generator.
# Each loader returns the same shape: (words, secret_phrase, secret_clue),
# where words is a list of {'word', 'clue'} dicts. Returns (None, ...) on error.

import json

DEFAULT_SECRET = 'SECRET'
DEFAULT_CLUE = 'Secret phrase:'


def load_from_json(path):
    """Load words from a JSON file."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        return None, None, None
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from '{path}'.")
        return None, None, None

    # bare list is shorthand for words-only, no secret overrides
    if isinstance(data, list):
        return data, DEFAULT_SECRET, DEFAULT_CLUE
    return (
        data.get('words', []),
        data.get('secret', DEFAULT_SECRET),
        data.get('secret_clue', DEFAULT_CLUE),
    )


def load_from_txt(path):
    """Load words from a WORD|Clue text file; '#' lines, SECRET: and CLUE: directives handled inline."""
    words = []
    secret = DEFAULT_SECRET
    secret_clue = DEFAULT_CLUE

    try:
        with open(path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        return None, None, None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # directives match case-insensitively; words keep their original casing on the clue side
        if line.upper().startswith('SECRET:'):
            secret = line.split(':', 1)[1].strip().upper()
        elif line.upper().startswith('CLUE:'):
            secret_clue = line.split(':', 1)[1].strip()
        elif '|' in line:
            raw_word, clue = line.split('|', 1)
            words.append({'word': raw_word.strip().upper(), 'clue': clue.strip()})

    return words, secret, secret_clue


def manual_input():
    """Prompt for words and clues until the user types DONE."""
    secret = input('Enter secret phrase: ').strip().upper()
    secret_clue = input('Enter secret clue: ').strip()

    words = []
    print("\nEnter words and clues (type 'DONE' when finished):")
    while True:
        word = input('\nWord: ').strip().upper()
        if word == 'DONE':
            break
        if not word:
            continue
        clue = input(f"Clue for '{word}': ").strip()
        words.append({'word': word, 'clue': clue})

    return words, secret, secret_clue
