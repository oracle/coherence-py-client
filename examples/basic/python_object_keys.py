import asyncio
from dataclasses import dataclass

from coherence import NamedMap, Processors, Session


@dataclass
class AccountKey:
    accountId: int
    accountType: str


@dataclass
class Account:
    accountId: int
    accountType: str
    name: str
    balance: float


async def do_run() -> None:
    """
    Demonstrates basic CRUD operations against a NamedMap using
    `AccountKey` keys with `Account` values.

    :return: None
    """
    session: Session = Session()
    try:
        namedMap: NamedMap[AccountKey, Account] = await session.get_map("accounts")

        await namedMap.clear()

        new_account_key: AccountKey = AccountKey(100, "savings")
        new_account: Account = Account(new_account_key.accountId, new_account_key.accountType, "John Doe", 100000.00)

        print(f"Add new account {new_account} with key {new_account_key}")
        await namedMap.put(new_account_key, new_account)

        print("NamedMap size is : " + str(await namedMap.size()))

        print("Account from get() : " + str(await namedMap.get(new_account_key)))

        print("Update account balance using processor ...")
        await namedMap.invoke(new_account_key, Processors.update("balance", new_account.balance + 1000))

        print("Updated account is : " + str(await namedMap.get(new_account_key)))

        await namedMap.remove(new_account_key)

        print("NamedMap size is : " + str(await namedMap.size()))
    finally:
        await session.close()


asyncio.run(do_run())
