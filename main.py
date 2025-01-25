from dash import Dash, html, Input, Output, dcc, callback
import dash_bootstrap_components as dbc
import requests
import dbPool
from analysers import DOGE
from sqlalchemy import create_engine, Column, String, Integer, Float, Text
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import os


load_dotenv(".api")
DOGE_PRICE = os.getenv("DOGE")
dbPool.connect()
Base = declarative_base()

# Create database if not exist
if not database_exists(dbPool.get_engine().url):
    create_database(dbPool.get_engine().url)

class Price(Base):
    __tablename__ = "price"
    id = Column("id", Integer, primary_key=True, autoincrement="auto")
    title = Column("title", Text)
    description = Column("description", Text)
    last_update_date = Column("last_update_date", String(30))
    price = Column("price", Float(20))

    def __init__(self, id, title, description, last_update_date, price):
        self.id = id
        self.title = title
        self.description = description
        self.last_update_date = last_update_date
        self.price = price

    def __repr__(self):
        return f"({self.id}) ({self.title}) ({self.description}) ({self.last_update_date}) ({self.price})"

Base.metadata.create_all(bind=dbPool.get_engine())

app = Dash(__name__, assets_folder="./assets", external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout com Bootstrap
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1("Dogecoin Price Tracker", className="text-center"), width=12)
        ),
        html.Div(
            className="d-flex align-items-center justify-content-center rounded bg-light",
            children=[
                dbc.Container(
                    class_name="container",
                    children=[
                        
                        dbc.Row(
                            className="row",
                            children=[
                                dbc.Card(dbc.CardBody([dbc.Col(html.H4(id='analysis-display'), className="card-title", width=6)])),
                                dbc.Card(dbc.CardBody([dbc.Col(html.H6(id='price-display'), className="card-title", width=6)])),
                            ]
                        ),
                        
                        html.Div(
                            id="flex-div",
                            children=[
                                
                                dbc.Card(
                                    id="info-cards",
                                    style={"margin-left":"-10px"},
                                    children=[
                                        dbc.CardBody(
                                        [
                                            html.H4('Informações de Dogecoin', className="card-title"),
                                            html.P('Dogecoin é uma criptomoeda peer-to-peer de código aberto criada inicialmente como uma "moeda piada" em 06 de dezembro de 2013, desenvolvendo rapidamente sua própria comunidade on-line, alcançando uma capitalização de US$ 60 milhões em janeiro de 2014', className="card-text"),
                                        ]),
                                    ]
                                ),
                                dbc.Card(
                                    id="info-cards",
                                    style={"margin-left":"-10px"},
                                    children=[
                                        dbc.CardBody(
                                        [
                                            html.H4('Website', className="card-title"),
                                            html.A(href="https://dogecoin.com/", children=['Dogecoin WebSite'], className="card-text"),
                                        ]),
                                    ]
                                )
                        ]),
                    ]
                ),
                html.Div(
                    className="rounded bg-light d-grid gap-3",
                    children=[
                        html.Div(
                            html.Img(className="img-fluid img-thumbnail border", src="https://seeklogo.com/images/D/dogecoin-doge-logo-2A9D141D45-seeklogo.com.png")
                        ),
                        html.Div(
                            html.Img(className="img-fluid img-thumbnail border", id="shiba-img", src="https://cdn.pixabay.com/photo/2021/05/29/07/05/shiba-6292659_960_720.jpg")
                        )
                    ]
                )
            ]
        ),
        dcc.Interval(
            id='interval',
            interval=10 * 1000,  # Atualiza a cada 10 segundos
            n_intervals=0
        ),
    ],
    fluid=True,  # Usando layout fluido (ajustável)
)


@app.callback(
    [Output('price-display', 'children'), Output('analysis-display', 'children')],
    [Input('interval', 'n_intervals')]
)
def update_data(_):
    data = GetData(DOGE_PRICE)
    if data and 'Price' in data:
        current_price = data['Price']
        if isinstance(data, list):
            new_data = pd.DataFrame(data)
        elif isinstance(data, dict):
            new_data = pd.DataFrame([data])

        new_data = new_data.rename(columns={
            'Symbol': 'title',
            'Name': 'description',
            'Price': 'price',
            'Time': 'last_update_date',
        })
        
        new_data = new_data.drop(columns=['Address'])
        new_data = new_data.drop(columns=['Blockchain'])
        new_data = new_data.drop(columns=['PriceYesterday'])
        new_data = new_data.drop(columns=['VolumeYesterdayUSD'])
        new_data = new_data.drop(columns=['Source'])
        new_data = new_data.drop(columns=['Signature'])
        StoreData(new_data)
        
        analysis = DOGE.analyse(GetDBPriceHistorical())
        
        return f"Preço Atual: {current_price:.4f}", analysis

    return "Falha ao buscar preço", "Sem análise disponível"



def GetData(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        print
        return data
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

    
def StoreData(new_data):
    Session = sessionmaker(bind=dbPool.get_engine())
    session = Session()
    last_record = session.query(Price).order_by(Price.id.desc()).first()
    
    if last_record:
        last_record_dict = last_record.__dict__
        last_record_dict.pop('_sa_instance_state', None)
        db_df = pd.DataFrame([last_record_dict])
    else:
        db_df = pd.DataFrame()
        price = Price(
            id=None, 
            title = new_data['title'].iloc[0],
            description = new_data['description'].iloc[0],
            last_update_date = new_data['last_update_date'].iloc[0],
            price = new_data['price'].iloc[0],
        )
        session.add(price)
        session.commit()
    
    if not db_df.empty:
        if db_df.iloc[0]['last_update_date']  != new_data['last_update_date'].iloc[0]:     
            price = Price(
                id=None, 
                title = new_data['title'].iloc[0],
                description = new_data['description'].iloc[0],
                last_update_date = new_data['last_update_date'].iloc[0],
                price = new_data['price'].iloc[0],
            )
            session.add(price)
            session.commit()
        
    session.close()
    return db_df

def GetDBPriceHistorical():
    Session = sessionmaker(bind=dbPool.get_engine())
    session = Session()
    try:
        # Fetch data from the database
        database = session.query(Price).order_by(Price.id.asc()).all()
        
        if not database:
            print("Aviso: Nenhum dado encontrado na tabela Price.")
            return pd.DataFrame()  # Retorna um DataFrame vazio
        
        # Convert database objects to dictionaries
        data = [item.__dict__ for item in database]
        
        # Remove a chave '_sa_instance_state' gerada pelo SQLAlchemy
        for item in data:
            item.pop('_sa_instance_state', None)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Validar colunas esperadas
        if 'price' not in df.columns or 'id' not in df.columns:
            raise ValueError("Dados retornados não possuem as colunas esperadas ('price', 'id', etc.).")
        
        # Garantir que a coluna 'price' é numérica
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Remover valores NaN
        df = df.dropna(subset=['price'])  # Remover linhas com 'NaN' na coluna 'price'
        
    except Exception as e:
        print(f"Erro ao recuperar dados do banco de dados: {e}")
        df = pd.DataFrame()
    finally:
        session.close()
        return df




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port="9990")