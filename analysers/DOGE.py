import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from datetime import datetime

def analyse(price_history):
    df_h = price_history
    df = pd.DataFrame()

    # Verificar se a coluna 'price' existe e se o DataFrame não está vazio
    if not df_h.empty and 'price' in df_h.columns:
        print("Columns in DataFrame:", df_h.columns)
        
        # Calcular indicadores técnicos
        # RSI
        rsi_indicator = RSIIndicator(close=df_h['price'], window=14)
        df['RSI'] = rsi_indicator.rsi()

        # MACD
        macd_indicator = MACD(close=df_h['price'])
        df['MACD'] = macd_indicator.macd()
        df['Signal_Line'] = macd_indicator.macd_signal()

        # Bandas de Bollinger
        bb_indicator = BollingerBands(close=df_h['price'], window=20, window_dev=2)
        df['BB_High'] = bb_indicator.bollinger_hband()
        df['BB_Low'] = bb_indicator.bollinger_lband()

        # Determinar sinal baseado em regras simples
        def determine_signal(row):
            # Verificar se as colunas necessárias estão presentes
            if pd.isna(row['RSI']) or pd.isna(row['price']) or pd.isna(row['BB_Low']) or pd.isna(row['BB_High']):
                return 'Erro'  # Caso algum valor seja inválido
            if row['RSI'] < 30 and row['price'] < row['BB_Low']:
                return 'Comprar'
            elif row['RSI'] > 70 and row['price'] > row['BB_High']:
                return 'Vender'
            elif row['MACD'] > row['Signal_Line']:
                return 'Comprar'
            elif row['MACD'] < row['Signal_Line']:
                return 'Vender'
            else:
                return 'Neutro'

        df['Signal'] = df.apply(determine_signal, axis=1)

        # Última análise
        latest_data = df.iloc[-1]
        print("Últimos Dados:")
        print(latest_data.to_string() + "\n")  # Conversão para string para visualização

        # Retornar o sinal final com base na última análise
        if latest_data['Signal'] == 'Comprar':
            print("Indicação: O preço do DOGE tem potencial de subida com base nos indicadores técnicos.\n")
            return "Indicação: O preço do DOGE tem potencial de subida com base nos indicadores técnicos.\nBUY!"
        elif latest_data['Signal'] == 'Vender':
            print("Indicação: O preço do DOGE pode cair com base nos indicadores técnicos.\n")
            return "Indicação: O preço do DOGE pode cair com base nos indicadores técnicos.\nSELL!"
        else:
            print("Indicação: Nenhuma tendência clara detectada.\n")
            return "Indicação: Nenhuma tendência clara detectada.\nKEEP!"
    else:
        print("Erro: O DataFrame está vazio ou não contém a coluna 'price'.")
        return "Erro: O DataFrame está vazio ou não contém a coluna 'price'."
