from custom_hash import custom_hash256
import random
import time

class Transaction:
    def __init__(self, sender: str, receiver: str, amount: int):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = int(time.time())
        self.tx_id = self.compute_hash()

    def compute_hash(self) -> str:
        """create random transaction id"""
        data = f"{self.sender}|{self.receiver}|{self.amount}|{self.timestamp}"
        return custom_hash256(data)

    def __repr__(self):
        return f"{self.sender[:6]} → {self.receiver[:6]} : {self.amount} coins" #atspausdina pirmus 6
    
    def serialized_fields(self) -> str:
        return f"{self.sender}|{self.receiver}|{self.amount}|{self.timestamp}"

    def verify_id(self) -> bool:
        data = f"{self.sender}|{self.receiver}|{self.amount}|{self.timestamp}"
        return self.tx_id == custom_hash256(data)

# === UTXO transakcijos ===
from typing import List
from utxo import TxIn, TxOut
from custom_hash import custom_hash256
import time

class UTXOTransaction:
    def __init__(self, inputs: List[TxIn], outputs: List[TxOut], timestamp: int | None = None):
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = int(time.time()) if timestamp is None else timestamp
        self.tx_id = self.compute_hash()

    # deterministinis serializavimas
    def serialized_fields(self) -> str:
        ins = ",".join(f"{i.prev_tx_id}:{i.prev_index}" for i in self.inputs)
        outs = ",".join(f"{o.receiver}:{o.amount}" for o in self.outputs)
        return f"{ins}|{outs}|{self.timestamp}"

    def compute_hash(self) -> str:
        return custom_hash256(self.serialized_fields())

    def verify_id(self) -> bool:
        return self.tx_id == custom_hash256(self.serialized_fields())

    def __repr__(self):
        total_out = sum(o.amount for o in self.outputs)
        return f"UTXO(tx={self.tx_id[:8]}.., in={len(self.inputs)}, out={len(self.outputs)}, sum_out={total_out})"
    
    def to_dict(self) -> dict: #kitaip json serializacija crashins programa
        return {
            "type": "utxo",
            "tx_id": self.tx_id,
            "timestamp": self.timestamp,
            "inputs": [{"prev_tx_id": i.prev_tx_id, "prev_index": i.prev_index} for i in self.inputs],
            "outputs": [{"receiver": o.receiver, "amount": o.amount} for o in self.outputs],
        }
