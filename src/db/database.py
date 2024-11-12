import asyncpg
import redis.asyncio as redis
import logging
from typing import Dict, List, Set, Tuple
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
            # Drop existing hangar_ships table to apply new schema
            await conn.execute('DROP TABLE IF EXISTS hangar_ships')
            
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
                    audio_config TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add audio_config column if it doesn't exist
            await conn.execute('''
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_info' 
                        AND column_name = 'audio_config'
                    ) THEN
                        ALTER TABLE system_info ADD COLUMN audio_config TEXT;
                    END IF;
                END $$;
            ''')

            # Create hangar table with detailed ship information
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS hangar_ships (
                    user_id BIGINT NOT NULL,
                    ship_code TEXT NOT NULL,
                    ship_name TEXT,
                    manufacturer_code TEXT NOT NULL,
                    manufacturer_name TEXT NOT NULL,
                    lti BOOLEAN NOT NULL,
                    name TEXT NOT NULL,
                    warbond BOOLEAN NOT NULL,
                    entity_type TEXT NOT NULL,
                    pledge_id TEXT NOT NULL,
                    pledge_name TEXT NOT NULL,
                    pledge_date TEXT NOT NULL,
                    pledge_cost TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, ship_code, pledge_id)
                )
            ''')

            # Create indexes
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_info_updated 
                ON system_info(updated_at)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_hangar_ships_user 
                ON hangar_ships(user_id)
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
                # Convert None values to empty strings for Redis
                cache_dict = {k: '' if v is None else str(v) for k, v in data_dict.items()}
                await self.cache.hmset(cache_key, cache_dict)
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

    async def update_peripherals(self, user_id: int, keyboard: str = None, mouse: str = None, other_controllers: str = None, audio_config: str = None):
        """Update peripherals information in database and cache"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE system_info 
                SET keyboard = $2, mouse = $3, other_controllers = $4, audio_config = $5,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            ''', user_id, keyboard, mouse, other_controllers, audio_config)
            
        # Invalidate cache
        cache_key = f"system_info:{user_id}"
        await self.cache.delete(cache_key)

    async def save_hangar_data(self, user_id: int, ships_json: str):
        """Save hangar data from JSON import with detailed ship information"""
        try:
            ships = json.loads(ships_json)
            logger.info(f"Saving {len(ships)} ships for user {user_id}")
            
            async with self.pool.acquire() as conn:
                # First, delete existing ships for this user
                await conn.execute('''
                    DELETE FROM hangar_ships WHERE user_id = $1
                ''', user_id)
                
                # Insert each ship with full details
                for ship in ships:
                    await conn.execute('''
                        INSERT INTO hangar_ships (
                            user_id, ship_code, ship_name, manufacturer_code,
                            manufacturer_name, lti, name, warbond, entity_type,
                            pledge_id, pledge_name, pledge_date, pledge_cost
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ''', 
                    user_id,
                    ship['ship_code'],
                    ship.get('ship_name', ship['name']),  # Use custom name if available, else default name
                    ship['manufacturer_code'],
                    ship['manufacturer_name'],
                    ship['lti'],
                    ship['name'],
                    ship['warbond'],
                    ship['entity_type'],
                    ship['pledge_id'],
                    ship['pledge_name'],
                    ship['pledge_date'],
                    ship['pledge_cost']
                    )
                
            # Invalidate caches
            cache_key = f"hangar:{user_id}"
            await self.cache.delete(cache_key)
            await self.cache.delete("fleet_total")
            await self.cache.delete("fleet_ships")
            
            # Verify the data was saved
            async with self.pool.acquire() as conn:
                count = await conn.fetchval('''
                    SELECT COUNT(*) FROM hangar_ships WHERE user_id = $1
                ''', user_id)
                logger.info(f"Saved {count} ships for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving hangar data: {e}")
            return False

    async def get_hangar_data(self, user_id: int) -> List[Dict]:
        """Get hangar data from cache or database"""
        cache_key = f"hangar:{user_id}"
        
        try:
            # Try cache first
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
                
            # If not in cache, get from database
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT 
                        ship_code, ship_name, manufacturer_code, manufacturer_name,
                        lti, name, warbond, entity_type, pledge_id, pledge_name,
                        pledge_date, pledge_cost
                    FROM hangar_ships 
                    WHERE user_id = $1
                    ORDER BY manufacturer_name, name
                ''', user_id)
                
                if rows:
                    # Convert to list of dictionaries
                    ships = [dict(row) for row in rows]
                    # Cache the result
                    await self.cache.set(cache_key, json.dumps(ships))
                    await self.cache.expire(cache_key, 3600)  # Cache for 1 hour
                    return ships
                    
                return []
        except Exception as e:
            logger.error(f"Error retrieving hangar data: {e}")
            return []

    async def get_fleet_total(self) -> Dict[str, Dict]:
        """Get total fleet counts with detailed information"""
        cache_key = "fleet_total"
        
        try:
            # Try cache first
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            # If not in cache, calculate from database
            async with self.pool.acquire() as conn:
                # First check if we have any ships at all
                count = await conn.fetchval('SELECT COUNT(*) FROM hangar_ships')
                logger.info(f"Total ships in database: {count}")
                
                if count == 0:
                    logger.info("No ships found in database")
                    return {}

                # Get fleet statistics
                rows = await conn.fetch('''
                    SELECT 
                        manufacturer_name, name,
                        COUNT(*) as count,
                        COUNT(*) FILTER (WHERE lti = true) as lti_count,
                        COUNT(*) FILTER (WHERE warbond = true) as warbond_count,
                        STRING_AGG(DISTINCT ship_name, ', ' ORDER BY ship_name) as custom_names
                    FROM hangar_ships
                    GROUP BY manufacturer_name, name
                    ORDER BY manufacturer_name, name
                ''')
                
                logger.info(f"Fleet query returned {len(rows)} rows")
                
                fleet_data = {}
                for row in rows:
                    key = f"{row['manufacturer_name']} {row['name']}"
                    fleet_data[key] = {
                        'count': row['count'],
                        'lti_count': row['lti_count'],
                        'warbond_count': row['warbond_count'],
                        'custom_names': row['custom_names'] if row['custom_names'] != row['name'] else None
                    }
                    logger.info(f"Added fleet data for {key}: {fleet_data[key]}")

                if not fleet_data:
                    logger.error("No fleet data generated from query results")
                    return {}

                # Cache the result
                await self.cache.set(cache_key, json.dumps(fleet_data))
                await self.cache.expire(cache_key, 3600)  # Cache for 1 hour
                
                return fleet_data
        except Exception as e:
            logger.error(f"Error getting fleet total: {e}")
            return {}

    async def get_ship_owners(self, ship_name: str) -> List[Dict]:
        """Get detailed information about owners of a specific ship"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT 
                        user_id, ship_name, lti, warbond,
                        pledge_date, pledge_cost, pledge_name
                    FROM hangar_ships
                    WHERE manufacturer_name || ' ' || name = $1
                    ORDER BY pledge_date
                ''', ship_name)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting ship owners: {e}")
            return []

    async def get_all_ship_models(self) -> Set[str]:
        """Get a set of all unique ship models in the fleet"""
        cache_key = "fleet_ships"
        
        try:
            # Try cache first
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return set(json.loads(cached_data))

            # If not in cache, get from database
            async with self.pool.acquire() as conn:
                # First check if we have any ships at all
                count = await conn.fetchval('SELECT COUNT(*) FROM hangar_ships')
                logger.info(f"Total ships in database: {count}")
                
                if count == 0:
                    logger.info("No ships found in database")
                    return set()

                rows = await conn.fetch('''
                    SELECT DISTINCT manufacturer_name || ' ' || name as full_name
                    FROM hangar_ships
                    ORDER BY full_name
                ''')
                
                logger.info(f"Found {len(rows)} unique ship models")
                ship_models = {row['full_name'] for row in rows}

                if not ship_models:
                    logger.error("No ship models found in query results")
                    return set()

                # Cache the result
                await self.cache.set(cache_key, json.dumps(list(ship_models)))
                await self.cache.expire(cache_key, 3600)  # Cache for 1 hour
                
                return ship_models
        except Exception as e:
            logger.error(f"Error getting ship models: {e}")
            return set()

    async def close(self):
        """Close database and cache connections"""
        if self.pool:
            await self.pool.close()
        if self.cache:
            await self.cache.aclose()
