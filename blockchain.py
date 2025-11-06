from typing import List, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from user import User

from block import Block
from custom_hash import custom_hash256
from transaction import Transaction, UTXOTransaction
from user import update_balances
from utxo import UTXOSet, TxIn, TxOut
import time, random


def validate_transactions_account_model(tx_list, users_by_key):
    """
    Pre-validate a candidate batch using the account model.
    Checks: tx_id correctness, known parties, positive amount, and balance (on a temp snapshot).
    Returns: (valid_tx_list, rejected_list_of_(reason, tx)).
    """
    valid, rejected = [], []
    temp_bal = {k: u.balance for k, u in users_by_key.items()}

    for tx in tx_list:
        if not getattr(tx, "verify_id", None) or not tx.verify_id():
            rejected.append(("bad_tx_id", tx))
            continue
        s = users_by_key.get(tx.sender)
        r = users_by_key.get(tx.receiver)
        if s is None or r is None:
            rejected.append(("unknown_party", tx))
            continue
        if tx.amount <= 0:
            rejected.append(("non_positive", tx))
            continue
        if temp_bal[tx.sender] < tx.amount:
            rejected.append(("insufficient", tx))
            continue
        temp_bal[tx.sender] -= tx.amount
        temp_bal[tx.receiver] += tx.amount
        valid.append(tx)

    return valid, rejected


def validate_transactions_utxo(tx_list, utxo_set: UTXOSet):
    """
    UTXO pre-validate ant laikino snapshot.
    Taisykles:
      - coinbase: inputs tuscias, visada leidziamas (tik viena per bloka, bet cia tikrinam per kandidata)
      - kiekvienas TxIn turi egzistuoti UTXO rinkinyje
      - sum(inputs) >= sum(outputs)
      - tx_id teisingas (deterministinis)
    Grazina: (valid_list, rejected_list_of_(reason, tx))
    """
    valid, rejected = [], []
    temp = utxo_set.copy()

    for tx in tx_list:
        # id verifikacija
        if not getattr(tx, "verify_id", None) or not tx.verify_id():
            rejected.append(("bad_tx_id", tx))
            continue

        # coinbase? (inputs == 0) -> leidziam
        if isinstance(tx, UTXOTransaction) and len(tx.inputs) == 0:
            # prideti outputs i laikiną rinkini
            for idx, o in enumerate(tx.outputs):
                temp.add_output(tx.tx_id, idx, o)
            valid.append(tx)
            continue

        # paprasta UTXO tx
        if not isinstance(tx, UTXOTransaction):
            rejected.append(("wrong_type", tx))
            continue

        # patikrinam visus inputus
        total_in = 0
        inputs_ok = True
        for tin in tx.inputs:
            if not temp.has(tin):
                inputs_ok = False
                break
            amt = temp.get_amount(tin)
            if amt is None:
                inputs_ok = False
                break
            total_in += amt
        if not inputs_ok:
            rejected.append(("missing_input", tx))
            continue

        total_out = sum(o.amount for o in tx.outputs)
        if total_in < total_out:
            rejected.append(("overspend", tx))
            continue

        # pritaikom laikinai: spend inputs, add outputs
        for tin in tx.inputs:
            temp.spend(tin)
        for idx, o in enumerate(tx.outputs):
            temp.add_output(tx.tx_id, idx, o)

        valid.append(tx)

    return valid, rejected


def apply_block_utxo(block, utxo_set: UTXOSet):
    """
    Po laimetu bloko mining coinu pritaikom tx i realu UTXO rinkini.
    Coinbase leidziamas (inputs tuscias).
    """
    applied, skipped = 0, 0
    for tx in block.transactions:
        if isinstance(tx, UTXOTransaction) and len(tx.inputs) == 0:
            # coinbase
            for idx, o in enumerate(tx.outputs):
                utxo_set.add_output(tx.tx_id, idx, o)
            applied += 1
            continue

        if not isinstance(tx, UTXOTransaction):
            skipped += 1
            continue

        # privalo egzistuoti visi inputai
        ok = True
        for tin in tx.inputs:
            if not utxo_set.has(tin):
                ok = False
                break
        if not ok:
            skipped += 1
            continue

        # spend + add
        for tin in tx.inputs:
            utxo_set.spend(tin)
        for idx, o in enumerate(tx.outputs):
            utxo_set.add_output(tx.tx_id, idx, o)
        applied += 1
    return applied, skipped


