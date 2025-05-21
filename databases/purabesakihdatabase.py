from models.purabesakih import *
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
import os
from typing import List

uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_pura = database["pura-besakih"]
collection_status = database["status"]
collection_hariraya = database["hariraya"]
collection_golongan = database["golongan-pura"]

# Get status functions
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

# Get hari raya functions
async def get_hariraya():
    hariraya = []
    
    response = collection_hariraya.find({})
    
    async for response_hariraya in response:
        hariraya_data = {
            "_id": str(response_hariraya["_id"]),
            "nama_hari_raya": response_hariraya["nama_hari_raya"],
            "description": response_hariraya.get("description", "")
        }
        hariraya.append(hariraya_data)

    return {"hariraya_list": hariraya}

# Get golongan functions
async def get_golongan():
    golongan = []
    
    response = collection_golongan.find({})
    
    async for response_golongan in response:
        golongan_data = {
            "_id": str(response_golongan["_id"]),
            "golongan": response_golongan["golongan"]
        }
        golongan.append(golongan_data)

    return {"golongan_list": golongan}

async def fetch_one_pura(id: str):
    try:
        object_id = ObjectId(id)
        document = await collection_pura.find_one({"_id": object_id})
        
        if not document:
            # Mengembalikan list kosong dalam wrapper jika tidak ada dokumen
            return {"data_pura": []}
        
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
        
        # Get hariraya information
        hariraya_info = []
        if "hariraya_id" in document and document["hariraya_id"]:
            for hariraya_id in document["hariraya_id"]:
                try:
                    hariraya_doc = await collection_hariraya.find_one({"_id": ObjectId(hariraya_id)})
                    if hariraya_doc:
                        hariraya_info.append({
                            "_id": str(hariraya_doc["_id"]),
                            "nama_hari_raya": hariraya_doc.get("nama_hari_raya", ""),
                            "description": hariraya_doc.get("description", "")
                        })
                except Exception as e:
                    print(f"Error fetching hariraya info for ID {hariraya_id}: {e}") # Tambahkan ID untuk debugging
        
        # Get status information
        status_info = None # Mengganti nama variabel agar lebih jelas
        if "status_id" in document:
            try:
                status_doc = await collection_status.find_one({"_id": ObjectId(document["status_id"])})
                if status_doc:
                    status_info = {
                        "_id": str(status_doc["_id"]),
                        "status": status_doc.get("status", "")
                    }
            except Exception as e:
                print(f"Error fetching status info for ID {document['status_id']}: {e}") # Tambahkan ID untuk debugging
        
        # Get golongan information (as seen in your PuraBesakihDataItem)
        golongan_info = None
        if "golongan_id" in document:
            try:
                # Assuming you have a 'collection_golongan' similar to 'collection_status'
                # and 'golongan' is a field in that document.
                # If not, you might need to adjust this part or fetch it differently.
                golongan_doc = await collection_golongan.find_one({"_id": ObjectId(document["golongan_id"])})
                if golongan_doc:
                    golongan_info = {
                        "_id": str(golongan_doc["_id"]),
                        "golongan": golongan_doc.get("golongan", "") # Assuming field name is 'golongan'
                    }
            except Exception as e:
                print(f"Error fetching golongan info for ID {document['golongan_id']}: {e}")

        pura_data = {
            "_id": str(document["_id"]),
            "nama_pura": document.get("nama_pura", ""),
            "description": document.get("description", ""),
            "audio_description": document.get("audio_description", ""),
            "image_pura": document.get("image_pura", ""),
            "hariraya_id": [str(hid) for hid in document.get("hariraya_id", [])], # Pastikan ini list of strings
            "hariraya_info": hariraya_info, # Ini akan menjadi list of objects
            "status_id": document.get("status_id", ""), # Ini tetap string ID
            "status": status_info.get("status") if status_info else None, # Mengambil nama status langsung
            "golongan_id": document.get("golongan_id", ""), # Ini tetap string ID
            "golongan": golongan_info.get("golongan") if golongan_info else None, # Mengambil nama golongan langsung
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }

        # Membungkus data tunggal dalam sebuah list dan kemudian dalam dictionary "data_pura"
        return {"data_pura": [pura_data]}
    except Exception as e:
        print(f"Error fetching pura: {e}")
        # Mengembalikan list kosong dalam wrapper jika terjadi error
        return {"data_pura": [], "error": str(e)}

