from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Diagnostico:
    phase: Literal["lexical", "syntactic"]
    line: int
    column: int
    message: str
