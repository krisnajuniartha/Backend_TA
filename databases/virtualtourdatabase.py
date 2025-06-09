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
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import Annotated, List, Optional

uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_virtual_tour = database["virtual-tour"]

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected from virtualtourdatabase to MongoDB!")
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

async def create_virtual_tour_data(nama_virtual_path: str, description_area: str, panorama_url: str, thumbnail_url: str, pura_id: str):
    timestamps = time.time()

    # Logika mencari order_index terbesar
    existing_virtual_tours = collection_virtual_tour.find({"pura_id": pura_id}).sort("order_index", -1).limit(1)
    max_order_index = -1
    async for document in existing_virtual_tours:
        existing_index = document.get("order_index", -1)
        try:
            max_order_index = int(existing_index)
        except (ValueError, TypeError):
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

    # Kembalikan respons yang lebih lengkap, sama seperti di contoh pura-besakih
    inserted_document = await collection_virtual_tour.find_one({"_id": result.inserted_id})
    if inserted_document:
        inserted_document["_id"] = str(inserted_document["_id"])
        # Tambahkan pesan sukses jika perlu
        # inserted_document["message"] = "Virtual tour created successfully"
        return inserted_document
    else:
        raise HTTPException(status_code=404, detail="Gagal menemukan dokumen yang baru dibuat.")




async def update_virtual_tour_data(
    id: str,
    nama_virtual_path: Optional[str] = None,
    description_area: Optional[str] = None,
    panorama_file: Optional[UploadFile] = None,
    thumbnail_file: Optional[UploadFile] = None
):
    """
    Fungsi "gemuk" yang melakukan semua proses update untuk virtual tour.
    """
    try:
        object_id = ObjectId(id)
        # Ambil data lama untuk referensi (misal: menghapus file lama)
        existing_document = await collection_virtual_tour.find_one({"_id": object_id})
        if not existing_document:
            return None # Akan ditangani sebagai 404 oleh endpoint

        update_data = {}
        
        ## --- Handle data teks ---
        if nama_virtual_path is not None:
            update_data["nama_virtual_path"] = nama_virtual_path
        if description_area is not None:
            update_data["description_area"] = description_area
            
        ## --- Handle upload file panorama ---
        if panorama_file and panorama_file.filename:
            # Hapus file lama dari Cloudinary jika ada
            if old_url := existing_document.get("panorama_url"):
                if public_id := extract_public_id(old_url):
                    try:
                        cloudinary.uploader.destroy(public_id, resource_type="image")
                    except Exception as e:
                        print(f"Gagal hapus panorama lama: {e}")
            
            # Upload file baru
            contents = await panorama_file.read()
            upload_result = cloudinary.uploader.upload(contents, folder="virtual-tour")
            update_data["panorama_url"] = upload_result.get("secure_url")
            await panorama_file.close()

        ## --- Handle upload file thumbnail ---
        if thumbnail_file and thumbnail_file.filename:
            # Hapus file lama dari Cloudinary jika ada
            if old_url := existing_document.get("thumbnail_url"):
                if public_id := extract_public_id(old_url):
                    try:
                        cloudinary.uploader.destroy(public_id, resource_type="image")
                    except Exception as e:
                        print(f"Gagal hapus thumbnail lama: {e}")

            # Upload file baru
            contents = await thumbnail_file.read()
            upload_result = cloudinary.uploader.upload(contents, folder="virtual-tour-thumbnails")
            update_data["thumbnail_url"] = upload_result.get("secure_url")
            await thumbnail_file.close()

        ## --- Lakukan update ke database jika ada perubahan ---
        if update_data:
            update_data["updatedAt"] = time.time()
            
            await collection_virtual_tour.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
        
        # Selalu kembalikan data terbaru setelah proses selesai
        updated_document = await collection_virtual_tour.find_one({"_id": object_id})
        updated_document["_id"] = str(updated_document["_id"])
        
        return {
            "message": "Data virtual tour berhasil diperbarui",
            "updated_data": updated_document
        }

    except Exception as e:
        print(f"Error di logic update_virtual_tour_data: {e}")
        raise e # Lempar exception agar ditangkap oleh endpoint

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
    
async def delete_virtual_tour_by_pura_id(pura_id: str):
    """
    Menghapus semua virtual tour berdasarkan pura_id termasuk file di cloudinary
    """
    try:
        # Ambil semua virtual tour untuk pura tersebut
        response = await fetch_virtual_tour_by_pura_id(pura_id)
        virtual_tours = response.get("data_virtual_tour", [])
        
        # Hapus semua file dari cloudinary
        for tour in virtual_tours:
            # Hapus panorama
            if tour.get("panorama_url") and tour.get("panorama_url") != "none":
                panorama_url = tour.get("panorama_url")
                public_id = extract_public_id(panorama_url)
                if public_id:
                    try:
                        # Hapus panorama dari cloudinary
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting panorama from cloudinary: {e}")
            
            # Hapus thumbnail
            if tour.get("thumbnail_url") and tour.get("thumbnail_url") != "none":
                thumbnail_url = tour.get("thumbnail_url")
                public_id = extract_public_id(thumbnail_url)
                if public_id:
                    try:
                        # Hapus thumbnail dari cloudinary
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting thumbnail from cloudinary: {e}")
        
        # Hapus semua virtual tour dari database
        result = await collection_virtual_tour.delete_many({"pura_id": pura_id})
        
        return True, result.deleted_count
    
    except Exception as e:
        print(f"Error deleting virtual tours by pura_id: {e}")
        return False, 0

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