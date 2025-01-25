from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

engine = None


def connect(mariadb=None):
    
    """
    Args:
        mariadb (Bool): True if is mariadb DB, if isn't (False), connects as MySQL DB.
    """
    
    global engine
    load_dotenv('.env')
    host = os.getenv('HOST')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    database = os.getenv('DATABASE')


    # Establishes the connection to the server
    if mariadb is False:
        engine = create_engine(
                            f"mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8mb4",
                            pool_size=10,
                            max_overflow=15,
                            pool_timeout=60,
                            pool_recycle=18)
    elif mariadb is True:
        engine = create_engine(
                            f"mariadb+mariadbconnector://{user}:{password}@{host}/{database}?charset=utf8mb4",
                            pool_size=10,
                            max_overflow=15,
                            pool_timeout=60,
                            pool_recycle=18)
    else:
        print("\033[1;34mSet the dbPool.connect() mariadb var to True if is mariaDB, if is a MySQL set to False")
        engine = create_engine(
                            f"mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8mb4",
                            pool_size=10,
                            max_overflow=15,
                            pool_timeout=60,
                            pool_recycle=18)
        
def get_engine():
    global engine
    return engine