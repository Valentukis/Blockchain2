from custom_hash import custom_hash256
import random
import time

class Transaction:
    def __init__(self, sender: str, receiver: str, amount: int):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()
        self.tx_id = self.compute_hash()

    def compute_hash(self) -> str:
        """create random transaction id"""
        data = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return custom_hash256(data)

    def __repr__(self):
        return f"{self.sender[:6]} → {self.receiver[:6]} : {self.amount} coins" #print first 6 of each
