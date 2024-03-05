import json
from random import randint

import requests
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_202_ACCEPTED

from constant import *
import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from utils import auth_cdek, get_calculate_delivery, get_total_amount, \
    register_order_alfa, register_order_bepaid, cdek_order_registrations
from sqlmodel import Session
from typing import List, Union

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get('/get_deliverypoints')
async def get_delivery_points():
    url = 'https://api.edu.cdek.ru/v2/deliverypoints'
    get_access_token = auth_cdek()
    r = requests.get(url, headers={
        'Authorization': 'Bearer {}'.format(get_access_token)})
    request_data = json.loads(r.text)
    if request_data:
        return request_data[:10]


@app.post('/get_product_amount')
async def get_product_amount(product_id: list[int],
                             to_location: schemas.ToLocation = None,
                             db: Session = Depends(get_db)):
    products = crud.get_products(db=db, list_id=product_id)
    data = get_total_amount(products, to_location)
    if data.get('status_code') == HTTP_400_BAD_REQUEST:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=json.dumps(data.get('detail')))
    return Response(content=json.dumps(data.get('content')),
                    status_code=HTTP_200_OK)


@app.post("/create/order")
async def create_order(order: schemas.OrderCreate,
                       to_location: schemas.ToLocation = None,
                       db: Session = Depends(get_db)):
    products = crud.get_products(db=db, list_id=order.product_ids)
    data = get_total_amount(products, to_location)
    if data.get('status_code') == HTTP_400_BAD_REQUEST:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=json.dumps(data.get('detail')))
    order = crud.create_order(db=db,
                              order=order,
                              total_amount=data.get('total_amount'))
    data = register_order_bepaid(order=order,)
    if data.get('status_code') == HTTP_400_BAD_REQUEST:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=json.dumps(data.get('detail')))
    else:
        print(data.get('content'))
        return RedirectResponse(data.get('content'))


@app.post('/order_registration_cdek')
async def order_registration_cdek(order: schemas.Order,
                                  db: Session = Depends(get_db)):
    products = crud.get_products_by_order_id(db=db, id=order.id)
    data = cdek_order_registrations(order, products)
    if data.get('status_code') == HTTP_400_BAD_REQUEST:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=json.dumps(data.get('detail')))
    else:
        return Response(content=data.get('content'),
                        status_code=HTTP_202_ACCEPTED)


# @app.get("/order/{orderNumber}/{amount}")
# async def order_product_alfa(order_number: str, amount: str):
#     url = 'https://abby.rbsuat.com/payment/rest/register.do'
#     params = {'userName': username, 'password': password,
#               'orderNumber': order_number, 'amount': amount,
#               'returnUrl': 'http://127.0.0.1:8000//order_status'}
#     r = requests.post(url, data=params)
#     request_data = json.loads(r.text)
#     if request_data.get('errorCode'):
#         raise HTTPException(status_code=400,
#                             detail={"error_code": request_data.get('errorCode'),
#                                     "error_message": request_data.get(
#                                         'errorMessage')})
#     else:
#         print(request_data['formUrl'], request_data['orderId'])
#         return RedirectResponse(request_data['formUrl'])
#         # return {'order_id': request_data.get('orderID'),
#         #         'form_url': request_data.get('formUrl')}
#         # return RedirectResponse(url='/')
#
#
# @app.get("/order_status")
# async def get_status_order_alfa(order_id: str, order_number: str):
#     url = 'https://abby.rbsuat.com/payment/rest/getOrderStatusExtended.do'
#     params = {'userName': username, 'password': password,
#               'orderNumber': order_number, 'orderId': order_id,
#               'returnUrl': 'http://127.0.0.1:8000/docs#/default/order_product_order_get'}
#     r = requests.post(url, data=params)
#     request_data = json.loads(r.text)
#     if request_data.get('actionCodeDescription'):
#         return request_data
#     else:
#         raise HTTPException(status_code=400)

# @app.post("/create/order")
# async def create_order_by_alfa(order: schemas.OrderCreate,
#                        to_location: schemas.ToLocation = None,
#                        db: Session = Depends(get_db)):
#     products = crud.get_products(db=db, list_id=order.product_ids)
#     data = get_total_amount(products, to_location)
#     if data.get('status_code') == HTTP_400_BAD_REQUEST:
#         raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
#                             detail=json.dumps(data.get('detail')))
#     order = crud.create_order(db=db,
#                               order=order,
#                               total_amount=data.get('total_amount'))
#     data = register_order_alfa(order=order,)
#     if data.get('status_code') == HTTP_400_BAD_REQUEST:
#         raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
#                             detail=json.dumps(data.get('detail')))
#     else:
#         print(data.get('content'))
#         return RedirectResponse(data.get('content'))


# @app.post("/product/")
# async def product_be_paid(amount: int):
#     url = 'https://checkout.bepaid.by/ctp/api/checkouts'
#     params = {'checkout': {
#         'test': True,
#         'transaction_type': 'payment',
#         'settings': {
#             'return_url': 'https://www.google.com/'
#         },
#         'payment_method': {
#             'types': ['credit_card']
#         },
#         'order': {
#             'amount': amount,
#             'currency': 'BYN',
#             'description': "Order description",
#         },
#         'customer': {
#             "address": "Nezavisimosti 181",
#             "country": "BY",
#             "city": "Minsk",
#             "email": "kirill@example.com"
#         },
#     }}
#     data = requests.post(url,
#                          auth=(TEST_USER_FOR_PAYMENT,
#                                TEST_PASSWORD_FOR_PAYMENT),
#                          json=params)
#     return data.text

