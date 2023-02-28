import os
import time
from typing import List
from enum import Enum
import csv

import requests

BASE_URL = "https://tpservice.gov.taipei"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'

class COUPON_TYPE(Enum):
    STAY = 61
    BUY = 63
    SPORT = 64
    ART = 62
    PLAY = 66  # 農好券
    EAT = 52  # 市集券

class DISTRICT(Enum):
    zhongzheng = '中正區'
    datong = '大同區'
    zhongshan = '中山區'
    songshan = '松山區'
    daan = '大安區'
    wanhua = '萬華區'
    xinyi = '信義區'
    shilin = '士林區'
    beitou = '北投區'
    neihu = '內湖區'
    nangang = '南港區'
    wenshan = '文山區'

def newSession():
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['origin'] = 'https://tpservice.gov.taipei'
    session.headers['referer'] = 'https://tpservice.gov.taipei/'
    session.headers['authorization'] = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0YWlwZWkiLCJqdGkiOiJmY2I3M2EyZS1lYTZiLTQ2MDEtYTM0OC05NjJmNTZjOTY5ZmMiLCJyb2xlcyI6WyJBZG1pbiIsIlVzZXJzIl0sIm5iZiI6MTYzMzY2MDc4MywiZXhwIjoxOTQ5MTkzNTgzLCJpYXQiOjE2MzM2NjA3ODMsImlzcyI6Ikp3dFRhaXBlaSJ9.cTyWFhmd3moXltT3nv4xroxFE0fMcZzKqubrI4R7Dps'
    resp = session.get(BASE_URL)
    if resp.status_code != 200:
        raise ConnectionError(f'status code: {resp.status_code}')

    return session

session = newSession()

def search_coupon(coupon: COUPON_TYPE, district: DISTRICT):
    lng = 24.0334334
    lat = 120.5006263
    result = []

    url = f'{BASE_URL}:5003/api/WebStore/search'
    page = 1
    while True:
        print(f'search page {page}...')
        params = {
            'Lng': lng,
            'Lat': lat,
            'CouponTypes': coupon.value,
            'Districts': district.value,
            'Page': page,
            'PerPageLimt': 120,
        }
        resp = session.get(url, params=params)
        if resp.status_code != 200:
            raise ConnectionError(f'status code: {resp.status_code}')
    
        for s in resp.json().get('list', []):
            id = s.get('id', None)
            name = s.get('name', None)
            if id and name:
                detail = get_shop_detail(id)
                result.append({
                    'id': id, 
                    'name': name,
                    'description': detail['description'],
                    'address': detail['address'],
                })

        if resp.json().get('totalPages', page) <= page:
            break

        page += 1
        time.sleep(0.1)

    return result
    '''
    sample response : 
    {
    'totalPages': 1,
    'currentPage': 1,
    'itemsPerPage': 1,
    'totals': 1,
    'oriTotals': 0,
    'list': [
        {
        'id': '00022dda-e7d5-43a3-b059-b2d3892efd9f',
        'name': '蘭州38號攤',
        'bannerImageURL': None,
        'earlyBird': None,
        'voucherTypeList': [
            49,
            52
        ]
        }
    ]
    }
    '''


def get_shop_detail(id: str):
    url = f'{BASE_URL}:5003/api/WebStore/{id}'
    resp = session.get(url)
    if resp.status_code != 200:
        raise ConnectionError(f'status code: {resp.status_code}')

    return {
        'id': resp.json().get('id', ''),
        'name': resp.json().get('name', ''),
        'description': resp.json().get(
            'description', '').replace('\r\n', ' ').replace('\n', ' '),
        'address': resp.json().get('address', ''),
    }
    '''
    sample resp:
    {
        "id": "001211a0-744f-4115-a0f1-671edc466e92",
        "name": "遠東SOGO復興館-DEVIN",
        "district": "大安區",
        "description": "休閒服飾",
        "categories": [
            {
            "id": 63,
            "ads": ""
            }
        ],
        "address": "臺北市大安區忠孝東路3段300號7F",
        "logoImageURL": "https://taipeipass-jrsys.cdn.hinet.net/images/725e5356-846c-4632-a279-c5f31ef9f55a",
        "bannerImageURL": null,
        "earlyBird": null
    }
    '''

def save(type: COUPON_TYPE, district: DISTRICT, shops: List):
    print('save csv...')
    title = ['ID', '行政區', '地址', '店名', '店家說明']
    if not os.path.exists(type.name):
        os.makedirs(type.name)
    with open(f'{type.name}/{district.value}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(title)
        for shop in shops:
            writer.writerow([
                shop['id'], 
                district.value, 
                shop['address'],
                shop['name'],
                shop['description'],
            ])


def main():
    for coupon in COUPON_TYPE:
        print(f'start {coupon.name}...')
        for district in DISTRICT:
            print(f'start {district.value}...')
            shops = search_coupon(coupon, district)
            save(coupon, district, shops)
    print('success!')


if __name__ == '__main__':
    main()
