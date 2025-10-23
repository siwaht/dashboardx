"""
Analytics API Endpoints

Provides REST API endpoints for analytics operations including:
- Query execution
- Data source management
- Visualization generation
- Insight retrieval
- Export functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import pandas as pd
import io
import asyncio
from pydantic import BaseModel, Field

# Internal imports
from app.analytics.engine import AnalyticsEngine, AnalysisType, QueryType
from app.analytics.connectors import DataConnectorFactory, DataSourceType
from app.analytics.processors import DataProcessor
from app.analytics.ml_models import MLEngine, ModelConfig
from app.analytics.agents import AnalyticsAgentOrchestrator
from app.security.auth import get_current_user, AuthenticatedUser

# Type alias for compatibility
User = AuthenticatedUser

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Initialize components
analytics_engine = AnalyticsEngine()
connector_factory = DataConnectorFactory()
data_processor = DataProcessor()
ml_engine = MLEngine()
agent_orchestrator = AnalyticsAgentOrchestrator()


# Pydantic models for request/response

class QueryRequest(BaseModel):
    """Analytics query request model"""
    query: str = Field(..., description="Natural language or SQL query")
    query_type: str = Field(default="natural_language", description="Type of query")
    data_source_id: Optional[str] = Field(None, description="Specific data source to use")
    analysis_type: str = Field(default="exploratory", description="Type of analysis")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    streaming: bool = Field(default=False, description="Stream results")


class DataSourceConfig(BaseModel):
    """Data source configuration model"""
    name: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data source type")
    config: Dict[str, Any] = Field(..., description="Connection configuration")
    description: Optional[str] = Field(None, description="Description")


class VisualizationRequest(BaseModel):
    """Visualization request model"""
    data: Union[List[Dict], Dict[str, Any]] = Field(..., description="Data to visualize")
    chart_type: Optional[str] = Field(None, description="Specific chart type")
    config: Optional[Dict[str, Any]] = Field(None, description="Chart configuration")


class ExportRequest(BaseModel):
    """Export request model"""
    data: Union[List[Dict], Dict[str, Any]] = Field(..., description="Data to export")
    format: str = Field("csv", description="Export format (csv, excel, json)")
    filename: Optional[str] = Field(None, description="Output filename")


class MLTrainingRequest(BaseModel):
    """ML model training request"""
    data: Union[List[Dict], Dict[str, Any]] = Field(..., description="Training data")
    model_config: Dict[str, Any] = Field(..., description="Model configuration")
    target_column: str = Field(..., description="Target variable column")


class PredictionRequest(BaseModel):
    """Prediction request model"""
    data: Union[List[Dict], Dict[str, Any]] = Field(..., description="Data for prediction")
    model_id: Optional[str] = Field(None, description="Specific model to use")
    include_confidence: bool = Field(True, description="Include confidence scores")


# Analytics Query Endpoints

@router.post("/query")
async def execute_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute an analytics query
    
    Supports natural language queries, SQL, and various analysis types.
    """
    try:
        # Convert string enums
        query_type = QueryType[request.query_type.upper()]
        analysis_type = AnalysisType[request.analysis_type.upper()]
        
        # Execute query
        result = await analytics_engine.analyze(
            query=request.query,
            query_type=query_type,
            data_source_id=request.data_source_id,
            analysis_type=analysis_type,
            context=request.context,
            streaming=request.streaming
        )
        
        # Log query for audit
        await _log_query(current_user.id, request.query, result.get("metadata"))
        
        return {
            "success": True,
            "result": result,
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/stream")
async def stream_query_results(
    query: str = Query(..., description="Query to execute"),
    data_source_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Stream real-time query results
    
    Returns Server-Sent Events (SSE) stream for real-time data.
    """
    async def generate():
        try:
            # Execute streaming query
            result = await analytics_engine.analyze(
                query=query,
                query_type=QueryType.NATURAL_LANGUAGE,
                data_source_id=data_source_id,
                analysis_type=AnalysisType.REAL_TIME,
                streaming=True
            )
            
            # Stream results
            if result.get("type") == "streaming":
                async for chunk in result["stream"]:
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.1)  # Rate limiting
            else:
                yield f"data: {json.dumps(result)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/query/explain")
async def explain_query(
    query: str = Body(..., description="Query to explain"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Explain what a query does
    
    Provides natural language explanation of SQL queries.
    """
    try:
        from app.rag.structured_rag import StructuredDataRAG
        
        rag = StructuredDataRAG()
        explanation = await rag.explain_query(query)
        
        return {
            "success": True,
            "query": query,
            "explanation": explanation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data Source Management Endpoints

@router.get("/data-sources")
async def list_data_sources(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available data sources
    """
    try:
        sources = await connector_factory.list_data_sources()
        
        return {
            "success": True,
            "data_sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-sources")
async def create_data_source(
    config: DataSourceConfig,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new data source connection
    """
    try:
        # Validate connection
        source_type = DataSourceType[config.type.upper()]
        connector = await connector_factory.create_connector(source_type, config.config)
        
        # Test connection
        if not await connector.test_connection():
            raise HTTPException(status_code=400, detail="Connection test failed")
        
        # Save configuration (would save to database in production)
        data_source_id = f"{config.type}_{datetime.utcnow().timestamp()}"
        
        return {
            "success": True,
            "data_source_id": data_source_id,
            "message": "Data source created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-sources/{source_id}/schema")
async def get_data_source_schema(
    source_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get schema information for a data source
    """
    try:
        connector = await connector_factory.get_connector(source_id)
        schema = await connector.get_schema()
        
        return {
            "success": True,
            "data_source_id": source_id,
            "schema": schema
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-sources/{source_id}/test")
async def test_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test data source connection
    """
    try:
        connector = await connector_factory.get_connector(source_id)
        is_connected = await connector.test_connection()
        
        return {
            "success": True,
            "data_source_id": source_id,
            "connected": is_connected,
            "message": "Connection successful" if is_connected else "Connection failed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data Processing Endpoints

@router.post("/process/explore")
async def explore_data(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Explore and profile data
    """
    try:
        exploration = await data_processor.explore_data(data)
        
        return {
            "success": True,
            "exploration": exploration
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/clean")
async def clean_data(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    options: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clean and preprocess data
    """
    try:
        cleaned_data = await data_processor.clean_data(data, options)
        
        return {
            "success": True,
            "data": cleaned_data.to_dict('records'),
            "rows_before": len(data) if isinstance(data, list) else len(data.get("data", [])),
            "rows_after": len(cleaned_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/aggregate")
async def aggregate_data(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    group_by: List[str] = Body(...),
    aggregations: Dict[str, str] = Body(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Aggregate data with grouping
    """
    try:
        aggregated = await data_processor.aggregate_data(data, group_by, aggregations)
        
        return {
            "success": True,
            "data": aggregated.to_dict('records'),
            "group_by": group_by,
            "aggregations": aggregations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Visualization Endpoints

@router.post("/visualize")
async def create_visualization(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate visualization recommendations and configurations
    """
    try:
        # Get visualization recommendations
        from app.analytics.agents import VisualizationAgent
        
        viz_agent = VisualizationAgent()
        recommendations = await viz_agent.analyze(request.data, request.config)
        
        # Filter by requested chart type if specified
        if request.chart_type:
            filtered = [
                r for r in recommendations["recommendations"]
                if r["type"] == request.chart_type
            ]
            recommendations["recommendations"] = filtered
        
        return {
            "success": True,
            "visualizations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualize/types")
async def get_visualization_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available visualization types
    """
    return {
        "success": True,
        "types": [
            {"id": "line", "name": "Line Chart", "category": "time_series"},
            {"id": "bar", "name": "Bar Chart", "category": "categorical"},
            {"id": "scatter", "name": "Scatter Plot", "category": "correlation"},
            {"id": "pie", "name": "Pie Chart", "category": "proportion"},
            {"id": "heatmap", "name": "Heatmap", "category": "matrix"},
            {"id": "histogram", "name": "Histogram", "category": "distribution"},
            {"id": "boxplot", "name": "Box Plot", "category": "statistical"},
            {"id": "area", "name": "Area Chart", "category": "time_series"},
            {"id": "treemap", "name": "Treemap", "category": "hierarchical"},
            {"id": "sankey", "name": "Sankey Diagram", "category": "flow"},
            {"id": "map", "name": "Geographic Map", "category": "geographic"},
            {"id": "gauge", "name": "Gauge", "category": "metric"},
            {"id": "funnel", "name": "Funnel Chart", "category": "conversion"},
            {"id": "radar", "name": "Radar Chart", "category": "multivariate"},
            {"id": "waterfall", "name": "Waterfall Chart", "category": "cumulative"}
        ]
    }


# Insights Endpoints

@router.post("/insights")
async def generate_insights(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    analysis_type: str = Body(default="exploratory"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate insights from data
    """
    try:
        # Use agent orchestrator to generate insights
        analysis_type_enum = AnalysisType[analysis_type.upper()]
        insights = await agent_orchestrator.generate_insights(
            {"data": data},
            analysis_type_enum
        )
        
        return {
            "success": True,
            "insights": insights,
            "count": len(insights)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/recent")
async def get_recent_insights(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recently generated insights
    """
    try:
        # This would fetch from database in production
        recent_insights = []  # Placeholder
        
        return {
            "success": True,
            "insights": recent_insights,
            "count": len(recent_insights)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Machine Learning Endpoints

@router.post("/ml/train")
async def train_model(
    request: MLTrainingRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Train a machine learning model
    """
    try:
        # Prepare data
        X, y = await ml_engine.prepare_data(request.data)
        
        # Create model config
        config = ModelConfig(
            model_type=request.model_config.get("model_type", "regression"),
            algorithm=request.model_config.get("algorithm", "random_forest"),
            hyperparameters=request.model_config.get("hyperparameters", {}),
            features=list(X.columns),
            target=request.target_column,
            auto_tune=request.model_config.get("auto_tune", True)
        )
        
        # Train model
        result = await ml_engine.train_model(X, y, config)
        
        return {
            "success": True,
            "model": result,
            "message": "Model trained successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/predict")
async def make_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Make predictions using trained model
    """
    try:
        context = {"model_id": request.model_id} if request.model_id else None
        predictions = await ml_engine.predict(request.data, context)
        
        # Add confidence scores if requested
        if request.include_confidence:
            confidence = await ml_engine.calculate_confidence(predictions)
            predictions["confidence_scores"] = confidence
        
        return {
            "success": True,
            "predictions": predictions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/forecast")
async def forecast_time_series(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    target_column: str = Body(...),
    periods: int = Body(default=30),
    method: str = Body(default="auto"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform time series forecasting
    """
    try:
        df = pd.DataFrame(data if isinstance(data, list) else data.get("data", []))
        forecast = await ml_engine.forecast_time_series(df, target_column, periods, method)
        
        return {
            "success": True,
            "forecast": forecast
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/anomalies")
async def detect_anomalies(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    method: str = Body(default="isolation_forest"),
    contamination: float = Body(default=0.1, ge=0.01, le=0.5),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Detect anomalies in data
    """
    try:
        df = pd.DataFrame(data if isinstance(data, list) else data.get("data", []))
        anomalies = await ml_engine.detect_anomalies(df, method, contamination)
        
        return {
            "success": True,
            "anomalies": anomalies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/models")
async def list_models(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available ML models
    """
    try:
        models = await ml_engine.get_model_info()
        
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints

@router.post("/export")
async def export_data(
    request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Export data in various formats
    """
    try:
        df = pd.DataFrame(request.data if isinstance(request.data, list) else request.data.get("data", []))
        
        # Generate filename
        filename = request.filename or f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if request.format == "csv":
            # Export as CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.csv"
                }
            )
            
        elif request.format == "excel":
            # Export as Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.xlsx"
                }
            )
            
        elif request.format == "json":
            # Export as JSON
            json_data = df.to_json(orient='records', date_format='iso')
            
            return StreamingResponse(
                io.BytesIO(json_data.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.json"
                }
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/report")
async def generate_report(
    data: Union[List[Dict], Dict[str, Any]] = Body(...),
    insights: List[Dict[str, Any]] = Body(...),
    visualizations: List[Dict[str, Any]] = Body(...),
    format: str = Body(default="pdf"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive analytics report
    """
    try:
        # This would use a report generation library in production
        # For now, return a simple JSON report
        report = {
            "title": "Analytics Report",
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user.email,
            "summary": {
                "data_points": len(data) if isinstance(data, list) else len(data.get("data", [])),
                "insights_count": len(insights),
                "visualizations_count": len(visualizations)
            },
            "data": data,
            "insights": insights,
            "visualizations": visualizations
        }
        
        if format == "json":
            return StreamingResponse(
                io.BytesIO(json.dumps(report, indent=2).encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        else:
            # PDF generation would be implemented here
            raise HTTPException(status_code=501, detail="PDF export not yet implemented")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# File Upload Endpoints

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload data file for analysis
    """
    try:
        # Read file content
        content = await file.read()
        
        # Process based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Profile the data
        profile = await data_processor.profile_data(df)
        
        return {
            "success": True,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "profile": profile,
            "data": df.head(100).to_dict('records')  # Return first 100 rows
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def _log_query(user_id: str, query: str, metadata: Dict[str, Any]):
    """Log query for audit trail"""
    # This would save to database in production
    pass


# WebSocket endpoint for real-time collaboration
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time collaboration
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "query":
                # Execute query and broadcast results
                result = await analytics_engine.analyze(
                    query=data.get("query"),
                    query_type=QueryType.NATURAL_LANGUAGE,
                    analysis_type=AnalysisType.EXPLORATORY
                )
                await manager.broadcast({
                    "type": "query_result",
                    "result": result
                })
            
            elif data.get("type") == "cursor":
                # Broadcast cursor position for collaboration
                await manager.broadcast({
                    "type": "cursor_update",
                    "user": data.get("user"),
                    "position": data.get("position")
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
