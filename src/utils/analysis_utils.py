import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Union
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class TradingAnalyzer:
    """
    Clase para análisis de trading y generación de señales basadas en predicciones
    del modelo LSTM para el tipo de cambio USD/MXN.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        
    def calculate_trading_signals(self,
                                actual_values: np.ndarray,
                                predictions: np.ndarray,
                                threshold: float = 0.001) -> Dict[str, np.ndarray]:
        """
        Genera señales de trading basadas en las predicciones y valores reales.
        """
        # Calcular cambios porcentuales en predicciones
        pred_changes = np.diff(predictions.flatten()) / predictions[:-1].flatten()
        
        # Generar señales
        signals = np.zeros(len(pred_changes))
        signals[pred_changes > threshold] = 1  # Señal de compra
        signals[pred_changes < -threshold] = -1  # Señal de venta
        
        # Calcular rendimientos
        returns = np.diff(actual_values.flatten()) / actual_values[:-1].flatten()
        
        return {
            'signals': signals,
            'pred_changes': pred_changes,
            'actual_returns': returns
        }
    
    def calculate_risk_metrics(self,
                             actual_values: np.ndarray,
                             predictions: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas de riesgo basadas en las predicciones.
        """
        # Calcular errores
        errors = predictions.flatten() - actual_values.flatten()
        
        # Calcular métricas básicas
        mae = mean_absolute_error(actual_values, predictions)
        rmse = np.sqrt(mean_squared_error(actual_values, predictions))
        
        # Calcular VaR y CVaR
        var = np.percentile(errors, (1 - self.confidence_level) * 100)
        cvar = np.mean(errors[errors <= var])
        
        # Calcular volatilidad
        volatility = np.std(errors)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'var': var,
            'cvar': cvar,
            'volatility': volatility
        }
    
    def plot_trading_signals(self,
                           actual_values: np.ndarray,
                           predictions: np.ndarray,
                           signals: np.ndarray) -> go.Figure:
        """
        Visualiza las señales de trading junto con los valores reales y predicciones.
        """
        fig = make_subplots(rows=2, cols=1,
                           subplot_titles=('Precio USD/MXN y Señales',
                                         'Señales de Trading'))
        
        # Plotear precios y predicciones
        fig.add_trace(
            go.Scatter(y=actual_values.flatten(),
                      name='Valor Real',
                      line=dict(color='blue')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(y=predictions.flatten(),
                      name='Predicción',
                      line=dict(color='red')),
            row=1, col=1
        )
        
        # Plotear señales
        fig.add_trace(
            go.Scatter(y=signals,
                      name='Señales',
                      line=dict(color='green')),
            row=2, col=1
        )
        
        fig.update_layout(height=800,
                         title_text='Análisis de Trading USD/MXN',
                         showlegend=True)
        
        return fig
    
    def plot_risk_metrics(self,
                         risk_metrics: Dict[str, float]) -> go.Figure:
        """
        Visualiza las métricas de riesgo en un dashboard.
        """
        fig = go.Figure()
        
        # Crear gráfico de barras para métricas
        fig.add_trace(go.Bar(
            x=list(risk_metrics.keys()),
            y=list(risk_metrics.values()),
            text=[f'{value:.4f}' for value in risk_metrics.values()],
            textposition='auto',
        ))
        
        fig.update_layout(
            title='Métricas de Riesgo',
            xaxis_title='Métrica',
            yaxis_title='Valor',
            template='plotly_white'
        )
        
        return fig

class ForecastAnalyzer:
    """
    Clase para análisis detallado de las predicciones del tipo de cambio.
    """
    
    def __init__(self):
        pass
    
    def calculate_forecast_metrics(self,
                                 actual_values: np.ndarray,
                                 predictions: np.ndarray,
                                 dates: np.ndarray) -> Dict[str, pd.Series]:
        """
        Calcula métricas detalladas de las predicciones.
        """
        errors = predictions.flatten() - actual_values.flatten()
        
        metrics = pd.DataFrame({
            'actual': actual_values.flatten(),
            'predicted': predictions.flatten(),
            'error': errors,
            'error_pct': (errors / actual_values.flatten()) * 100
        }, index=dates)
        
        return metrics
    
    def plot_forecast_analysis(self,
                             metrics: pd.DataFrame) -> go.Figure:
        """
        Crea un dashboard completo del análisis de predicciones.
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Valores Reales vs Predicciones',
                          'Distribución de Errores',
                          'Error Porcentual en el Tiempo',
                          'Scatter Plot Predicción vs Real')
        )
        
        # Valores reales vs predicciones
        fig.add_trace(
            go.Scatter(y=metrics['actual'],
                      name='Real',
                      line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(y=metrics['predicted'],
                      name='Predicción',
                      line=dict(color='red')),
            row=1, col=1
        )
        
        # Distribución de errores
        fig.add_trace(
            go.Histogram(x=metrics['error'],
                        name='Distribución de Errores'),
            row=1, col=2
        )
        
        # Error porcentual en el tiempo
        fig.add_trace(
            go.Scatter(y=metrics['error_pct'],
                      name='Error %',
                      line=dict(color='green')),
            row=2, col=1
        )
        
        # Scatter plot
        fig.add_trace(
            go.Scatter(x=metrics['actual'],
                      y=metrics['predicted'],
                      mode='markers',
                      name='Predicción vs Real'),
            row=2, col=2
        )
        
        fig.update_layout(height=800,
                         showlegend=True,
                         title_text='Análisis Detallado de Predicciones')
        
        return fig