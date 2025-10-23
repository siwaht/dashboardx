"""
Structured Data RAG for Analytics

Handles natural language to SQL conversion, schema understanding,
and cross-data source querying for structured data.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# LangChain components
from langchain.prompts import ChatPromptTemplate, FewShotPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# SQL parsing and validation
import sqlparse
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class StructuredDataRAG:
    """
    RAG system specialized for structured data analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Structured Data RAG"""
        self.config = config or {}
        self.llm = ChatOpenAI(
            model=self.config.get("model", "gpt-4"),
            temperature=self.config.get("temperature", 0.1)
        )
        self.embeddings = OpenAIEmbeddings()
        self.memory = ConversationBufferMemory(return_messages=True)
        
        # Schema cache
        self.schema_cache = {}
        self.table_descriptions = {}
        
        # Query templates and examples
        self.query_examples = self._load_query_examples()
        
        logger.info("StructuredDataRAG initialized")
    
    async def natural_language_to_sql(
        self,
        query: str,
        data_source_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert natural language query to SQL
        
        Args:
            query: Natural language query
            data_source_id: ID of the data source
            context: Additional context
            
        Returns:
            SQL query string
        """
        logger.info(f"Converting NL to SQL: {query}")
        
        # Get schema information
        schema = await self._get_schema(data_source_id)
        
        # Find relevant tables
        relevant_tables = await self._find_relevant_tables(query, schema)
        
        # Generate SQL query
        sql_query = await self._generate_sql(query, relevant_tables, schema, context)
        
        # Validate and optimize query
        sql_query = await self._validate_and_optimize_sql(sql_query, schema)
        
        logger.info(f"Generated SQL: {sql_query}")
        return sql_query
    
    async def _get_schema(self, data_source_id: str) -> Dict[str, Any]:
        """Get schema information for data source"""
        if data_source_id in self.schema_cache:
            return self.schema_cache[data_source_id]
        
        # This would connect to actual data source
        # For now, return mock schema
        schema = {
            "tables": {
                "sales": {
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "date", "type": "date"},
                        {"name": "product_id", "type": "integer", "foreign_key": "products.id"},
                        {"name": "customer_id", "type": "integer", "foreign_key": "customers.id"},
                        {"name": "quantity", "type": "integer"},
                        {"name": "amount", "type": "decimal"},
                        {"name": "region", "type": "varchar"}
                    ],
                    "description": "Sales transactions"
                },
                "products": {
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "name", "type": "varchar"},
                        {"name": "category", "type": "varchar"},
                        {"name": "price", "type": "decimal"},
                        {"name": "cost", "type": "decimal"}
                    ],
                    "description": "Product catalog"
                },
                "customers": {
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "name", "type": "varchar"},
                        {"name": "email", "type": "varchar"},
                        {"name": "segment", "type": "varchar"},
                        {"name": "created_at", "type": "timestamp"}
                    ],
                    "description": "Customer information"
                }
            },
            "relationships": [
                {
                    "from": "sales.product_id",
                    "to": "products.id",
                    "type": "many_to_one"
                },
                {
                    "from": "sales.customer_id",
                    "to": "customers.id",
                    "type": "many_to_one"
                }
            ]
        }
        
        self.schema_cache[data_source_id] = schema
        return schema
    
    async def _find_relevant_tables(
        self,
        query: str,
        schema: Dict[str, Any]
    ) -> List[str]:
        """Find tables relevant to the query"""
        relevant_tables = []
        query_lower = query.lower()
        
        # Check for table name mentions
        for table_name, table_info in schema.get("tables", {}).items():
            # Check if table name is mentioned
            if table_name.lower() in query_lower:
                relevant_tables.append(table_name)
                continue
            
            # Check if table description matches
            description = table_info.get("description", "").lower()
            if any(word in query_lower for word in description.split()):
                relevant_tables.append(table_name)
                continue
            
            # Check column names
            for column in table_info.get("columns", []):
                if column["name"].lower() in query_lower:
                    relevant_tables.append(table_name)
                    break
        
        # If no tables found, use semantic search
        if not relevant_tables:
            relevant_tables = await self._semantic_table_search(query, schema)
        
        return list(set(relevant_tables))  # Remove duplicates
    
    async def _semantic_table_search(
        self,
        query: str,
        schema: Dict[str, Any]
    ) -> List[str]:
        """Use semantic search to find relevant tables"""
        # Create documents from schema
        documents = []
        for table_name, table_info in schema.get("tables", {}).items():
            # Create document with table information
            content = f"Table: {table_name}\n"
            content += f"Description: {table_info.get('description', '')}\n"
            content += "Columns: " + ", ".join(
                [col["name"] for col in table_info.get("columns", [])]
            )
            
            documents.append(Document(
                page_content=content,
                metadata={"table": table_name}
            ))
        
        # Create vector store
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        
        # Search for relevant tables
        results = vectorstore.similarity_search(query, k=3)
        
        return [doc.metadata["table"] for doc in results]
    
    async def _generate_sql(
        self,
        query: str,
        tables: List[str],
        schema: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate SQL query from natural language"""
        
        # Build schema context
        schema_context = self._build_schema_context(tables, schema)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL expert. Convert the natural language query to SQL.
            
            Database Schema:
            {schema}
            
            Guidelines:
            1. Use only the tables and columns provided in the schema
            2. Include appropriate JOINs when multiple tables are needed
            3. Use proper SQL syntax for the database type
            4. Add appropriate WHERE clauses for filtering
            5. Include GROUP BY when aggregating
            6. Add ORDER BY for sorting when relevant
            7. Use LIMIT for top N queries
            8. Handle date/time columns appropriately
            
            Examples:
            {examples}
            """),
            ("user", "Convert this to SQL: {query}")
        ])
        
        # Get relevant examples
        examples = await self._get_relevant_examples(query)
        
        # Generate SQL
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(
            schema=schema_context,
            examples=examples,
            query=query
        )
        
        # Extract SQL from response
        sql = self._extract_sql_from_response(result)
        
        return sql
    
    def _build_schema_context(
        self,
        tables: List[str],
        schema: Dict[str, Any]
    ) -> str:
        """Build schema context for prompt"""
        context_parts = []
        
        for table in tables:
            if table in schema.get("tables", {}):
                table_info = schema["tables"][table]
                context_parts.append(f"\nTable: {table}")
                
                if "description" in table_info:
                    context_parts.append(f"Description: {table_info['description']}")
                
                context_parts.append("Columns:")
                for col in table_info.get("columns", []):
                    col_desc = f"  - {col['name']} ({col['type']})"
                    if col.get("primary_key"):
                        col_desc += " PRIMARY KEY"
                    if col.get("foreign_key"):
                        col_desc += f" REFERENCES {col['foreign_key']}"
                    context_parts.append(col_desc)
        
        # Add relationships
        relationships = schema.get("relationships", [])
        relevant_relationships = [
            r for r in relationships
            if any(table in r["from"] or table in r["to"] for table in tables)
        ]
        
        if relevant_relationships:
            context_parts.append("\nRelationships:")
            for rel in relevant_relationships:
                context_parts.append(f"  - {rel['from']} -> {rel['to']} ({rel['type']})")
        
        return "\n".join(context_parts)
    
    async def _get_relevant_examples(self, query: str) -> str:
        """Get relevant SQL examples for few-shot learning"""
        examples = []
        
        # Common query patterns
        if "total" in query.lower() or "sum" in query.lower():
            examples.append({
                "nl": "What is the total sales amount?",
                "sql": "SELECT SUM(amount) as total_sales FROM sales;"
            })
        
        if "average" in query.lower() or "avg" in query.lower():
            examples.append({
                "nl": "What is the average order value?",
                "sql": "SELECT AVG(amount) as avg_order_value FROM sales;"
            })
        
        if "top" in query.lower() or "best" in query.lower():
            examples.append({
                "nl": "Show top 10 products by sales",
                "sql": """SELECT p.name, SUM(s.amount) as total_sales
                         FROM sales s
                         JOIN products p ON s.product_id = p.id
                         GROUP BY p.id, p.name
                         ORDER BY total_sales DESC
                         LIMIT 10;"""
            })
        
        if "group by" in query.lower() or "by" in query.lower():
            examples.append({
                "nl": "Show sales by region",
                "sql": """SELECT region, SUM(amount) as total_sales
                         FROM sales
                         GROUP BY region
                         ORDER BY total_sales DESC;"""
            })
        
        if "trend" in query.lower() or "over time" in query.lower():
            examples.append({
                "nl": "Show sales trend over time",
                "sql": """SELECT DATE_TRUNC('month', date) as month,
                                SUM(amount) as monthly_sales
                         FROM sales
                         GROUP BY month
                         ORDER BY month;"""
            })
        
        # Format examples
        if examples:
            formatted = []
            for ex in examples[:3]:  # Limit to 3 examples
                formatted.append(f"NL: {ex['nl']}\nSQL: {ex['sql']}")
            return "\n\n".join(formatted)
        
        return "No specific examples available"
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Look for SQL code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Look for SELECT statement
        select_pattern = r'(SELECT.*?;)'
        match = re.search(select_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Return cleaned response
        return response.strip()
    
    async def _validate_and_optimize_sql(
        self,
        sql: str,
        schema: Dict[str, Any]
    ) -> str:
        """Validate and optimize SQL query"""
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql)[0]
            
            # Format SQL
            formatted = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper'
            )
            
            # Basic validation
            if not self._is_valid_sql(formatted, schema):
                logger.warning(f"Invalid SQL generated: {formatted}")
                # Attempt to fix common issues
                formatted = self._fix_common_sql_issues(formatted, schema)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error validating SQL: {str(e)}")
            return sql
    
    def _is_valid_sql(self, sql: str, schema: Dict[str, Any]) -> bool:
        """Check if SQL is valid"""
        # Basic validation checks
        sql_upper = sql.upper()
        
        # Check for required keywords
        if "SELECT" not in sql_upper:
            return False
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            return False
        
        # Check table names exist
        tables = schema.get("tables", {})
        for table in tables.keys():
            if table.upper() in sql_upper:
                return True
        
        return False
    
    def _fix_common_sql_issues(self, sql: str, schema: Dict[str, Any]) -> str:
        """Fix common SQL issues"""
        # Add semicolon if missing
        if not sql.strip().endswith(';'):
            sql = sql.strip() + ';'
        
        # Fix table name case
        tables = schema.get("tables", {})
        for table in tables.keys():
            # Replace case-insensitive
            pattern = re.compile(re.escape(table), re.IGNORECASE)
            sql = pattern.sub(table, sql)
        
        return sql
    
    async def generate_drill_down_query(
        self,
        dimension: str,
        value: Any,
        level: int,
        data_source_id: str
    ) -> str:
        """
        Generate drill-down query for hierarchical data exploration
        
        Args:
            dimension: Dimension to drill down on
            value: Current value to drill into
            level: Current drill level
            data_source_id: Data source ID
            
        Returns:
            SQL query for drill-down
        """
        schema = await self._get_schema(data_source_id)
        
        # Define drill-down hierarchies
        hierarchies = {
            "time": ["year", "quarter", "month", "week", "day"],
            "geography": ["country", "region", "state", "city", "zip"],
            "product": ["category", "subcategory", "product", "sku"],
            "customer": ["segment", "account", "user"]
        }
        
        # Find appropriate hierarchy
        hierarchy = None
        for h_name, h_levels in hierarchies.items():
            if dimension.lower() in [l.lower() for l in h_levels]:
                hierarchy = h_levels
                current_index = h_levels.index(dimension.lower())
                break
        
        if not hierarchy or current_index >= len(hierarchy) - 1:
            # Can't drill down further
            return f"SELECT * FROM sales WHERE {dimension} = '{value}';"
        
        # Get next level in hierarchy
        next_level = hierarchy[current_index + 1]
        
        # Generate drill-down query
        query = f"""
        SELECT 
            {next_level},
            COUNT(*) as count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM sales
        WHERE {dimension} = '{value}'
        GROUP BY {next_level}
        ORDER BY total_amount DESC;
        """
        
        return query.strip()
    
    async def apply_filters_to_query(
        self,
        base_query: str,
        filters: Dict[str, Any],
        data_source_id: str
    ) -> str:
        """
        Apply filters to an existing query
        
        Args:
            base_query: Base SQL query
            filters: Filters to apply
            data_source_id: Data source ID
            
        Returns:
            Modified SQL query with filters
        """
        if not filters:
            return base_query
        
        # Parse the base query
        parsed = sqlparse.parse(base_query)[0]
        
        # Build WHERE clause
        where_conditions = []
        for column, filter_value in filters.items():
            if isinstance(filter_value, dict):
                # Handle complex filters
                if "min" in filter_value:
                    where_conditions.append(f"{column} >= {filter_value['min']}")
                if "max" in filter_value:
                    where_conditions.append(f"{column} <= {filter_value['max']}")
                if "in" in filter_value:
                    values = ", ".join([f"'{v}'" for v in filter_value["in"]])
                    where_conditions.append(f"{column} IN ({values})")
                if "like" in filter_value:
                    where_conditions.append(f"{column} LIKE '{filter_value['like']}'")
            elif isinstance(filter_value, list):
                # Handle list filters
                values = ", ".join([f"'{v}'" for v in filter_value])
                where_conditions.append(f"{column} IN ({values})")
            else:
                # Handle simple equality
                if isinstance(filter_value, str):
                    where_conditions.append(f"{column} = '{filter_value}'")
                else:
                    where_conditions.append(f"{column} = {filter_value}")
        
        # Combine conditions
        where_clause = " AND ".join(where_conditions)
        
        # Modify query
        if "WHERE" in base_query.upper():
            # Add to existing WHERE clause
            modified_query = base_query.replace(
                "WHERE",
                f"WHERE ({where_clause}) AND",
                1
            )
        else:
            # Add new WHERE clause
            # Find insertion point (before GROUP BY, ORDER BY, or semicolon)
            insert_point = len(base_query)
            for keyword in ["GROUP BY", "ORDER BY", ";"]:
                idx = base_query.upper().find(keyword)
                if idx != -1 and idx < insert_point:
                    insert_point = idx
            
            modified_query = (
                base_query[:insert_point].rstrip() +
                f" WHERE {where_clause} " +
                base_query[insert_point:]
            )
        
        return modified_query
    
    async def explain_query(self, sql: str) -> Dict[str, Any]:
        """
        Explain what a SQL query does in natural language
        
        Args:
            sql: SQL query to explain
            
        Returns:
            Explanation of the query
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL expert. Explain what this SQL query does in simple terms.
            
            Provide:
            1. A brief summary of what the query does
            2. What data it retrieves
            3. Any filters or conditions applied
            4. How the results are organized
            5. Any calculations or aggregations performed
            """),
            ("user", "Explain this SQL query:\n{sql}")
        ])
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        explanation = await chain.arun(sql=sql)
        
        # Parse the explanation
        parsed = sqlparse.parse(sql)[0]
        
        return {
            "summary": explanation,
            "query_type": self._get_query_type(sql),
            "tables_used": self._extract_tables(sql),
            "columns_selected": self._extract_columns(sql),
            "has_aggregation": "GROUP BY" in sql.upper(),
            "has_filtering": "WHERE" in sql.upper(),
            "has_sorting": "ORDER BY" in sql.upper(),
            "has_limit": "LIMIT" in sql.upper()
        }
    
    def _get_query_type(self, sql: str) -> str:
        """Determine the type of SQL query"""
        sql_upper = sql.upper()
        
        if "SELECT" in sql_upper:
            if "GROUP BY" in sql_upper:
                return "aggregation"
            elif "JOIN" in sql_upper:
                return "join"
            else:
                return "simple_select"
        elif "INSERT" in sql_upper:
            return "insert"
        elif "UPDATE" in sql_upper:
            return "update"
        elif "DELETE" in sql_upper:
            return "delete"
        else:
            return "unknown"
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        tables = []
        
        # Simple extraction using regex
        from_pattern = r'FROM\s+(\w+)'
        join_pattern = r'JOIN\s+(\w+)'
        
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        
        tables.extend(from_matches)
        tables.extend(join_matches)
        
        return list(set(tables))
    
    def _extract_columns(self, sql: str) -> List[str]:
        """Extract column names from SELECT clause"""
        columns = []
        
        # Extract SELECT clause
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            select_clause = match.group(1)
            
            # Handle SELECT *
            if select_clause.strip() == "*":
                return ["*"]
            
            # Split by comma and clean
            parts = select_clause.split(",")
            for part in parts:
                # Remove aliases and functions
                clean_part = part.strip()
                
                # Extract column name (simplified)
                if " as " in clean_part.lower():
                    clean_part = clean_part.split(" as ")[0].strip()
                
                # Remove function calls
                if "(" in clean_part:
                    # Extract column from function
                    col_pattern = r'\((\w+)\)'
                    col_match = re.search(col_pattern, clean_part)
                    if col_match:
                        columns.append(col_match.group(1))
                else:
                    # Remove table prefixes
                    if "." in clean_part:
                        clean_part = clean_part.split(".")[-1]
                    columns.append(clean_part)
        
        return columns
    
    def _load_query_examples(self) -> List[Dict[str, str]]:
        """Load example queries for few-shot learning"""
        return [
            {
                "nl": "Show total sales by month",
                "sql": """SELECT 
                    DATE_TRUNC('month', date) as month,
                    SUM(amount) as total_sales
                FROM sales
                GROUP BY month
                ORDER BY month;"""
            },
            {
                "nl": "Find top 5 customers by revenue",
                "sql": """SELECT 
                    c.name,
                    SUM(s.amount) as total_revenue
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
                LIMIT 5;"""
            },
            {
                "nl": "Compare sales between regions",
                "sql": """SELECT 
                    region,
                    COUNT(*) as num_sales,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM sales
                GROUP BY region
                ORDER BY total_amount DESC;"""
            }
        ]


