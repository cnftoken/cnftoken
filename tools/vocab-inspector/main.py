#!/usr/bin/env python3

def inspect_vocab(path: str):
    print('Inspecting', path)


if __name__ == '__main__':
    import sys
    inspect_vocab(sys.argv[1] if len(sys.argv) > 1 else 'vocab.bin')
