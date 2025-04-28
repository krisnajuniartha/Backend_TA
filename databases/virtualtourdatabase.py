from models.pengguna import *
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import time
from datetime import datetime
import re

uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_virtual_tour = database["virtual-tour"]

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

async def fetch_one_virtual_tour(id: str):
    try:
        object_id = ObjectId(id)
        document = await collection_virtual_tour.find_one({"_id": object_id})
        
        if not document:
            return None
        
        # Process timestamps
        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None
        
        virtual_tour_data = {
            "_id": str(document["_id"]),
            "nama_virtual_path": document.get("nama_virtual_path", ""),
            "description_area": document.get("description_area", ""),
            "panorama_url": document.get("panorama_url", ""),
            "order_index": document.get("order_index", ""),
            "thumbnail_url": document.get("thumbnail_url", ""),
            "pura_id": document.get("pura_id", ""),
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }

        return virtual_tour_data
    except Exception as e:
        print(f"Error fetching virtual tour: {e}")
        return None

async def fetch_all_virtual_tour():
    virtual_tour_list = []
    
    cursor = collection_virtual_tour.find({})
    
    async for document in cursor:
        # Process timestamps
        ts = document.get("createdAt")
        if ts is not None:
            dt = datetime.fromtimestamp(ts)
            tanggal = dt.date()
            waktu = dt.time()
        else:
            dt, tanggal, waktu = None, None, None

        updateTs = document.get("updatedAt")
        if updateTs is not None:
            updateDt = datetime.fromtimestamp(updateTs)
            updateTanggal = updateDt.date()
            updateWaktu = updateDt.time()
        else:
            updateDt, updateTanggal, updateWaktu = None, None, None
        
        virtual_tour_data = {
            "_id": str(document["_id"]),
            "nama_virtual_path": document.get("nama_virtual_path", ""),
            "description_area": document.get("description_area", ""),
            "panorama_url": document.get("panorama_url", ""),
            "order_index": document.get("order_index", ""),
            "thumbnail_url": document.get("thumbnail_url", ""),
            "pura_id": document.get("pura_id", ""),
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }
        
        virtual_tour_list.append(virtual_tour_data)
    
    return {"data_virtual_tour": virtual_tour_list}

async def create_virtual_tour_data(nama_virtual_path: str, description_area: str, panorama_url: str, thumbnail_url: str, pura_id: str = ""):
    timestamps = time.time()

    # Cari order_index terbesar untuk pura_id yang sama
    existing_virtual_tours = collection_virtual_tour.find({"pura_id": pura_id}).sort("order_index", -1).limit(1)
    max_order_index = -1

    async for document in existing_virtual_tours:
        existing_index = document.get("order_index", -1)
        try:
            max_order_index = int(existing_index)
        except ValueError:
            max_order_index = -1

    new_order_index = max_order_index + 1

    document = {
        "nama_virtual_path": nama_virtual_path,
        "description_area": description_area,
        "panorama_url": panorama_url,
        "order_index": new_order_index,
        "thumbnail_url": thumbnail_url,
        "pura_id": pura_id,
        "createdAt": timestamps,
        "updatedAt": timestamps
    }

    result = await collection_virtual_tour.insert_one(document)

    return {
        "_id": str(result.inserted_id),
        "nama_virtual_path": nama_virtual_path,
        "order_index": new_order_index,
        "message": "Virtual tour created successfully with correct order_index"
    }



async def update_virtual_tour_data(id: str, nama_virtual_path: str = None, description_area: str = None, order_index: str = None, pura_id: str = None):
    try:
        object_id = ObjectId(id)
        
        update_data = {}
        timestamps = time.time()
        
        if nama_virtual_path:
            update_data["nama_virtual_path"] = nama_virtual_path
            
        if description_area:
            update_data["description_area"] = description_area
            
        if order_index:
            update_data["order_index"] = order_index
            
        if pura_id:
            update_data["pura_id"] = pura_id
            
        if update_data:
            update_data["updatedAt"] = timestamps
            
        result = await collection_virtual_tour.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"message": "Successfully Updated Virtual Tour!", "updated_data": update_data}
        else:
            return {"message": "No changes made to the virtual tour"}
        
            
    except Exception as e:
        print(f"Error updating virtual tour: {e}")
        return {"message": f"Error updating virtual tour: {str(e)}"}