class StructuredDataOptimizer:
    """
    Optimizer for structured data queries
    """
    
    def __init__(self):
        """Initialize query optimizer"""
        self.optimization_rules = self._load_optimization_rules()
        
    async def optimize_query(self, sql: str, schema: Dict[str, Any]) -> str:
        """
        Optimize SQL query for better performance
        
        Args:
            sql: SQL query to optimize
            schema: Database schema
            
        Returns:
            Optimized SQL query
        """
        optimized = sql
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            optimized = await self._apply_rule(optimized, rule, schema)
        
        # Add appropriate indexes hints
        optimized = await self._add_index_hints(optimized, schema)
        
        return optimized
    
    async def _apply_rule(
        self,
        sql: str,
        rule: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> str:
        """Apply optimization rule to query"""
        # Implement specific optimization rules
        return sql
    
    async def _add_index_hints(self, sql: str, schema: Dict[str, Any]) -> str:
        """Add index hints for better performance"""
        # Analyze query and suggest indexes
        return sql
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Load query optimization rules"""
        return [
            {
                "name": "push_down_predicates",
                "description": "Push WHERE conditions closer to data source"
            },
            {
                "name": "eliminate_subqueries",
                "description": "Convert subqueries to JOINs when possible"
            },
            {
                "name": "optimize_joins",
                "description": "Reorder JOINs for better performance"
            }
        ]
