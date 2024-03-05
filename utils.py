from http.client import HTTPException

import requests
import json

from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, \
    HTTP_202_ACCEPTED

import schemas
from constant import TARIF_CODE, username, password, TEST_USER_FOR_PAYMENT, \
    TEST_PASSWORD_FOR_PAYMENT, SHIPMENT_POINT, DELIVERY_POINT
from models import Product


def auth_cdek():
    url = 'https://api.edu.cdek.ru/v2/oauth/token'
    params = {'grant_type': 'client_credentials',
              'client_id': 'EMscd6r9JnFiQ3bLoyjJY6eM78JrJceI',
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


def register_order_bepaid(order: schemas.Order):
    url = 'https://checkout.bepaid.by/ctp/api/checkouts'
    params = {'checkout': {
        'test': True,
        'transaction_type': 'payment',
        'settings': {
            'return_url': 'https://www.google.com/'
        },
        'payment_method': {
            'types': ['credit_card']
        },
        'order': {
            'amount': str(int(order.amount)),
            'currency': 'BYN',
            'description': "Order description",
        },
        'customer': {
            "address": "Nezavisimosti 181",
            "country": "BY",
            "city": "Minsk",
            "email": "kirill@example.com"
        },
    }}
    r = requests.post(url,
                      auth=(TEST_USER_FOR_PAYMENT,
                            TEST_PASSWORD_FOR_PAYMENT),
                      json=params)
    request_data = json.loads(r.text)
    if request_data.get('errors'):
        return {'status_code': HTTP_400_BAD_REQUEST,
                'detail': {"error_code": r.status_code,
                           "error_message": request_data.get('message')}
                }
    else:
        return {'status_code': HTTP_200_OK,
                'content': request_data['checkout'].get('redirect_url')}


def cdek_order_registrations(order: schemas.Order, products):
    items = []
    url = 'https://api.edu.cdek.ru/v2/orders'
    get_access_token = auth_cdek()
    total_amount = get_total_amount(products)
    params = {'number': order.id,
              'tariff_code': TARIF_CODE,
              'shipment_point': SHIPMENT_POINT,
              'delivery_point': DELIVERY_POINT,
              'recipient': {'name': order.name,
                            'email': order.email,
                            'phones': {'number': order.phone}
                            },
              'packages': [{'number': order.order_id.hex,
                            'weight': int(total_amount.get('total_amount')),
                            'length': 33,
                            'width': 25,
                            'height': 15,
                            }]}
    for product in products:
        dict_items = {'name': product.name, 'ware_key': product.id,
                      'payment': {'value': 0},
                      'cost': 0, 'weight': int(product.weight),
                      'amount': int(product.amount)}
        items.append(dict_items)
    params['packages'][0].update({'items': items})
    r = requests.post(url, headers={
        'Authorization': 'Bearer {}'.format(get_access_token)}, json=params)
    request_data = json.loads(r.text)
    if r.status_code == HTTP_202_ACCEPTED:
        return {'status_code': HTTP_202_ACCEPTED,
                'content': request_data}
    else:
        return {'status_code': HTTP_400_BAD_REQUEST,
                'detail': {"error_code": r.status_code,
                           "error_message":
                               request_data.get('requests')[0].get('errors')[
                                   0].get('message')}
                }



