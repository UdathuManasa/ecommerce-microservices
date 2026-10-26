from fastapi import FastAPI
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods = ['*'],
    allow_headers=['*']
)

redis = get_redis_connection(
    host="localhost",
    port=6380,
    password="",
    decode_responses=True,
)

class Order(HashModel):
    product_id : str
    price: float 
    fee : float
    total: float
    quantity: int
    status: str #pending,completed ,refunded
    class Meta:
        database = redis

@app.post('/orders')
async def create(request:Request): #id, quantity
    body = await request.json()
    req = requests.get('http://localhost:8000/products/%s' % body['id'])
    return req.json()


