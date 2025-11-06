import random
import string
from  custom_hash import custom_hash256
from typing import Dict, Iterable, Tuple


class User:
    def __init__(self, name: str, public_key: str, balance: int):
        self.name = name
        self.public_key = public_key
        self.balance = balance

    def __repr__(self): 
        return f"{self.name} ({self.public_key[:8]}...) : {self.balance} coins" #Printinam pirmus 8 kad konsoles neuzkist, jei ka pakeisim


def generate_public_key(name: str) -> str:
    """generuoti Public key"""
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    key_input = f"{name}{salt}"
    return custom_hash256(key_input)
    
def generate_users(n: int = 1000):
    """sugeneruot n vartotoju"""
    users = []
    for i in range(n):
        name = f"User{i+1}"
        pub = generate_public_key(name)
        balance = random.randint(100, 1_000_000)
        users.append(User(name, pub, balance))
    return users

def update_balances(transactions: Iterable, users_by_key: Dict[str, "User"]) -> Tuple[int, int]:
    """
    paskyros model update.
    skip tx jei siuntejas neturi pakankamai fondu/yra nezinomas
    """
    applied = 0
    skipped = 0
    for tx in transactions:
        s = users_by_key.get(tx.sender)
        r = users_by_key.get(tx.receiver)

        if s is None or r is None:
            print(f"Skipping tx {tx.tx_id[:8]}…: unknown participant.")
            skipped += 1
            continue

        if tx.amount <= 0:
            print(f"Skipping tx {tx.tx_id[:8]}…: non-positive amount ({tx.amount}).")
            skipped += 1
            continue

        if s.balance < tx.amount:
            print(f"Skipping tx {tx.tx_id[:8]}…: insufficient funds for {s.name} "
                  f"(bal={s.balance}, amt={tx.amount}).")
            skipped += 1
            continue

        s.balance -= tx.amount
        r.balance += tx.amount
        applied += 1

    return applied, skipped

if __name__ == "__main__": # debuginimui
    users = generate_users(5)
    for u in users:
        print(u)