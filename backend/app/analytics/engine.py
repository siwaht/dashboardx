"""
Core Analytics Engine

Orchestrates all analytics operations including:
- Query processing
- Data analysis
- Insight generation
- Visualization recommendations
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np
from enum import Enum

from app.analytics.connectors import DataConnectorFactory
from app.analytics.processors import DataProcessor, StreamProcessor
from app.analytics.ml_models import MLEngine
from app.analytics.agents import AnalyticsAgentOrchestrator
from app.rag.structured_rag import StructuredDataRAG
from app.rag.statistical_rag import StatisticalRAG
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis supported"""
    EXPLORATORY = "exploratory"
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"
    REAL_TIME = "real_time"


class QueryType(Enum):
    """Types of queries supported"""
    NATURAL_LANGUAGE = "natural_language"
    SQL = "sql"
    VISUAL = "visual"
    STATISTICAL = "statistical"
    ML_PREDICTION = "ml_prediction"


class AnalyticsEngine:
    """
    Main analytics engine that orchestrates all analytics operations
    """
    
    def __init__(self):
        """Initialize the analytics engine with all components"""
        self.connector_factory = DataConnectorFactory()
        self.data_processor = DataProcessor()
        self.stream_processor = StreamProcessor()
        self.ml_engine = MLEngine()
        self.agent_orchestrator = AnalyticsAgentOrchestrator()
        self.structured_rag = StructuredDataRAG()
        self.statistical_rag = StatisticalRAG()
        
        # Cache for frequently accessed data with TTL and max size to prevent memory leaks
        self._cache_Now I need to update the cache initialization to use TTLCache:

