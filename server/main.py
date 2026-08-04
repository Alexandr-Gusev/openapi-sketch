from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Response, status
from fastapi.openapi.utils import get_openapi
from pydantic import conint

from generated.models import (
    Empty,
    Error,
    Language,
    Order,
    OrderCreateRequest,
    OrderList,
    OrderStatus,
    OrderUpdateRequest,
    SessionCreate,
    SessionListItem,
)

from auth import authenticate_user, set_auth_cookies
from config import settings
from dependencies import (
    SubFromAccessCookie,
    SubFromRefreshCookie,
    sub_from_access_cookie,
    sub_from_refresh_cookie,
)
from errors import ApiError, api_error_handler

app = FastAPI(
    title='API магазина',
    version='1.0',
    description='API магазина',
    contact={'name': 'Поддержка', 'email': 'support@example.com'},
    servers=[{'url': f'http://localhost{settings.api_prefix}', 'description': 'Тестовый сервер'}],
    root_path_in_servers=False,
)
app.add_exception_handler(ApiError, api_error_handler)

login_router = APIRouter()
refresh_router = APIRouter(
    dependencies=[Depends(sub_from_refresh_cookie)],
)
api_router = APIRouter(
    dependencies=[Depends(sub_from_access_cookie)],
)

# orderId -> (owner, order)
orders: Dict[str, Tuple[str, Order]] = {}
# "{owner}:{idempotencyKey}" -> order
order_idempotency: Dict[str, Order] = {}
# sessionId -> (owner, session)
sessions: Dict[str, Tuple[str, SessionListItem]] = {}


def _get_owned_order(order_id: str, owner: str) -> Order:
    stored_owner, order = orders.get(order_id, (None, None))
    if stored_owner != owner:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "Order not found",
        )
    return order


@api_router.post(
    '/orders',
    response_model=Order,
    status_code=201,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '409': {'model': Error},
        '422': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Order'],
)
def order_create(
    body: OrderCreateRequest, sub: SubFromAccessCookie
) -> Union[Order, Error]:
    idem_key = f"{sub}:{body.idempotencyKey}"
    cached = order_idempotency.get(idem_key)
    if cached is not None:
        return cached

    order = Order(
        orderId=str(uuid4()),
        orderVer=1,
        status=OrderStatus.DRAFT,
        createdAt=datetime.now(timezone.utc),
        phone=body.order.phone,
        deliveryAddress=body.order.deliveryAddress,
        items=body.order.items,
    )
    orders[order.orderId] = (sub, order)
    order_idempotency[idem_key] = order
    return order


@api_router.get(
    '/orders',
    response_model=OrderList,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Order'],
)
def order_list(
    sub: SubFromAccessCookie,
    language: Optional[Language] = None,
    limit: Optional[conint(ge=1)] = 100,
    cursor: Optional[str] = None,
    status_filter: Optional[OrderStatus] = Query(None, alias='status'),
    order_id: Optional[str] = Query(None, alias='orderId'),
) -> Union[OrderList, Error]:
    items = [order for owner, order in orders.values() if owner == sub]
    if order_id is not None:
        items = [order for order in items if order.orderId == order_id]
    if status_filter is not None:
        items = [order for order in items if order.status == status_filter]
    items.sort(key=lambda order: order.orderId)

    if cursor is not None:
        for index, order in enumerate(items):
            if int(order.orderId) >= int(cursor):
                items = items[index + 1 :]
                break

    page_size = int(limit)
    page = items[:page_size]
    next_cursor = page[-1].orderId if len(items) > page_size else None
    return OrderList(cursor=next_cursor, items=page)


@api_router.patch(
    '/orders/{orderId}',
    response_model=Order,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '404': {'model': Error},
        '409': {'model': Error},
        '422': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Order'],
)
def order_update(
    body: OrderUpdateRequest,
    sub: SubFromAccessCookie,
    order_id: str = Path(..., alias='orderId'),
) -> Union[Order, Error]:
    idem_key = f"{sub}:{body.idempotencyKey}"
    cached = order_idempotency.get(idem_key)
    if cached is not None:
        return cached

    order = _get_owned_order(order_id, sub)
    update = body.order
    if update.orderVer != order.orderVer:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Order version conflict",
        )

    data = order.model_dump()
    data.update(update.model_dump(exclude_none=True))
    data['orderVer'] = order.orderVer + 1

    updated = Order.model_validate(data)
    orders[order_id] = (sub, updated)
    order_idempotency[idem_key] = updated
    return updated


@api_router.delete(
    '/orders/{orderId}',
    response_model=None,
    status_code=204,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '404': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Order'],
)
def order_delete(
    body: Empty,
    sub: SubFromAccessCookie,
    order_id: str = Path(..., alias='orderId'),
) -> Optional[Error]:
    _get_owned_order(order_id, sub)
    del orders[order_id]
    keys = [
        key for key, order in order_idempotency.items() if order.orderId == order_id
    ]
    for key in keys:
        del order_idempotency[key]


@refresh_router.post(
    '/refreshedSessions',
    response_model=None,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Session'],
)
def session_refresh(
    body: Empty, response: Response, sub: SubFromRefreshCookie
) -> Optional[Error]:
    set_auth_cookies(response, sub)


@login_router.post(
    '/sessions',
    response_model=None,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Session'],
)
def session_create(body: SessionCreate, response: Response) -> Optional[Error]:
    if not authenticate_user(body.user, body.password):
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid credentials",
        )
    session = SessionListItem(
        id=str(uuid4()),
        createdAt=datetime.now(timezone.utc),
        info="info",
    )
    sessions[session.id] = (body.user, session)
    set_auth_cookies(response, body.user)


@api_router.get(
    '/sessions',
    response_model=List[SessionListItem],
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Session'],
)
def session_list(
    sub: SubFromAccessCookie,
    language: Optional[Language] = None,
) -> Union[List[SessionListItem], Error]:
    items = [session for owner, session in sessions.values() if owner == sub]
    items.sort(key=lambda session: session.createdAt, reverse=True)
    return items


@api_router.delete(
    '/sessions/{sessionId}',
    response_model=None,
    status_code=204,
    responses={
        '400': {'model': Error},
        '401': {'model': Error},
        '404': {'model': Error},
        '500': {'model': Error},
    },
    tags=['Session'],
)
def session_delete(
    body: Empty,
    sub: SubFromAccessCookie,
    session_id: str = Path(..., alias='sessionId'),
) -> Optional[Error]:
    stored = sessions.get(session_id)
    if not stored or stored[0] != sub:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "Session not found",
        )
    del sessions[session_id]


app.include_router(login_router)
app.include_router(refresh_router)
app.include_router(api_router)

root = FastAPI()
root.mount(settings.api_prefix, app)
