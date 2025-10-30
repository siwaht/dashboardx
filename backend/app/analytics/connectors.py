"""
Data Connectors for Various Data Sources

Supports connections to:
- SQL databases (PostgreSQL, MySQL, SQLite)
- NoSQL databases (MongoDB, Redis)
- File systems (CSV, Excel, JSON, Parquet)
- APIs (REST, GraphQL)
- Streaming sources (Kafka, WebSocket)
"""

import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import pandas as pd
import json
from datetime import datetime
from enum import Enum

# Database connectors
import asyncpg
import aiomysql
import aiosqlite
from motor.motor_asyncio import AsyncIOMotorClient
import aioredis

# File handling
import aiofiles
import openpyxl
import pyarrow.parquet as pq

# API clients
import httpx

# Streaming
from aiokafka import AIOKafkaConsumer
import websockets

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Supported data source types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    KAFKA = "kafka"
    WEBSOCKET = "websocket"


class BaseConnector(ABC):
    """Abstract base class for all data connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to data source"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a query against the data source"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema/structure information"""
        pass


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL database connector"""
    
    async def connect(self) -> None:
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                user=self.config.get("user"),
                password=self.config.get("password"),
                database=self.config.get("database")
            )
            self.connected = True
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL"""
        if self.connection:
            await self.connection.close()
            self.connected = False
            logger.info("Disconnected from PostgreSQL")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute SQL query"""
        if not self.connected:
            await self.connect()
        
        try:
            # Execute query
            if params:
                rows = await self.connection.fetch(query, *params.values())
            else:
                rows = await self.connection.fetch(query)
            
            # Convert to list of dicts
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            if not self.connected:
                await self.connect()
            
            result = await self.connection.fetchval("SELECT 1")
            return result == 1
        except Exception:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.connected:
            await self.connect()
        
        # Get all tables
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        tables = await self.connection.fetch(tables_query)
        
        schema = {}
        for table in tables:
            table_name = table['table_name']
            
            # Get columns for each table
            columns_query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            columns = await self.connection.fetch(columns_query, table_name)
            
            schema[table_name] = {
                "columns": [
                    {
                        "name": col['column_name'],
                        "type": col['data_type'],
                        "nullable": col['is_nullable'] == 'YES'
                    }
                    for col in columns
                ]
            }
        
        return schema


class MySQLConnector(BaseConnector):
    """MySQL database connector"""
    
    async def connect(self) -> None:
        """Connect to MySQL database"""
        try:
            self.connection = await aiomysql.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user"),
                password=self.config.get("password"),
                db=self.config.get("database"),
                autocommit=True
            )
            self.connected = True
            logger.info("Connected to MySQL database")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MySQL"""
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("Disconnected from MySQL")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute SQL query"""
        if not self.connected:
            await self.connect()
        
        try:
            async with self.connection.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, list(params.values()))
                else:
                    await cursor.execute(query)
                
                result = await cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test MySQL connection"""
        try:
            if not self.connected:
                await self.connect()
            
            async with self.connection.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                return result[0] == 1
        except Exception:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.connected:
            await self.connect()
        
        schema = {}
        
        async with self.connection.cursor() as cursor:
            # Get all tables
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Get columns for each table
                # Properly quote table name to prevent SQL injection issues.
                await cursor.execute(f"DESCRIBE `{table_name.replace('`', '``')}`")
                columns = await cursor.fetchall()
                
                schema[table_name] = {
                    "columns": [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == 'YES'
                        }
                        for col in columns
                    ]
                }
        
        return schema


