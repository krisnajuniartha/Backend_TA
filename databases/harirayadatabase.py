from models.hariraya import *
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import time
from datetime import datetime
import re
import os
from typing import List


uri = "mongodb+srv://krisnajuniartha:ffx9GWKjBMaQAuMm@tugas-akhir-database.ekayh.mongodb.net/?retryWrites=true&w=majority&appName=tugas-akhir-database"

client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
database = client["tugas_akhir_krisna"]

collection_hariraya = database["hari-raya"]
collection_status = database["status"]

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

async def fetch_one_hariraya(id: str):
    try:
        object_id = ObjectId(id)
        document = await collection_hariraya.find_one({"_id": object_id})
        
        if not document:
            return None
        
        # Process timestamps
        tanggal_mulai = document.get("tanggal_mulai")
        if tanggal_mulai is not None:
            tanggal_mulai_dt = datetime.fromtimestamp(tanggal_mulai)
        else:
            tanggal_mulai_dt = None

        tanggal_berakhir = document.get("tanggal_berakhir")
        if tanggal_berakhir is not None:
            tanggal_berakhir_dt = datetime.fromtimestamp(tanggal_berakhir)
        else:
            tanggal_berakhir_dt = None

        created_ts = document.get("createdAt")
        if created_ts is not None:
            created_dt = datetime.fromtimestamp(created_ts)
            created_tanggal = created_dt.date()
            created_waktu = created_dt.time()
        else:
            created_dt, created_tanggal, created_waktu = None, None, None

        updated_ts = document.get("updatedAt")
        if updated_ts is not None:
            updated_dt = datetime.fromtimestamp(updated_ts)
            updated_tanggal = updated_dt.date()
            updated_waktu = updated_dt.time()
        else:
            updated_dt, updated_tanggal, updated_waktu = None, None, None
        
        hariraya_data = {
            "_id": str(document["_id"]),
            "nama_hari_raya": document["nama_hari_raya"],
            "description": document["description"],
            "tanggal_mulai": tanggal_mulai_dt,
            "tanggal_berakhir": tanggal_berakhir_dt,
            "status_id": document["status_id"],
            "createdAt": created_dt,
            "createdDate": str(created_tanggal),
            "createdTime": str(created_waktu),
            "updatedAt": updated_dt,
            "updatedDate": str(updated_tanggal),
            "updateTime": str(updated_waktu)
        }
       
        
        return {"data_hariraya": hariraya_data}
    
    except Exception as e:
        print(f"Error fetching hari raya: {e}")
        return None

async def fetch_all_hariraya():
    hariraya_list = []
    
    cursor = collection_hariraya.find({})
    
    async for document in cursor:
        # Process timestamps
        tanggal_mulai = document.get("tanggal_mulai")
        if tanggal_mulai is not None:
            tanggal_mulai_dt = datetime.fromtimestamp(tanggal_mulai)
        else:
            tanggal_mulai_dt = None

        tanggal_berakhir = document.get("tanggal_berakhir")
        if tanggal_berakhir is not None:
            tanggal_berakhir_dt = datetime.fromtimestamp(tanggal_berakhir)
        else:
            tanggal_berakhir_dt = None

        created_ts = document.get("createdAt")
        if created_ts is not None:
            created_dt = datetime.fromtimestamp(created_ts)
            created_tanggal = created_dt.date()
            created_waktu = created_dt.time()
        else:
            created_dt, created_tanggal, created_waktu = None, None, None

        updated_ts = document.get("updatedAt")
        if updated_ts is not None:
            updated_dt = datetime.fromtimestamp(updated_ts)
            updated_tanggal = updated_dt.date()
            updated_waktu = updated_dt.time()
        else:
            updated_dt, updated_tanggal, updated_waktu = None, None, None
        
        hariraya_data = {
            "_id": str(document["_id"]),
            "nama_hari_raya": document.get("nama_hari_raya", ""),
            "description": document.get("description", ""),
            "tanggal_mulai": tanggal_mulai_dt,
            "tanggal_berakhir": tanggal_berakhir_dt,
            "status_id": document.get("status_id", ""),
            "createdAt": created_dt,
            "createdDate": str(created_tanggal) if created_tanggal else None,
            "createdTime": str(created_waktu) if created_waktu else None,
            "updatedAt": updated_dt,
            "updatedDate": str(updated_tanggal) if updated_tanggal else None,
            "updateTime": str(updated_waktu) if updated_waktu else None
        }
        
        hariraya_list.append(hariraya_data)
    
    return {"data_hariraya": hariraya_list}