class Blockchain:
    def __init__(self, difficulty: int = 3, version: str = "v0.1", mode: str = "account"):
        self.difficulty = difficulty
        self.version = version
        self.mode = mode  # "account" arba "utxo"
        self.chain: List[Block] = []
        self.utxo: UTXOSet | None = UTXOSet() if mode == "utxo" else None

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

    def seed_utxo_from_balances(self, users_by_key):
        """
        UTXO genesis: convert kiekvieno vartotojo balansa i UTXO isleidima.
        Tai leidzia UTXO tranzakcijoms tureti realius inputus.
        """
        if self.mode != "utxo" or self.utxo is None:
            return
        for pk, u in users_by_key.items():
            if u.balance <= 0:
                continue
            fake_txid = custom_hash256(f"genesis|{pk}|{u.balance}")
            # viena output i savininka su pilnu balansu
            self.utxo.add_output(fake_txid, 0, TxOut(amount=u.balance, receiver=pk))

    @property
    def last_block(self) -> Optional[Block]:
        return self.chain[-1] if self.chain else None

    def add_block(self, block: Block) -> bool:
        """Validate full block before appending."""
        prev = self.last_block
        if not self.verify_block(block, prev):
            print("❌ Block verification failed.")
            return False

        self.chain.append(block)

        print(
            f"   merkle_root={block.tx_root[:16]}… "
            f"tx_count={len(block.transactions)} "
            f"pow_ok={block.is_valid_pow()} "
            f"merkle_ok={block.verify_merkle_root()}"
        )
        return True

    def verify_block(self, block: Block, prev_block: Optional[Block]) -> bool:
        if prev_block and block.prev_hash != prev_block.hash:
            print("❌ verify_block: prev_hash mismatch")
            return False
        if not block.is_valid_pow():
            print("❌ verify_block: invalid PoW")
            return False
        if not block.verify_merkle_root():
            print("❌ verify_block: bad Merkle root")
            return False
        # pertikrinam transakciju id
        for tx in block.transactions:
            if not tx.verify_id():
                print("❌ verify_block: tx id mismatch")
                return False
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

        if not self.chain:  # first block in chain
            self.create_genesis_block()

        prev_hash = self.last_block.hash if self.last_block else "0" * 64
        block_index = len(self.chain)
        num_miners = len(miners)

        # Account modeliui be poole nieko neveikiam, bet UTXO rezime leidziam coinbase-only
        if not tx_pool and self.mode != "utxo":
            print("No transactions to mine.")
            return None

        # 1) Paruošiam candidate blocks
        candidates = []
        for miner in miners:
            if self.mode == "utxo":
                # UTXO: coinbase -> miner gauna block_reward i nauja TxOut (pool nereikalingas)
                coinbase = UTXOTransaction(
                    inputs=[],  # coinbase neturi inputu
                    outputs=[TxOut(amount=block_reward, receiver=miner.public_key)]
                )
                utxo_tx_list = [coinbase]

                valid, rejected = validate_transactions_utxo(utxo_tx_list, self.utxo)
                if rejected:
                    print(f"ℹ️  UTXO candidate filtering: {len(valid)} valid, {len(rejected)} rejected.")
                if not valid:
                    continue

                txs = valid  # coinbase-only

            else:
                # ACCOUNT model: imu is tx_pool
                sample_size = min(100, len(tx_pool))
                if sample_size == 0:
                    continue
                tx_batch = random.sample(tx_pool, sample_size)

                valid, rejected = validate_transactions_account_model(tx_batch, users_by_key)
                if rejected:
                    print(f"ℹ️  Candidate filtering: {len(valid)} valid, {len(rejected)} rejected (balance/tx_id).")
                if not valid:
                    continue

                txs = valid[:100]

            block = Block(
                index=block_index,
                transactions=txs,
                prev_hash=prev_hash,
                version=self.version,
                difficulty=self.difficulty,
            )
            candidates.append((miner, block))

        if not candidates:
            # UTXO: nereik pooolo revalidacijos, tiesiog praleidziam raunda
            if self.mode == "utxo":
                print("No UTXO candidates this round.")
                return None
            else:
                # ACCOUNT: Pertikrinam visa pool'a, gal liko tik blogos tx
                valid_all, rejected_all = validate_transactions_account_model(tx_pool, users_by_key)
                if not valid_all and rejected_all:
                    invalid = [tx for (_, tx) in rejected_all]
                    print(
                        f"⚠️  All remaining {len(tx_pool)} tx are invalid "
                        f"({len(invalid)} rejected). Dropping them and ending mining."
                    )
                    remove_from_pool(invalid)
                return None

        print(f"\nStarting parallel mining round with {num_miners} miners "
              f"({len(tx_pool)} pending tx, diff={self.difficulty})")
        print(f"   Each miner works for {mining_time_limit}s window...")

        found_event = threading.Event()
        result_holder = []

        # kiekvienas mineris dirba skirtingose gijose
        def miner_worker(miner, block):
            target_prefix = "0" * self.difficulty
            start_time = time.time()
            while not found_event.is_set() and (time.time() - start_time < mining_time_limit):
                h = block.compute_hash()
                if h.startswith(target_prefix):
                    found_event.set()
                    result_holder.append((miner, block, h))
                    return
                block.nonce += 1

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
        if self.mode == "utxo":
            applied, skipped = apply_block_utxo(block, self.utxo)
            # UTXO mode: is pool'o salinam tik ne-coinbase (coinbase niekada nebuvo poole)
            mined_non_coinbase = [
                t for t in block.transactions
                if not (isinstance(t, UTXOTransaction) and len(t.inputs) == 0)
            ]
            remove_from_pool(mined_non_coinbase)
        else:
            applied, skipped = update_balances(block.transactions, users_by_key)
            remove_from_pool(block.transactions)

        # 6) Laimejes mineris gauna coins
        fees = sum(getattr(tx, "fee", 0) for tx in block.transactions)
        if self.mode == "account":
            miner.balance += block_reward + fees  # account mode – kaip buvo
            print(f"Miner reward: {block_reward} + {fees} fees = {block_reward + fees} coins")
        else:
            # UTXO mode – atlygis jau iskeltas i coinbase TxOut
            print(f"Miner reward paid via coinbase output: {block_reward} coins")

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
            prev = self.chain[i - 1]
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
