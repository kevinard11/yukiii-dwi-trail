import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import os
import psycopg2
from psycopg2.extras import RealDictCursor

options={
   'model':'./cfg/yolo.cfg',        #specifying the path of model
   'load':'./bin/yolov2.weights',   #weights
   'threshold':0.3                  #minimum confidence factor to create a box, greater than 0.3 good
}

DB_CONFIG = {
    'dbname': 'stl',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',  # atau IP server database Anda
    'port': '5432'
}

tfnet=TFNet(options)
inputPath = os.getcwd() + "/test_stl/"
outputPath = os.getcwd() + "/output_stl/"

def detectVehicles(filename):
   global tfnet, inputPath, outputPath
   img=cv2.imread(inputPath+filename,cv2.IMREAD_COLOR)
   # img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
   result=tfnet.return_predict(img)
   vehicleTypes = {'car':0, 'bus':0, 'truck':0, 'rickshaw':0, 'motorbike':0}
   print(result)
   for vehicle in result:
      label=vehicle['label']   #extracting label
      if(label=="car" or label=="bus" or label=="motorbike" or label=="truck" or label=="rickshaw"):    # drawing box and writing label
         top_left=(vehicle['topleft']['x'],vehicle['topleft']['y'])
         bottom_right=(vehicle['bottomright']['x'],vehicle['bottomright']['y'])
         img=cv2.rectangle(img,top_left,bottom_right,(0,255,0),3)    #green box of width 5
         img=cv2.putText(img,label,top_left,cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,0),1)   #image, label, position, font, font scale, colour: black, line width
         vehicleTypes[label] += 1

   outputFilename = outputPath + "output_" +filename
   cv2.imwrite(outputFilename,img)
   print('Output image stored at:', outputFilename)
   # plt.imshow(img)
   # plt.show()
   return vehicleTypes


def insert_vehicle_data(car_count, bus_count, truck_count, bike_count, rickshaw_count):
    try:
        # Koneksi ke database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query SQL untuk menyisipkan data
        query = """
            INSERT INTO vehicle (car_count, bus_count, truck_count, bike_count, rickshaw_count, created_date)
            VALUES (%s, %s, %s, %s, %s, now())
        """
        values = (car_count, bus_count, truck_count, bike_count, rickshaw_count)

        # Eksekusi query
        cursor.execute(query, values)
        connection.commit()

        print(f"Data inserted successfully: {values}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

for filename in os.listdir(inputPath):
   vehicleTypes = []
   if(filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg")):
      vehicleTypes = detectVehicles(filename)

   insert_vehicle_data(vehicleTypes['car'], vehicleTypes['bus'], vehicleTypes['truck'], vehicleTypes['motorbike'], vehicleTypes['rickshaw'])

print("Done!")