async def create_hariraya_data(nama_hari_raya: str, description: str, tanggal_mulai: float, tanggal_berakhir: float, status_id: str = "678a4449e3ce40b8dc1f014c"):
    timestamps = time.time()
    
    # Cek apakah nama hari raya sudah ada dengan tanggal yang tumpang tindih
    existing_hariraya = await check_overlapping_hariraya(nama_hari_raya, tanggal_mulai, tanggal_berakhir)
    
    # Jika ada yang tumpang tindih, tetap buat data baru (tidak apa-apa jika sama dalam 1 bulan)
    # Tapi berikan pesan peringatan
    warning_message = ""
    if existing_hariraya:
        warning_message = f"Perhatian: Hari raya dengan nama yang sama ({nama_hari_raya}) sudah ada dalam rentang waktu yang tumpang tindih. Sistem tetap membuat data baru."
    
    document = {
        "nama_hari_raya": nama_hari_raya,
        "description": description,
        "tanggal_mulai": tanggal_mulai,
        "tanggal_berakhir": tanggal_berakhir,
        "status_id": status_id,
        "createdAt": timestamps,
        "updatedAt": timestamps
    }
    
    result = await collection_hariraya.insert_one(document)
    
    response = {
        "_id": str(result.inserted_id),
        "nama_hari_raya": nama_hari_raya,
        "message": "Hari Raya created successfully"
    }
    
    if warning_message:
        response["warning"] = warning_message
    
    return response

async def check_overlapping_hariraya(nama_hari_raya: str, tanggal_mulai: float, tanggal_berakhir: float):
    # Cari hari raya dengan nama yang sama dan tanggal yang tumpang tindih
    cursor = collection_hariraya.find({
        "nama_hari_raya": nama_hari_raya,
        "$or": [
            # Tanggal mulai berada dalam range hari raya yang sudah ada
            {"$and": [
                {"tanggal_mulai": {"$lte": tanggal_mulai}},
                {"tanggal_berakhir": {"$gte": tanggal_mulai}}
            ]},
            # Tanggal berakhir berada dalam range hari raya yang sudah ada
            {"$and": [
                {"tanggal_mulai": {"$lte": tanggal_berakhir}},
                {"tanggal_berakhir": {"$gte": tanggal_berakhir}}
            ]},
            # Range baru melingkupi hari raya yang sudah ada
            {"$and": [
                {"tanggal_mulai": {"$gte": tanggal_mulai}},
                {"tanggal_berakhir": {"$lte": tanggal_berakhir}}
            ]}
        ]
    })
    
    overlapping_hariraya = []
    async for doc in cursor:
        overlapping_hariraya.append(doc)
    
    return overlapping_hariraya

async def update_hariraya_data(id: str, nama_hari_raya: str = None, description: str = None, tanggal_mulai: float = None, tanggal_berakhir: float = None):
    try:
        object_id = ObjectId(id)
        
        update_data = {}
        timestamps = time.time()
        
        if nama_hari_raya:
            update_data["nama_hari_raya"] = nama_hari_raya
            
        if description:
            update_data["description"] = description
            
        if tanggal_mulai:
            update_data["tanggal_mulai"] = tanggal_mulai
            
        if tanggal_berakhir:
            update_data["tanggal_berakhir"] = tanggal_berakhir
            
        if update_data:
            update_data["updatedAt"] = timestamps
            
        # Jika ada perubahan tanggal atau nama, cek tumpang tindih
        warning_message = ""
        if (nama_hari_raya or tanggal_mulai or tanggal_berakhir):
            # Ambil data hariraya yang ada
            current_hariraya = await fetch_one_hariraya(id)
            if current_hariraya:
                # Gunakan nilai yang baru jika ada, jika tidak gunakan yang lama
                check_nama = nama_hari_raya if nama_hari_raya else current_hariraya["nama_hari_raya"]
                check_mulai = tanggal_mulai if tanggal_mulai else time.mktime(current_hariraya["tanggal_mulai"].timetuple())
                check_akhir = tanggal_berakhir if tanggal_berakhir else time.mktime(current_hariraya["tanggal_berakhir"].timetuple())
                
                # Cek tumpang tindih
                overlapping = await check_overlapping_hariraya(check_nama, check_mulai, check_akhir)
                
                # Filter agar tidak menghitung data hariraya yang sedang diupdate
                overlapping = [doc for doc in overlapping if str(doc["_id"]) != id]
                
                if overlapping:
                    warning_message = f"Perhatian: Update dilakukan tetapi hari raya dengan nama yang sama ({check_nama}) sudah ada dalam rentang waktu yang tumpang tindih."
            
        result = await collection_hariraya.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        response = {}
        if result.modified_count > 0:
            response["message"] = "Successfully Updated Hari Raya!"
            response["updated_data"] = update_data
        else:
            response["message"] = "No changes made to the Hari Raya"
            
        if warning_message:
            response["warning"] = warning_message
            
        return response
            
    except Exception as e:
        print(f"Error updating hari raya: {e}")
        return {"message": f"Error updating hari raya: {str(e)}"}

