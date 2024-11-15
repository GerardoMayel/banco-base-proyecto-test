"""
Tests for the market data collector functionality.
"""
import sys
import os
from datetime import datetime, timedelta
import logging
from pathlib import Path
import pandas as pd

# Configurar logging
def setup_logging():
    # Crear directorio logs si no existe
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configurar el logging
    log_file = log_dir / 'test_execution.log'
    
    # Configurar handlers
    handlers = [
        logging.FileHandler(log_file, mode='w'),  # 'w' para sobrescribir
        logging.StreamHandler(sys.stdout)
    ]
    
    # Configurar formato
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.collectors import MarketDataCollector

def test_banxico_data():
    """Test específico para datos de Banxico"""
    logger.info("\n=== Iniciando Prueba de Banxico ===")
    collector = MarketDataCollector()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    logger.info(f"Período de prueba: {start_date} a {end_date}")
    
    try:
        logger.info("Obteniendo datos de Banxico...")
        fx_data = collector.get_banxico_data(start_date, end_date)
        
        if not fx_data.empty:
            logger.info("✓ Datos obtenidos exitosamente")
            logger.info(f"Total de registros: {len(fx_data)}")
            
            expected_columns = ['usdmxn_fix']
            actual_columns = fx_data.columns.tolist()
            
            if all(col in actual_columns for col in expected_columns):
                logger.info("✓ Estructura de datos correcta")
            else:
                logger.error(f"✗ Columnas incorrectas. Esperadas: {expected_columns}, Obtenidas: {actual_columns}")
            
            logger.info("\nMuestra de datos:")
            logger.info(f"\n{fx_data.head(3)}")
            logger.info("\nTipos de datos:")
            logger.info(f"\n{fx_data.dtypes}")
            
            fecha_inicial = fx_data.index.min().strftime('%Y-%m-%d')
            fecha_final = fx_data.index.max().strftime('%Y-%m-%d')
            logger.info("\nRango de fechas:")
            logger.info(f"Primera fecha: {fecha_inicial}")
            logger.info(f"Última fecha: {fecha_final}")
            
            logger.info("\nEstadísticas:")
            logger.info(f"Valor mínimo: {fx_data['usdmxn_fix'].min():.4f}")
            logger.info(f"Valor máximo: {fx_data['usdmxn_fix'].max():.4f}")
            logger.info(f"Valor promedio: {fx_data['usdmxn_fix'].mean():.4f}")
            
            nulos = fx_data.isnull().sum()
            if nulos.sum() == 0:
                logger.info("✓ No hay valores nulos")
            else:
                logger.warning(f"⚠ Valores nulos encontrados: {nulos}")
        else:
            logger.error("✗ No se obtuvieron datos de Banxico")
            
    except Exception as e:
        logger.error(f"✗ Error en prueba de Banxico: {str(e)}")
        raise

def test_yahoo_finance():
    """Test específico para Yahoo Finance"""
    logger.info("\n=== Iniciando Prueba de Yahoo Finance ===")
    collector = MarketDataCollector()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Incluir el tipo de cambio USD/MXN junto con otros tickers
    tickers = ['GFNORTEO.MX', 'VOLARA.MX', 'MXNUSD=X']
    try:
        stocks = collector.get_yahoo_data(tickers, start_date, end_date)
        
        if not stocks.empty:
            logger.info("✓ Datos obtenidos correctamente")
            logger.info(f"Total de registros: {len(stocks)}")
            logger.info("\nMuestra de datos:")
            logger.info(f"\n{stocks.head(2)}")
            
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns_tickers = [
                ticker for ticker in tickers if not all((ticker, col) in stocks.columns for col in expected_columns)
            ]
            
            if missing_columns_tickers:
                logger.warning(f"⚠ Algunas columnas esperadas no están presentes en los tickers: {missing_columns_tickers}")
            else:
                logger.info("✓ Estructura de datos correcta para todos los tickers")
            
            nulos = stocks.isnull().sum().sum()
            if nulos == 0:
                logger.info("✓ No hay valores nulos")
            else:
                logger.warning(f"⚠ Se encontraron {nulos} valores nulos")
        else:
            logger.warning("⚠ No se obtuvieron datos de Yahoo Finance para los tickers especificados.")
    except Exception as e:
        logger.error(f"Error en Yahoo Finance: {str(e)}")



