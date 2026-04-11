from __future__ import annotations

from typing import NotRequired, TypedDict, Unpack

from torch import Tensor


class Sequence(dict[str, Tensor]):
    class ShiftableColumnsKwargs(TypedDict):
        q: NotRequired[int]
        c: NotRequired[int]
        r: NotRequired[float]
        t: NotRequired[int]
        ut: NotRequired[int]

    def insert_next_entry(self, **kwargs: Unpack[ShiftableColumnsKwargs]) -> None:
        shiftable_columns = ["q", "c", "r", "t", "ut"]
        entry_idx = self["masks"].cpu().numpy().sum()
        for column in shiftable_columns:
            if column in kwargs.keys():
                key = column + "seqs"
                self[key][0][entry_idx] = self["shft_" + key][0][entry_idx - 1]
                self["shft_" + key][0][entry_idx] = kwargs[column]

        self["masks"][0][entry_idx] = True
        self["smasks"][0][entry_idx] = True

    @classmethod
    def from_dict(cls, d: dict[str, Tensor]) -> Sequence:
        return cls(d)
