from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


class SegmentAnnotation(BaseModel):

    segment_type: Literal["ad", "content"]
    segment_index: int


class SegmentAnnotations(BaseModel):

    annotations: list[SegmentAnnotation]


@dataclass
class Window:

    start: float
    end: float
    segment_type: Literal["ad", "content"]

    def duration(self) -> float:
        return self.end - self.start

    def __repr__(self) -> str:
        return f"Window({self.start}-{self.end}, {self.segment_type})"