async def delete_hariraya_data(id: str):
    try:
        object_id = ObjectId(id)
        
        # Hapus hari raya dari database
        result = await collection_hariraya.delete_one({"_id": object_id})
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting hari raya: {e}")
        return False

async def approval_hariraya_data(id: str, status_id: str):
    try:
        object_id = ObjectId(id)
        
        # Validasi status jika perlu
        status_list = await get_status()
        status_name = None
        
        if status_list and status_list["status_list"]:
            for status_data in status_list["status_list"]:
                if status_data.get("_id") == status_id:
                    status_name = status_data.get("status", "")
                    break
        
        timestamps = time.time()
        
        update_response = await collection_hariraya.update_one(
            {"_id": object_id},
            {"$set": {"status_id": status_id, "updatedAt": timestamps}}
        )
        
        if update_response.modified_count > 0:
            return f"Status Hari Raya berhasil diubah menjadi: {status_name or status_id}"
        else:
            return f"Gagal mengubah status Hari Raya dengan ID: {id}"
            
    except Exception as e:
        print(f"Error approving hari raya: {e}")
        return f"Error: {str(e)}"

async def fetch_hariraya_by_filter_status(statusId: list[str]):
    hariraya_list = []
    
    # Pastikan statusId adalah list
    if not isinstance(statusId, list):
        statusId = [statusId]
    
    # Bersihkan statusId dari tanda kutip jika ada
    if statusId:
        statusId = [re.sub(r'^"|"$', '', s) for s in statusId]
    
    try:
        # Query database dengan filter status_id
        cursor = collection_hariraya.find({"status_id": {"$in": statusId}})
        
        # Proses hasil query
        async for document in cursor:
            # Process timestamps
            tanggal_mulai = document.get("tanggal_mulai")
            if tanggal_mulai is not None:
                tanggal_mulai_dt = datetime.fromtimestamp(tanggal_mulai)
            else:
                tanggal_mulai_dt = None

            tanggal_berakhir = document.get("tanggal_berakhir")
            if tanggal_berakhir is not None:
                tanggal_berakhir_dt = datetime.fromtimestamp(tanggal_berakhir)
            else:
                tanggal_berakhir_dt = None

            created_ts = document.get("createdAt")
            if created_ts is not None:
                created_dt = datetime.fromtimestamp(created_ts)
                created_tanggal = created_dt.date()
                created_waktu = created_dt.time()
            else:
                created_dt, created_tanggal, created_waktu = None, None, None

            updated_ts = document.get("updatedAt")
            if updated_ts is not None:
                updated_dt = datetime.fromtimestamp(updated_ts)
                updated_tanggal = updated_dt.date()
                updated_waktu = updated_dt.time()
            else:
                updated_dt, updated_tanggal, updated_waktu = None, None, None
            
            hariraya_data = {
                "_id": str(document["_id"]),
                "nama_hari_raya": document.get("nama_hari_raya", ""),
                "description": document.get("description", ""),
                "tanggal_mulai": tanggal_mulai_dt,
                "tanggal_berakhir": tanggal_berakhir_dt,
                "status_id": document.get("status_id", ""),
                "createdAt": created_dt,
                "createdDate": str(created_tanggal) if created_tanggal else None,
                "createdTime": str(created_waktu) if created_waktu else None,
                "updatedAt": updated_dt,
                "updatedDate": str(updated_tanggal) if updated_tanggal else None,
                "updateTime": str(updated_waktu) if updated_waktu else None
            }
            
            hariraya_list.append(hariraya_data)
        
        return {"data_hariraya": hariraya_list}
    except Exception as e:
        print(f"Error fetching hari raya by status: {e}")
        return {"error": str(e)}

