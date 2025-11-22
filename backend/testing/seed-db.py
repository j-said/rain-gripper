import logging
import uuid
import random
from datetime import datetime, timedelta, timezone
import json

from database import (
    SessionLocal,
    create_all_tables,
    User,
    DeviceGroup,
    Device,
    SensorData,
    DeviceRepository,
)
from crud import get_password_hash

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def seed():
    db = SessionLocal()

    log.info("Creating tables if not exist...")
    create_all_tables()

    users_data = [
        ("test@example.com", "tester", "Test User"),
        ("agronomist@example.com", "agro_bob", "Bob The Builder"),
        ("manager@example.com", "manager_alice", "Alice Manager"),
    ]

    created_users = {}

    for email, username, name in users_data:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                username=username,
                email=email,
                name=name,
                hashed_password=get_password_hash("password123"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info(f"Created user: {email}")
        created_users[email] = user

    main_user = created_users["test@example.com"]

    # --- 3. HARDWARE REPOSITORY (Factory) ---
    # We need:
    # - Group 1: 2 devices
    # - Group 2: 1 device
    # - Unused: 5 devices
    # Total needed: 8 devices. Let's create 10 to be safe and round numbers.

    repo_devices = [
        ("AA:00:00:00:00:01", "RainGripper Pro"),  # For Group 1
        ("AA:00:00:00:00:02", "RainGripper Pro"),  # For Group 1
        ("AA:00:00:00:00:03", "RainGripper Mini"),  # For Group 2
        ("XX:00:00:00:00:01", "RainGripper Pro"),  # Unused 1
        ("XX:00:00:00:00:02", "RainGripper Pro"),  # Unused 2
        ("XX:00:00:00:00:03", "RainGripper Mini"),  # Unused 3
        ("XX:00:00:00:00:04", "RainGripper Mini"),  # Unused 4
        ("XX:00:00:00:00:05", "RainGripper X"),  # Unused 5
    ]

    for mac, model in repo_devices:
        if not db.query(DeviceRepository).filter_by(mac_address=mac).first():
            item = DeviceRepository(mac_address=mac, model=model)
            db.add(item)
    db.commit()
    log.info(f"Hardware repository stocked with {len(repo_devices)} items.")

    group_1 = (
        db.query(DeviceGroup)
        .filter_by(owner_user_id=main_user.user_id, local_name="a")
        .first()
    )
    if not group_1:
        group_1 = DeviceGroup(
            owner_user_id=main_user.user_id,
            local_name="a",
            display_name="Alpha Fields (North)",
        )
        db.add(group_1)

    # Group 2: 1 device
    group_2 = (
        db.query(DeviceGroup)
        .filter_by(owner_user_id=main_user.user_id, local_name="b")
        .first()
    )
    if not group_2:
        group_2 = DeviceGroup(
            owner_user_id=main_user.user_id,
            local_name="b",
            display_name="Beta Greenhouse",
        )
        db.add(group_2)

    # Group 3: Empty
    group_3 = (
        db.query(DeviceGroup)
        .filter_by(owner_user_id=main_user.user_id, local_name="c")
        .first()
    )
    if not group_3:
        group_3 = DeviceGroup(
            owner_user_id=main_user.user_id,
            local_name="c",
            display_name="Gamma Storage (Empty)",
        )
        db.add(group_3)

    db.commit()
    db.refresh(group_1)
    db.refresh(group_2)
    db.refresh(group_3)

    assignments = [
        # (Group Object, MAC, Local ID, Name)
        (group_1, "AA:00:00:00:00:01", 1, "Sensor North-1"),
        (group_1, "AA:00:00:00:00:02", 2, "Sensor North-2"),
        (group_2, "AA:00:00:00:00:03", 1, "Greenhouse Main"),
    ]

    for grp, mac, local_id, name in assignments:
        existing = db.query(Device).filter_by(mac_address=mac).first()
        if not existing:
            dev = Device(
                group_id=grp.group_id,
                mac_address=mac,
                local_id=local_id,
                device_name=name,
            )
            db.add(dev)
    db.commit()
    log.info("Devices assigned to groups.")

    log.info("Generating 7 days of sensor data...")

    assigned_devices = (
        db.query(Device)
        .join(DeviceGroup)
        .filter(DeviceGroup.owner_user_id == main_user.user_id)
        .all()
    )

    now = datetime.now(timezone.utc)
    data_buffer = []

    group_locations = {
        "a": (50.4500, 30.5200),  # Kyiv Center
        "b": (50.4600, 30.5300),  # Slightly North-East
    }

    for dev in assigned_devices:
        base_lat, base_lon = group_locations.get(dev.group.local_name, (50.0, 30.0))
        dev_lat = base_lat + (dev.local_id * 0.002)
        dev_lon = base_lon + (dev.local_id * 0.002)

        # 7 Days * 24 Hours = 168 points
        for hour in range(24 * 7):
            time_point = now - timedelta(hours=hour)

            # Simulate daily cycle (temperature drops at night)
            hour_of_day = time_point.hour
            is_day = 6 <= hour_of_day <= 20

            temp_base = 20 if is_day else 15

            payload = {
                "water_level": round(40 + random.uniform(-5, 5), 1),
                "air_temp": round(temp_base + random.uniform(-2, 2), 1),
                "soil_temp": round(
                    (temp_base - 2) + random.uniform(-0.5, 0.5), 1
                ),  # Soil is more stable
                "air_humidity": round(60 + random.uniform(-10, 10), 1),
                "soil_humidity": round(50 + random.uniform(-2, 2), 1),
                "latitude": dev_lat,
                "longitude": dev_lon,
                "battery": round(
                    100 - (hour * 0.05), 1
                ),  # Battery draining over the week
            }

            record = SensorData(
                timestamp=time_point,
                device_id=dev.device_id,
                owner_user_id=main_user.user_id,
                # FIX: Pass the dictionary directly
                payload=payload
            )
            data_buffer.append(record)

            # Commit in chunks of 500 to avoid memory issues
            if len(data_buffer) >= 500:
                db.add_all(data_buffer)
                db.commit()
                data_buffer = []

    if data_buffer:
        db.add_all(data_buffer)
        db.commit()

    log.info("Database seed complete.")
    db.close()


if __name__ == "__main__":
    seed()
