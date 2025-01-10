from base.connector import rds_client


async def get_redis_session():
    # 获取 Redis 连接
    redis = await rds_client.get_redis()
    return redis