async def fetch_all_pura():
    pura_list = []
    
    cursor = collection_pura.find({})
    
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
        
        # Get hariraya information
        hariraya_info = []
        if "hariraya_id" in document and document["hariraya_id"]:
            for hariraya_id in document["hariraya_id"]:
                try:
                    hariraya_doc = await collection_hariraya.find_one({"_id": ObjectId(hariraya_id)})
                    if hariraya_doc:
                        hariraya_info.append({
                            "_id": str(hariraya_doc["_id"]),
                            "nama_hari_raya": hariraya_doc.get("nama_hari_raya", ""),
                            "description": hariraya_doc.get("description", "")
                        })
                except Exception as e:
                    print(f"Error fetching hariraya info: {e}")
        
        # Get status information
        status_info = None
        if "status_id" in document:
            try:
                status_doc = await collection_status.find_one({"_id": ObjectId(document["status_id"])})
                if status_doc:
                    status_info = {
                        "_id": str(status_doc["_id"]),
                        "status": status_doc.get("status", "")
                    }
            except Exception as e:
                print(f"Error fetching status info: {e}")
        
        pura_data = {
            "_id": str(document["_id"]),
            "nama_pura": document.get("nama_pura", ""),
            "description": document.get("description", ""),
            "audio_description": document.get("audio_description", ""),
            "image_pura": document.get("image_pura", ""),
            "status_id": document.get("status_id", ""),
            "status_info": status_info,
            "hariraya_id": document.get("hariraya_id", []),
            "hariraya_info": hariraya_info,
            "golongan_id": document.get("golongan_id", ""),
            "createdAt": dt,
            "createdDate": str(tanggal),
            "createdTime": str(waktu),
            "updatedAt": updateDt,
            "updatedDate": str(updateTanggal),
            "updateTime": str(updateWaktu)
        }
        
        pura_list.append(pura_data)
    
    return {"data_pura": pura_list}

async def create_pura_data(
    nama_pura: str, 
    description: str, 
    audio_description: str,
    image_pura: str, 
    hariraya_id: list,
    golongan_id: str,
    status_id: str = "678a4449e3ce40b8dc1f014c"
):
    timestamps = time.time()
    
    # Process hariraya_id to ensure it's a list of individual IDs
    processed_hariraya_ids = []
    
    # If hariraya_id is provided as a single string with comma-separated values
    if isinstance(hariraya_id, list):
        for item in hariraya_id:
            if isinstance(item, str) and "," in item:
                # Split comma-separated string into individual IDs
                ids = [id.strip() for id in item.split(",")]
                processed_hariraya_ids.extend(ids)
            else:
                processed_hariraya_ids.append(item)
    elif isinstance(hariraya_id, str):
        # If hariraya_id is a single string with comma-separated values
        if "," in hariraya_id:
            processed_hariraya_ids = [id.strip() for id in hariraya_id.split(",")]
        else:
            processed_hariraya_ids = [hariraya_id]
    
    document = {
        "nama_pura": nama_pura,
        "description": description,
        "audio_description": audio_description,  # Ensure this accepts MP3 URLs
        "image_pura": image_pura,
        "status_id": status_id,
        "hariraya_id": processed_hariraya_ids,  # Use the processed list
        "golongan_id": golongan_id,
        "createdAt": timestamps,
        "updatedAt": timestamps
    }
    
    result = await collection_pura.insert_one(document)
    
    return {
        "_id": str(result.inserted_id),
        "nama_pura": nama_pura,
        "message": "Pura Besakih created successfully"
    }

