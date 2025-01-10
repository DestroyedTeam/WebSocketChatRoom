import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatRoomBaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(str(Path(__file__).parents[1]), ".env"),
        extra="ignore",
    )


class BaseConfig(ChatRoomBaseConfig):
    LOG_PATH: str
    LOG_LEVEL: str

    def __init__(self):
        super().__init__()


class DatabaseConfig(ChatRoomBaseConfig):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    def __init__(self):
        super().__init__()

    @property
    def postgres_url(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )


class RedisConfig(ChatRoomBaseConfig):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""

    def __init__(self):
        super().__init__()

    @property
    def redis_url(self):
        return f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.redis.REDIS_HOST}:{config.redis.REDIS_PORT}/{config.redis.REDIS_DB}"


class Config(BaseSettings):
    base: BaseConfig = BaseConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()


config = Config()


if __name__ == "__main__":
    print(config)
