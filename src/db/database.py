import asyncpg
import redis.asyncio as redis
import logging
from typing import Dict, List
import json
from collections import defaultdict

logger = logging.getLogger('DraXon_FORGE')

async def init_db(database_url: str) -> asyncpg.Pool:
    """Initialize PostgreSQL connection pool"""
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(database_url)
        
        # Initialize database tables
        async with pool.acquire() as conn:
            # Create system_info table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS system_info (
                    user_id BIGINT PRIMARY KEY,
                    os TEXT NOT NULL,
                    cpu TEXT NOT NULL,
                    gpu TEXT NOT NULL,
                    memory TEXT NOT NULL,
                    storage TEXT NOT NULL,
                    keyboard TEXT,
                    mouse TEXT,
                    other_controllers TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create hangar table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS hangar_ships (
                    user_id BIGINT PRIMARY KEY,
                    ships JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_info_updated 
                ON system_info(updated_at)
            ''')

        return pool
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

async def init_redis(redis_url: str) -> redis.Redis:
    """Initialize Redis connection"""
    try:
        # Create Redis connection
        redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        await redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis initialization error: {e}")
        raise

class Database:
    def __init__(self, pool: asyncpg.Pool, cache: redis.Redis):
        self.pool = pool
        self.cache = cache
        
    async def get_system_info(self, user_id: int) -> Dict:
        """Get system information from cache or database"""
        # Try cache first
        cache_key = f"system_info:{user_id}"
        cached_data = await self.cache.hgetall(cache_key)
        
        if cached_data:
            return cached_data
            
        # If not in cache, get from database
        async with self.pool.acquire() as conn:
            data = await conn.fetchrow('''
                SELECT * FROM system_info WHERE user_id = $1
            ''', user_id)
            
            if data:
                # Convert to dict and cache
                data_dict = dict(data)
                # Convert datetime to string for Redis
                data_dict['updated_at'] = data_dict['updated_at'].isoformat()
                await self.cache.hmset(cache_key, data_dict)
                await self.cache.expire(cache_key, 3600)  # Cache for 1 hour
                return data_dict
                
            return None

    async def save_system_info(self, user_id: int, os: str, cpu: str, gpu: str, memory: str, storage: str):
        """Save system information to database and cache"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO system_info (user_id, os, cpu, gpu, memory, storage)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    os = $2, cpu = $3, gpu = $4, memory = $5, storage = $6,
                    updated_at = CURRENT_TIMESTAMP
            ''', user_id, os, cpu, gpu, memory, storage)
            
        # Invalidate cache
        cache_key = f"system_info:{user_id}"
        await self.cache.delete(cache_key)

    async def update_peripherals(self, user_id: int, keyboard: str = None, mouse: str = None, other_controllers: str = None):
        """Update peripherals information in database and cache"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE system_info 
                SET keyboard = $2, mouse = $3, other_controllers = $4,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            ''', user_id, keyboard, mouse, other_controllers)
            
        # Invalidate cache
        cache_key = f"system_info:{user_id}"
        await self.cache.delete(cache_key)

    async def save_hangar_data(self, user_id: int, ships_json: str):
        """Save hangar data from JSON import"""
        try:
            ships = json.loads(ships_json)
            # Create a simple dictionary of ship counts
            ship_counts = defaultdict(int)
            
            for ship in ships:
                # Combine manufacturer and name for the full ship name
                full_name = f"{ship['manufacturer_name']} {ship['name']}"
                ship_counts[full_name] += 1
            
            # Store as simple dictionary
            ship_data = dict(ship_counts)
            logger.info(f"Saving ship data: {ship_data}")  # Debug log
            
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO hangar_ships (user_id, ships)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        ships = $2,
                        updated_at = CURRENT_TIMESTAMP
                ''', user_id, json.dumps(ship_data))
                
            # Invalidate cache
            cache_key = f"hangar:{user_id}"
            await self.cache.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Error saving hangar data: {e}")
            return False

    async def get_hangar_data(self, user_id: int) -> Dict:
        """Get hangar data from cache or database"""
        cache_key = f"hangar:{user_id}"
        
        try:
            # Try cache first
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Retrieved cached hangar data: {data}")  # Debug log
                return data
                
            # If not in cache, get from database
            async with self.pool.acquire() as conn:
                data = await conn.fetchval('''
                    SELECT ships FROM hangar_ships WHERE user_id = $1
                ''', user_id)
                
                if data:
                    parsed_data = json.loads(data)
                    logger.info(f"Retrieved database hangar data: {parsed_data}")  # Debug log
                    # Cache the result
                    await self.cache.set(cache_key, data)
                    await self.cache.expire(cache_key, 3600)  # Cache for 1 hour
                    return parsed_data
                    
                return None
        except Exception as e:
            logger.error(f"Error retrieving hangar data: {e}")
            return None

    async def close(self):
        """Close database and cache connections"""
        if self.pool:
            await self.pool.close()
        if self.cache:
            await self.cache.aclose()
