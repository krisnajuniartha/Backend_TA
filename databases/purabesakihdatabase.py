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
from fastapi import UploadFile

uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=100000)
database = client["tugas_akhir_krisna"]

collection_pura = database["pura-besakih"]
collection_status = database["status"]
collection_hariraya = database["hariraya"]
collection_golongan = database["golongan-pura"]

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected from purabesakihdatabase to MongoDB!")
except Exception as e:
    print(e)

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
    
    processed_hariraya_ids = []
    
    if isinstance(hariraya_id, list):
        for item in hariraya_id:
            if isinstance(item, str) and "," in item:
                ids = [id.strip() for id in item.split(",")]
                processed_hariraya_ids.extend(ids)
            else:
                processed_hariraya_ids.append(item)
    elif isinstance(hariraya_id, str):
        if "," in hariraya_id:
            processed_hariraya_ids = [id.strip() for id in hariraya_id.split(",")]
        else:
            processed_hariraya_ids = [hariraya_id]
            
    # --- TAMBAHKAN BARIS INI ---
    # Membersihkan setiap ID dari tanda kutip ganda yang tidak perlu
    cleaned_hariraya_ids = [re.sub(r'^"|"$', '', str(id).strip()) for id in processed_hariraya_ids]
    
    document = {
        "nama_pura": nama_pura,
        "description": description,
        "audio_description": audio_description,
        "image_pura": image_pura,
        "status_id": status_id,
        "hariraya_id": cleaned_hariraya_ids,  # Gunakan list yang sudah dibersihkan
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
    golongan_id: str = None,
    image_file: UploadFile = None,
    audio_file: UploadFile = None
):
    try:
        object_id = ObjectId(id)
        existing_data = await collection_pura.find_one({"_id": object_id})
        if not existing_data:
            return None

        update_data = {}
        timestamps = time.time()
        defaultNote = "Menunggu konfirmasi dari admin. Mohon ditunggu beberapa saat."
        
        # Handle text fields
        if nama_pura is not None:
            update_data["nama_pura"] = nama_pura
            
        if description is not None:
            update_data["description"] = description
            
        if hariraya_id is not None:
            processed_hariraya_ids = process_hariraya_ids(hariraya_id)
            update_data["hariraya_id"] = processed_hariraya_ids
                
        if golongan_id is not None:
            update_data["golongan_id"] = golongan_id
        
        # Handle image upload
        if image_file and image_file.filename:
            # Hapus gambar lama jika ada
            old_image = existing_data.get("image_pura")
            if old_image and old_image != "none":
                public_id = extract_public_id(old_image)
                if public_id:
                    try:
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")
            
            # Upload gambar baru
            contents = await image_file.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="pura_besakih",
                resource_type="image"
            )
            update_data["image_pura"] = upload_result.get("secure_url")
            await image_file.close()
        
        if hariraya_id is not None:
        # Proses untuk memisahkan jika ada string dengan koma
            processed_ids = []
            for item in hariraya_id:
                if isinstance(item, str) and "," in item:
                    processed_ids.extend([i.strip() for i in item.split(",")])
                else:
                    processed_ids.append(item)

            cleaned_hariraya_ids = [re.sub(r'^"|"$', '', str(id).strip()) for id in processed_ids]
            update_data["hariraya_id"] = cleaned_hariraya_ids

        # Handle audio upload
        if audio_file and audio_file.filename:
            # Hapus audio lama jika ada
            old_audio = existing_data.get("audio_description")
            if old_audio and old_audio != "none":
                public_id = extract_public_id(old_audio)
                if public_id:
                    try:
                        cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"Error deleting old audio: {e}")
            
            # Upload audio baru
            audio_contents = await audio_file.read()
            audio_upload_result = cloudinary.uploader.upload(
                audio_contents,
                folder="pura_besakih_audio",
                resource_type="auto"
            )
            update_data["audio_description"] = audio_upload_result.get("secure_url")
            await audio_file.close()
        
        if update_data:
            # Set status to Pending seperti di API instrumen
            status = await get_status()
            status_id: str = ""
            if status:
                for status_list in status["status_list"]:
                    if status_list.get("status") == "Pending":
                        status_id = status_list.get("_id", "")
                        break
            
            update_data["status_id"] = status_id
            update_data["updatedAt"] = timestamps
            
            # # Update note
            # await updateNote(id, defaultNote, status_id)
            
            await collection_pura.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
        # Return data terbaru
        updated_document = await collection_pura.find_one({"_id": object_id})
        if updated_document:
            updated_document["_id"] = str(updated_document["_id"])
            return {
                "message": "Data updated successfully", 
                "Updated_data": updated_document
            }
        return None
        
    except Exception as e:
        print(f"Error in update: {e}")
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

async def fetch_pura_by_filter(statusId: list[str], golonganId: list[str]):
    pura_list = []
    
    # Membuat filter query secara dinamis
    filter_query = {}

    # Membersihkan dan menambahkan filter status jika ada
    if statusId:
        cleaned_status_ids = [re.sub(r'^"|"$', '', s) for s in statusId]
        if cleaned_status_ids:
            filter_query["status_id"] = {"$in": cleaned_status_ids}

    # Membersihkan dan menambahkan filter golongan jika ada
    if golonganId:
        cleaned_golongan_ids = [re.sub(r'^"|"$', '', g) for g in golonganId]
        if cleaned_golongan_ids:
            filter_query["golongan_id"] = {"$in": cleaned_golongan_ids}
            
    try:
        # Jalankan query hanya jika ada filter yang diterapkan
        if filter_query:
            cursor = collection_pura.find(filter_query)
        else:
            # Jika tidak ada filter sama sekali, kembalikan semua data
            cursor = collection_pura.find({})

        # Bagian ini sama persis dengan fungsi fetch_pura_by_filter_status Anda
        # untuk memastikan struktur data respons tidak berubah.
        async for document in cursor:
            # Process timestamps
            ts = document.get("createdAt")
            dt = datetime.fromtimestamp(ts) if ts else None
            tanggal = dt.date() if dt else None
            waktu = dt.time() if dt else None

            updateTs = document.get("updatedAt")
            updateDt = datetime.fromtimestamp(updateTs) if updateTs else None
            updateTanggal = updateDt.date() if updateDt else None
            updateWaktu = updateDt.time() if updateDt else None
            
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
            status_name = ""
            if "status_id" in document and document.get("status_id"):
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
                "status": status_name,
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
        print(f"Error fetching pura by filter: {e}")
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

def process_hariraya_ids(hariraya_id):
    """Process hariraya_id input into a list of valid IDs"""
    processed_ids = []
    
    if isinstance(hariraya_id, list):
        for item in hariraya_id:
            if isinstance(item, str):
                if "," in item:
                    processed_ids.extend([id.strip() for id in item.split(",") if id.strip()])
                else:
                    if item.strip():
                        processed_ids.append(item.strip())
    elif isinstance(hariraya_id, str):
        if "," in hariraya_id:
            processed_ids = [id.strip() for id in hariraya_id.split(",") if id.strip()]
        else:
            if hariraya_id.strip():
                processed_ids = [hariraya_id.strip()]
    
    return processed_ids