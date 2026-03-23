#!/usr/bin/env python3
from pathlib import Path


def build_corpus(path: str):
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'vocab.bin').write_text('corpus')
    print('Corpus built:', out)


if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else 'corpus-output'
    build_corpus(target)
