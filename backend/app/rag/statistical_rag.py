"""
Statistical RAG for Advanced Analytics

Handles statistical analysis from natural language queries,
automated insight generation, and statistical recommendations.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import json
from scipy import stats
from sklearn.preprocessing import StandardScaler
import warnings

# LangChain components
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# Statistical analysis libraries
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from scipy.stats import normaltest, shapiro, anderson
from scipy.stats import ttest_ind, ttest_rel, f_oneway, chi2_contingency
from scipy.stats import pearsonr, spearmanr, kendalltau

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class StatisticalRAG:
    """
    RAG system specialized for statistical analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Statistical RAG"""
        self.config = config or {}
        self.llm = ChatOpenAI(
            model=self.config.get("model", "gpt-4"),
            temperature=self.config.get("temperature", 0.1)
        )
        self.memory = ConversationBufferMemory(return_messages=True)
        
        # Statistical test mappings
        self.statistical_tests = self._initialize_statistical_tests()
        
        logger.info("StatisticalRAG initialized")
    
    async def analyze(
        self,
        query: str,
        data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis based on natural language query
        
        Args:
            query: Natural language query about statistical analysis
            data: Data to analyze
            context: Additional context
            
        Returns:
            Statistical analysis results
        """
        logger.info(f"Statistical analysis for query: {query}")
        
        # Convert data to DataFrame
        df = self._prepare_data(data)
        
        # Determine analysis type from query
        analysis_type = await self._determine_analysis_type(query)
        
        # Perform appropriate analysis
        if analysis_type == "descriptive":
            results = await self._descriptive_statistics(df, query)
        elif analysis_type == "inferential":
            results = await self._inferential_statistics(df, query)
        elif analysis_type == "correlation":
            results = await self._correlation_analysis(df, query)
        elif analysis_type == "regression":
            results = await self._regression_analysis(df, query)
        elif analysis_type == "time_series":
            results = await self._time_series_analysis(df, query)
        elif analysis_type == "distribution":
            results = await self._distribution_analysis(df, query)
        else:
            results = await self._general_statistical_analysis(df, query)
        
        # Generate insights
        insights = await self._generate_statistical_insights(results, query)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(results, df)
        
        return {
            "analysis_type": analysis_type,
            "results": results,
            "insights": insights,
            "recommendations": recommendations,
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _prepare_data(self, data: Any) -> pd.DataFrame:
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
    
    async def _determine_analysis_type(self, query: str) -> str:
        """Determine the type of statistical analysis from query"""
        query_lower = query.lower()
        
        # Keywords for different analysis types
        descriptive_keywords = ["mean", "average", "median", "mode", "std", "variance", 
                               "summary", "describe", "statistics", "quartile", "percentile"]
        inferential_keywords = ["test", "hypothesis", "significant", "p-value", "confidence",
                               "compare", "difference", "t-test", "anova", "chi-square"]
        correlation_keywords = ["correlation", "relationship", "association", "relate",
                               "pearson", "spearman", "kendall"]
        regression_keywords = ["regression", "predict", "forecast", "model", "linear",
                              "coefficient", "r-squared", "fit"]
        time_series_keywords = ["trend", "seasonal", "time series", "forecast", "decompose",
                               "autocorrelation", "lag", "moving average"]
        distribution_keywords = ["distribution", "normal", "skew", "kurtosis", "histogram",
                               "density", "probability", "quantile"]
        
        # Check keywords
        if any(keyword in query_lower for keyword in descriptive_keywords):
            return "descriptive"
        elif any(keyword in query_lower for keyword in inferential_keywords):
            return "inferential"
        elif any(keyword in query_lower for keyword in correlation_keywords):
            return "correlation"
        elif any(keyword in query_lower for keyword in regression_keywords):
            return "regression"
        elif any(keyword in query_lower for keyword in time_series_keywords):
            return "time_series"
        elif any(keyword in query_lower for keyword in distribution_keywords):
            return "distribution"
        else:
            return "general"
    
    async def _descriptive_statistics(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Calculate descriptive statistics"""
        results = {}
        
        # Basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_stats = {
                "count": int(df[col].count()),
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "mode": float(df[col].mode()[0]) if not df[col].mode().empty else None,
                "std": float(df[col].std()),
                "variance": float(df[col].var()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "range": float(df[col].max() - df[col].min()),
                "q1": float(df[col].quantile(0.25)),
                "q3": float(df[col].quantile(0.75)),
                "iqr": float(df[col].quantile(0.75) - df[col].quantile(0.25)),
                "skewness": float(df[col].skew()),
                "kurtosis": float(df[col].kurtosis()),
                "cv": float(df[col].std() / df[col].mean() * 100) if df[col].mean() != 0 else None,
                "sem": float(df[col].sem()),  # Standard error of mean
                "mad": float(df[col].mad()),  # Mean absolute deviation
            }
            
            # Add percentiles
            percentiles = [5, 10, 25, 50, 75, 90, 95]
            for p in percentiles:
                col_stats[f"p{p}"] = float(df[col].quantile(p/100))
            
            results[col] = col_stats
        
        # Categorical statistics
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            results[col] = {
                "count": int(df[col].count()),
                "unique": int(df[col].nunique()),
                "top": df[col].mode()[0] if not df[col].mode().empty else None,
                "freq": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0,
                "value_counts": df[col].value_counts().head(10).to_dict()
            }
        
        return {
            "descriptive_statistics": results,
            "summary": df.describe(include='all').to_dict(),
            "data_shape": {"rows": len(df), "columns": len(df.columns)}
        }
    
    async def _inferential_statistics(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Perform inferential statistical tests"""
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Determine which test to perform based on query
        query_lower = query.lower()
        
        if "t-test" in query_lower or "compare" in query_lower:
            # Perform t-tests
            if len(numeric_cols) >= 2:
                col1, col2 = numeric_cols[0], numeric_cols[1]
                
                # Independent samples t-test
                t_stat, p_value = ttest_ind(
                    df[col1].dropna(),
                    df[col2].dropna()
                )
                
                results["t_test"] = {
                    "test_type": "independent_samples",
                    "columns": [col1, col2],
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "interpretation": self._interpret_p_value(p_value)
                }
                
                # Effect size (Cohen's d)
                mean1, mean2 = df[col1].mean(), df[col2].mean()
                pooled_std = np.sqrt((df[col1].var() + df[col2].var()) / 2)
                cohens_d = (mean1 - mean2) / pooled_std if pooled_std != 0 else 0
                
                results["t_test"]["effect_size"] = {
                    "cohens_d": float(cohens_d),
                    "interpretation": self._interpret_effect_size(cohens_d)
                }
        
        elif "anova" in query_lower:
            # Perform ANOVA
            if len(numeric_cols) >= 3:
                groups = [df[col].dropna() for col in numeric_cols[:5]]  # Limit to 5 groups
                f_stat, p_value = f_oneway(*groups)
                
                results["anova"] = {
                    "test_type": "one_way_anova",
                    "groups": list(numeric_cols[:5]),
                    "f_statistic": float(f_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "interpretation": self._interpret_p_value(p_value)
                }
        
        elif "chi" in query_lower or "categorical" in query_lower:
            # Perform chi-square test
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) >= 2:
                # Create contingency table
                contingency = pd.crosstab(
                    df[categorical_cols[0]],
                    df[categorical_cols[1]]
                )
                
                chi2, p_value, dof, expected = chi2_contingency(contingency)
                
                results["chi_square"] = {
                    "test_type": "independence",
                    "variables": list(categorical_cols[:2]),
                    "chi2_statistic": float(chi2),
                    "p_value": float(p_value),
                    "degrees_of_freedom": int(dof),
                    "significant": p_value < 0.05,
                    "interpretation": self._interpret_p_value(p_value),
                    "cramers_v": self._calculate_cramers_v(chi2, contingency.sum().sum(), 
                                                           contingency.shape[0], 
                                                           contingency.shape[1])
                }
        
        # Normality tests
        if len(numeric_cols) > 0:
            normality_results = {}
            for col in numeric_cols[:3]:  # Test first 3 columns
                data = df[col].dropna()
                if len(data) >= 3:
                    # Shapiro-Wilk test
                    if len(data) <= 5000:
                        stat, p_value = shapiro(data)
                        normality_results[col] = {
                            "test": "shapiro_wilk",
                            "statistic": float(stat),
                            "p_value": float(p_value),
                            "is_normal": p_value > 0.05
                        }
                    else:
                        # Anderson-Darling test for larger samples
                        result = anderson(data)
                        normality_results[col] = {
                            "test": "anderson_darling",
                            "statistic": float(result.statistic),
                            "critical_values": result.critical_values.tolist(),
                            "significance_levels": result.significance_level.tolist()
                        }
            
            results["normality_tests"] = normality_results
        
        return results
    
    async def _correlation_analysis(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Perform correlation analysis"""
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for correlation analysis"}
        
        # Correlation matrix
        corr_matrix = df[numeric_cols].corr()
        results["correlation_matrix"] = corr_matrix.to_dict()
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:  # Threshold for strong correlation
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    
                    # Calculate different correlation coefficients
                    data1 = df[col1].dropna()
                    data2 = df[col2].dropna()
                    
                    # Align data
                    aligned = pd.DataFrame({'x': data1, 'y': data2}).dropna()
                    if len(aligned) > 2:
                        pearson_r, pearson_p = pearsonr(aligned['x'], aligned['y'])
                        spearman_r, spearman_p = spearmanr(aligned['x'], aligned['y'])
                        kendall_tau, kendall_p = kendalltau(aligned['x'], aligned['y'])
                        
                        strong_correlations.append({
                            "variables": [col1, col2],
                            "pearson": {
                                "coefficient": float(pearson_r),
                                "p_value": float(pearson_p),
                                "significant": pearson_p < 0.05
                            },
                            "spearman": {
                                "coefficient": float(spearman_r),
                                "p_value": float(spearman_p),
                                "significant": spearman_p < 0.05
                            },
                            "kendall": {
                                "coefficient": float(kendall_tau),
                                "p_value": float(kendall_p),
                                "significant": kendall_p < 0.05
                            },
                            "interpretation": self._interpret_correlation(pearson_r)
                        })
        
        results["strong_correlations"] = strong_correlations
        
        # Partial correlations (controlling for other variables)
        if len(numeric_cols) >= 3:
            results["partial_correlations"] = await self._calculate_partial_correlations(df, numeric_cols)
        
        # Multicollinearity check (VIF)
        if len(numeric_cols) >= 2:
            vif_data = []
            for i, col in enumerate(numeric_cols):
                try:
                    vif = variance_inflation_factor(df[numeric_cols].values, i)
                    vif_data.append({
                        "variable": col,
                        "vif": float(vif),
                        "multicollinearity": vif > 5
                    })
                except:
                    pass
            results["multicollinearity"] = vif_data
        
        return results
    
    async def _regression_analysis(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Perform regression analysis"""
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        from sklearn.model_selection import train_test_split
        
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for regression"}
        
        # Simple linear regression (first two columns)
        X = df[numeric_cols[0]].values.reshape(-1, 1)
        y = df[numeric_cols[1]].values
        
        # Remove NaN values
        mask = ~(np.isnan(X.flatten()) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) < 10:
            return {"error": "Insufficient data for regression"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Fit model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Metrics
        results["simple_linear_regression"] = {
            "predictor": numeric_cols[0],
            "target": numeric_cols[1],
            "coefficients": {
                "intercept": float(model.intercept_),
                "slope": float(model.coef_[0])
            },
            "metrics": {
                "r2_train": float(r2_score(y_train, y_pred_train)),
                "r2_test": float(r2_score(y_test, y_pred_test)),
                "rmse_train": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                "rmse_test": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                "mae_train": float(mean_absolute_error(y_train, y_pred_train)),
                "mae_test": float(mean_absolute_error(y_test, y_pred_test))
            },
            "equation": f"y = {model.intercept_:.2f} + {model.coef_[0]:.2f} * x"
        }
        
        # Residual analysis
        residuals = y_test - y_pred_test
        results["residual_analysis"] = {
            "mean_residual": float(np.mean(residuals)),
            "std_residual": float(np.std(residuals)),
            "durbin_watson": float(durbin_watson(residuals)),
            "normality_test": self._test_residual_normality(residuals)
        }
        
        # Multiple regression if more than 2 columns
        if len(numeric_cols) > 2:
            X_multi = df[numeric_cols[:-1]].values
            y_multi = df[numeric_cols[-1]].values
            
            # Remove NaN values
            mask = ~np.any(np.isnan(X_multi), axis=1) & ~np.isnan(y_multi)
            X_multi = X_multi[mask]
            y_multi = y_multi[mask]
            
            if len(X_multi) >= 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_multi, y_multi, test_size=0.2, random_state=42
                )
                
                model_multi = LinearRegression()
                model_multi.fit(X_train, y_train)
                
                y_pred_test = model_multi.predict(X_test)
                
                results["multiple_regression"] = {
                    "predictors": list(numeric_cols[:-1]),
                    "target": numeric_cols[-1],
                    "coefficients": {
                        "intercept": float(model_multi.intercept_),
                        "slopes": {col: float(coef) for col, coef in 
                                 zip(numeric_cols[:-1], model_multi.coef_)}
                    },
                    "r2_score": float(r2_score(y_test, y_pred_test)),
                    "adjusted_r2": self._calculate_adjusted_r2(
                        r2_score(y_test, y_pred_test),
                        len(y_test),
                        len(numeric_cols) - 1
                    )
                }
        
        return results
    
    async def _time_series_analysis(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Perform time series analysis"""
        from statsmodels.tsa.seasonal import seasonal_decompose
        from statsmodels.tsa.stattools import adfuller, acf, pacf
        
        results = {}
        
        # Find time column and value column
        date_cols = df.select_dtypes(include=['datetime64']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(date_cols) == 0 or len(numeric_cols) == 0:
            return {"error": "Need datetime and numeric columns for time series analysis"}
        
        # Use first date and numeric columns
        time_col = date_cols[0]
        value_col = numeric_cols[0]
        
        # Sort by time
        df_sorted = df.sort_values(time_col)
        ts_data = df_sorted.set_index(time_col)[value_col]
        
        # Remove NaN values
        ts_data = ts_data.dropna()
        
        if len(ts_data) < 10:
            return {"error": "Insufficient data for time series analysis"}
        
        # Stationarity test (ADF)
        adf_result = adfuller(ts_data)
        results["stationarity_test"] = {
            "test": "augmented_dickey_fuller",
            "adf_statistic": float(adf_result[0]),
            "p_value": float(adf_result[1]),
            "critical_values": {
                "1%": float(adf_result[4]["1%"]),
                "5%": float(adf_result[4]["5%"]),
                "10%": float(adf_result[4]["10%"])
            },
            "is_stationary": adf_result[1] < 0.05
        }
        
        # Decomposition (if enough data)
        if len(ts_data) >= 24:  # Need at least 2 periods
            try:
                decomposition = seasonal_decompose(ts_data, model='additive', period=12)
                results["decomposition"] = {
                    "trend": decomposition.trend.dropna().tolist()[-10:],  # Last 10 points
                    "seasonal": decomposition.seasonal.dropna().tolist()[-10:],
                    "residual": decomposition.resid.dropna().tolist()[-10:],
                    "model": "additive"
                }
            except:
                pass
        
        # Autocorrelation
        if len(ts_data) >= 20:
            acf_values = acf(ts_data, nlags=min(20, len(ts_data)//2))
            pacf_values = pacf(ts_data, nlags=min(20, len(ts_data)//2))
            
            results["autocorrelation"] = {
                "acf": acf_values.tolist()[:10],
                "pacf": pacf_values.tolist()[:10],
                "significant_lags": self._find_significant_lags(acf_values, len(ts_data))
            }
        
        # Basic time series statistics
        results["time_series_stats"] = {
            "start_date": str(ts_data.index.min()),
            "end_date": str(ts_data.index.max()),
            "frequency": self._detect_frequency(ts_data.index),
            "length": len(ts_data),
            "missing_periods": self._detect_missing_periods(ts_data.index)
        }
        
        return results
    
    async def _distribution_analysis(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Analyze data distributions"""
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            
            if len(data) < 3:
                continue
            
            # Distribution tests
            distribution_tests = {}
            
            # Normality tests
            if len(data) <= 5000:
                shapiro_stat, shapiro_p = shapiro(data)
                distribution_tests["shapiro_wilk"] = {
                    "statistic": float(shapiro_stat),
                    "p_value": float(shapiro_p),
                    "is_normal": shapiro_p > 0.05
                }
            
            # Anderson-Darling test
            anderson_result = anderson(data)
            distribution_tests["anderson_darling"] = {
                "statistic": float(anderson_result.statistic),
                "critical_values": {
                    f"{level}%": float(cv) 
                    for level, cv in zip(anderson_result.significance_level, 
                                        anderson_result.critical_values)
                }
            }
            
            # D'Agostino's K-squared test
            if len(data) >= 8:
                k2_stat, k2_p = normaltest(data)
                distribution_tests["dagostino_k2"] = {
                    "statistic": float(k2_stat),
                    "p_value": float(k2_p),
                    "is_normal": k2_p > 0.05
                }
            
            # Distribution parameters
            results[col] = {
                "tests": distribution_tests,
                "parameters": {
                    "mean": float(data.mean()),
                    "std": float(data.std()),
                    "skewness": float(data.skew()),
                    "kurtosis": float(data.kurtosis()),
                    "median": float(data.median()),
                    "mode": float(data.mode()[0]) if not data.mode().empty else None
                },
                "distribution_type": self._identify_distribution_type(data),
                "outliers": self._detect_outliers(data)
            }
        
        return results
    
    async def _general_statistical_analysis(
        self,
        df: pd.DataFrame,
        query: str
    ) -> Dict[str, Any]:
        """Perform general statistical analysis"""
        results = {}
        
        # Combine multiple analyses
        results["descriptive"] = await self._descriptive_statistics(df, query)
        
        # Add correlation if multiple numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            results["correlations"] = await self._correlation_analysis(df, query)
        
        # Add distribution analysis
        results["distributions"] = await self._distribution_analysis(df, query)
        
        return results
    
    async def _generate_statistical_insights(
        self,
        results: Dict[str, Any],
        query: str
    ) -> List[Dict[str, Any]]:
        """Generate insights from statistical results"""
        insights = []
        
        # Analyze results and generate insights
        if "descriptive_statistics" in results:
            desc_stats = results["descriptive_statistics"]
            for col, stats in desc_stats.items():
                if isinstance(stats, dict) and "cv" in stats:
                    cv = stats.get("cv")
                    if cv and cv > 50:
                        insights.append({
                            "type": "high_variability",
                            "column": col,
                            "message": f"High variability detected in {col} (CV: {cv:.1f}%)",
                            "severity": "warning"
                        })
                    
                    skewness = stats.get("skewness")
                    if skewness and abs(skewness) > 1:
                        insights.append({
                            "type": "skewed_distribution",
                            "column": col,
                            "message": f"{col} shows {'positive' if skewness > 0 else 'negative'} skew ({skewness:.2f})",
                            "recommendation": "Consider transformation for normality"
                        })
        
        # Correlation insights
        if "strong_correlations" in results:
            for corr in results["strong_correlations"]:
                vars = corr["variables"]
                pearson_r = corr["pearson"]["coefficient"]
                insights.append({
                    "type": "correlation",
                    "variables": vars,
                    "message": f"Strong correlation between {vars[0]} and {vars[1]} (r={pearson_r:.3f})",
                    "interpretation": corr["interpretation"]
                })
        
        # Test result insights
        if "t_test" in results:
            t_test = results["t_test"]
            if t_test["significant"]:
                insights.append({
                    "type": "statistical_test",
                    "test": "t-test",
                    "message": f"Significant difference found (p={t_test['p_value']:.4f})",
                    "effect_size": t_test.get("effect_size", {}).get("interpretation", "unknown")
                })
        
        return insights
    
    async def _generate_recommendations(
        self,
        results: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[str]:
        """Generate statistical recommendations"""
        recommendations = []
        
        # Check for normality issues
        if "normality_tests" in results:
            non_normal = [col for col, test in results["normality_tests"].items() 
                         if not test.get("is_normal", True)]
            if non_normal:
                recommendations.append(
                    f"Consider data transformation for non-normal distributions: {', '.join(non_normal)}"
                )
        
        # Check for multicollinearity
        if "multicollinearity" in results:
            high_vif = [item["variable"] for item in results["multicollinearity"] 
                       if item.get("multicollinearity", False)]
            if high_vif:
                recommendations.append(
                    f
