import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import ta
from scipy import stats
from statsmodels.tsa.stattools import adfuller

class EnhancedMarketProcessor:
    """
    Procesador avanzado de datos de mercado con énfasis en el mercado mexicano.
    Incluye análisis estadístico, técnico y características específicas del mercado MXN.
    """
    
    def __init__(self):
        self.required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        self._validate_requirements()
        
    def _validate_requirements(self):
        """Valida que todas las dependencias necesarias estén instaladas"""
        try:
            import ta
            import scipy
            import statsmodels
        except ImportError as e:
            raise ImportError(f"Falta dependencia requerida: {str(e)}")

    def process_market_data(self, df: pd.DataFrame, 
                            calculate_stats: bool = True,
                            include_technicals: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Procesa datos de mercado aplicando análisis completo
        
        Args:
            df: DataFrame con datos OHLCV (Open, High, Low, Close, Volume)
            calculate_stats: Si se calculan estadísticas
            include_technicals: Si se incluyen indicadores técnicos
            
        Returns:
            Tuple[DataFrame procesado, Dict con estadísticas]
        """
        # Validación inicial para asegurar que todas las columnas requeridas estén presentes
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Columnas faltantes en el DataFrame: {missing_cols}")
        
        # Copia para no modificar el DataFrame original
        processed_df = df.copy()
        
        # 1. Cálculos básicos
        processed_df = self.calculate_basic_metrics(processed_df)
        
        # 2. Análisis estadístico
        stats_dict = {}
        if calculate_stats:
            stats_dict = self.calculate_statistical_metrics(processed_df)
            
        # 3. Indicadores técnicos
        if include_technicals:
            processed_df = self.add_technical_indicators(processed_df)
            
        # 4. Características específicas del mercado mexicano
        processed_df = self.add_mexican_market_features(processed_df)
        
        return processed_df, stats_dict
        
    def calculate_basic_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula métricas básicas de mercado"""
        # Retornos logarítmicos
        df['returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['returns_std'] = df['returns'].rolling(window=20).std()
        
        # Rango diario y brechas
        df['daily_range'] = df['High'] - df['Low']
        df['gap'] = df['Open'] - df['Close'].shift(1)
        
        # Volatilidad anualizada usando ventana de 20 días
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        return df
        
    def calculate_statistical_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calcula métricas estadísticas avanzadas
        Implementa conceptos de análisis financiero y de series de tiempo
        """
        returns = df['returns'].dropna()
        
        # Test de normalidad
        normality_test = stats.normaltest(returns)
        
        # Test de estacionariedad (ADF)
        adf_test = adfuller(returns)
        
        # Estadísticas de distribución
        stats_dict = {
            'normality': {
                'statistic': normality_test.statistic,
                'p_value': normality_test.pvalue,
                'is_normal': normality_test.pvalue > 0.05
            },
            'stationarity': {
                'adf_statistic': adf_test[0],
                'p_value': adf_test[1],
                'is_stationary': adf_test[1] < 0.05
            },
            'distribution': {
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'jarque_bera': stats.jarque_bera(returns)
            }
        }
        
        return stats_dict
        
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega indicadores técnicos avanzados usando la librería `ta`"""
        # Tendencia
        df['sma_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['ema_20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['adx'] = ta.trend.adx(df['High'], df['Low'], df['Close'])
        
        # Volatilidad
        df['bb_high'] = ta.volatility.bollinger_hband(df['Close'])
        df['bb_low'] = ta.volatility.bollinger_lband(df['Close'])
        df['atr'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
        
        # Momentum
        df['rsi'] = ta.momentum.rsi(df['Close'])
        df['macd'] = ta.trend.macd_diff(df['Close'])
        df['stoch'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
        
        # Volumen
        df['volume_sma'] = ta.volume.volume_weighted_average_price(
            df['High'], df['Low'], df['Close'], df['Volume']
        )
        
        return df
        
    def add_mexican_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega características específicas del mercado mexicano
        Basado en patrones observados en el mercado MXN
        """
        # Horarios específicos del mercado mexicano
        df['session_time'] = df.index.time
        df['is_mexico_market_hours'] = (
            (df['session_time'] >= pd.Timestamp('08:30').time()) &
            (df['session_time'] <= pd.Timestamp('15:00').time())
        )
        
        # Períodos de alta volatilidad (apertura NY, cierre MX)
        df['is_high_impact_period'] = (
            (df['session_time'] >= pd.Timestamp('08:30').time()) &
            (df['session_time'] <= pd.Timestamp('09:30').time()) |
            (df['session_time'] >= pd.Timestamp('14:00').time()) &
            (df['session_time'] <= pd.Timestamp('15:00').time())
        )
        
        return df
