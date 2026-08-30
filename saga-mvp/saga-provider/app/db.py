import os

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "saga")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

users_col = db["users"]
agents_col = db["agents"]


async def ensure_indexes():
    await users_col.create_index("uid", unique=True)
    await agents_col.create_index("aid", unique=True)
