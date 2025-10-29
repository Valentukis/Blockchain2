from typing import List, Dict, Optional
from block import Block
from custom_hash import custom_hash
from transaction import Transaction
from user import update_balances

class Blockchain:
    def __init__(self, difficulty: int = 3, version: str = "v0.1"):
        self.difficulty = difficulty
        self.version = version
        self.chain: List[Block] = []

    def create_genesis_block(self) -> Block:
        """Genesis with empty tx list, prev_hash of 64 zeros."""
        prev = "0" * 64
        genesis = Block(
            index=0,
            transactions=[],
            prev_hash=prev,
            version=self.version,
            difficulty=self.difficulty,
        )
        # Make the genesis hash deterministic without PoW (or do a quick PoW if you prefer)
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)
        print(f"✅ Genesis block created: idx=0, hash={genesis.hash[:12]}…, tx=0")
        return genesis

    @property
    def last_block(self) -> Optional[Block]:
        return self.chain[-1] if self.chain else None

    def add_block(self, block: Block) -> bool:
        """Validate linking and PoW; append if valid."""
        if self.last_block and block.prev_hash != self.last_block.hash:
            print("❌ Cannot add block: prev_hash mismatch.")
            return False
        if not block.is_valid_pow() and block.index != 0:
            print("❌ Cannot add block: invalid PoW.")
            return False
        self.chain.append(block)
        return True

    def mine_next_block(
        self,
        tx_batch: List[Transaction],
        users_by_key: Dict[str, "User"],   # forward ref
        remove_from_pool: callable,        # function to remove mined txs from the pool
    ) -> Optional[Block]:
        """Form, mine, validate, append, and apply balances."""
        if not self.chain:
            self.create_genesis_block()

        idx = len(self.chain)
        prev_hash = self.last_block.hash if self.last_block else "0"*64

        block = Block(
            index=idx,
            transactions=tx_batch,
            prev_hash=prev_hash,
            version=self.version,
            difficulty=self.difficulty,
        )

        print(f"\n⛏️  Mining block #{block.index} (tx={len(tx_batch)}, diff={self.difficulty})")
        print(f"   prev_hash = {prev_hash[:16]}…  tx_root = {block.tx_root[:16]}…")
        found = block.mine()
        print(f"✅ Block #{block.index} mined! nonce={block.nonce}  hash={found}")

        if not self.add_block(block):
            print("❌ Mining succeeded but adding block failed.")
            return None

        # Apply state updates (account model)
        update_balances(block.transactions, users_by_key)
        # Remove mined tx from the pool
        remove_from_pool(block.transactions)

        print(f"📦 Block #{block.index} added. Chain length = {len(self.chain)}")
        return block

    def is_valid_chain(self) -> bool:
        """Full-chain validation: links and PoW."""
        if not self.chain:
            return True
        # genesis integrity
        if self.chain[0].index != 0:
            return False
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]
            if curr.prev_hash != prev.hash:
                return False
            if not curr.is_valid_pow():
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "difficulty": self.difficulty,
            "version": self.version,
            "length": len(self.chain),
            "blocks": [b.to_dict() for b in self.chain],
        }
