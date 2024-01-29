import uuid
from typing import List

from pydantic import BaseModel, EmailStr


class ToLocation(BaseModel):
    code: int = None
    postal_code: str = None
    country_code: str = None
    city: str = None
    address: str = None


class ProductBase(BaseModel):
    name: str = None
    amount: float = None
    weight: float = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    email: EmailStr
    name: str
    phone: str


class OrderCreate(OrderBase):
    product_ids: List[int] = []


class Order(OrderBase):
    id: int
    owner_id: int
    amount: float
    order_id: uuid.UUID

    class Config:
        orm_mode = True


class ProductOut(Product):
    orders: List[Order]


class OrderOut(Order):
    products: List[Product]


class UserBase(Product):
    email: str


class UserCreate(UserBase):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    orders: List[Order] = []

    class Config:
        orm_mode = True
