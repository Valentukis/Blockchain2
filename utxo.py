# Paprastas UTXO rinkinys: (txid, idx) -> TxOut
# Be elektroniniu parasu (cia supaprastintas modelis)

from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

@dataclass
class TxOut:
    receiver: str
    amount: int

@dataclass
class TxIn:
    prev_tx_id: str
    prev_index: int

class UTXOSet:
    def __init__(self):
        # key: (txid, index), value: TxOut
        self._map: Dict[Tuple[str, int], TxOut] = {}

    def copy(self) -> "UTXOSet":
        clone = UTXOSet()
        clone._map = self._map.copy()
        return clone

    # ar egzistuoja nespentas out
    def has(self, txin: TxIn) -> bool:
        return (txin.prev_tx_id, txin.prev_index) in self._map

    def get_amount(self, txin: TxIn) -> Optional[int]:
        o = self._map.get((txin.prev_tx_id, txin.prev_index))
        return o.amount if o else None

    def spend(self, txin: TxIn) -> Optional["TxOut"]:
        return self._map.pop((txin.prev_tx_id, txin.prev_index), None)

    def add_output(self, tx_id: str, index: int, out: TxOut) -> None:
        self._map[(tx_id, index)] = out

    def __len__(self) -> int:
        return len(self._map)

    def to_dict(self) -> Dict[str, Dict]:
        # optional, jei reikes debuginti
        return {f"{k[0]}:{k[1]}": {"receiver": v.receiver, "amount": v.amount}
                for k, v in self._map.items()}
