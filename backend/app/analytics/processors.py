"""
Data Processing Module

Handles data transformation, cleaning, and processing for analytics.
Includes both batch and stream processing capabilities.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import json

# Statistical libraries
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles batch data processing operations
    """
    
    def __init__(self):
        """Initialize data processor"""
        self.scalers = {}
        self.imputers = {}
        logger.info("DataProcessor initialized")
    
    async def explore_data(self, data: Any) -> Dict[str, Any]:
        """
        Perform exploratory data analysis
        
        Args:
            data: Input data (DataFrame, list of dicts, etc.)
            
        Returns:
            Exploration results including statistics, patterns, and anomalies
        """
        df = self._to_dataframe(data)
        
        exploration = {
            "basic_info": await self._get_basic_info(df),
            "statistics": await self._get_statistics(df),
            "data_quality": await self._assess_data_quality(df),
            "patterns": await self._detect_patterns(df),
            "anomalies": await self._detect_anomalies(df),
            "correlations": await self._calculate_correlations(df),
            "distributions": await self._analyze_distributions(df),
            "data": df.to_dict('records')
        }
        
        return exploration
    
    async def describe_data(self, data: Any) -> Dict[str, Any]:
        """
        Generate descriptive statistics for the data
        
        Args:
            data: Input data
            
        Returns:
            Descriptive statistics and summaries
        """
        df = self._to_dataframe(data)
        
        description = {
            "summary_statistics": df.describe(include='all').to_dict(),
            "data_types": df.dtypes.to_dict(),
            "unique_values": {col: df[col].nunique() for col in df.columns},
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage": df.memory_usage(deep=True).to_dict(),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "data": df.to_dict('records')
        }
        
        # Add categorical summaries
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            description["categorical_summaries"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts().head(10)
                description["categorical_summaries"][col] = value_counts.to_dict()
        
        # Add temporal summaries if date columns exist
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            description["temporal_summaries"] = {}
            for col in date_cols:
                description["temporal_summaries"][col] = {
                    "min": str(df[col].min()),
                    "max": str(df[col].max()),
                    "range_days": (df[col].max() - df[col].min()).days
                }
        
        return description
    
    async def diagnose_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform diagnostic analysis to understand causes and relationships
        
        Args:
            data: Input data
            context: Additional context for diagnosis
            
        Returns:
            Diagnostic insights and root cause analysis
        """
        df = self._to_dataframe(data)
        context = context or {}
        
        diagnosis = {
            "root_causes": await self._identify_root_causes(df, context),
            "impact_analysis": await self._analyze_impact(df, context),
            "trend_analysis": await self._analyze_trends(df),
            "segmentation": await self._perform_segmentation(df),
            "hypothesis_tests": await self._run_hypothesis_tests(df, context),
            "data": df.to_dict('records')
        }
        
        return diagnosis
    
    async def process_streaming_data(self, data_batch: List[Dict]) -> Dict[str, Any]:
        """
        Process streaming data in batches
        
        Args:
            data_batch: Batch of streaming data
            
        Returns:
            Processed data with real-time statistics
        """
        if not data_batch:
            return {"data": [], "statistics": {}}
        
        df = pd.DataFrame(data_batch)
        
        # Calculate streaming statistics
        statistics = {
            "batch_size": len(df),
            "timestamp": datetime.utcnow().isoformat(),
            "numeric_stats": {},
            "categorical_stats": {}
        }
        
        # Process numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            statistics["numeric_stats"][col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "median": float(df[col].median())
            }
        
        # Process categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            top_values = df[col].value_counts().head(5)
            statistics["categorical_stats"][col] = {
                "unique_count": df[col].nunique(),
                "top_values": top_values.to_dict()
            }
        
        # Detect anomalies in streaming data
        anomalies = await self._detect_streaming_anomalies(df)
        
        return {
            "data": df.to_dict('records'),
            "statistics": statistics,
            "anomalies": anomalies
        }
    
    async def profile_data(self, data: Any) -> Dict[str, Any]:
        """
        Create a comprehensive profile of the data
        
        Args:
            data: Input data
            
        Returns:
            Data profile with column types, distributions, etc.
        """
        df = self._to_dataframe(data)
        
        profile = {
            "columns": {},
            "relationships": {},
            "quality_score": 0,
            "recommendations": []
        }
        
        # Profile each column
        for col in df.columns:
            col_profile = {
                "name": col,
                "type": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "memory_usage": int(df[col].memory_usage())
            }
            
            # Add type-specific profiling
            if pd.api.types.is_numeric_dtype(df[col]):
                col_profile.update({
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "quartiles": {
                        "25%": float(df[col].quantile(0.25)),
                        "50%": float(df[col].quantile(0.50)),
                        "75%": float(df[col].quantile(0.75))
                    },
                    "skewness": float(df[col].skew()),
                    "kurtosis": float(df[col].kurtosis())
                })
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_profile.update({
                    "min_date": str(df[col].min()),
                    "max_date": str(df[col].max()),
                    "date_range": str(df[col].max() - df[col].min())
                })
            elif pd.api.types.is_object_dtype(df[col]):
                top_values = df[col].value_counts().head(10)
                col_profile.update({
                    "top_values": top_values.to_dict(),
                    "avg_length": float(df[col].astype(str).str.len().mean())
                })
            
            profile["columns"][col] = col_profile
        
        # Identify column types for visualization
        profile["numeric_columns"] = list(df.select_dtypes(include=[np.number]).columns)
        profile["categorical_columns"] = list(df.select_dtypes(include=['object']).columns)
        profile["datetime_columns"] = list(df.select_dtypes(include=['datetime64']).columns)
        
        # Identify potential time column
        if profile["datetime_columns"]:
            profile["time_column"] = profile["datetime_columns"][0]
        elif "date" in [col.lower() for col in df.columns]:
            for col in df.columns:
                if "date" in col.lower():
                    profile["time_column"] = col
                    break
        
        # Calculate data quality score
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.count().sum()
        profile["quality_score"] = (non_null_cells / total_cells * 100) if total_cells > 0 else 0
        
        # Generate recommendations
        if profile["quality_score"] < 80:
            profile["recommendations"].append("Consider handling missing values")
        
        if len(profile["numeric_columns"]) > 1:
            profile["recommendations"].append("Correlation analysis recommended")
        
        if profile.get("time_column"):
            profile["recommendations"].append("Time series analysis available")
        
        return profile
    
    async def clean_data(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Clean and preprocess data
        
        Args:
            data: Input data
            options: Cleaning options
            
        Returns:
            Cleaned DataFrame
        """
        df = self._to_dataframe(data)
        options = options or {}
        
        # Handle missing values
        if options.get("handle_missing", True):
            df = await self._handle_missing_values(df, options.get("missing_strategy", "drop"))
        
        # Remove duplicates
        if options.get("remove_duplicates", True):
            df = df.drop_duplicates()
        
        # Handle outliers
        if options.get("handle_outliers", False):
            df = await self._handle_outliers(df, options.get("outlier_method", "iqr"))
        
        # Normalize/scale numeric columns
        if options.get("normalize", False):
            df = await self._normalize_data(df, options.get("normalization_method", "standard"))
        
        # Convert data types
        if options.get("convert_types", True):
            df = await self._convert_data_types(df)
        
        return df
    
    async def aggregate_data(
        self,
        data: Any,
        group_by: List[str],
        aggregations: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Aggregate data based on grouping and aggregation functions
        
        Args:
            data: Input data
            group_by: Columns to group by
            aggregations: Dictionary of column: aggregation_function
            
        Returns:
            Aggregated DataFrame
        """
        df = self._to_dataframe(data)
        
        # Prepare aggregation dictionary
        agg_dict = {}
        for col, func in aggregations.items():
            if col in df.columns:
                agg_dict[col] = func
        
        # Perform aggregation
        if group_by and agg_dict:
            result = df.groupby(group_by).agg(agg_dict).reset_index()
        else:
            result = df
        
        return result
    
    # Private helper methods
    
    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert various data formats to DataFrame"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            if "data" in data:
                return pd.DataFrame(data["data"])
            else:
                return pd.DataFrame([data])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    async def _get_basic_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic information about the DataFrame"""
        return {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
            "has_duplicates": df.duplicated().any(),
            "duplicate_count": df.duplicated().sum()
        }
    
    async def _get_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        stats = {}
        
        # Numeric statistics
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            stats["numeric"] = {
                "describe": numeric_df.describe().to_dict(),
                "correlation_matrix": numeric_df.corr().to_dict(),
                "covariance_matrix": numeric_df.cov().to_dict()
            }
        
        # Categorical statistics
        categorical_df = df.select_dtypes(include=['object'])
        if not categorical_df.empty:
            stats["categorical"] = {}
            for col in categorical_df.columns:
                stats["categorical"][col] = {
                    "unique_count": categorical_df[col].nunique(),
                    "mode": categorical_df[col].mode().tolist()[0] if not categorical_df[col].mode().empty else None,
                    "value_counts": categorical_df[col].value_counts().head(10).to_dict()
                }
        
        return stats
    
    async def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality metrics"""
        total_cells = len(df) * len(df.columns)
        
        quality = {
            "completeness": (df.count().sum() / total_cells * 100) if total_cells > 0 else 0,
            "missing_by_column": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "duplicate_percentage": (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
        }
        
        # Check for potential data issues
        issues = []
        
        # High missing data
        for col, pct in quality["missing_percentage"].items():
            if pct > 30:
                issues.append(f"Column '{col}' has {pct:.1f}% missing values")
        
        # High cardinality in categorical columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) > 0.9 and len(df) > 10:
                issues.append(f"Column '{col}' has very high cardinality")
        
        quality["issues"] = issues
        
        return quality
    
    async def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in the data"""
        patterns = {
            "trends": {},
            "seasonality": {},
            "cycles": {}
        }
        
        # Detect trends in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if len(df) > 10:
                # Simple trend detection using linear regression
                x = np.arange(len(df))
                y = df[col].fillna(df[col].mean()).values
                
                if len(y) > 0 and not np.all(np.isnan(y)):
                    slope, intercept = np.polyfit(x, y, 1)
                    patterns["trends"][col] = {
                        "slope": float(slope),
                        "direction": "increasing" if slope > 0 else "decreasing",
                        "strength": abs(float(slope)) / (df[col].std() + 1e-10)
                    }
        
        return patterns
    
    async def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the data"""
        anomalies = {
            "outliers": {},
            "unusual_patterns": []
        }
        
        # Detect outliers using IQR method
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            if len(outliers) > 0:
                anomalies["outliers"][col] = {
                    "count": len(outliers),
                    "percentage": len(outliers) / len(df) * 100,
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "indices": outliers.index.tolist()[:10]  # First 10 indices
                }
        
        return anomalies
    
    async def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlations between variables"""
        correlations = {}
        
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # Strong correlation threshold
                        strong_correlations.append({
                            "var1": corr_matrix.columns[i],
                            "var2": corr_matrix.columns[j],
                            "correlation": float(corr_value),
                            "strength": "strong positive" if corr_value > 0 else "strong negative"
                        })
            
            correlations = {
                "matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_correlations
            }
        
        return correlations
    
    async def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distributions of numeric variables"""
        distributions = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 0:
                distributions[col] = {
                    "skewness": float(data.skew()),
                    "kurtosis": float(data.kurtosis()),
                    "normality_test": self._test_normality(data),
                    "distribution_type": self._identify_distribution(data)
                }
        
        return distributions
    
    def _test_normality(self, data: pd.Series) -> Dict[str, Any]:
        """Test if data follows normal distribution"""
        if len(data) < 3:
            return {"test": "insufficient_data"}
        
        try:
            statistic, p_value = stats.normaltest(data)
            return {
                "test": "normaltest",
                "statistic": float(statistic),
                "p_value": float(p_value),
                "is_normal": p_value > 0.05
            }
        except:
            return {"test": "error"}
    
    def _identify_distribution(self, data: pd.Series) -> str:
        """Identify the type of distribution"""
        skewness = data.skew()
        kurtosis = data.kurtosis()
        
        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return "normal"
        elif skewness > 1:
            return "right_skewed"
        elif skewness < -1:
            return "left_skewed"
        elif kurtosis > 3:
            return "leptokurtic"
        elif kurtosis < -3:
            return "platykurtic"
        else:
            return "unknown"
    
    async def _identify_root_causes(self, df: pd.DataFrame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential root causes for issues"""
        root_causes = []
        
        # Analyze based on context
        target_column = context.get("target_column")
        if target_column and target_column in df.columns:
            # Find variables most correlated with target
            numeric_df = df.select_dtypes(include=[np.number])
            if target_column in numeric_df.columns:
                correlations = numeric_df.corr()[target_column].sort_values(ascending=False)
                
                for col, corr in correlations.items():
                    if col != target_column and abs(corr) > 0.5:
                        root_causes.append({
                            "variable": col,
                            "correlation": float(corr),
                            "impact": "high" if abs(corr) > 0.7 else "medium",
                            "relationship": "positive" if corr > 0 else "negative"
                        })
        
        return root_causes
    
    async def _analyze_impact(self, df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact of variables"""
        impact_analysis = {}
        
        # Placeholder for impact analysis
        # This would typically involve more sophisticated statistical methods
        
        return impact_analysis
    
    async def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in time series data"""
        trends = {}
        
        # Find datetime columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        if len(date_cols) > 0:
            # Use first date column as time index
            time_col = date_cols[0]
            df_sorted = df.sort_values(time_col)
            
            # Analyze trends for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                # Simple moving average
                if len(df_sorted) > 7:
                    df_sorted[f"{col}_ma7"] = df_sorted[col].rolling(window=7).mean()
                    
                    trends[col] = {
                        "has_trend": True,
                        "direction": self._get_trend_direction(df_sorted[col].values),
                        "change_points": []  # Placeholder for change point detection
                    }
        
        return trends
    
    def _get_trend_direction(self, values: np.ndarray) -> str:
        """Determine trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear regression for trend
        x = np.arange(len(values))
        valid_mask = ~np.isnan(values)
        
        if np.sum(valid_mask) < 2:
            return "insufficient_data"
        
        slope, _ = np.polyfit(x[valid_mask], values[valid_mask], 1)
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    async def _perform_segmentation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform data segmentation"""
        segmentation = {}
        
        # Placeholder for segmentation logic
        # This would typically involve clustering algorithms
        
        return segmentation
    
    async def _run_hypothesis_tests(self, df: pd.DataFrame, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run statistical hypothesis tests"""
        tests = []
        
        # Placeholder for hypothesis testing
        # This would include t-tests, chi-square tests, ANOVA, etc.
        
        return tests
    
    async def _detect_streaming_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in streaming data"""
        anomalies = []
        
        # Simple anomaly detection for streaming data
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Z-score based anomaly detection
            mean = df[col].mean()
            std = df[col].std()
            
            if std > 0:
                df[f"{col}_zscore"] = (df[col] - mean) / std
                anomaly_mask = abs(df[f"{col}_zscore"]) > 3
                
                if anomaly_mask.any():
                    anomaly_indices = df[anomaly_mask].index.tolist()
                    for idx in anomaly_indices:
                        anomalies.append({
                            "index": int(idx),
                            "column": col,
                            "value": float(df.loc[idx, col]),
                            "z_score": float(df.loc[idx, f"{col}_zscore"]),
                            "severity": "high" if abs(df.loc[idx, f"{col}_zscore"]) > 4 else "medium"
                        })
        
        return anomalies
    
    async def _handle_missing_values(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Handle missing values based on strategy"""
        if strategy == "drop":
            return df.dropna()
        elif strategy == "mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif strategy == "median":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        elif strategy == "forward_fill":
            df = df.fillna(method='ffill')
        elif strategy == "backward_fill":
            df = df.fillna(method='bfill')
        
        return df
    
    async def _handle_outliers(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """Handle outliers based on method"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == "iqr":
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                df[col] = df[col].clip(lower_bound, upper_bound)
        elif method == "zscore":
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    df[col] = df[col].apply(
                        lambda x: x if abs((x - mean) / std) <= 3 else mean
                    )
        
        return df
    
    async def _normalize_data(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """Normalize numeric data"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == "standard":
            scaler = StandardScaler()
            df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        elif method == "minmax":
            scaler = MinMaxScaler()
            df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        
        return df
    
    async def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Automatically convert data types"""
        for col in df.columns:
            # Try to convert to numeric
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                # Try to convert to datetime
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    # Keep as string/object
                    pass
        
        return df


class StreamProcessor:
    """
    Handles real-time stream processing
    """
    
    def __init__(self):
        """Initialize stream processor"""
        self.streams = {}
        self.buffers = defaultdict(list)
        self.window_size = 1000  # Default window size for streaming analytics
        logger.info("StreamProcessor initialized")
    
    async def connect(self, data_source_id: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Connect to a streaming data source
        
        Args:
            data_source_id: ID of the streaming source
            context: Connection context
            
        Returns:
            Stream connection object
        """
        # This would connect to actual streaming sources
        # For now, return a mock stream
        stream_id = f"stream_{data_source_id}_{datetime.utcnow().timestamp()}"
        self.streams[stream_id] = {
            "source_id": data_source_id,
            "connected_at": datetime.utcnow(),
            "context": context or {}
        }
        
        return stream_id
    
    async def get_recent_batch(self, stream_id: str, limit: int = 100) -> List[Dict]:
        """
        Get recent batch of data from stream
        
        Args:
            stream_id: Stream identifier
            limit: Number of records to retrieve
            
        Returns:
            List of recent records
        """
        # Return buffered data or generate mock data
        if stream_id in self.buffers:
            return self.buffers[stream_id][-limit:]
        
        # Generate mock streaming data
        mock_data = []
        for i in range(limit):
            mock_data.append({
                "timestamp": datetime.utcnow().isoformat(),
                "value": np.random.randn(),
                "category": np.random.choice(["A", "B", "C"]),
                "stream_id": stream_id
            })
        
        return mock_data
    
    async def process_window(
        self,
        stream_id: str,
        window_type: str = "tumbling",
        window_size: int = None
    ) -> Dict[str, Any]:
        """
        Process data using windowing functions
        
        Args:
"""
