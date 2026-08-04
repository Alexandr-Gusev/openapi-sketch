import asyncio
import json
from CookieAuth import CookieAuth
from generated.client import Client
from generated.api.order import order_list
from generated.models.order_create_request import OrderCreateRequest
from generated.models.order_create import OrderCreate
from generated.models.order_item import OrderItem
from generated.api.order import order_create


async def main():
    base_url = "http://localhost/api/1.0"
    auth = CookieAuth(
        login_url="/sessions",
        refresh_url="/refreshedSessions",
        auth_data={"user": "admin", "password": "12345"},
        cookie_name="accessToken",
        base_url=base_url,
    )
    _client = Client(
        base_url=base_url,
        httpx_args={"auth": auth},
    )
    async with _client as client:
        res = await order_create.asyncio(
            client=client,
            body=OrderCreateRequest(
                idempotency_key="demo-1",
                order=OrderCreate(
                    phone="123",
                    delivery_address="456",
                    items=[OrderItem(
                        id="1",
                        count=1
                    )]
                )
            )
        )
        print("POST /orders", json.dumps(res.to_dict(), indent=2, ensure_ascii=False))

        res = await order_list.asyncio(client=client)
        print("GET /orders", json.dumps(res.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