import logging
from datetime import datetime, timedelta

def test_rss_news():
    """Test específico para RSS News incluyendo noticias de la FED."""
    logger.info("\n=== Iniciando Prueba de RSS ===")
    collector = MarketDataCollector()
    
    try:
        news = collector.get_rss_news()
        if not news.empty:
            logger.info("✓ Noticias obtenidas correctamente")
            logger.info(f"Total de noticias: {len(news)}")
            
            expected_columns = ['title', 'summary', 'source', 'link', 'sentiment_score']
            if all(col in news.columns for col in expected_columns):
                logger.info("✓ Estructura de datos correcta")
            else:
                logger.warning("⚠ Faltan algunas columnas esperadas")
            
            logger.info("\nÚltimas noticias:")
            logger.info(f"\n{news['title'].head(3)}")
            
            # Verificar estadísticas de sentimiento general
            logger.info("\nEstadísticas de sentimiento general:")
            logger.info(f"Sentimiento promedio: {news['sentiment_score'].mean():.3f}")
            logger.info(f"Sentimiento máximo: {news['sentiment_score'].max():.3f}")
            logger.info(f"Sentimiento mínimo: {news['sentiment_score'].min():.3f}")
            
            # Estadísticas de sentimiento específico para las noticias de la FED
            fed_news = news[news['source'] == 'fed_minutas']
            if not fed_news.empty:
                logger.info("\nEstadísticas de sentimiento para noticias de la FED:")
                logger.info(f"Sentimiento promedio FED: {fed_news['sentiment_score'].mean():.3f}")
                logger.info(f"Sentimiento máximo FED: {fed_news['sentiment_score'].max():.3f}")
                logger.info(f"Sentimiento mínimo FED: {fed_news['sentiment_score'].min():.3f}")
            else:
                logger.warning("⚠ No se obtuvieron noticias de la FED")

        else:
            logger.warning("⚠ No se obtuvieron noticias")
    except Exception as e:
        logger.error(f"Error en RSS: {str(e)}")

def test_collector():
    """Test completo del collector incluyendo datos de la FED."""
    logger.info("\n=== Iniciando Test Completo del Collector ===")
    collector = MarketDataCollector()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    logger.info(f"Periodo de prueba: {start_date} a {end_date}")
    
    try:
        logger.info("Obteniendo todos los datos del mercado...")
        market_data = collector.get_all_market_data(start_date, end_date)
        
        for key, df in market_data.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"Validando datos de {key}:")
            if not df.empty:
                logger.info(f"✓ Datos obtenidos para {key}")
                logger.info(f"Dimensiones: {df.shape}")
                logger.info(f"Registros: {len(df)}")
                
                # Validación específica para noticias de la FED
                if key == 'news' and 'fed_minutas' in df['source'].values:
                    fed_news = df[df['source'] == 'fed_minutas']
                    logger.info(f"✓ Noticias de la FED obtenidas: {len(fed_news)}")
                else:
                    logger.warning("⚠ No se obtuvieron noticias de la FED en este conjunto de datos.")
            else:
                logger.warning(f"⚠ No se obtuvieron datos para {key}")
    except Exception as e:
        logger.error(f"Error en collector principal: {str(e)}")

if __name__ == "__main__":
    logger.info(f"\nIniciando suite de pruebas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_banxico_data()
        test_yahoo_finance()
        test_rss_news()
        test_collector()
        logger.info("\n✓ Todas las pruebas completadas")
    except Exception as e:
        logger.error(f"\n✗ Error en las pruebas: {str(e)}")
    
    logger.info(f"\nPruebas finalizadas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

