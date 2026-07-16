class Account:
    def __init__(self, balance: int) -> None:
        self.balance = balance

    def withdraw(self, amount: int) -> bool:
        self.balance -= amount
        return True