async def update_pura_data(
    id: str, 
    nama_pura: str = None, 
    description: str = None, 
    hariraya_id: list = None,
    golongan_id: str = None
):
    try:
        object_id = ObjectId(id)
        
        update_data = {}
        timestamps = time.time()
        
        if nama_pura:
            update_data["nama_pura"] = nama_pura
            
        if description:
            update_data["description"] = description
            
        if hariraya_id:
            # Process hariraya_id to ensure it's a list of individual IDs
            processed_hariraya_ids = []
            
            if isinstance(hariraya_id, list):
                for item in hariraya_id:
                    if isinstance(item, str) and "," in item:
                        # Split comma-separated string into individual IDs
                        ids = [id.strip() for id in item.split(",")]
                        processed_hariraya_ids.extend(ids)
                    else:
                        processed_hariraya_ids.append(item)
            elif isinstance(hariraya_id, str):
                # If hariraya_id is a single string with comma-separated values
                if "," in hariraya_id:
                    processed_hariraya_ids = [id.strip() for id in hariraya_id.split(",")]
                else:
                    processed_hariraya_ids = [hariraya_id]
                    
            update_data["hariraya_id"] = processed_hariraya_ids
            
        if golongan_id:
            update_data["golongan_id"] = golongan_id
            
        if update_data:
            update_data["updatedAt"] = timestamps
            
        result = await collection_pura.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"message": "Successfully Updated Pura Besakih!", "updated_data": update_data}
        else:
            return {"message": "No changes made to the pura"}
            
    except Exception as e:
        print(f"Error updating pura: {e}")
        return {"message": f"Error updating pura: {str(e)}"}

