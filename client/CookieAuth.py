import asyncio
import threading
import httpx
import json


class CookieAuth(httpx.Auth):
    def __init__(
        self,
        login_url: str,
        refresh_url: str,
        auth_data: dict,
        cookie_name: str,
        base_url: str,
    ):
        self.login_url = login_url
        self.refresh_url = refresh_url
        self.auth_data = auth_data
        self.cookie_name = cookie_name
        self.base_url = base_url
        self.cookies = httpx.Cookies()
        self._async_lock = asyncio.Lock()
        self._sync_lock = threading.Lock()

    def _apply_access_cookie(self, request: httpx.Request) -> None:
        token = self.cookies.get(self.cookie_name)
        if token is not None:
            request.headers["Cookie"] = f"{self.cookie_name}={token}"

    async def _login(self) -> httpx.Response:
        async with httpx.AsyncClient(
            base_url=self.base_url,
        ) as client:
            response = await client.post(self.login_url, json=self.auth_data)
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"login error ({response.status_code})",
                    request=response.request,
                    response=response,
                )
            self.cookies.update(response.cookies)
            return response

    async def _refresh(self) -> httpx.Response:
        async with httpx.AsyncClient(
            base_url=self.base_url, cookies=self.cookies
        ) as client:
            response = await client.post(self.refresh_url)
            if response.status_code == 401:
                self.cookies.clear()
                return await self._login()
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"refresh error ({response.status_code})",
                    request=response.request,
                    response=response,
                )
            self.cookies.update(response.cookies)
            return response

    async def async_auth_flow(self, request: httpx.Request):
        async with self._async_lock:
            if self.cookie_name not in self.cookies:
                await self._login()
            self._apply_access_cookie(request)

        response = yield request

        if response.status_code == 401:
            async with self._async_lock:
                await self._refresh()
                self._apply_access_cookie(request)
            yield request


async def main():
    base_url = "http://localhost/api/1.0"
    auth = CookieAuth(
        login_url="/sessions",
        refresh_url="/refreshedSessions",
        auth_data={"user": "admin", "password": "12345"},
        cookie_name="accessToken",
        base_url=base_url,
    )
    async with httpx.AsyncClient(base_url=base_url, auth=auth) as client:
        res = await client.post(
            "/orders",
            json={
                "idempotencyKey": "demo-1",
                "order": {
                    "phone": "123",
                    "deliveryAddress": "456",
                    "items": [{"id": "1", "count": 1}],
                },
            },
        )
        print("POST /orders", json.dumps(res.json(), indent=2, ensure_ascii=False))

        res = await client.get("/orders")
        print("GET /orders", json.dumps(res.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
