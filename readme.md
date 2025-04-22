# Info

Study case: simpang dago kota bandung

---

### Prerequisites

1. [Python 3.7](https://www.python.org/downloads/release/python-370/)
2. [Microsoft Visual C++ build tools](http://go.microsoft.com/fwlink/?LinkId=691126&fixForIE=.exe.) (For Windows only)

---

### Installation

- Clone the Repository
-  Download the weights file from [here](https://drive.google.com/file/d/1flTehMwmGg-PMEeQCsDS2VWRLGzV6Wdo/view?usp=sharing) and place it in the Dwi-Trail/Code/YOLO/darkflow/bin directory
- Install the required packages

```sh
# On the terminal, move into Dwi-Trail/Code/YOLO/darkflow directory
$ cd Dwi-Trail/Code/YOLO/darkflow
$ pip install -r requirements.txt
$ python setup.py build_ext --inplace
```

- Step IV: Create docker

```sh
# To run create database with docker
$ docker-compose up -d
```

- Step IV: Run the code

```sh
# To run create table and seed data traffic_light and weather
$ python migrate_and_seed.py

# To run vehicle detection and insert data vehicle
$ python vehicle_detection.py

# To run visualization
$ python smart_traffic_light_dt.py

Option:
--show-count: Show vehicle count per direction.
--show-crossed: Show vehicle crossed per direction.
--weather-update: Integrate real time with weather data.
--atcs-update: Integrate real time with atcs data.
--traffic-simulation: Simulate traffic light management.

# To run simulation
$ python smart_traffic_light_dt.py --show-crossed --show-count --weather-update --atcs-update --traffic-simulation
```

---

### Contributors

- Muhammad Kevin Ardela - [kevinard11](https://github.com/kevinard11)
- Mohammad Febri Ramadlan - [mohammadfebrir](https://github.com/mohammadfebrir)
- Rahayu Utari

---

### Credit

base code using https://github.com/mihir-m-gandhi/Adaptive-Traffic-Signal-Timer
