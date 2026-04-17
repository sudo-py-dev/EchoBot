from sqlalchemy import BigInteger, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from db.models.base import Base


class ChannelSettings(Base):
    __tablename__ = "channel_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    forward_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    destinations: Mapped[str | None] = mapped_column(Text, default="[]")

    add_credit: Mapped[bool] = mapped_column(Boolean, default=True)
    credit_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    forward_media: Mapped[bool] = mapped_column(Boolean, default=True)
    forward_text: Mapped[bool] = mapped_column(Boolean, default=True)