class CSVConnector(BaseConnector):
    """CSV file connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.dataframe = None
    
    async def connect(self) -> None:
        """Load CSV file"""
        try:
            file_path = self.config.get("file_path")
            
            # Read CSV file
            self.dataframe = pd.read_csv(
                file_path,
                encoding=self.config.get("encoding", "utf-8"),
                delimiter=self.config.get("delimiter", ","),
                parse_dates=self.config.get("parse_dates", True)
            )
            
            self.connected = True
            logger.info(f"Loaded CSV file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Clear dataframe"""
        self.dataframe = None
        self.connected = False
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute pandas query on CSV data"""
        if not self.connected:
            await self.connect()
        
        try:
            # Support SQL-like queries using pandasql or simple filtering
            if query.upper().startswith("SELECT"):
                # Use pandasql for SQL queries
                from pandasql import sqldf
                result_df = sqldf(query, {"df": self.dataframe})
            else:
                # Use pandas query method
                result_df = self.dataframe.query(query) if query else self.dataframe
            
            return result_df.to_dict('records')
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test CSV file access"""
        try:
            if not self.connected:
                await self.connect()
            return self.dataframe is not None and not self.dataframe.empty
        except Exception:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get CSV schema (columns and types)"""
        if not self.connected:
            await self.connect()
        
        return {
            "columns": [
                {
                    "name": col,
                    "type": str(self.dataframe[col].dtype),
                    "nullable": self.dataframe[col].isnull().any()
                }
                for col in self.dataframe.columns
            ],
            "row_count": len(self.dataframe),
            "file_path": self.config.get("file_path")
        }


class RESTAPIConnector(BaseConnector):
    """REST API connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
    
    async def connect(self) -> None:
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(
            base_url=self.config.get("base_url"),
            headers=self.config.get("headers", {}),
            timeout=self.config.get("timeout", 30.0)
        )
        self.connected = True
        logger.info(f"REST API client initialized for {self.config.get('base_url')}")
    
    async def disconnect(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.connected = False
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute API request"""
        if not self.connected:
            await self.connect()
        
        try:
            # Parse query as endpoint and method
            # Format: "GET /endpoint" or "POST /endpoint"
            parts = query.split(" ", 1)
            method = parts[0].upper() if parts else "GET"
            endpoint = parts[1] if len(parts) > 1 else "/"
            
            # Make request
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params if method == "GET" else None,
                json=params if method in ["POST", "PUT", "PATCH"] else None
            )
            
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            if not self.connected:
                await self.connect()
            
            # Try health check endpoint if configured
            health_endpoint = self.config.get("health_endpoint", "/")
            response = await self.client.get(health_endpoint)
            return response.status_code < 400
        except Exception:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get API schema (if available)"""
        if not self.connected:
            await self.connect()
        
        # Try to get OpenAPI/Swagger schema if available
        schema_endpoints = ["/openapi.json", "/swagger.json", "/api-docs"]
        
        for endpoint in schema_endpoints:
            try:
                response = await self.client.get(endpoint)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                continue
        
        # Return basic info if no schema available
        return {
            "base_url": self.config.get("base_url"),
            "endpoints": self.config.get("endpoints", [])
        }


class KafkaConnector(BaseConnector):
    """Kafka streaming connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.consumer = None
    
    async def connect(self) -> None:
        """Connect to Kafka"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.config.get("topics", []),
                bootstrap_servers=self.config.get("bootstrap_servers", "localhost:9092"),
                group_id=self.config.get("group_id", "analytics-consumer"),
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            await self.consumer.start()
            self.connected = True
            logger.info("Connected to Kafka")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Kafka"""
        if self.consumer:
            await self.consumer.stop()
            self.connected = False
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Consume messages from Kafka"""
        if not self.connected:
            await self.connect()
        
        try:
            # Get batch of messages
            batch_size = params.get("batch_size", 100) if params else 100
            timeout = params.get("timeout", 5) if params else 5
            
            messages = []
            end_time = asyncio.get_event_loop().time() + timeout
            
            async for msg in self.consumer:
                messages.append({
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "timestamp": msg.timestamp,
                    "key": msg.key.decode('utf-8') if msg.key else None,
                    "value": msg.value
                })
                
                if len(messages) >= batch_size:
                    break
                
                if asyncio.get_event_loop().time() >= end_time:
                    break
            
            return messages
        except Exception as e:
            logger.error(f"Failed to consume messages: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test Kafka connection"""
        try:
            if not self.connected:
                await self.connect()
            
            # Check if consumer is active
            return self.consumer is not None
        except Exception:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get Kafka topics information"""
        if not self.connected:
            await self.connect()
        
        topics = await self.consumer.topics()
        partitions = {}
        
        for topic in topics:
            partitions[topic] = len(self.consumer.partitions_for_topic(topic) or [])
        
        return {
            "topics": list(topics),
            "partitions": partitions,
            "group_id": self.config.get("group_id")
        }


class DataConnectorFactory:
    """Factory for creating data connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.connector_classes = {
            DataSourceType.POSTGRESQL: PostgreSQLConnector,
            DataSourceType.MYSQL: MySQLConnector,
            DataSourceType.CSV: CSVConnector,
            DataSourceType.REST_API: RESTAPIConnector,
            DataSourceType.KAFKA: KafkaConnector,
        }
    
    async def create_connector(
        self,
        source_type: DataSourceType,
        config: Dict[str, Any]
    ) -> BaseConnector:
        """Create a new connector instance"""
        
        connector_class = self.connector_classes.get(source_type)
        if not connector_class:
            raise ValueError(f"Unsupported data source type: {source_type}")
        
        connector = connector_class(config)
        await connector.connect()
        
        return connector
    
    async def get_connector(self, data_source_id: str) -> BaseConnector:
        """Get or create a connector by ID"""
        
        if data_source_id in self.connectors:
            return self.connectors[data_source_id]
        
        # Load configuration from database or config file
        config = await self._load_connector_config(data_source_id)
        
        # Create connector
        source_type = DataSourceType(config.get("type"))
        connector = await self.create_connector(source_type, config)
        
        # Cache connector
        self.connectors[data_source_id] = connector
        
        return connector
    
    async def _load_connector_config(self, data_source_id: str) -> Dict[str, Any]:
        """Load connector configuration from storage"""
        
        # This would typically load from database
        # For now, return sample configurations
        configs = {
            "postgres_main": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "analytics",
                "user": "analytics_user",
                "password": "password"
            },
            "mysql_sales": {
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "sales",
                "user": "sales_user",
                "password": "password"
            },
            "csv_data": {
                "type": "csv",
                "file_path": "/data/analytics.csv"
            },
            "api_external": {
                "type": "rest_api",
                "base_url": "https://api.example.com",
                "headers": {"Authorization": "Bearer token"}
            },
            "kafka_events": {
                "type": "kafka",
                "bootstrap_servers": "localhost:9092",
                "topics": ["events", "metrics"],
                "group_id": "analytics-consumer"
            }
        }
        
        config = configs.get(data_source_id)
        if not config:
            raise ValueError(f"Unknown data source: {data_source_id}")
        
        return config
    
    async def list_data_sources(self) -> List[Dict[str, Any]]:
        """List all available data sources"""
        
        # This would typically query from database
        return [
            {
                "id": "postgres_main",
                "name": "Main PostgreSQL",
                "type": "postgresql",
                "status": "active"
            },
            {
                "id": "mysql_sales",
                "name": "Sales MySQL",
                "type": "mysql",
                "status": "active"
            },
            {
                "id": "csv_data",
                "name": "CSV Data Files",
                "type": "csv",
                "status": "active"
            },
            {
                "id": "api_external",
                "name": "External API",
                "type": "rest_api",
                "status": "active"
            },
            {
                "id": "kafka_events",
                "name": "Event Stream",
                "type": "kafka",
                "status": "active"
            }
        ]
    
    async def close_all(self):
        """Close all active connections"""
        for connector in self.connectors.values():
            await connector.disconnect()
        
        self.connectors.clear()
        logger.info("All connectors closed")
