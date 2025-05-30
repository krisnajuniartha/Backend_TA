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
from fastapi import UploadFile



uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_berita = database["berita-pura"]
collection_status =database["status"]


try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


async def get_status():
    status = []

    response = collection_status.find({})
    
    async for response_status in response:
        status_data = {
            "_id": str(response_status["_id"]),
            "status": response_status["status"]
        }
        status.append(status_data)

    return {"status_list": status}

async def fetch_one_berita(id: str):
    try:
        object_id = ObjectId(id)
        document = await collection_berita.find_one({"_id": object_id})
        
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
        
        berita_data = {
            "_id": str(document["_id"]),
            "judul_berita": document["judul_berita"],
            "description": document["description"],
            "foto_berita": document["foto_berita"],
            "status": document["status"],
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }

        return {"data_berita": [berita_data]}
    except Exception as e:
        print(f"Error fetching pura: {e}")
        # Mengembalikan list kosong dalam wrapper jika terjadi error
        return {"data_berita": [], "error": str(e)}

async def fetch_all_berita():
    berita_list = []
    
    cursor = collection_berita.find({})
    
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
        
        berita_data = {
            "_id": str(document["_id"]),
            "judul_berita": document.get("judul_berita", ""),
            "description": document.get("description", ""),
            "foto_berita": document.get("foto_berita", ""),
            "status": document.get("status", ""),
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }
        
        berita_list.append(berita_data)
    
    return {"data_berita": berita_list}

async def create_berita_data(judul_berita: str, description: str, foto_berita: str, status: str = "678a4449e3ce40b8dc1f014c"):
    timestamps = time.time()
    
    document = {
        "judul_berita": judul_berita,
        "description": description,
        "foto_berita": foto_berita,
        "status": status,
        "createdAt": timestamps,
        "updatedAt": timestamps
    }
    
    result = await collection_berita.insert_one(document)
    
    return {
        "_id": str(result.inserted_id),
        "judul_berita": judul_berita,
        "message": "Berita created successfully"
    }

async def update_berita_data(
    id: str, 
    judul_berita: str = None, 
    description: str = None,
    foto_berita: UploadFile = None
):
    try:
        object_id = ObjectId(id)
        existing_data = await collection_berita.find_one({"_id": object_id})
        if not existing_data:
            return None

        update_data = {}
        timestamps = time.time()
        
        # Handle text fields
        if judul_berita is not None:
            update_data["judul_berita"] = judul_berita
            
        if description is not None:
            update_data["description"] = description
        
        # Handle image upload
        if foto_berita and foto_berita.filename:
            # Hapus foto lama jika ada
            old_foto = existing_data.get("foto_berita")
            if old_foto and old_foto != "none":
                public_id = extract_public_id(old_foto)
                if public_id:
                    try:
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting old photo: {e}")
            
            # Upload foto baru
            contents = await foto_berita.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="berita-pura",
                resource_type="auto"
            )
            update_data["foto_berita"] = upload_result.get("secure_url")
            await foto_berita.close()
        
        if update_data:
            update_data["updatedAt"] = timestamps
            
            await collection_berita.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
        # Return data terbaru
        updated_document = await collection_berita.find_one({"_id": object_id})
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
            return updated_document
        return None
        
    except Exception as e:
        print(f"Error in update: {e}")
        return None
    
async def delete_berita_data(id: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil foto berita untuk dihapus dari cloudinary
        document = await collection_berita.find_one({"_id": object_id})
        if document and document.get("foto_berita") != "none":
            foto_berita = document.get("foto_berita")
            public_id = extract_public_id(foto_berita)
            if public_id:
                try:
                    # Hapus foto dari cloudinary
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting photo from cloudinary: {e}")
        
        # Hapus berita dari database
        result = await collection_berita.delete_one({"_id": object_id})
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting berita: {e}")
        return False

async def approval_berita_data(id: str, status: str):
    try:
        object_id = ObjectId(id)
        
        # Validasi status jika perlu
        status_list = await get_status()
        status_name = None
        
        if status_list and status_list["status_list"]:
            for status_data in status_list["status_list"]:
                if status_data.get("_id") == status:
                    status_name = status_data.get("status", "")
                    break
        
        timestamps = time.time()
        
        update_response = await collection_berita.update_one(
            {"_id": object_id},
            {"$set": {"status": status, "updatedAt": timestamps}}
        )
        
        if update_response.modified_count > 0:
            return f"Status Berita berhasil diubah menjadi: {status_name or status}"
        else:
            return f"Gagal mengubah status Berita dengan ID: {id}"
            
    except Exception as e:
        print(f"Error approving berita: {e}")
        return f"Error: {str(e)}"

async def fetch_berita_by_filter_status(status: list[str]):
    berita_list = []
    
    # Pastikan statusId adalah list
    if not isinstance(status, list):
        status = [status]
    
    # Bersihkan statusId dari tanda kutip jika ada
    if status:
        status = [re.sub(r'^"|"$', '', s) for s in status]
    
    try:
        # Query database dengan filter status_id
        cursor = collection_berita.find({"status": {"$in": status}})
        
        # Proses hasil query
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
            
            berita_data = {
                "_id": str(document["_id"]),
                "judul_berita": document.get("judul_berita", ""),
                "description": document.get("description", ""),
                "foto_berita": document.get("foto_berita", ""),
                "status": document.get("status", ""),
                "createdAt": dt,
                "createdDate": str(tanggal) if tanggal else None,
                "createdTime": str(waktu) if waktu else None,
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal) if updateTanggal else None,
                "updateTime": str(updateWaktu) if updateWaktu else None
            }
            
            berita_list.append(berita_data)
        
        return {"data_berita": berita_list}
    except Exception as e:
        print(f"Error fetching berita by status: {e}")

# Helper function untuk mengekstrak public_id dari URL cloudinary
def extract_public_id(secure_url):
    pattern = r"/upload/(?:v\d+/)?(.+)\.\w+$"
    match = re.search(pattern, secure_url)
    if match:
        return match.group(1)
    else:
        return None

# Function to search berita by title
async def fetch_berita_by_title(title: str):
    berita_list = []
    
    try:
        cursor = collection_berita.find({"judul_berita": {"$regex": f"(?i){title}"}})
        
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
            
            berita_data = {
                "_id": str(document["_id"]),
                "judul_berita": document.get("judul_berita", ""),
                "description": document.get("description", ""),
                "foto_berita": document.get("foto_berita", ""),
                "status": document.get("status", ""),
                "createdAt": dt,
                "createdDate": str(tanggal),
                "createdTime": str(waktu),
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal),
                "updateTime": str(updateWaktu)
            }
            
            berita_list.append(berita_data)
        
        return {"data_berita": berita_list}
    
    except Exception as e:
        print(f"Error searching berita by title: {e}")
        return {"error": str(e)}