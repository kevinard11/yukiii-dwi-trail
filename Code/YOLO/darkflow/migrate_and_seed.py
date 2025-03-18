from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import requests
from io import BytesIO
import psycopg2
from psycopg2.extras import RealDictCursor

# Konfigurasi database
DB_CONFIG = {
    'dbname': 'stl',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# OpenWeather API Configuration
API_KEY = "4214fafba3bc355f824d5de9edbd3515"  # Ganti dengan API Key Anda
CITY = "Bandung"

# Inisialisasi SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Definisi tabel berdasarkan ERD
class TrafficLight(Base):
    __tablename__ = 'traffic_light'
    id = Column(Integer, primary_key=True, autoincrement=True)
    green_light = Column(Integer, nullable=False)
    yellow_light = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, autoincrement=True)
    car_count = Column(Integer, nullable=False)
    bus_count = Column(Integer, nullable=False)
    truck_count = Column(Integer, nullable=False)
    bike_count = Column(Integer, nullable=False)
    rickshaw_count = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

class Weather(Base):
    __tablename__ = 'weather'
    id = Column(Integer, primary_key=True, autoincrement=True)
    main = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    description = Column(String, nullable=False)
    temp = Column(Float, nullable=False)
    pressure = Column(Integer, nullable=False)
    humidity = Column(Integer, nullable=False)
    wind_speed = Column(Float, nullable=False)
    city = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)

# Migrasi: Membuat tabel
def migrate():
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

# Memasukkan data awal
def seed_data():
    # Data untuk tabel traffic_light

    get_openweather()
    get_atcsspdago()
    print("Initial data inserted successfully.")

# Jalankan fungsi untuk mengisi data awal
def get_openweather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        main = data["weather"][0]["main"]
        icon_code = data["weather"][0]["icon"]
        description = data["weather"][0]["description"]
        temp = data['main']['temp']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        city = data['name']
        lon = data['coord']['lon']
        lat = data['coord']['lat']

        insert_openweather_data(main, icon_code, description, temp, pressure, humidity, wind_speed, city, lon, lat)

    else:
        print("Gagal mengambil data cuaca")

def get_atcsspdago():
    url = f"https://c7f7d465-72e5-46ba-a18d-0a78d95a0128.mock.pstmn.io/atcs-spdago"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        green_light = data["green_light"]
        yellow_light = data["yellow_light"]

        insert_atcsspdago_data(green_light, yellow_light)

    else:
        print("Gagal mengambil data atcs")

def insert_openweather_data(main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat):
    try:
        # Koneksi ke database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query SQL untuk menyisipkan data
        query = """
            INSERT INTO weather (main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        """
        values = (main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat)

        # Eksekusi query
        cursor.execute(query, values)
        connection.commit()

        print(f"Weather data inserted successfully: {values}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_atcsspdago_data(green_light, yellow_light):
    try:
        # Koneksi ke database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query SQL untuk menyisipkan data
        query = """
            INSERT INTO traffic_light (green_light, yellow_light, created_date)
            VALUES (%s, %s, now())
        """
        values = (green_light, yellow_light)

        # Eksekusi query
        cursor.execute(query, values)
        connection.commit()

        print(f"Traffic light data inserted successfully: {values}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

migrate()
seed_data()

