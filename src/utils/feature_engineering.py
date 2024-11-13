# src/utils/feature_engineering.py

import numpy as np
import pandas as pd
from typing import Union, List, Dict
from sklearn.preprocessing import StandardScaler

class FeatureEngineer:
    """
    Clase para crear características (features) técnicas y estadísticas para el análisis 
    del tipo de cambio USD/MXN.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def calculate_technical_indicators(self, df: pd.DataFrame, 
                                    price_col: str = 'usdmxn_fix',
                                    periods: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """
        Calcula indicadores técnicos básicos para una serie de precios.
        
        Args:
            df: DataFrame con los datos
            price_col: Nombre de la columna de precios
            periods: Lista de períodos para los indicadores
            
        Returns:
            DataFrame con los indicadores técnicos calculados
        """
        result = df.copy()
        
        # Retornos logarítmicos
        result['returns'] = np.log(result[price_col] / result[price_col].shift(1))
        
        for period in periods:
            # Medias móviles
            result[f'sma_{period}'] = result[price_col].rolling(window=period).mean()
            
            # Volatilidad histórica
            result[f'volatility_{period}'] = result['returns'].rolling(window=period).std() * np.sqrt(252)
            
            # RSI
            delta = result[price_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            result[f'rsi_{period}'] = 100 - (100 / (1 + rs))
            
            # Momentum
            result[f'momentum_{period}'] = result[price_col] / result[price_col].shift(period)
        
        return result
    
    def calculate_statistical_features(self, df: pd.DataFrame, 
                                    target_col: str = 'returns',
                                    windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """
        Calcula características estadísticas para una serie temporal.
        
        Args:
            df: DataFrame con los datos
            target_col: Columna objetivo para los cálculos
            windows: Lista de ventanas temporales
            
        Returns:
            DataFrame con las características estadísticas
        """
        result = df.copy()
        
        for window in windows:
            # Estadísticas de ventana móvil
            result[f'mean_{window}'] = result[target_col].rolling(window=window).mean()
            result[f'std_{window}'] = result[target_col].rolling(window=window).std()
            result[f'skew_{window}'] = result[target_col].rolling(window=window).skew()
            result[f'kurt_{window}'] = result[target_col].rolling(window=window).kurt()
            
        return result
    
    def process_sentiment_features(self, df: pd.DataFrame, 
                                 sentiment_col: str = 'sentiment_score') -> pd.DataFrame:
        """
        Procesa y agrega características basadas en sentimiento.
        
        Args:
            df: DataFrame con scores de sentimiento
            sentiment_col: Nombre de la columna de sentimiento
            
        Returns:
            DataFrame con características de sentimiento procesadas
        """
        result = df.copy()
        
        # Normalizar scores de sentimiento
        result[f'{sentiment_col}_normalized'] = self.scaler.fit_transform(
            result[sentiment_col].values.reshape(-1, 1)
        )
        
        # Categorizar sentimiento
        result['sentiment_category'] = pd.cut(
            result[sentiment_col],
            bins=[-float('inf'), -0.3, 0.3, float('inf')],
            labels=['negative', 'neutral', 'positive']
        )
        
        # Agregar indicadores de sentimiento extremo
        result['extreme_sentiment'] = result[sentiment_col].abs() > result[sentiment_col].std() * 2
        
        return result