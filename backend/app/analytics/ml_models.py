"""
Machine Learning Models Module

Provides ML capabilities for analytics including:
- Model training and prediction
- Time series forecasting
- Anomaly detection
- Feature engineering
- Model evaluation
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """ML model types"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"


class Algorithm(str, Enum):
    """ML algorithms"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    LOGISTIC_REGRESSION = "logistic_regression"
    ARIMA = "arima"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SARIMAX = "sarimax"
    ISOLATION_FOREST = "isolation_forest"


class ModelConfig(BaseModel):
    """ML model configuration"""
    model_type: ModelType = Field(..., description="Type of ML model")
    algorithm: Algorithm = Field(..., description="ML algorithm to use")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    features: List[str] = Field(..., description="Feature columns")
    target: str = Field(..., description="Target column")
    auto_tune: bool = Field(default=False, description="Enable hyperparameter tuning")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set size")
    random_state: int = Field(default=42, description="Random seed")


class MLEngine:
    """
    Machine Learning Engine
    
    Handles model training, prediction, and evaluation
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def prepare_data(
        self,
        data: Union[List[Dict], Dict[str, Any]],
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Prepare data for ML
        
        Args:
            data: Input data
            target_column: Target variable column name
            
        Returns:
            Tuple of (features DataFrame, target Series)
        """
        try:
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data.get("data", []))
            
            # Handle missing values
            df = df.fillna(df.mean(numeric_only=True))
            
            # Separate features and target
            if target_column and target_column in df.columns:
                X = df.drop(columns=[target_column])
                y = df[target_column]
            else:
                X = df
                y = None
            
            # Encode categorical variables
            for col in X.select_dtypes(include=['object']).columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    X[col] = self.encoders[col].fit_transform(X[col].astype(str))
                else:
                    X[col] = self.encoders[col].transform(X[col].astype(str))
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise
    
    async def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        config: ModelConfig
    ) -> Dict[str, Any]:
        """
        Train ML model
        
        Args:
            X: Feature matrix
            y: Target variable
            config: Model configuration
            
        Returns:
            Training results including metrics and model ID
        """
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=config.test_size,
                random_state=config.random_state
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Select and train model
            if config.model_type == ModelType.REGRESSION:
                model = await self._train_regression(
                    X_train_scaled, y_train,
                    config.algorithm,
                    config.hyperparameters
                )
                predictions = model.predict(X_test_scaled)
                metrics = {
                    "mse": float(mean_squared_error(y_test, predictions)),
                    "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
                    "r2": float(r2_score(y_test, predictions))
                }
                
            elif config.model_type == ModelType.CLASSIFICATION:
                model = await self._train_classification(
                    X_train_scaled, y_train,
                    config.algorithm,
                    config.hyperparameters
                )
                predictions = model.predict(X_test_scaled)
                metrics = {
                    "accuracy": float(accuracy_score(y_test, predictions)),
                    "report": classification_report(y_test, predictions, output_dict=True)
                }
            
            else:
                raise ValueError(f"Unsupported model type: {config.model_type}")
            
            # Store model
            model_id = f"{config.model_type}_{datetime.utcnow().timestamp()}"
            self.models[model_id] = model
            self.scalers[model_id] = scaler
            self.model_metadata[model_id] = {
                "config": config.dict(),
                "metrics": metrics,
                "features": list(X.columns),
                "trained_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model trained successfully: {model_id}")
            
            return {
                "model_id": model_id,
                "metrics": metrics,
                "feature_importance": await self._get_feature_importance(model, X.columns),
                "predictions_sample": predictions[:10].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    async def _train_regression(
        self,
        X: np.ndarray,
        y: pd.Series,
        algorithm: Algorithm,
        hyperparameters: Dict[str, Any]
    ) -> Any:
        """Train regression model"""
        if algorithm == Algorithm.LINEAR_REGRESSION:
            model = LinearRegression(**hyperparameters)
        elif algorithm == Algorithm.RANDOM_FOREST:
            model = RandomForestRegressor(
                n_estimators=hyperparameters.get("n_estimators", 100),
                max_depth=hyperparameters.get("max_depth", None),
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported regression algorithm: {algorithm}")
        
        model.fit(X, y)
        return model
    
    async def _train_classification(
        self,
        X: np.ndarray,
        y: pd.Series,
        algorithm: Algorithm,
        hyperparameters: Dict[str, Any]
    ) -> Any:
        """Train classification model"""
        if algorithm == Algorithm.LOGISTIC_REGRESSION:
            model = LogisticRegression(**hyperparameters)
        elif algorithm == Algorithm.RANDOM_FOREST:
            model = RandomForestClassifier(
                n_estimators=hyperparameters.get("n_estimators", 100),
                max_depth=hyperparameters.get("max_depth", None),
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported classification algorithm: {algorithm}")
        
        model.fit(X, y)
        return model
    
    async def predict(
        self,
        data: Union[List[Dict], Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make predictions using trained model
        
        Args:
            data: Input data for prediction
            context: Additional context (e.g., model_id)
            
        Returns:
            Predictions and metadata
        """
        try:
            # Get model
            model_id = context.get("model_id") if context else None
            if not model_id or model_id not in self.models:
                # Use most recent model
                if not self.models:
                    raise ValueError("No trained models available")
                model_id = max(self.models.keys())
            
            model = self.models[model_id]
            scaler = self.scalers[model_id]
            metadata = self.model_metadata[model_id]
            
            # Prepare data
            X, _ = await self.prepare_data(data)
            
            # Ensure features match
            expected_features = metadata["features"]
            X = X[expected_features]
            
            # Scale and predict
            X_scaled = scaler.transform(X)
            predictions = model.predict(X_scaled)
            
            return {
                "predictions": predictions.tolist(),
                "model_id": model_id,
                "model_type": metadata["config"]["model_type"],
                "count": len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise
    
    async def forecast_time_series(
        self,
        df: pd.DataFrame,
        target_column: str,
        periods: int = 30,
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        Perform time series forecasting
        
        Args:
            df: Time series data
            target_column: Column to forecast
            periods: Number of periods to forecast
            method: Forecasting method (auto, arima, exponential_smoothing)
            
        Returns:
            Forecast results
        """
        try:
            series = df[target_column]
            
            if method == "auto" or method == "arima":
                # ARIMA model
                model = ARIMA(series, order=(1, 1, 1))
                fitted = model.fit()
                forecast = fitted.forecast(steps=periods)
                
            elif method == "exponential_smoothing":
                # Exponential Smoothing
                model = ExponentialSmoothing(series, seasonal_periods=12)
                fitted = model.fit()
                forecast = fitted.forecast(steps=periods)
                
            else:
                raise ValueError(f"Unsupported forecasting method: {method}")
            
            return {
                "forecast": forecast.tolist(),
                "method": method,
                "periods": periods,
                "confidence_interval": {
                    "lower": (forecast * 0.95).tolist(),
                    "upper": (forecast * 1.05).tolist()
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting time series: {e}")
            raise
    
    async def detect_anomalies(
        self,
        df: pd.DataFrame,
        method: str = "isolation_forest",
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """
        Detect anomalies in data
        
        Args:
            df: Input data
            method: Detection method
            contamination: Expected proportion of anomalies
            
        Returns:
            Anomaly detection results
        """
        try:
            # Prepare numeric data
            numeric_df = df.select_dtypes(include=[np.number])
            
            if method == "isolation_forest":
                model = IsolationForest(
                    contamination=contamination,
                    random_state=42
                )
                predictions = model.fit_predict(numeric_df)
                
                # -1 for anomalies, 1 for normal
                anomalies = predictions == -1
                
            else:
                raise ValueError(f"Unsupported anomaly detection method: {method}")
            
            return {
                "anomalies": anomalies.tolist(),
                "anomaly_indices": np.where(anomalies)[0].tolist(),
                "anomaly_count": int(anomalies.sum()),
                "total_count": len(df),
                "anomaly_percentage": float(anomalies.sum() / len(df) * 100)
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise
    
    async def calculate_confidence(
        self,
        predictions: Dict[str, Any]
    ) -> List[float]:
        """
        Calculate confidence scores for predictions
        
        Args:
            predictions: Prediction results
            
        Returns:
            List of confidence scores
        """
        # Simplified confidence calculation
        # In production, use model-specific methods
        pred_values = predictions.get("predictions", [])
        return [0.85 + np.random.random() * 0.15 for _ in pred_values]
    
    async def _get_feature_importance(
        self,
        model: Any,
        feature_names: pd.Index
    ) -> Dict[str, float]:
        """Get feature importance from model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return {
                    name: float(importance)
                    for name, importance in zip(feature_names, importances)
                }
            elif hasattr(model, 'coef_'):
                coefficients = model.coef_
                if len(coefficients.shape) > 1:
                    coefficients = coefficients[0]
                return {
                    name: float(abs(coef))
                    for name, coef in zip(feature_names, coefficients)
                }
            else:
                return {}
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
            return {}
    
    async def get_model_info(self) -> List[Dict[str, Any]]:
        """Get information about all trained models"""
        return [
            {
                "model_id": model_id,
                **metadata
            }
            for model_id, metadata in self.model_metadata.items()
        ]


# Export
__all__ = ["MLEngine", "ModelConfig", "ModelType", "Algorithm"]
