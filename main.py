from typing import List
import random
import time

from data_gen import generate_users, generate_transactions
from blockchain import Blockchain
from transaction import Transaction


# === parameters you can tweak ===
BATCH_SIZE = 100           # transactions per block candidate
DIFFICULTY = 3             # "000" prefix requirement
BLOCK_REWARD = 50          # coins paid to miner
MINING_TIME_LIMIT = 5      # seconds each round


def chunked(lst: List, n: int):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    print("🚀 Generating data…")
    users = generate_users(100)  # fewer users for faster tests
    users_by_key = {u.public_key: u for u in users}
    tx_pool: List[Transaction] = generate_transactions(users, 500)
    print(f"✅ Users: {len(users)}  |  Transactions: {len(tx_pool)}")

    # Choose 3 miners randomly
    miners = random.sample(users, 3)
    print("\n👷 Selected miners:")
    for m in miners:
        print(f"   • {m.name} ({m.public_key[:10]}…)")

    # Define how mined txs are removed
    def remove_from_pool(mined: List[Transaction]):
        mined_ids = {t.tx_id for t in mined}
        tx_pool[:] = [t for t in tx_pool if t.tx_id not in mined_ids]
        print(f"🧹 Removed {len(mined)} tx from pool. Remaining: {len(tx_pool)}")

    # Initialize blockchain
    bc = Blockchain(difficulty=DIFFICULTY, version="v0.2")
    bc.create_genesis_block()

    # Mine until all transactions are processed
    block_count = 0
    while tx_pool:
        bc.mine_next_block(
            tx_pool=tx_pool,
            users_by_key=users_by_key,
            remove_from_pool=remove_from_pool,
            miners=miners,
            block_reward=BLOCK_REWARD,
            mining_time_limit=MINING_TIME_LIMIT,
        )
        block_count += 1

    # === final summary ===
    print("\n🔎 Final chain check:", "valid ✅" if bc.is_valid_chain() else "invalid ❌")
    print(f"⛓️  Total blocks (incl. genesis): {len(bc.chain)}")
    print("🧾 Last 3 blocks:")
    for b in bc.chain[-3:]:
        print(f"  • #{b.index} | hash={b.hash[:16]}… | tx={len(b.transactions)} | nonce={b.nonce}")

    # Save optional JSON snapshot
    # import json
    # with open("blockchain_v0_2.json", "w") as f:
    #     json.dump(bc.to_dict(), f, indent=2)
    # print("💾 Saved chain to blockchain_v0_2.json")


if __name__ == "__main__":
    main()
