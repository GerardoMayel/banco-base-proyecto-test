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
        # Handler para archivo
        logging.FileHandler(log_file, mode='w'),  # 'w' para sobrescribir
        # Handler para consola
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

from src.data import MarketDataCollector

def test_banxico_data():
    """Test específico para datos de Banxico"""
    logger.info("\n=== Iniciando Prueba de Banxico ===")
    collector = MarketDataCollector()
    
    # Definir período de prueba
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    logger.info(f"Período de prueba: {start_date} a {end_date}")
    
    try:
        # Obtener datos
        logger.info("Obteniendo datos de Banxico...")
        fx_data = collector.get_banxico_data(start_date, end_date)
        
        if not fx_data.empty:
            logger.info("✓ Datos obtenidos exitosamente")
            logger.info(f"Total de registros: {len(fx_data)}")
            
            # Validar estructura
            expected_columns = ['usdmxn_fix']
            actual_columns = fx_data.columns.tolist()
            
            if all(col in actual_columns for col in expected_columns):
                logger.info("✓ Estructura de datos correcta")
            else:
                logger.error(f"✗ Columnas incorrectas. Esperadas: {expected_columns}, Obtenidas: {actual_columns}")
            
            # Mostrar datos de muestra
            logger.info("\nMuestra de datos:")
            logger.info(f"\n{fx_data.head(3)}")
            
            # Validar tipos de datos
            logger.info("\nTipos de datos:")
            logger.info(f"\n{fx_data.dtypes}")
            
            # Validar rango de fechas
            fecha_inicial = fx_data.index.min().strftime('%Y-%m-%d')
            fecha_final = fx_data.index.max().strftime('%Y-%m-%d')
            logger.info("\nRango de fechas:")
            logger.info(f"Primera fecha: {fecha_inicial}")
            logger.info(f"Última fecha: {fecha_final}")
            
            # Estadísticas básicas
            logger.info("\nEstadísticas:")
            logger.info(f"Valor mínimo: {fx_data['usdmxn_fix'].min():.4f}")
            logger.info(f"Valor máximo: {fx_data['usdmxn_fix'].max():.4f}")
            logger.info(f"Valor promedio: {fx_data['usdmxn_fix'].mean():.4f}")
            
            # Verificar valores nulos
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
    
    try:
        stocks = collector.get_yahoo_data(['GFNORTEO.MX'], start_date, end_date)
        if not stocks.empty:
            logger.info("✓ Datos obtenidos correctamente")
            logger.info(f"Total de registros: {len(stocks)}")
            logger.info("\nMuestra de datos:")
            logger.info(f"\n{stocks.head(2)}")
            
            # Validar columnas esperadas
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if all(col in stocks.columns.get_level_values(1) for col in expected_columns):
                logger.info("✓ Estructura de datos correcta")
            else:
                logger.warning("⚠ Algunas columnas esperadas no están presentes")
            
            # Verificar valores nulos
            nulos = stocks.isnull().sum().sum()
            if nulos == 0:
                logger.info("✓ No hay valores nulos")
            else:
                logger.warning(f"⚠ Se encontraron {nulos} valores nulos")
        else:
            logger.warning("⚠ No se obtuvieron datos de Yahoo Finance")
    except Exception as e:
        logger.error(f"Error en Yahoo Finance: {str(e)}")

def test_rss_news():
    """Test específico para RSS News"""
    logger.info("\n=== Iniciando Prueba de RSS ===")
    collector = MarketDataCollector()
    
    try:
        news = collector.get_rss_news()
        if not news.empty:
            logger.info("✓ Noticias obtenidas correctamente")
            logger.info(f"Total de noticias: {len(news)}")
            
            # Validar estructura
            expected_columns = ['title', 'summary', 'source', 'link', 'sentiment_score']
            if all(col in news.columns for col in expected_columns):
                logger.info("✓ Estructura de datos correcta")
            else:
                logger.warning("⚠ Faltan algunas columnas esperadas")
            
            logger.info("\nÚltimas noticias:")
            logger.info(f"\n{news['title'].head(3)}")
            
            # Verificar scores de sentimiento
            logger.info("\nEstadísticas de sentimiento:")
            logger.info(f"Sentimiento promedio: {news['sentiment_score'].mean():.3f}")
            logger.info(f"Sentimiento máximo: {news['sentiment_score'].max():.3f}")
            logger.info(f"Sentimiento mínimo: {news['sentiment_score'].min():.3f}")
        else:
            logger.warning("⚠ No se obtuvieron noticias")
    except Exception as e:
        logger.error(f"Error en RSS: {str(e)}")

def test_collector():
    """Test completo del collector"""
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