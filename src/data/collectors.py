# src/data/collectors.py
import os
from datetime import datetime, timedelta
import pandas as pd
import requests
import feedparser
from dotenv import load_dotenv
from typing import Dict, List, Optional

class MarketDataCollector:
    """Colector integrado de datos de mercado mexicano"""
    
    def __init__(self):
        load_dotenv()
        self.banxico_token = os.getenv('BANXICO_TOKEN')
        self.base_url = "https://yahoo-finance-api-xi.vercel.app"
        self.feeds = {
            'banxico': 'https://www.banxico.org.mx/informacion-para-la-prensa/comunicados/politica-monetaria/boletines/_feed/comunicados.xml',
            'el_economista': 'https://www.eleconomista.com.mx/rss/mercados',
            'expansion': 'https://expansion.mx/rss/mercados',
            'fed_minutas': 'https://www.federalreserve.gov/feeds/press_monetary.xml',  # Minutas directamente de la FED
            'reuters_fed': 'http://feeds.reuters.com/reuters/USFederalReserveNews',    # Noticias de la FED en Reuters
            'wsj_fed': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',               # Noticias de mercados del Wall Street Journal (WSJ)
            'bloomberg_economy': 'https://www.bloomberg.com/feed/podcast/bloomberg-surveillance'  # Actualizaciones económicas generales
        }

        
    def get_banxico_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        series_id = "SF43718"  # Serie para el tipo de cambio Fix
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{series_id}/datos/{start_date}/{end_date}"
        headers = {
            "Bmx-Token": self.banxico_token,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Error en la respuesta de Banxico. Status code: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return pd.DataFrame()
                
            data = response.json()
            if 'bmx' not in data or 'series' not in data['bmx'] or not data['bmx']['series']:
                print("La respuesta de Banxico no tiene el formato esperado")
                return pd.DataFrame()
                
            series_data = data['bmx']['series'][0]['datos']
            df = pd.DataFrame(series_data)
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
            df['dato'] = pd.to_numeric(df['dato'])
            df.rename(columns={'dato': 'usdmxn_fix'}, inplace=True)
            df.set_index('fecha', inplace=True)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {e}")
            return pd.DataFrame()
        except ValueError as e:
            print(f"Error procesando los datos: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error inesperado: {e}")
            return pd.DataFrame()
        
    def get_banxico_interest_rate(self, start_date: str, end_date: str) -> pd.DataFrame:
        series_id = "SF61745"  # Serie para la Tasa de Interés Objetivo
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{series_id}/datos/{start_date}/{end_date}"
        headers = {
            "Bmx-Token": self.banxico_token,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Error en la respuesta de Banxico. Status code: {response.status_code}")
                return pd.DataFrame()
                
            data = response.json()
            if 'bmx' not in data or 'series' not in data['bmx'] or not data['bmx']['series']:
                print("La respuesta de Banxico no tiene el formato esperado")
                return pd.DataFrame()
                
            series_data = data['bmx']['series'][0]['datos']
            df = pd.DataFrame(series_data)
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
            df['dato'] = pd.to_numeric(df['dato'])
            df.rename(columns={'dato': 'tasa_interes_banxico'}, inplace=True)
            df.set_index('fecha', inplace=True)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {e}")
            return pd.DataFrame()
        except ValueError as e:
            print(f"Error procesando los datos: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error inesperado: {e}")
            return pd.DataFrame()

    def get_yahoo_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        dfs = {}
        
        for ticker in tickers:
            url = f"{self.base_url}/history/{ticker}"
            params = {"start_date": start_date, "end_date": end_date}
            try:
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    print(f"Error obteniendo datos para {ticker}. Status code: {response.status_code}")
                    continue
                
                data = response.json()
                if data:
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.index = pd.to_datetime(df.index)
                    
                    # Verificar que las columnas requeridas estén presentes
                    if all(col in df.columns for col in required_columns):
                        dfs[ticker] = df
                        print(f"✓ Datos completos obtenidos para {ticker}")
                    else:
                        print(f"⚠ Datos incompletos para {ticker}. Columnas presentes: {df.columns.tolist()}")
                else:
                    print(f"No hay datos disponibles para {ticker}.")
            
            except requests.exceptions.RequestException as e:
                print(f"Error en la solicitud HTTP para {ticker}: {e}")
        
        if dfs:
            return pd.concat(dfs, axis=1)
        return pd.DataFrame()

    def get_rss_news(self) -> pd.DataFrame:
        """
        Obtiene y procesa noticias de feeds RSS, incluida la FED.
        """
        all_news = []
        
        for source, url in self.feeds.items():
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries:
                    # Obtener noticias y aplicar el análisis de sentimiento adecuado
                    sentiment_score = self._calculate_sentiment_fed(entry.title + " " + entry.summary) \
                        if source == 'fed_minutas' else self._calculate_basic_sentiment(entry.title + " " + entry.summary)
                    
                    news_item = {
                        'title': entry.title,
                        'date': datetime(*entry.published_parsed[:6]),
                        'summary': entry.summary,
                        'source': source,
                        'link': entry.link,
                        'sentiment_score': sentiment_score
                    }
                    all_news.append(news_item)
                    
            except Exception as e:
                print(f"Error procesando feed {source}: {e}")
                continue
        
        if all_news:
            df = pd.DataFrame(all_news)
            df.set_index('date', inplace=True)
            return df
        return pd.DataFrame()

    def _calculate_basic_sentiment(self, text: str) -> float:
        """
        Análisis de sentimiento básico en español utilizando palabras ponderadas.
        """
        # Diccionario de palabras positivas y sus pesos
        positive_words = {
            'sube': 1.0, 'aumenta': 1.2, 'crece': 1.1, 'positivo': 1.3, 'mejora': 1.0,
            'gana': 1.2, 'fortalece': 1.1, 'optimista': 1.3, 'beneficio': 1.5, 'favorable': 1.3,
            'expansión': 1.4, 'recuperación': 1.2, 'incremento': 1.1, 'rentable': 1.3, 'bonanza': 1.4
        }
        
        # Diccionario de palabras negativas y sus pesos
        negative_words = {
            'baja': -1.0, 'cae': -1.2, 'disminuye': -1.1, 'negativo': -1.3, 'pierde': -1.2,
            'preocupación': -1.1, 'riesgo': -1.3, 'débil': -1.2, 'deterioro': -1.5, 'adverso': -1.4,
            'recesión': -1.6, 'crisis': -1.5, 'pérdida': -1.3, 'incertidumbre': -1.1, 'contracción': -1.4
        }
        
        text = text.lower()
        
        # Calcular la puntuación de sentimiento ponderada
        positive_score = sum(weight for word, weight in positive_words.items() if word in text)
        negative_score = sum(weight for word, weight in negative_words.items() if word in text)
        
        # Calcular el puntaje total de sentimiento
        sentiment_score = (positive_score + negative_score) / (len(text.split()) + 1)
        
        return sentiment_score

    def _calculate_sentiment_fed(self, text: str) -> float:
        """
        Análisis de sentimiento para las minutas de la FED en inglés utilizando palabras ponderadas.
        """
        # Diccionario de palabras positivas y sus pesos en inglés
        positive_words_en = {
            'increase': 1.0, 'growth': 1.2, 'positive': 1.1, 'improve': 1.3, 'gain': 1.0,
            'strengthen': 1.2, 'optimistic': 1.3, 'benefit': 1.4, 'favorable': 1.2, 'expansion': 1.5,
            'recovery': 1.3, 'stability': 1.2, 'upturn': 1.4, 'profit': 1.2
        }
        
        # Diccionario de palabras negativas y sus pesos en inglés
        negative_words_en = {
            'decrease': -1.0, 'fall': -1.2, 'drop': -1.1, 'negative': -1.3, 'loss': -1.2,
            'concern': -1.1, 'risk': -1.3, 'weakness': -1.2, 'deterioration': -1.5, 'adverse': -1.4,
            'recession': -1.6, 'crisis': -1.5, 'uncertainty': -1.3, 'contraction': -1.4
        }
        
        text = text.lower()
        
        # Calcular la puntuación de sentimiento ponderada
        positive_score = sum(weight for word, weight in positive_words_en.items() if word in text)
        negative_score = sum(weight for word, weight in negative_words_en.items() if word in text)
        
        # Calcular el puntaje total de sentimiento
        sentiment_score = (positive_score + negative_score) / (len(text.split()) + 1)
        
        return sentiment_score

    def get_all_market_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        mx_tickers = ['GFNORTEO.MX', 'BSMX.MX', 'VOLARA.MX', 'AMXL.MX']
        return {
            'fx_rates': self.get_banxico_data(start_date, end_date),
            'stocks': self.get_yahoo_data(mx_tickers, start_date, end_date),
            'news': self.get_rss_news()
        }
