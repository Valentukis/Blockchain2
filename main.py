from typing import List
from generate_data import generate_users, generate_transactions  # your existing code
from blockchain import Blockchain
from transaction import Transaction

BATCH_SIZE = 100
DIFFICULTY = 3  # "000" prefix

def chunked(lst: List, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def main():
    print("🚀 Generating data…")
    users = generate_users(1000)
    users_by_key = {u.public_key: u for u in users}
    tx_pool: List[Transaction] = generate_transactions(users, 10_000)
    print(f"✅ Users: {len(users)}  |  Transactions: {len(tx_pool)}")

    # Pool removal function (captures tx_pool by closure)
    def remove_from_pool(mined: List[Transaction]):
        mined_ids = {t.tx_id for t in mined}
        nonlocal tx_pool
        tx_pool = [t for t in tx_pool if t.tx_id not in mined_ids]
        print(f"🧹 Removed {len(mined)} tx from pool. Remaining: {len(tx_pool)}")

    bc = Blockchain(difficulty=DIFFICULTY, version="v0.1")
    bc.create_genesis_block()

    # Mine until pool is empty
    block_count = 0
    for batch in chunked(tx_pool, BATCH_SIZE):
        if not batch:
            break
        mined = bc.mine_next_block(batch, users_by_key, remove_from_pool)
        if mined:
            block_count += 1

    print("\n🔎 Final chain check:", "valid ✅" if bc.is_valid_chain() else "invalid ❌")
    print(f"⛓️  Total blocks (incl. genesis): {len(bc.chain)}")
    print("🧾 Last 3 blocks:")
    for b in bc.chain[-3:]:
        print(f"  • #{b.index} | hash={b.hash[:16]}… | tx={len(b.transactions)} | nonce={b.nonce}")

    # Optionally: write to JSON for screenshots/README
    # import json
    # with open("blockchain_v0_1.json", "w") as f:
    #     json.dump(bc.to_dict(), f, indent=2)
    # print("💾 Saved chain to blockchain_v0_1.json")

if __name__ == "__main__":
    main()
