import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db
from datetime import date

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_integration_booking_flow():
    # 1. Напрямую создаем изолированную БД в памяти прямо внутри теста
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # 2. Пишем чистую функцию подмены зависимости без всяких генераторов и фикстур
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Проверяем доступность комнат
            res = await ac.get(f"/rooms/availability?booking_date={date.today()}")
            assert res.status_code == 200
            
            # Создаем бронь сотрудником emp_10
            booking_payload = {
                "room_id": "Room-B",
                "date": str(date.today()),
                "slot": "13:00-15:00",
                "employee_id": "emp_10"
            }
            res_post = await ac.post("/bookings", json=booking_payload, headers={"x-user-id": "emp_10"})
            assert res_post.status_code == 201
            booking_id = res_post.json()["id"]

            # Пробуем удалить её под другим пользователем emp_wrong (Ожидаем 403)
            res_del_fail = await ac.delete(f"/bookings/{booking_id}", headers={"x-user-id": "emp_wrong", "x-role": "employee"})
            assert res_del_fail.status_code == 403

            # Удаляем под администратором (Ожидаем 200)
            res_del_success = await ac.delete(f"/bookings/{booking_id}", headers={"x-user-id": "admin_1", "x-role": "admin"})
            assert res_del_success.status_code == 200
    finally:
        # Очищаем подмену после теста
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