<edit_file>
<path>backend/app/analytics/engine.py</path>
<content>
<<<<<<< SEARCH
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour default TTL
=======
        # Cache for frequently accessed data with TTL and max size
        self._cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour TTL, max 100 items
        
        logger.info("Analytics Engine initialized successfully")
    
    async def analyze(
        self,
        query: str,
        query_type: QueryType,
        data_source_id: Optional[str] = None,
        analysis_type: AnalysisType = AnalysisType.EXPLORATORY,
        context: Optional[Dict[str, Any]] = None,
        streaming: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point for all analytics operations
        
        Args:
            query: The analysis query (natural language, SQL, etc.)
            query_type: Type of query being executed
            data_source_id: Optional specific data source to use
            analysis_type: Type of analysis to perform
            context: Additional context for the analysis
            streaming: Whether to stream results
            
        Returns:
            Analysis results including data, insights, and visualizations
        """
        try:
            start_time = datetime.utcnow()
            
            # Log the analysis request
            logger.info(f"Starting analysis: type={analysis_type.value}, query_type={query_type.value}")
            
            # Check cache first
            cache_key = self._generate_cache_key(query, data_source_id, analysis_type)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if self._is_cache_valid(cached_result):
                    logger.info("Returning cached result")
                    return cached_result['data']
            
            # Route to appropriate handler based on analysis type
            if analysis_type == AnalysisType.REAL_TIME:
                result = await self._handle_real_time_analysis(query, data_source_id, context, streaming)
            elif analysis_type == AnalysisType.PREDICTIVE:
                result = await self._handle_predictive_analysis(query, data_source_id, context)
            elif analysis_type == AnalysisType.PRESCRIPTIVE:
                result = await self._handle_prescriptive_analysis(query, data_source_id, context)
            else:
                result = await self._handle_standard_analysis(
                    query, query_type, data_source_id, analysis_type, context
                )
            
            # Generate insights using agents
            insights = await self.agent_orchestrator.generate_insights(result, analysis_type)
            
            # Add visualization recommendations
            visualizations = await self._recommend_visualizations(result, analysis_type)
            
            # Prepare final response
            response = {
                "query": query,
                "analysis_type": analysis_type.value,
                "data": result.get("data"),
                "insights": insights,
                "visualizations": visualizations,
                "statistics": result.get("statistics"),
                "metadata": {
                    "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                    "data_source": data_source_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "row_count": len(result.get("data", [])) if isinstance(result.get("data"), list) else None
                }
            }
            
            # Cache the result
            self._cache[cache_key] = {
                "data": response,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Analysis completed in {response['metadata']['execution_time']:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise
    
    async def _handle_standard_analysis(
        self,
        query: str,
        query_type: QueryType,
        data_source_id: Optional[str],
        analysis_type: AnalysisType,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle standard analysis types (exploratory, descriptive, diagnostic)"""
        
        # Get data from source
        data = await self._fetch_data(query, query_type, data_source_id, context)
        
        # Validate data is not empty
        if not data or (isinstance(data, (list, dict)) and len(data) == 0):
            logger.warning("No data available for analysis")
            return {
                "data": [],
                "error": "No data available for analysis",
                "statistics": None
            }
        
        # Process data based on analysis type
        try:
            if analysis_type == AnalysisType.EXPLORATORY:
                processed_data = await self.data_processor.explore_data(data)
            elif analysis_type == AnalysisType.DESCRIPTIVE:
                processed_data = await self.data_processor.describe_data(data)
            elif analysis_type == AnalysisType.DIAGNOSTIC:
                processed_data = await self.data_processor.diagnose_data(data, context)
            else:
                processed_data = data
            
            # Apply statistical analysis if needed
            if query_type == QueryType.STATISTICAL and processed_data:
                # Ensure we have valid data before statistical analysis
                if isinstance(processed_data, dict) and processed_data.get("data"):
                    statistics = await self.statistical_rag.analyze(query, processed_data)
                    processed_data["statistics"] = statistics
                else:
                    processed_data["statistics"] = {"error": "Insufficient data for statistical analysis"}
            
            return processed_data
            
        except ZeroDivisionError as e:
            logger.error(f"Division by zero error during analysis: {str(e)}")
            return {
                "data": data,
                "error": "Mathematical error: division by zero encountered",
                "statistics": None
            }
        except Exception as e:
            logger.error(f"Error during standard analysis: {str(e)}")
            return {
                "data": data,
                "error": f"Analysis error: {str(e)}",
                "statistics": None
            }
    
    async def _handle_predictive_analysis(
        self,
        query: str,
        data_source_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle predictive analytics using ML models"""
        
        # Fetch historical data
        data = await self._fetch_data(query, QueryType.NATURAL_LANGUAGE, data_source_id, context)
        
        # Prepare data for ML
        prepared_data = await self.ml_engine.prepare_data(data)
        
        # Generate predictions
        predictions = await self.ml_engine.predict(prepared_data, context)
        
        # Add confidence scores and explanations
        predictions["confidence_scores"] = await self.ml_engine.calculate_confidence(predictions)
        predictions["explanations"] = await self.ml_engine.explain_predictions(predictions)
        
        return {
            "data": data,
            "predictions": predictions,
            "model_info": await self.ml_engine.get_model_info()
        }
    
    async def _handle_prescriptive_analysis(
        self,
        query: str,
        data_source_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle prescriptive analytics for recommendations and optimization"""
        
        # Get current state data
        current_data = await self._fetch_data(query, QueryType.NATURAL_LANGUAGE, data_source_id, context)
        
        # Run predictive analysis first
        predictions = await self._handle_predictive_analysis(query, data_source_id, context)
        
        # Generate recommendations
        recommendations = await self.agent_orchestrator.generate_recommendations(
            current_data,
            predictions,
            context
        )
        
        # Optimize based on constraints
        optimizations = await self.ml_engine.optimize(current_data, context.get("constraints", {}))
        
        return {
            "data": current_data,
            "predictions": predictions,
            "recommendations": recommendations,
            "optimizations": optimizations
        }
    
    async def _handle_real_time_analysis(
        self,
        query: str,
        data_source_id: Optional[str],
        context: Optional[Dict[str, Any]],
        streaming: bool
    ) -> Dict[str, Any]:
        """Handle real-time streaming analytics"""
        
        # Set up stream connection
        stream = await self.stream_processor.connect(data_source_id, context)
        
        if streaming:
            # Return async generator for streaming results
            return {
                "stream": self._stream_results(stream, query, context),
                "type": "streaming"
            }
        else:
            # Process batch of recent data
            recent_data = await self.stream_processor.get_recent_batch(stream, limit=1000)
            processed = await self.data_processor.process_streaming_data(recent_data)
            
            return {
                "data": processed,
                "type": "batch",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _stream_results(self, stream, query: str, context: Dict[str, Any]):
        """Async generator for streaming results"""
        async for data_batch in stream:
            processed = await self.data_processor.process_streaming_data(data_batch)
            insights = await self.agent_orchestrator.generate_real_time_insights(processed)
            
            yield {
                "data": processed,
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _fetch_data(
        self,
        query: str,
        query_type: QueryType,
        data_source_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Fetch data from the appropriate source"""
        
        if query_type == QueryType.SQL:
            # Direct SQL execution
            connector = await self.connector_factory.get_connector(data_source_id)
            return await connector.execute_query(query)
        
        elif query_type == QueryType.NATURAL_LANGUAGE:
            # Convert natural language to SQL using RAG
            sql_query = await self.structured_rag.natural_language_to_sql(query, data_source_id)
            connector = await self.connector_factory.get_connector(data_source_id)
            return await connector.execute_query(sql_query)
        
        elif query_type == QueryType.VISUAL:
            # Handle visual query (e.g., from a chart interaction)
            return await self._process_visual_query(query, data_source_id, context)
        
        else:
            # Default to natural language processing
            return await self._fetch_data(query, QueryType.NATURAL_LANGUAGE, data_source_id, context)
    
    async def _recommend_visualizations(
        self,
        data: Dict[str, Any],
        analysis_type: AnalysisType
    ) -> List[Dict[str, Any]]:
        """Recommend appropriate visualizations based on data and analysis type"""
        
        recommendations = []
        
        # Analyze data characteristics
        data_profile = await self.data_processor.profile_data(data.get("data", {}))
        
        # Get recommendations from visualization agent
        viz_recommendations = await self.agent_orchestrator.recommend_visualizations(
            data_profile,
            analysis_type
        )
        
        # Add specific chart configurations
        for rec in viz_recommendations:
            chart_config = self._generate_chart_config(rec, data_profile)
            recommendations.append(chart_config)
        
        return recommendations
    
    def _generate_chart_config(
        self,
        recommendation: Dict[str, Any],
        data_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate specific chart configuration based on recommendation"""
        
        chart_type = recommendation.get("type", "line")
        
        config = {
            "type": chart_type,
            "title": recommendation.get("title", ""),
            "description": recommendation.get("description", ""),
            "priority": recommendation.get("priority", 0),
            "config": {}
        }
        
        # Add type-specific configurations
        if chart_type == "line":
            config["config"] = {
                "x_axis": data_profile.get("time_column"),
                "y_axis": data_profile.get("numeric_columns", [])[0] if data_profile.get("numeric_columns") else None,
                "show_trend": True,
                "show_forecast": recommendation.get("show_forecast", False)
            }
        elif chart_type == "bar":
            config["config"] = {
                "x_axis": data_profile.get("categorical_columns", [])[0] if data_profile.get("categorical_columns") else None,
                "y_axis": data_profile.get("numeric_columns", [])[0] if data_profile.get("numeric_columns") else None,
                "orientation": "vertical",
                "show_values": True
            }
        elif chart_type == "scatter":
            numeric_cols = data_profile.get("numeric_columns", [])
            config["config"] = {
                "x_axis": numeric_cols[0] if len(numeric_cols) > 0 else None,
                "y_axis": numeric_cols[1] if len(numeric_cols) > 1 else None,
                "size": numeric_cols[2] if len(numeric_cols) > 2 else None,
                "color": data_profile.get("categorical_columns", [])[0] if data_profile.get("categorical_columns") else None,
                "show_regression": True
            }
        elif chart_type == "heatmap":
            config["config"] = {
                "x_axis": data_profile.get("categorical_columns", [])[0] if data_profile.get("categorical_columns") else None,
                "y_axis": data_profile.get("categorical_columns", [])[1] if len(data_profile.get("categorical_columns", [])) > 1 else None,
                "value": data_profile.get("numeric_columns", [])[0] if data_profile.get("numeric_columns") else None,
                "color_scale": "viridis"
            }
        
        return config
    
    async def _process_visual_query(
        self,
        query: str,
        data_source_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Process visual queries (e.g., chart interactions)"""
        
        # Parse visual query context
        visual_context = context.get("visual_context", {})
        
        # Generate appropriate data query based on visual interaction
        if visual_context.get("action") == "drill_down":
            return await self._handle_drill_down(visual_context, data_source_id)
        elif visual_context.get("action") == "filter":
            return await self._handle_visual_filter(visual_context, data_source_id)
        else:
            # Default to standard query
            return await self._fetch_data(query, QueryType.NATURAL_LANGUAGE, data_source_id, context)
    
    async def _handle_drill_down(
        self,
        visual_context: Dict[str, Any],
        data_source_id: Optional[str]
    ) -> Any:
        """Handle drill-down operations from visualizations"""
        
        # Get the drill-down parameters
        dimension = visual_context.get("dimension")
        value = visual_context.get("value")
        current_level = visual_context.get("level", 0)
        
        # Generate drill-down query
        drill_query = await self.structured_rag.generate_drill_down_query(
            dimension,
            value,
            current_level,
            data_source_id
        )
        
        # Execute query
        connector = await self.connector_factory.get_connector(data_source_id)
        return await connector.execute_query(drill_query)
    
    async def _handle_visual_filter(
        self,
        visual_context: Dict[str, Any],
        data_source_id: Optional[str]
    ) -> Any:
        """Handle filter operations from visualizations"""
        
        filters = visual_context.get("filters", {})
        base_query = visual_context.get("base_query", "")
        
        # Apply filters to query
        filtered_query = await self.structured_rag.apply_filters_to_query(
            base_query,
            filters,
            data_source_id
        )
        
        # Execute filtered query
        connector = await self.connector_factory.get_connector(data_source_id)
        return await connector.execute_query(filtered_query)
    
    def _generate_cache_key(
        self,
        query: str,
        data_source_id: Optional[str],
        analysis_type: AnalysisType
    ) -> str:
        """Generate cache key for results"""
        import hashlib
        
        key_parts = [
            query,
            data_source_id or "default",
            analysis_type.value
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is still valid"""
        if not cached_item:
            return False
        
        cached_time = cached_item.get("timestamp")
        if not cached_time:
            return False
        
        age = (datetime.utcnow() - cached_time).total_seconds()
        return age < self._cache_ttl
    
    async def clear_cache(self):
        """Clear the analytics cache"""
        self._cache.clear()
        logger.info("Analytics cache cleared")
    
    async def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get list of available data sources"""
        return await self.connector_factory.list_data_sources()
    
    async def test_connection(self, data_source_id: str) -> bool:
        """Test connection to a data source"""
        try:
            connector = await self.connector_factory.get_connector(data_source_id)
            return await connector.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
