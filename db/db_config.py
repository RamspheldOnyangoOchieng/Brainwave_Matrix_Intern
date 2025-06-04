import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DatabaseConfig:
    _instance = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        """Initialize Supabase client with environment variables."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError("Missing Supabase credentials in environment variables")

            self._client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if not self._client:
            self._initialize_client()
        return self._client

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query (str): SQL query to execute
            params (Dict[str, Any], optional): Query parameters
            
        Returns:
            Any: Query results
        """
        try:
            response = await self.client.rpc('execute_query', {
                'query': query,
                'params': params or {}
            })
            return response
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def insert_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a record into the specified table.
        
        Args:
            table (str): Table name
            data (Dict[str, Any]): Record data
            
        Returns:
            Dict[str, Any]: Inserted record
        """
        try:
            response = await self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to insert record into {table}: {str(e)}")
            raise

    async def get_record(self, table: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get a single record from the specified table.
        
        Args:
            table (str): Table name
            query (Dict[str, Any]): Query conditions
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved record
        """
        try:
            response = await self.client.table(table).select("*").match(query).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get record from {table}: {str(e)}")
            raise

    async def update_record(self, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record in the specified table.
        
        Args:
            table (str): Table name
            query (Dict[str, Any]): Query conditions
            data (Dict[str, Any]): Update data
            
        Returns:
            Dict[str, Any]: Updated record
        """
        try:
            response = await self.client.table(table).update(data).match(query).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update record in {table}: {str(e)}")
            raise

    async def delete_record(self, table: str, query: Dict[str, Any]) -> bool:
        """
        Delete a record from the specified table.
        
        Args:
            table (str): Table name
            query (Dict[str, Any]): Query conditions
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            response = await self.client.table(table).delete().match(query).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete record from {table}: {str(e)}")
            raise

# Create a singleton instance
db = DatabaseConfig()

# Export the database instance
__all__ = ['db']
