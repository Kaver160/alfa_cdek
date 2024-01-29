from fastapi import HTTPException
from sqlalchemy.orm import Session

import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(username=user.username,
                          email=user.email,
                          password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()


def get_products(db: Session, list_id: list[int]):
    return db.query(models.Product).filter(models.User.id.in_(list_id))


def create_order(db: Session, order: schemas.OrderCreate, total_amount: float):
    db_product = db.query(models.Product).filter(models.Product.id.in_(order.product_ids))
    if not db_product:
        raise HTTPException(status_code=409,
                            detail="Product not found in system.")
    db_item = models.Order(amount=total_amount,
                           email=order.email,
                           name=order.name,
                           phone=order.phone)
    for product in db_product:
        db_item.products.append(product)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
