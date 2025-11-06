"""
tamper_test.py – Bloku grandines integralumo testas
---------------------------------------------------
Sis skriptas uzkrauna (arba sugeneruoja) bloku grandine ir atlieka
keletos tyciniu pakeitimu (tamper) testus, kad parodytu jog validacijos
logika teisingai aptinka duomenu pazeidimus (Merkle root, tx_id, PoW ir t.t.).
"""

import json, os
from blockchain import Blockchain
from data_gen import generate_users, generate_transactions
from user import update_balances


def load_blockchain_from_json(path: str) -> Blockchain:
    """Load a blockchain from a saved JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    bc = Blockchain(difficulty=data["difficulty"], version=data["version"])
    for b in data["blocks"]:
        from block import Block
        from transaction import Transaction
        txs = [Transaction(t["sender"], t["receiver"], t["amount"]) for t in b["transactions"]]
        block = Block(
            index=b["index"],
            transactions=txs,
            prev_hash=b["header"]["prev_hash"],
            version=b["header"]["version"],
            difficulty=b["header"]["difficulty"],
            nonce=b["header"]["nonce"],
        )
        block.hash = b["hash"]
        bc.chain.append(block)
    print(f"✅ Loaded blockchain with {len(bc.chain)} blocks.")
    return bc


def run_tamper_tests(bc: Blockchain):
    """Perform tamper tests and print results."""
    print("\n🔬 Running tamper tests on blockchain…")

    # Praleidziam genesis bloka
    if len(bc.chain) < 2:
        print("⚠️  Not enough blocks to test.")
        return
    block = bc.chain[1]

    # 1️⃣ Merkle root pakeitimo testas
    # keiciam turini + perskaiciuojam tx_id, kad pasikeistu Merkle medis
    original_tx = block.transactions[0]
    original_amount = original_tx.amount
    original_txid = original_tx.tx_id

    original_tx.amount += 1
    original_tx.tx_id = original_tx.compute_hash()  # svarbu: atnaujinam tx_id po pakeitimo

    merkle_ok = block.verify_merkle_root()
    print(f"1️⃣ Merkle root test: {merkle_ok}")
    assert merkle_ok is False, "❌ Merkle root test failed – tamper not detected!"

    # atstatom
    original_tx.amount = original_amount
    original_tx.tx_id = original_txid

    # 2️⃣ Tx ID tamper
    block.transactions[0].tx_id = "deadbeef" * 8
    tx_tamper_ok = bc.verify_block(block, bc.chain[0])
    print(f"2️⃣ Tx ID tamper (verify_block): {tx_tamper_ok}")
    assert tx_tamper_ok is False, "❌ Tx ID tamper test failed – invalid tx not detected!"

    # 3️⃣ Chain link tamper (netinkamas prev_hash)
    block.prev_hash = "1" * 64
    prevhash_ok = bc.verify_block(block, bc.chain[0])
    print(f"3️⃣ Wrong prev_hash test: {prevhash_ok}")
    assert prevhash_ok is False, "❌ Prev_hash tamper test failed – link not detected!"

    # 4️⃣ PoW tamper
    block.hash = block.hash.replace("0", "f", 1)
    pow_ok = block.is_valid_pow()
    print(f"4️⃣ PoW tamper test: {pow_ok}")
    assert pow_ok is False, "❌ PoW tamper test failed – invalid PoW not detected!"

    print("\n✅ Tamper detection working as expected if all asserts passed.")



def main():
    filename = "blockchain_v0_2.json"
    if os.path.exists(filename):
        bc = load_blockchain_from_json(filename)
    else:
        print("⚙️  No saved blockchain found, generating a quick demo chain…")
        users = generate_users(5)
        users_by_key = {u.public_key: u for u in users}
        tx_pool = generate_transactions(users, 20)
        bc = Blockchain(difficulty=3, version="v0.2")
        bc.create_genesis_block()
        bc.mine_next_block(tx_pool, users_by_key, lambda x: None, miners=users[:3])

    run_tamper_tests(bc)


if __name__ == "__main__":
    main()
