import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from datetime import date

@pytest.mark.asyncio
async def test_integration_booking_flow(db_session):
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"/rooms/availability?booking_date={date.today()}")
        assert res.status_code == 200
        
        booking_payload = {
            "room_id": "Room-B",
            "date": str(date.today()),
            "slot": "13:00-15:00",
            "employee_id": "emp_10"
        }
        res_post = await ac.post("/bookings", json=booking_payload, headers={"x-user-id": "emp_10"})
        assert res_post.status_code == 201
        booking_id = res_post.json()["id"]

        res_del_fail = await ac.delete(f"/bookings/{booking_id}", headers={"x-user-id": "emp_wrong", "x-role": "employee"})
        assert res_del_fail.status_code == 403

        res_del_success = await ac.delete(f"/bookings/{booking_id}", headers={"x-user-id": "admin_1", "x-role": "admin"})
        assert res_del_success.status_code == 200

    app.dependency_overrides.clear()
