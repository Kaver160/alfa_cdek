from http.client import HTTPException

import requests
import json

from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

import schemas
from constant import TARIF_CODE, username, password
from models import Product


def auth_cdek():
    url = 'https://api.edu.cdek.ru/v2/oauth/token'
    params = {'grant_type': 'client_credentials',
              'client_id':'EMscd6r9JnFiQ3bLoyjJY6eM78JrJceI',
              'client_secret': 'PjLZkKBHEiLK3YsjtNrt3TGNG0ahs3kG'
              }
    r = requests.post(url, data=params)
    request_data = json.loads(r.text)
    return request_data.get('access_token')


def get_total_amount(products: list[Product],
                     to_location: schemas.ToLocation = None,):
    product_amount = sum([product.amount for product in products])
    if to_location:
        weight_product = sum([product.weight for product in products])
        delivery_data = get_calculate_delivery(to_location, weight_product)
        if delivery_data.get('errorCode'):
            return {'status_code': HTTP_400_BAD_REQUEST,
                    'detail': {'error:code': delivery_data.get('errorCode'),
                               'error_message': delivery_data.get('errorMessage')
                               }
                    }
        else:
            amount_delivery = delivery_data.get('total_sum')
            total_amount = amount_delivery + product_amount
        return {'status_code': HTTP_200_OK,
                'total_amount': total_amount,
                'content': {'product_amount': product_amount,
                            'delivery_amount': amount_delivery,
                            'total_amount': total_amount}
                }
    return {'status_code': HTTP_200_OK,
            'total_amount': product_amount,
            'content': {'product_amount': product_amount}
            }


def get_calculate_delivery(to_location: schemas.ToLocation, weight_product):
    url = 'https://api.edu.cdek.ru/v2/calculator/tariff'
    params = {'tariff_code': TARIF_CODE,
              'from_location': {'code': 44,
                                'postal_code': '117639',
                                'country_code': 'RU',
                                'city': 'Москва',
                                'address': "пр-т Балаклавский, 5"},
              'to_location': to_location.dict(),
              "packages": [
                  {
                      "weight": weight_product,
                  }
              ]
              }
    r = requests.post(url,  headers={
        'Authorization': 'Bearer {}'.format(auth_cdek())}, json=params)
    request_data = json.loads(r.text)
    return request_data


def register_order_alfa(order: schemas.Order):
    url = 'https://abby.rbsuat.com/payment/rest/register.do'
    params = {'userName': username, 'password': password,
              'orderNumber': order.order_id, 'amount': str(int(order.amount)),
              'returnUrl': 'http://127.0.0.1:8000/order_status'}
    r = requests.post(url, data=params)
    request_data = json.loads(r.text)
    if request_data.get('errorCode'):
        return {'status_code': HTTP_400_BAD_REQUEST,
                'detail': {"error_code": request_data.get('errorCode'),
                           "error_message": request_data.get('errorMessage')}
                }
    else:
        return {'status_code': HTTP_200_OK,
                'content': request_data['formUrl']}

