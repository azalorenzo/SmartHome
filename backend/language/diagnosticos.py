from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Diagnostico:
    fase: Literal["lexica", "sintactica"]
    linea: int
    columna: int
    mensaje: str