async def update_virtual_tour_panorama(id: str, panorama_url: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil panorama lama untuk dihapus dari cloudinary
        document = await collection_virtual_tour.find_one({"_id": object_id})
        if document and document.get("panorama_url") != "none":
            old_panorama = document.get("panorama_url")
            public_id = extract_public_id(old_panorama)
            if public_id:
                try:
                    # Hapus panorama lama dari cloudinary
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting old panorama from cloudinary: {e}")
        
        timestamps = time.time()
        updated_data = {
            "panorama_url": panorama_url,
            "updatedAt": timestamps
        }
        
        await collection_virtual_tour.update_one(
            {"_id": object_id},
            {"$set": updated_data}
        )
        
        updated_document = await collection_virtual_tour.find_one({"_id": object_id})
        return updated_document
        
    except Exception as e:
        print(f"Error updating virtual tour panorama: {e}")
        return None

async def update_virtual_tour_thumbnail(id: str, thumbnail_url: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil thumbnail lama untuk dihapus dari cloudinary
        document = await collection_virtual_tour.find_one({"_id": object_id})
        if document and document.get("thumbnail_url") != "none":
            old_thumbnail = document.get("thumbnail_url")
            public_id = extract_public_id(old_thumbnail)
            if public_id:
                try:
                    # Hapus thumbnail lama dari cloudinary
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting old thumbnail from cloudinary: {e}")
        
        timestamps = time.time()
        updated_data = {
            "thumbnail_url": thumbnail_url,
            "updatedAt": timestamps
        }
        
        await collection_virtual_tour.update_one(
            {"_id": object_id},
            {"$set": updated_data}
        )
        
        updated_document = await collection_virtual_tour.find_one({"_id": object_id})
        return updated_document
        
    except Exception as e:
        print(f"Error updating virtual tour thumbnail: {e}")
        return None

async def delete_virtual_tour_data(id: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil panorama dan thumbnail untuk dihapus dari cloudinary
        document = await collection_virtual_tour.find_one({"_id": object_id})
        if document:
            # Hapus panorama
            if document.get("panorama_url") != "none":
                panorama_url = document.get("panorama_url")
                public_id = extract_public_id(panorama_url)
                if public_id:
                    try:
                        # Hapus panorama dari cloudinary
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting panorama from cloudinary: {e}")
            
            # Hapus thumbnail
            if document.get("thumbnail_url") != "none":
                thumbnail_url = document.get("thumbnail_url")
                public_id = extract_public_id(thumbnail_url)
                if public_id:
                    try:
                        # Hapus thumbnail dari cloudinary
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting thumbnail from cloudinary: {e}")
        
        # Hapus virtual tour dari database
        result = await collection_virtual_tour.delete_one({"_id": object_id})
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting virtual tour: {e}")
        return False

async def fetch_virtual_tour_by_pura_id(pura_id: str):
    virtual_tour_list = []
    
    try:
        cursor = collection_virtual_tour.find({"pura_id": pura_id}).sort("order_index", 1)
        
        async for document in cursor:
            # Process timestamps
            ts = document.get("createdAt")
            if ts is not None:
                dt = datetime.fromtimestamp(ts)
                tanggal = dt.date()
                waktu = dt.time()
            else:
                dt, tanggal, waktu = None, None, None

            updateTs = document.get("updatedAt")
            if updateTs is not None:
                updateDt = datetime.fromtimestamp(updateTs)
                updateTanggal = updateDt.date()
                updateWaktu = updateDt.time()
            else:
                updateDt, updateTanggal, updateWaktu = None, None, None
            
            virtual_tour_data = {
                "_id": str(document["_id"]),
                "nama_virtual_path": document.get("nama_virtual_path", ""),
                "description_area": document.get("description_area", ""),
                "panorama_url": document.get("panorama_url", ""),
                "order_index": document.get("order_index", ""),
                "thumbnail_url": document.get("thumbnail_url", ""),
                "pura_id": document.get("pura_id", ""),
                "createdAt": dt,
                "createdDate": str(tanggal),
                "createdTime": str(waktu),
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal),
                "updateTime": str(updateWaktu)
            }
            
            virtual_tour_list.append(virtual_tour_data)
        
        return {"data_virtual_tour": virtual_tour_list}
    
    except Exception as e:
        print(f"Error fetching virtual tour by pura_id: {e}")
        return {"error": str(e)}

async def fetch_virtual_tour_by_name(name: str):
    virtual_tour_list = []
    
    try:
        cursor = collection_virtual_tour.find({"nama_virtual_path": {"$regex": f"(?i){name}"}})
        
        async for document in cursor:
            # Process timestamps
            ts = document.get("createdAt")
            if ts is not None:
                dt = datetime.fromtimestamp(ts)
                tanggal = dt.date()
                waktu = dt.time()
            else:
                dt, tanggal, waktu = None, None, None

            updateTs = document.get("updatedAt")
            if updateTs is not None:
                updateDt = datetime.fromtimestamp(updateTs)
                updateTanggal = updateDt.date()
                updateWaktu = updateDt.time()
            else:
                updateDt, updateTanggal, updateWaktu = None, None, None
            
            virtual_tour_data = {
                "_id": str(document["_id"]),
                "nama_virtual_path": document.get("nama_virtual_path", ""),
                "description_area": document.get("description_area", ""),
                "panorama_url": document.get("panorama_url", ""),
                "order_index": document.get("order_index", ""),
                "thumbnail_url": document.get("thumbnail_url", ""),
                "pura_id": document.get("pura_id", ""),
                "createdAt": dt,
                "createdDate": str(tanggal),
                "createdTime": str(waktu),
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal),
                "updateTime": str(updateWaktu)
            }
            
            virtual_tour_list.append(virtual_tour_data)
        
        return {"data_virtual_tour": virtual_tour_list}
    
    except Exception as e:
        print(f"Error searching virtual tour by name: {e}")
        return {"error": str(e)}

# Helper function untuk mengekstrak public_id dari URL cloudinary
def extract_public_id(secure_url):
    pattern = r"/upload/(?:v\d+/)?(.+)\.\w+$"
    match = re.search(pattern, secure_url)
    if match:
        return match.group(1)
    else:
        return None