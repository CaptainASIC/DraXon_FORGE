import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

async def init_database():
    """Initialize the database and create required tables"""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / 'env' / '.env'
    load_dotenv(env_path)

    # Get database configuration
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')

    try:
        # First connect to 'postgres' database to create our database if it doesn't exist
        sys_conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres',
            host=DB_HOST,
            port=DB_PORT
        )

        # Check if our database exists
        exists = await sys_conn.fetchval(
            'SELECT 1 FROM pg_database WHERE datname = $1',
            DB_NAME
        )

        if not exists:
            print(f"Creating database {DB_NAME}...")
            await sys_conn.execute(f'CREATE DATABASE "{DB_NAME}"')
        
        await sys_conn.close()

        # Now connect to our database and create tables
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )

        print("Creating tables...")
        
        # Create system_info table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS system_info (
                user_id BIGINT PRIMARY KEY,
                os TEXT NOT NULL,
                cpu TEXT NOT NULL,
                gpu TEXT NOT NULL,
                memory TEXT NOT NULL,
                storage TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_system_info_updated 
            ON system_info(updated_at)
        ''')

        print("Database initialization complete!")
        await conn.close()

    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

def main():
    """Main function to run database initialization"""
    print("Starting database initialization...")
    asyncio.run(init_database())

if __name__ == "__main__":
    main()
