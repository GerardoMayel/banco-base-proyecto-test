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
            'expansion': 'https://expansion.mx/rss/mercados'
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
        all_news = []
        for source, url in self.feeds.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    news_item = {
                        'title': entry.title,
                        'date': datetime(*entry.published_parsed[:6]),
                        'summary': entry.summary,
                        'source': source,
                        'link': entry.link,
                        'sentiment_score': self._calculate_basic_sentiment(
                            f"{entry.title} {entry.summary}"
                        )
                    }
                    all_news.append(news_item)
            except Exception as e:
                print(f"Error procesando feed {source}: {e}")
        
        if all_news:
            df = pd.DataFrame(all_news)
            df.set_index('date', inplace=True)
            return df
        return pd.DataFrame()

    def _calculate_basic_sentiment(self, text: str) -> float:
        positive_words = [
            'sube', 'aumenta', 'crece', 'positivo', 'mejora', 'gana',
            'fortalece', 'optimista', 'beneficio', 'favorable'
        ]
        negative_words = [
            'baja', 'cae', 'disminuye', 'negativo', 'pierde', 'riesgo',
            'débil', 'preocupación', 'deterioro', 'adverso'
        ]
        
        text = text.lower()
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        return (positive_score - negative_score) / (positive_score + negative_score + 1)

    def get_all_market_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        mx_tickers = ['GFNORTEO.MX', 'BSMX.MX', 'VOLARA.MX', 'AMXL.MX']
        return {
            'fx_rates': self.get_banxico_data(start_date, end_date),
            'stocks': self.get_yahoo_data(mx_tickers, start_date, end_date),
            'news': self.get_rss_news()
        }
