import os
from sqlalchemy import text
from .database import AsyncSessionLocal

async def transfer_funds(from_account: int, to_account: int, amount: float):
    """
    Transfer funds between two accounts using a database transaction.
    Args:
        from_account (int): Source account ID
        to_account (int): Destination account ID
        amount (float): Amount to transfer
    Returns:
        dict: Status and message
    Raises:
        Exception: If transfer fails
    """
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                # Debit from source
                await session.execute(
                    text("UPDATE accounts SET balance = balance - :amount WHERE id = :id"),
                    {"amount": amount, "id": from_account}
                )
                # Credit to destination
                await session.execute(
                    text("UPDATE accounts SET balance = balance + :amount WHERE id = :id"),
                    {"amount": amount, "id": to_account}
                )
                # Log transaction
                await session.execute(
                    text("""
                        INSERT INTO transactions (from_account, to_account, amount, type)
                        VALUES (:from_acc, :to_acc, :amount, 'transfer')
                    """),
                    {"from_acc": from_account, "to_acc": to_account, "amount": amount}
                )
                await session.commit()
            return {"status": "success", "message": "Transfer completed"}
        except Exception as e:
            await session.rollback()
            raise Exception(f"Transfer failed: {str(e)}")
