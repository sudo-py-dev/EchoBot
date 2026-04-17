"""
Generic base repository for shared database operations.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic base repository providing common database operations.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        model (type[T]): The SQLAlchemy model class.
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get(self, obj_id: int) -> T | None:
        """
        Retrieves a single record by its ID.

        Args:
            obj_id (int): Primay key ID.

        Returns:
            T | None: The model instance or None if not found.
        """
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[T]:
        """
        Retrieves all records for the model.

        Returns:
            list[T]: List of model instances.
        """
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """
        Creates and persists a new record.

        Args:
            **kwargs: Field values for the new record.

        Returns:
            T: The created model instance.
        """
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T, **kwargs) -> T:
        """
        Updates an existing record.

        Args:
            obj (T): The instance to update.
            **kwargs: New field values.

        Returns:
            T: The updated model instance.
        """
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        """
        Deletes a record from the database.

        Args:
            obj (T): The instance to delete.
        """
        await self.session.delete(obj)
        await self.session.commit()
