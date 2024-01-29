from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, \
    Table, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
import uuid


from database import Base

product_order = Table("product_order", Base.metadata,
                      Column("product_id",
                             ForeignKey("product.id"),
                             primary_key=True),
                      Column("order_id",
                             ForeignKey("order.id"),
                             primary_key=True))

class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username = mapped_column(String(50))
    email = mapped_column(String, unique=True)
    password = mapped_column(String(100))
    is_active = mapped_column(Boolean, default=True, nullable=True)

    # orders = relationship("Order", back_populates="owner")


class Order(Base):
    __tablename__ = "order"

    id = mapped_column(Integer, primary_key=True, index=True)
    order_id = Column(String,
                      default=lambda: str(uuid.uuid4()))
    amount = mapped_column(Float)
    # owner_id = mapped_column(Integer, ForeignKey("users.id"))
    # owner = relationship("User", back_populates="orders")
    products = relationship("Product", secondary=product_order,
                            back_populates="orders")
    email = mapped_column(String, nullable=False)
    name = mapped_column(String, nullable=False)
    phone = mapped_column(String, nullable=False)
    __table_args__ = (UniqueConstraint('order_id', name='unique_order_id'),)


class Product(Base):
    __tablename__ = "product"

    id = mapped_column(Integer, primary_key=True, index=True)
    name = mapped_column(String, index=True, nullable=False)
    weight = mapped_column(Float, index=True, nullable=False)
    amount = mapped_column(Float, nullable=False)
    # orders = relationship("Order", back_populates="order_product")
    orders: Mapped[List["Order"]] = relationship(secondary=product_order,
                                                 back_populates="products")

