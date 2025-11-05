from typing import List, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from user import User
from block import Block
from custom_hash import custom_hash256
from transaction import Transaction
from user import update_balances
import time, random

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
        # padarom genezini hash deterministini
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
    tx_pool: list,
    users_by_key: dict,
    remove_from_pool: callable,
    miners: list,
    block_reward: int = 50,
    mining_time_limit: int = 5,
    ):
        """Simulate decentralized mining competition with parallel threads"""
        import threading

        if not self.chain: #first block in chain
            self.create_genesis_block()

        prev_hash = self.last_block.hash if self.last_block else "0" * 64
        block_index = len(self.chain)
        num_miners = len(miners)

        if not tx_pool:
            print("No transactions to mine.")
            return None

        # 1) Prepare candidate blocks
        candidates = []
        for miner in miners:
            sample_size = min(100, len(tx_pool))
            tx_batch = random.sample(tx_pool, sample_size)
            # krc laukiu andriaus verification
            # tx_batch = [t for t in tx_batch if verified_andriaus()]
            block = Block(
                index=block_index,
                transactions=tx_batch,
                prev_hash=prev_hash,
                version=self.version,
                difficulty=self.difficulty,
            )
            candidates.append((miner, block))

        print(f"\nStarting parallel mining round with {num_miners} miners "
              f"({len(tx_pool)} pending tx, diff={self.difficulty})")
        print(f"   Each miner works for {mining_time_limit}s window...")

        found_event = threading.Event()
        result_holder = []

        #2) Each miner mines in a separate thread
        def miner_worker(miner, block):
            target_prefix = "0" * self.difficulty
            start_time = time.time()
            while not found_event.is_set() and (time.time() - start_time < mining_time_limit):
                h = block.compute_hash()
                if h.startswith(target_prefix):
                    found_event.set()
                    result_holder.append((miner, block, h))
                    return
                block.nonce += 1  # next try

        threads = []
        for miner, block in candidates:
            t = threading.Thread(target=miner_worker, args=(miner, block))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if not result_holder:
            print("TIMES UP: No miner found a valid hash within time window.")
            return None

        miner, block, found_hash = result_holder[0]
        block.hash = found_hash

        print(f"Miner {miner.name} mined block #{block.index}!")
        print(f"   hash={found_hash[:16]}…  nonce={block.nonce}")

        # 4) Validate and append 
        if not self.add_block(block):
            print("Block failed chain validation.")
            return None

        # 5) Apply state changes 
        applied, skipped = update_balances(block.transactions, users_by_key)
        remove_from_pool(block.transactions)

        # 6) Reward the winning miner 
        fees = sum(getattr(tx, "fee", 0) for tx in block.transactions)
        miner.balance += block_reward + fees

        print(f"Miner reward: {block_reward} + {fees} fees = "
              f"{block_reward + fees} coins")
        print(f"Block #{block.index} added. Chain length = {len(self.chain)} "
              f"({applied} tx applied, {skipped} skipped)")
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
