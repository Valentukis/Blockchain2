from user import generate_users
from transaction import Transaction
import random
import json

def generate_transactions(users, n=10000):
    txs = []
    for _ in range(n):
        sender = random.choice(users)
        receiver = random.choice(users)
        while receiver == sender:  # kad negaletu sau siust
            receiver = random.choice(users)

        amount = random.randint(1, sender.balance)
        tx = Transaction(sender.public_key, receiver.public_key, amount)
        txs.append(tx)

    return txs


if __name__ == "__main__":
    users = generate_users(1000)
    transactions = generate_transactions(users, 10_000)

    print(f"Generated {len(users)} users and {len(transactions)} transactions.\n")
    print("PVZ users:")
    for u in users[:5]:
        print(" ", u)

    print("\nPVZ transactions:")
    for t in transactions[:5]:
        print(" ", t)

    # Export data as jjson 
    data = {
        "users": [{"name": u.name, "pub": u.public_key, "balance": u.balance} for u in users],
        "transactions": [
            {"sender": t.sender, "receiver": t.receiver, "amount": t.amount, "tx_id": t.tx_id}
            for t in transactions
        ]
    }

    with open("blockchain_data.json", "w") as f:
        json.dump(data, f, indent=2)

