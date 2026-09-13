from pymongo import MongoClient
import gridfs
import uuid
from datetime import datetime, timedelta
import base64
import io
import random
import os
from PIL import Image

class PasuMotorForDbConnection:

    def __init__(self):
        self.client = MongoClient("mongodb://atc:hype@localhost:27017/HyPe?authSource=admin")

    def as_client(self):
        return self.client

class PasuMotorForAssetSchema(PasuMotorForDbConnection):

    def __init__(self):
        super().__init__()
        self.imagedir = "billboards"
        db = self.client["billboard_db"]
        self.fs = gridfs.GridFS(db)
    # -----------------------------
    # 🔹 Helpers
    # -----------------------------
    def random_date(self,start_year=2020, end_year=2025):
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        delta = end - start
        return start + timedelta(days=random.randint(0, delta.days))

    def generate_random_image_base64(self,width=256, height=256):
        """
        Generate a real random image and return base64 string
        """
        # Create random pixels
        pixels = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(width * height)
        ]

        img = Image.new("RGB", (width, height))
        img.putdata(pixels)

        # Save to memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")

        # Convert to base64
        return base64.b64encode(buffer.getvalue()).decode("utf-8")



    def encode_image_to_base64(self,path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def save_image_to_gridfs(self ,image_buffer, filename="billboard.jpg"):
        file_id = self.fs.put(
            image_buffer,
            filename=filename,
            content_type="image/jpeg"
        )
        return str(file_id)

    def upload_directory_to_gridfs(self):
        directory = self.imagedir
        file_ids = []

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            # skip non-files
            if not os.path.isfile(file_path):
                continue

            # optional: filter only images
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            with open(file_path, "rb") as f:
                file_id = self.fs.put(
                    f,
                    filename=filename,
                    content_type="image/jpeg"  # you can improve this dynamically
                )

                file_ids.append(str(file_id))
                print(f"Uploaded: {filename} → {file_id}")

        return file_ids

    def generate_billboard_images(self,count=2):
        """
        Pick random billboard images from folder and convert to base64
        """
        files = os.listdir(self.imagedir)
        selected = random.sample(files, min(count, len(files)))

        filed_id = self.save_image_to_gridfs()
        return [
            {
                "url": self.encode_image_to_base64(os.path.join(self.imagedir, file)),
                "name": file
            }
            for file in selected
        ]

    def generate_images_payload(self,count=2):
        return [
            {
                "url": self.generate_random_image_base64()
            }
            for _ in range(count)
        ]

    def generate_bill_board_asset(self):
        lat = round(random.uniform(9.90, 10.05), 6)
        long = round(random.uniform(76.20, 76.35), 6)
        return {
            "basic_info": {
                "asset_id": f"AST-{uuid.uuid4().hex[:6].upper()}",
                "asset_name": f"Billboard-{random.randint(100, 999)}",
                "status": random.choice(["AVAILABLE", "BOOKED", "MAINTENANCE", "INACTIVE"]),
                "installed_on": self.random_date().strftime("%Y-%m-%d")
            },
            "specifications": {
                "asset_type": "BILLBOARD",
                "billboard_type": "UNIPOLE",
                "billboard_media_type": random.choice(["DIGITAL", "STATIC"])
            },
            "physical_info": {
                "structure": {
                    "height_ft": str(random.randint(30, 100)),
                    "face_count": str(random.randint(1, 3)),
                    "orientation": random.choice(["North", "South", "East", "West"]),
                    "viewing_distance_m": str(random.randint(50, 300))
                },
                "display": {
                    "width_ft": str(random.randint(20, 60)),
                    "height_ft": str(random.randint(10, 30)),
                    "area_sqft": str(random.randint(200, 1500)),
                    "illumination": random.choice(["Yes", "No"]),
                    "illumination_type": random.choice(["LED", "Floodlight", "None"])
                }
            },
            "pricing": {
                "currency": "INR",
                "monthly_rate": random.randint(10000, 100000),
                "min_booking_days": random.choice([30, 60, 90])
            },
            "location": {
                "type":"Point",
                "coordinates": [long,lat],
                "lat": lat,  # Kerala-ish range
                "long": long
            },
            "audience": {},
            "compliance": {},
            "images": [{"url":None}],
            "operations": {
                "updated_on": datetime.now(),
                "updated_by": "pasu",
                "created_on": datetime.now(),
                "created_by": "pasu",
            }
        }

    def create_bill_board_asset(self):
        billboard =  self.generate_bill_board_asset()
        db = self.client['HyPe']['hype_asset_collective'].insert_one(billboard)