async def update_pura_image(id: str, image: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil image lama untuk dihapus dari cloudinary
        document = await collection_pura.find_one({"_id": object_id})
        if document and document.get("image_pura") != "none":
            old_image = document.get("image_pura")
            public_id = extract_public_id(old_image)
            if public_id:
                try:
                    # Hapus image lama dari cloudinary
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting old image from cloudinary: {e}")
        
        timestamps = time.time()
        updated_data = {
            "image_pura": image,
            "updatedAt": timestamps
        }
        
        await collection_pura.update_one(
            {"_id": object_id},
            {"$set": updated_data}
        )
        
        updated_document = await collection_pura.find_one({"_id": object_id})
        return updated_document
        
    except Exception as e:
        print(f"Error updating pura image: {e}")
        return None

async def update_pura_audio(id: str, audio: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil audio lama untuk dihapus dari cloudinary
        document = await collection_pura.find_one({"_id": object_id})
        if document and document.get("audio_description") != "none":
            old_audio = document.get("audio_description")
            public_id = extract_public_id(old_audio)
            if public_id:
                try:
                    # Hapus audio lama dari cloudinary
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting old audio from cloudinary: {e}")
        
        timestamps = time.time()
        updated_data = {
            "audio_description": audio,
            "updatedAt": timestamps
        }
        
        await collection_pura.update_one(
            {"_id": object_id},
            {"$set": updated_data}
        )
        
        updated_document = await collection_pura.find_one({"_id": object_id})
        return updated_document
        
    except Exception as e:
        print(f"Error updating pura audio: {e}")
        return None

async def delete_pura_data(id: str):
    try:
        object_id = ObjectId(id)
        
        # Ambil image dan audio pura untuk dihapus dari cloudinary
        document = await collection_pura.find_one({"_id": object_id})
        if document:
            # Delete image from cloudinary
            if document.get("image_pura") != "none":
                image_pura = document.get("image_pura")
                image_public_id = extract_public_id(image_pura)
                if image_public_id:
                    try:
                        cloudinary.uploader.destroy(image_public_id)
                    except Exception as e:
                        print(f"Error deleting image from cloudinary: {e}")
            
            # Delete audio from cloudinary
            if document.get("audio_description") != "none":
                audio_description = document.get("audio_description")
                audio_public_id = extract_public_id(audio_description)
                if audio_public_id:
                    try:
                        cloudinary.uploader.destroy(audio_public_id)
                    except Exception as e:
                        print(f"Error deleting audio from cloudinary: {e}")
        
        # Hapus pura dari database
        result = await collection_pura.delete_one({"_id": object_id})
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting pura: {e}")
        return False

async def approval_pura_data(id: str, status: str):
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
        
        update_response = await collection_pura.update_one(
            {"_id": object_id},
            {"$set": {"status_id": status, "updatedAt": timestamps}}
        )
        
        if update_response.modified_count > 0:
            return f"Status Pura berhasil diubah menjadi: {status_name or status}"
        else:
            return f"Gagal mengubah status Pura dengan ID: {id}"
            
    except Exception as e:
        print(f"Error approving pura: {e}")
        return f"Error: {str(e)}"

async def fetch_pura_by_filter_status(status: list[str]):
    pura_list = []
   
    # Pastikan status adalah list
    if not isinstance(status, list):
        status = [status]
   
    # Bersihkan status dari tanda kutip jika ada
    if status:
        status = [re.sub(r'^"|"$', '', s) for s in status]
   
    try:
        # Query database dengan filter status_id
        cursor = collection_pura.find({"status_id": {"$in": status}})
       
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
           
            # Get hariraya information
            hariraya_info = []
            if "hariraya_id" in document and document["hariraya_id"]:
                for hariraya_id in document["hariraya_id"]:
                    try:
                        hariraya_doc = await collection_hariraya.find_one({"_id": ObjectId(hariraya_id)})
                        if hariraya_doc:
                            hariraya_info.append({
                                "_id": str(hariraya_doc["_id"]),
                                "nama_hari_raya": hariraya_doc.get("nama_hari_raya", ""),
                                "description": hariraya_doc.get("description", "")
                            })
                    except Exception as e:
                        print(f"Error fetching hariraya info: {e}")
           
            # Get status information - sekarang menyimpan nama status langsung di objek respons
            status_name = ""
            if "status_id" in document:
                try:
                    status_doc = await collection_status.find_one({"_id": ObjectId(document["status_id"])})
                    if status_doc:
                        status_name = status_doc.get("status", "")
                except Exception as e:
                    print(f"Error fetching status info: {e}")
           
            pura_data = {
                "_id": str(document["_id"]),
                "nama_pura": document.get("nama_pura", ""),
                "description": document.get("description", ""),
                "audio_description": document.get("audio_description", ""),
                "image_pura": document.get("image_pura", ""),
                "status_id": document.get("status_id", ""),
                "status": status_name,  # Menyimpan nama status langsung seperti di berita
                "hariraya_id": document.get("hariraya_id", []),
                "hariraya_info": hariraya_info,
                "golongan_id": document.get("golongan_id", ""),
                "createdAt": dt,
                "createdDate": str(tanggal) if tanggal else None,
                "createdTime": str(waktu) if waktu else None,
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal) if updateTanggal else None,
                "updateTime": str(updateWaktu) if updateWaktu else None
            }
            
            pura_list.append(pura_data)
    
        return {"data_pura": pura_list}
    except Exception as e:
        print(f"Error fetching pura by status: {e}")
        return {"error": str(e)}

# Function to search pura by nama
async def fetch_pura_by_nama(nama_pura: str):
    pura_list = []
    
    try:
        cursor = collection_pura.find({"nama_pura": {"$regex": f"(?i){nama_pura}"}})
        
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
            
            # Get hariraya information
            hariraya_info = []
            if "hariraya_id" in document and document["hariraya_id"]:
                for hariraya_id in document["hariraya_id"]:
                    try:
                        hariraya_doc = await collection_hariraya.find_one({"_id": ObjectId(hariraya_id)})
                        if hariraya_doc:
                            hariraya_info.append({
                                "_id": str(hariraya_doc["_id"]),
                                "nama_hari_raya": hariraya_doc.get("nama_hari_raya", ""),
                                "description": hariraya_doc.get("description", "")
                            })
                    except Exception as e:
                        print(f"Error fetching hariraya info: {e}")
            
            # Get status information
            status_info = None
            if "status_id" in document:
                try:
                    status_doc = await collection_status.find_one({"_id": ObjectId(document["status_id"])})
                    if status_doc:
                        status_info = {
                            "_id": str(status_doc["_id"]),
                            "status": status_doc.get("status", "")
                        }
                except Exception as e:
                    print(f"Error fetching status info: {e}")
            
            pura_data = {
                "_id": str(document["_id"]),
                "nama_pura": document.get("nama_pura", ""),
                "description": document.get("description", ""),
                "audio_description": document.get("audio_description", ""),
                "image_pura": document.get("image_pura", ""),
                "status_id": document.get("status_id", ""),
                "status_info": status_info,
                "hariraya_id": document.get("hariraya_id", []),
                "hariraya_info": hariraya_info,
                "golongan_id": document.get("golongan_id", ""),
                "createdAt": dt,
                "createdDate": str(tanggal),
                "createdTime": str(waktu),
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal),
                "updateTime": str(updateWaktu)
            }
            
            pura_list.append(pura_data)
        
        return {"data_pura": pura_list}
    except Exception as e:
        print(f"Error searching pura by nama: {e}")
        return {"error": str(e)}

