from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import TYPE_CHECKING


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        data: Path


root = Path(__file__).parent.parent.resolve()
parser = argparse.ArgumentParser(
    description="Input preprocessor for benchmarking",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("data", type=Path, help="path to the data template file")


namespace = Namespace()
parser.parse_args(namespace=namespace)
with namespace.data.open("r", encoding="utf-8") as file:
    header, *lines = file.readlines()
    n, m, _, _, timeout = header.split()
    nodes = [int(tokens[0]) for tokens in map(str.split, lines[:int(n)])]
    start, end = random.sample(nodes, 2)


print(n, m, start, end, timeout)
print("".join(lines))
