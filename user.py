import random
import string
from  custom_hash import custom_hash256

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

if __name__ == "__main__": #for debug
    users = generate_users(5)
    for u in users:
        print(u)