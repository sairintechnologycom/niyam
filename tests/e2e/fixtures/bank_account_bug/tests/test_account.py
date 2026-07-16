from src.account import Account


def test_withdraw_rejects_overdraft() -> None:
    account = Account(10)

    assert account.withdraw(15) is False
    assert account.balance == 10