# Function to search hari raya by name
async def fetch_hariraya_by_name(name: str):
    hariraya_list = []
    
    try:
        cursor = collection_hariraya.find({"nama_hari_raya": {"$regex": f"(?i){name}"}})
        
        async for document in cursor:
            # Process timestamps
            tanggal_mulai = document.get("tanggal_mulai")
            if tanggal_mulai is not None:
                tanggal_mulai_dt = datetime.fromtimestamp(tanggal_mulai)
            else:
                tanggal_mulai_dt = None

            tanggal_berakhir = document.get("tanggal_berakhir")
            if tanggal_berakhir is not None:
                tanggal_berakhir_dt = datetime.fromtimestamp(tanggal_berakhir)
            else:
                tanggal_berakhir_dt = None

            created_ts = document.get("createdAt")
            if created_ts is not None:
                created_dt = datetime.fromtimestamp(created_ts)
                created_tanggal = created_dt.date()
                created_waktu = created_dt.time()
            else:
                created_dt, created_tanggal, created_waktu = None, None, None

            updated_ts = document.get("updatedAt")
            if updated_ts is not None:
                updated_dt = datetime.fromtimestamp(updated_ts)
                updated_tanggal = updated_dt.date()
                updated_waktu = updated_dt.time()
            else:
                updated_dt, updated_tanggal, updated_waktu = None, None, None
            
            hariraya_data = {
                "_id": str(document["_id"]),
                "nama_hari_raya": document.get("nama_hari_raya", ""),
                "description": document.get("description", ""),
                "tanggal_mulai": tanggal_mulai_dt,
                "tanggal_berakhir": tanggal_berakhir_dt,
                "status_id": document.get("status_id", ""),
                "createdAt": created_dt,
                "createdDate": str(created_tanggal) if created_tanggal else None,
                "createdTime": str(created_waktu) if created_waktu else None,
                "updatedAt": updated_dt,
                "updatedDate": str(updated_tanggal) if updated_tanggal else None,
                "updateTime": str(updated_waktu) if updated_waktu else None
            }
            
            hariraya_list.append(hariraya_data)
        
        return {"data_hariraya": hariraya_list}
    
    except Exception as e:
        print(f"Error searching hari raya by name: {e}")
        return {"error": str(e)}

# Function to get hari raya by date range
async def fetch_hariraya_by_date_range(start_date: float, end_date: float):
    hariraya_list = []
    
    try:
        # Find hari raya that overlap with the given date range
        cursor = collection_hariraya.find({
            "$or": [
                # Start date falls within hari raya range
                {"$and": [
                    {"tanggal_mulai": {"$lte": start_date}},
                    {"tanggal_berakhir": {"$gte": start_date}}
                ]},
                # End date falls within hari raya range
                {"$and": [
                    {"tanggal_mulai": {"$lte": end_date}},
                    {"tanggal_berakhir": {"$gte": end_date}}
                ]},
                # Hari raya falls completely within the given range
                {"$and": [
                    {"tanggal_mulai": {"$gte": start_date}},
                    {"tanggal_berakhir": {"$lte": end_date}}
                ]}
            ]
        })
        
        async for document in cursor:
            # Process timestamps
            tanggal_mulai = document.get("tanggal_mulai")
            if tanggal_mulai is not None:
                tanggal_mulai_dt = datetime.fromtimestamp(tanggal_mulai)
            else:
                tanggal_mulai_dt = None

            tanggal_berakhir = document.get("tanggal_berakhir")
            if tanggal_berakhir is not None:
                tanggal_berakhir_dt = datetime.fromtimestamp(tanggal_berakhir)
            else:
                tanggal_berakhir_dt = None

            created_ts = document.get("createdAt")
            if created_ts is not None:
                created_dt = datetime.fromtimestamp(created_ts)
                created_tanggal = created_dt.date()
                created_waktu = created_dt.time()
            else:
                created_dt, created_tanggal, created_waktu = None, None, None

            updated_ts = document.get("updatedAt")
            if updated_ts is not None:
                updated_dt = datetime.fromtimestamp(updated_ts)
                updated_tanggal = updated_dt.date()
                updated_waktu = updated_dt.time()
            else:
                updated_dt, updated_tanggal, updated_waktu = None, None, None
            
            hariraya_data = {
                "_id": str(document["_id"]),
                "nama_hari_raya": document.get("nama_hari_raya", ""),
                "description": document.get("description", ""),
                "tanggal_mulai": tanggal_mulai_dt,
                "tanggal_berakhir": tanggal_berakhir_dt,
                "status_id": document.get("status_id", ""),
                "createdAt": created_dt,
                "createdDate": str(created_tanggal) if created_tanggal else None,
                "createdTime": str(created_waktu) if created_waktu else None,
                "updatedAt": updated_dt,
                "updatedDate": str(updated_tanggal) if updated_tanggal else None,
                "updateTime": str(updated_waktu) if updated_waktu else None
            }
            
            hariraya_list.append(hariraya_data)
        
        return {"data_hariraya": hariraya_list}
    
    except Exception as e:
        print(f"Error fetching hari raya by date range: {e}")
        return {"error": str(e)}