# Helper function untuk mengekstrak public_id dari URL cloudinary
def extract_public_id(secure_url):
    pattern = r"/upload/(?:v\d+/)?(.+)\.\w+$"
    match = re.search(pattern, secure_url)
    if match:
        return match.group(1)
    else:
        return None

# Function to filter pura by golongan
async def fetch_pura_by_golongan(golongan: str):
    pura_list = []
    
    try:
        cursor = collection_pura.find({"golongan_id": golongan})
        
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
            
            # Get hariraya information
            hariraya_info = []
            if "hariraya_id" in document and document["hariraya_id"]:
                for hariraya_id in document["hariraya_id"]:
                    try:
                        hariraya_doc = await collection_hariraya.find_one({"_id": ObjectId(hariraya_id)})
                        if hariraya_doc:
                            hariraya_info.append({
                                "_id": str(hariraya_doc["_id"]),
                                "nama_hari_raya": hariraya_doc.get("nama_hari_raya", ""),
                                "description": hariraya_doc.get("description", "")
                            })
                    except Exception as e:
                        print(f"Error fetching hariraya info: {e}")
            
            # Get status information
            status_info = None
            if "status_id" in document:
                try:
                    status_doc = await collection_status.find_one({"_id": ObjectId(document["status_id"])})
                    if status_doc:
                        status_info = {
                            "_id": str(status_doc["_id"]),
                            "status": status_doc.get("status", "")
                        }
                except Exception as e:
                    print(f"Error fetching status info: {e}")
            
            pura_data = {
                "_id": str(document["_id"]),
                "nama_pura": document.get("nama_pura", ""),
                "description": document.get("description", ""),
                "audio_description": document.get("audio_description", ""),
                "image_pura": document.get("image_pura", ""),
                "status_id": document.get("status_id", ""),
                "status_info": status_info,
                "hariraya_id": document.get("hariraya_id", []),
                "hariraya_info": hariraya_info,
                "golongan_id": document.get("golongan_id", ""),
                "createdAt": dt,
                "createdDate": str(tanggal),
                "createdTime": str(waktu),
                "updatedAt": updateDt,
                "updatedDate": str(updateTanggal),
                "updateTime": str(updateWaktu)
            }
            
            pura_list.append(pura_data)
        
        return {"data_pura": pura_list}
    except Exception as e:
        print(f"Error fetching pura by golongan: {e}")
        return {"error": str(e)}
