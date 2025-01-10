from aioredis import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import create_async_engine

from base.config import config


class DatabaseConnector:
    def __init__(self):
        self.database_connect_url = config.database.postgres_url
        self.engine = None
        self.connect()

    def connect(self):
        self.engine = create_async_engine(self.database_connect_url)


class RedisConnector:
    def __init__(self):
        self.pool: ConnectionPool | None = None

    async def connect(self):
        if self.pool is None:
            self.pool = ConnectionPool.from_url(
                f"redis://{config.redis.REDIS_USER}:{config.redis.REDIS_PASSWORD}@{config.redis.REDIS_HOST}:{config.redis.REDIS_PORT}/{config.redis.REDIS_DB}",
                max_connections=config.redis.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.disconnect()
            self.pool = None

    async def release(self, rds: Redis):
        if self.pool:
            if rds.connection and rds.connection.is_connected:
                await self.pool.release(rds.connection)

    async def get_redis(self) -> Redis:
        if self.pool is None:
            await self.connect()
        return Redis(connection_pool=self.pool)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()


database_connector = DatabaseConnector()
rds_client = RedisConnector()
