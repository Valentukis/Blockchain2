from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone
from custom_hash import custom_hash256
from transaction import Transaction

def merkle_root_hash(tx_ids: list[str]) -> str:
    """
    Compute a Merkle root hash for a list of transaction IDs.
    If odd number of txs, duplicate the last one (Bitcoin style).
    Returns a single 256-bit hex string.
    """
    if not tx_ids:
        return custom_hash256("")

    layer = tx_ids[:]  # copy
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a  # duplicate if odd
            next_layer.append(custom_hash256(a + b))
        layer = next_layer
    return layer[0]


@dataclass
class BlockHeader:
    prev_hash: str
    timestamp: int                      # Unix seconds
    version: str                        # e.g. "v0.1"
    tx_root: str                        # Merkle (or simple) root
    nonce: int = 0
    difficulty: int = 3                 # number of leading zeros required

    def serialize(self) -> str:
        """Deterministic serialization of the 6 header fields, in order."""
        # NOTE: Keep this order: prev_hash | timestamp | version | tx_root | nonce | difficulty
        return "|".join([
            self.prev_hash,
            str(self.timestamp),
            self.version,
            self.tx_root,
            str(self.nonce),
            str(self.difficulty),
        ])

    def hash(self) -> str:
        return custom_hash256(self.serialize())


@dataclass
class Block:
    index: int
    transactions: List[Transaction]
    prev_hash: str
    version: str = "v0.1"
    difficulty: int = 3
    timestamp: int = field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    nonce: int = 0
    hash: Optional[str] = None

    # Derived fields (computed on init)
    tx_root: str = field(init=False)

    def __post_init__(self):
        tx_ids = [tx.tx_id for tx in self.transactions]
        self.tx_root = merkle_root_hash(tx_ids)

    @property
    def header(self) -> BlockHeader:
        return BlockHeader(
            prev_hash=self.prev_hash,
            timestamp=self.timestamp,
            version=self.version,
            tx_root=self.tx_root,
            nonce=self.nonce,
            difficulty=self.difficulty,
        )

    def compute_hash(self) -> str:
        return self.header.hash()

    def mine(self, log_every: int = 10_000) -> str:
        """Proof-of-Work: find hash with '0' * difficulty prefix."""
        target_prefix = "0" * self.difficulty
        attempts = 0
        while True:
            h = self.compute_hash()
            if h.startswith(target_prefix):
                self.hash = h
                return h
            # mutate nonce (encapsulation through header rebuild via property)
            self.nonce += 1
            attempts += 1
            if attempts % log_every == 0:
                print(f"  … still mining (nonce={self.nonce}, last_hash={h[:12]}…)")

    def header_dict(self) -> dict:
        return {
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "version": self.version,
            "tx_root": self.tx_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
        }

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "hash": self.hash,
            "header": self.header_dict(),
            "transactions": [tx.__dict__ for tx in self.transactions],
        }

    def is_valid_pow(self) -> bool:
        if self.hash is None:
            return False
        return self.hash.startswith("0" * self.difficulty) and self.hash == self.compute_hash()
