"""Prepare an isolated MATLAB component with two additional dispatch actions.

The numerical function bodies are copied byte-for-byte from a user-supplied
and explicitly pinned original source. This generator does not execute MATLAB
or approve a numerical run. A resource guard and resumable caller are required.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

OLD_NAME = b"ma_original_statistical_components_native_v1"
NEW_NAME = b"ma20_original_components_exposed_prepared_v1"
ANCHOR = b"elseif strcmp(action,'optimize'),[varargout{1:2}]=ma_optimize(varargin{:});"
ADDITIONS = (b"elseif strcmp(action,'coordinate'),[varargout{1:2}]=ma_coordinate(varargin{:});\n"
             b"elseif strcmp(action,'mrt_value'),[varargout{1}]=ma_mrt(varargin{:});\n")


def generate(source: bytes, expected_sha256: str) -> bytes:
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError('original source does not match the explicit pin')
    if source.count(OLD_NAME) != 1 or source.count(ANCHOR) != 1:
        raise ValueError('unexpected original source structure')
    augmented = source.replace(OLD_NAME, NEW_NAME, 1).replace(ANCHOR, ADDITIONS + ANCHOR, 1)
    # This round-trip proves no original numeric body was altered.
    if augmented.replace(NEW_NAME, OLD_NAME, 1).replace(ADDITIONS + ANCHOR, ANCHOR, 1) != source:
        raise AssertionError('source round-trip failed')
    return augmented


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.name != NEW_NAME.decode() + '.m':
        raise ValueError('MATLAB function and output name must match')
    raw = args.source.read_bytes()
    generated = generate(raw, args.source_sha256.lower())
    with args.output.open('xb') as stream:
        stream.write(generated)
        stream.flush()
    print('original_sha256=' + hashlib.sha256(raw).hexdigest())
    print('prepared_sha256=' + hashlib.sha256(generated).hexdigest())
    print('scientific_execution_started=false')


if __name__ == '__main__':
    main()
