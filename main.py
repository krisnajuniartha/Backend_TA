from fastapi import FastAPI, HTTPException, File, UploadFile, status, Depends, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from models.pengguna import *
import os
import jwt
from datetime import timedelta, datetime, timezone
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, PyJWTError
from jose import jwt, JWTError
from passlib.context import CryptContext
import re
from typing import Annotated, List, Optional
import json
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import time
import uvicorn

cloudinary.config( 
    cloud_name = "dlboopyh7", 
    api_key = "673794386736921", 
    api_secret = "9P5Tu59N8RKrh-bF_7hWGZDdn7g",
    secure=True
)

from databases.penggunadatabase import (
    fetch_one_user,
    fetch_all_user,
    create_user_data,
    update_user_data,
    delete_user_data,
    update_user_photo,
    fetch_all_user_with_name,
    fetch_user_specific,
    get_user,
    fetch_pengguna_by_filter,
    get_role,
    approval_users_data,
)

from databases.purabesakihdatabase import (
    fetch_all_pura,
    fetch_one_pura,
    create_pura_data,
    update_pura_data,
    update_pura_image,
    update_pura_audio,
    delete_pura_data,
    approval_pura_data,
    fetch_pura_by_filter_status,
    fetch_pura_by_nama,
    fetch_pura_by_golongan
)

from databases.beritapuradatabase import (
    create_berita_data,
    fetch_all_berita,
    fetch_one_berita,
    update_berita_data,
    delete_berita_data,
    approval_berita_data,
    fetch_berita_by_filter_status,
    fetch_berita_by_title,
    update_berita_foto
)

from databases.harirayadatabase import (
    fetch_all_hariraya,
    fetch_one_hariraya,
    create_hariraya_data,
    update_hariraya_data,
    delete_hariraya_data,
    approval_hariraya_data,
    fetch_hariraya_by_filter_status,
    fetch_hariraya_by_name,
    fetch_hariraya_by_date_range
)

from databases.virtualtourdatabase import (
    fetch_all_virtual_tour,
    fetch_one_virtual_tour,
    create_virtual_tour_data,
    update_virtual_tour_data,
    update_virtual_tour_panorama,
    update_virtual_tour_thumbnail,
    delete_virtual_tour_data,
    fetch_virtual_tour_by_pura_id,
    fetch_virtual_tour_by_name
)

SECRET_KEY = "inikrisna"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10000

#API object
app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data:dict, expirate_delta: timedelta | None=None):
    to_encode = data.copy()
    if expirate_delta:
        expirate = datetime.now(timezone.utc) + expirate_delta
    else:
        expirate = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expirate})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt    


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"},
    )

    user = None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)    
        user = await get_user(email=token_data.email)
        if user is None:
            raise credentials_exception
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired, please login again!")
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token Invalid!")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token Invalid!")
    except AttributeError:
        raise HTTPException(status_code=400, detail="Token has expired, please login again!")
    
    return user

async def get_current_active_user(
    current_user: Annotated =[UserInDB, Depends(get_current_user)]
    ):
    if current_user.email:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
)-> Token:
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Email or Password",
            headers={"WWW-Authenticate": "Barrier"},
        )
    
    access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={
            "nama":str(user.nama),
            "sub": str(user.email),
            "foto_profile": str(user.foto_profile),
            "test": str(user.test),
            "status": str(user.status),
            "createdAtDate": str(user.createdAtDate),
            "createdAtTime": str(user.createdAtTime),
            "updatedAtTime": str(user.updatedAtTime),
            "updatedAtDate": str(user.updatedAtDate),
            "role": str(user.role)
        },
        expirate_delta=access_token_expire
    )

    return Token(
                access_token=access_token, 
                user_id=user.test, 
                nama=user.nama, 
                foto_profile=user.foto_profile, 
                email=user.email,
                createdAtTime=user.createdAtTime,
                createdAtDate=user.createdAtDate,
                updatedAtDate=user.updatedAtDate,
                updatedAtTime=user.updatedAtTime,
                role=user.role,
                status=user.status, 
                token_type="bearer"
                )

@app.get("/")
async def read_root():
    return {"message": "Hello, ini Krisna"}

@app.get("/api/userdata/getalluser")
async def get_all_users(current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_all_user()
        if response:
            return response
        raise HTTPException(404, "Empty Users Data")

@app.get("/api/userdata/getallbyname/{name}")
async def get_all_user_by_name(name: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_all_user_with_name(name)
        if response:
            return response
        raise HTTPException(404, f"There is no user with this name {name}")

#User End Point

@app.get("/api/userdata/getspesific/{email}")
async def get_specific_by_email(email: str):
    valid = re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)

    if valid:
        response = await fetch_user_specific(email)
        if not response:
            return response
        raise HTTPException(404, f"Email already exists")
    raise HTTPException(404, f"Email is not valid")


@app.get("/api/userdata/getuserbyid/{id}")
async def get_user_by_id(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_one_user(id)
    if response:
        return response
    raise HTTPException(404, f"There is no user with this id {id}")    

@app.post("/api/userdata/registeruser")
async def create_data_user(nama: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()], role_input: Annotated[str, Form()]):
    await get_specific_by_email(email)

    password_hashed = get_password_hash(password)

    response = await create_user_data(nama, email, password_hashed, role_input)
    if response:
        return response
    
    # Raise HTTPException instead of tuple
    raise HTTPException(status_code=404, detail="Something went wrong")

@app.post("/api/userdata/fetchbyfilter")
async def fetch_pengguna_by_filter_role_status(roleId: Annotated[list[str], Form()], statusId: Annotated[list[str], Form()], current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_pengguna_by_filter(roleId, statusId)
        if response:
            return response
        raise HTTPException(404, "Empty Users Data")

@app.put("/api/userdata/updateprofile/{id}", response_model=UserData)
async def update_data_user(
    id: str,
    email: Annotated[Optional[str], Form()] = None,
    nama: Annotated[Optional[str], Form()] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        if email:
            existing_user = await fetch_user_specific(email)
            if existing_user and str(existing_user["_id"]) != id:
                raise HTTPException(status_code=400, detail="Email already exists")

        update_result = await update_user_data(id, email, nama)
        if update_result:
            updated_user_from_db = await fetch_one_user(id)
            if updated_user_from_db:
                # Pastikan data dari database sesuai dengan UserData
                return UserData(
                    _id=updated_user_from_db["_id"],
                    nama=updated_user_from_db["nama"],
                    email=updated_user_from_db["email"],
                    foto_profile=updated_user_from_db.get("foto_profile"),
                    password=updated_user_from_db["password"],
                    createdAt=str(updated_user_from_db["createdAt"]),  # Konversi ke string jika perlu
                    updatedAt=str(updated_user_from_db["updatedAt"]),  # Konversi ke string jika perlu
                    status=updated_user_from_db["status_id"],  # Asumsi mapping yang benar
                    role=updated_user_from_db["role_id"]     # Asumsi mapping yang benar
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated user data")
        else:
            raise HTTPException(f"There is no user with ID: {id}", status_code=404)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")
    

@app.post("/api/files/uploadphotoprofile/{id}")
async def upload_photo_profile_pengguna(id: str, files: list[UploadFile], current_user: UserInDB = Depends(get_current_user)):
    try:
        if current_user.foto_profile != "none":
            url_link = current_user.foto_profile

            public_id = extract_public_id(url_link)

            response = cloudinary.uploader.destroy(public_id)

        uploaded_files = []

        for file in files:
            file_content = await file.read()
            response = cloudinary.uploader.upload(file_content)
            uploaded_files.append(response["secure_url"])

            await update_photo_user(id, response["secure_url"])

        timestamps = time.time()

        return {"message": "Files saved successfully", "files": uploaded_files, "updatedAt": timestamps}

    except Exception as e:
        return {"message": f"Error occurred: {str(e)}"}
        
        
def extract_public_id(secure_url):
    pattern = r"/upload/(?:v\d+/)?(.+)\.\w+$"
    match = re.search(pattern, secure_url)
    if match:
        return match.group(1)
    else:
        return None

async def update_photo_user(id: str, foto: str):
    response = await update_user_photo(id, foto)
    if response:
        return response
    raise HTTPException(404, f"There is no user with this name {id}")


@app.delete("/api/userdata/deleteuser/{id}")
async def delete_data_user(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await delete_user_data(id)
        if response == True:
            return "Successfully deleted user!"
        raise HTTPException(404, f"There is no user with this name {id}")
    
@app.get("/api/getallrole/listrole")
async def get_role_list_data():
    response = await get_role()
    if response:
        return response
    raise HTTPException(404, f"There is no data role!")

@app.put("/api/userdata/approval/{id}")
async def update_data_approval_users(id: str, status: Annotated[str, Form()], current_user: UserInDB = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")

    # Validasi input status (opsional, tergantung kebutuhan)
    if not status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status tidak boleh kosong")

    response = await approval_users_data(id, status)

    if response:
        return response
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tidak ada data pengguna dengan ID {id}")

# Berita Besakih End Point

@app.get("/api/beritadata/getallberita")
async def get_all_berita_data():
    response = await fetch_all_berita()
    return response

@app.get("/api/beritadata/getoneberita/{id}")
async def get_one_berita_data(id: str):
    response = await fetch_one_berita(id)
    if response:
        return response
    raise HTTPException(404, f"Berita dengan ID {id} tidak ditemukan")

@app.get("/api/beritadata/search/{title}")
async def search_berita_by_title_data(title: str):
    response = await fetch_berita_by_title(title)
    return response

@app.post("/api/beritadata/filterstatus")
async def get_berita_by_status_data(statusId: Annotated[list[str], Form()], current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        if not statusId:
            raise HTTPException(400, "Parameter statusId diperlukan")
        response = await fetch_berita_by_filter_status(statusId)
        if response:
            return response
        raise HTTPException(404, "Data tidak ditemukan untuk filter yang diberikan")


@app.post("/api/beritadata/createberita")
async def create_berita_data_endpoint(
    judul_berita: str = Form(...),
    description: str = Form(...),
    foto: UploadFile = File(...),
    status: str = Form("678a4449e3ce40b8dc1f014c"),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    try:
        # Upload foto ke cloudinary
        result = cloudinary.uploader.upload(
            foto.file,
            folder="berita",
            resource_type="auto"
        )
        
        foto_url = result.get("secure_url")
        
        # Buat berita di database
        response = await create_berita_data(judul_berita, description, foto_url, status)
        return response
    except Exception as e:
        raise HTTPException(500, f"Gagal membuat berita: {str(e)}")

@app.put("/api/beritadata/updateberita/{id}")
async def update_berita_data_endpoint(
    id: str, 
    judul_berita: Optional[str] = Form(None), 
    description: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    berita = await fetch_one_berita(id)
    if not berita:
        raise HTTPException(404, f"Berita dengan ID {id} tidak ditemukan")
    
    # Update judul dan deskripsi
    if judul_berita is not None or description is not None:
        await update_berita_data(id, judul_berita, description)
    
    # Update foto jika disediakan
    if foto:
        try:
            # Upload foto baru ke cloudinary
            result = cloudinary.uploader.upload(
                foto.file,
                folder="berita-pura",  # Sesuaikan dengan folder di Cloudinary
                resource_type="auto"
            )
            
            foto_url = result.get("secure_url")
            
            # Update foto berita di database
            await update_berita_foto(id, foto_url)
        except Exception as e:
            raise HTTPException(500, f"Gagal memperbarui foto berita: {str(e)}")
    
    # Ambil data berita yang sudah diupdate
    updated_berita = await fetch_one_berita(id)
    return {"message": "Berita berhasil diperbarui", "berita": updated_berita}


@app.put("/api/beritadata/approval/{id}")
async def update_data_approval_berita(
    id: str, 
    status: Annotated[str, Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")

    # Validasi input status
    if not status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status tidak boleh kosong")
    
    berita = await fetch_one_berita(id)
    if not berita:
        raise HTTPException(404, f"Berita dengan ID {id} tidak ditemukan")
    
    response = await approval_berita_data(id, status)
    return {"message": response}

@app.delete("/api/beritadata/deleteberita/{id}")
async def delete_berita_data_endpoint(id: str, current_user: UserInDB = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    berita = await fetch_one_berita(id)
    if not berita:
        raise HTTPException(404, f"Berita dengan ID {id} tidak ditemukan")
    
    success = await delete_berita_data(id)
    if success:
        return {"message": f"Berita dengan ID {id} berhasil dihapus"}
    raise HTTPException(500, f"Gagal menghapus berita dengan ID {id}")


# Hari Raya End Point

@app.get("/api/hariraya")
async def get_all_hariraya(current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_all_hariraya()
        return response

# Endpoint to get hari raya by ID
@app.get("/api/hariraya/{id}")
async def get_hariraya(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_one_hariraya(id)
        if response:
            return response
        raise HTTPException(404, f"Hari raya dengan ID {id} tidak ditemukan")

# Endpoint to create new hari raya
@app.post("/api/hariraya/create")
async def create_hariraya(
    nama_hari_raya: Annotated[str, Form()],
    description: Annotated[str, Form()], 
    tanggal_mulai: Annotated[float, Form()],
    tanggal_berakhir: Annotated[float, Form()],
    status_id: Annotated[str, Form()] = "678a4449e3ce40b8dc1f014c",
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await create_hariraya_data(nama_hari_raya, description, tanggal_mulai, tanggal_berakhir, status_id)
        return response

# Endpoint to update hari raya data
@app.put("/api/hariraya/update/{id}")
async def update_hariraya(
    id: str,
    nama_hari_raya: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    tanggal_mulai: Annotated[Optional[float], Form()] = None,
    tanggal_berakhir: Annotated[Optional[float], Form()] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await update_hariraya_data(id, nama_hari_raya, description, tanggal_mulai, tanggal_berakhir)
        return response

# Endpoint to delete hari raya
@app.delete("/api/hariraya/delete/{id}")
async def delete_hariraya(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await delete_hariraya_data(id)
        if response:
            return {"message": f"Hari raya dengan ID {id} berhasil dihapus"}
        raise HTTPException(404, f"Hari raya dengan ID {id} tidak ditemukan")

# Endpoint to change hari raya status
@app.put("/api/hariraya/approval/{id}")
async def approval_hariraya(
    id: str, 
    status_id: Annotated[str, Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await approval_hariraya_data(id, status_id)
        return {"message": response}

# Endpoint to filter hari raya by status
@app.post("/api/hariraya/filterstatus")
async def get_hariraya_by_status(
    statusId: Annotated[list[str], Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        if not statusId:
            raise HTTPException(400, "Parameter statusId diperlukan")
        response = await fetch_hariraya_by_filter_status(statusId)
        if response:
            return response
        raise HTTPException(404, "Data tidak ditemukan untuk filter yang diberikan")

# Endpoint to search hari raya by name
@app.get("/api/hariraya/search/{name}")
async def search_hariraya_by_name(
    name: str,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await fetch_hariraya_by_name(name)
        return response

# Endpoint to get hari raya by date range
@app.post("/api/hariraya/bydate")
async def get_hariraya_by_date(
    start_date: Annotated[float, Form()],
    end_date: Annotated[float, Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await fetch_hariraya_by_date_range(start_date, end_date)
        return response


# Pura Besakih Endpoint

@app.get("/api/pura-besakih")
async def get_all_pura(current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_all_pura()
        return response

# Endpoint to get pura besakih by ID
@app.get("/api/pura-besakih/{id}")
async def get_pura(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await fetch_one_pura(id)
        if response:
            return response
        raise HTTPException(404, f"Pura dengan ID {id} tidak ditemukan")

# Endpoint to create new pura besakih
@app.post("/api/pura-besakih/create")
async def create_pura(
    nama_pura: Annotated[str, Form()],
    description: Annotated[str, Form()],
    hariraya_id: Annotated[List[str], Form()],
    golongan_id: Annotated[str, Form()],
    status_id: Annotated[str, Form()] = "678a4449e3ce40b8dc1f014c",
    audio_file: UploadFile = File(None),
    image_file: UploadFile = File(None),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        try:
            # Upload image to cloudinary if provided
            image_url = "none"
            if image_file:
                contents = await image_file.read()
                # Upload image to cloudinary
                upload_result = cloudinary.uploader.upload(
                    contents,
                    folder="pura_besakih",
                    resource_type="image"
                )
                image_url = upload_result.get("secure_url")
            
            # Upload audio to cloudinary if provided
            audio_url = "none"
            if audio_file:
                audio_contents = await audio_file.read()
                # Upload audio to cloudinary
                audio_upload_result = cloudinary.uploader.upload(
                    audio_contents,
                    folder="pura_besakih_audio",
                    resource_type="auto"
                )
                audio_url = audio_upload_result.get("secure_url")
            
            # Create pura data
            response = await create_pura_data(
                nama_pura=nama_pura,
                description=description,
                audio_description=audio_url,
                image_pura=image_url,
                hariraya_id=hariraya_id,
                golongan_id=golongan_id,
                status_id=status_id
            )
            
            return response
        except Exception as e:
            raise HTTPException(500, f"Error creating pura: {str(e)}")

# Endpoint to update pura besakih
@app.put("/api/pura-besakih/update/{id}")
async def update_pura(
    id: str,
    nama_pura: Annotated[str, Form()] = None,
    description: Annotated[str, Form()] = None,
    hariraya_id: Annotated[List[str], Form()] = None,
    golongan_id: Annotated[str, Form()] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await update_pura_data(
            id=id,
            nama_pura=nama_pura,
            description=description,
            hariraya_id=hariraya_id,
            golongan_id=golongan_id
        )
        return response

# Endpoint to update pura image
@app.put("/api/pura-besakih/update-image/{id}")
async def update_image(
    id: str,
    image_file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        try:
            contents = await image_file.read()
            # Upload image to cloudinary
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="pura_besakih",
                resource_type="image"
            )
            image_url = upload_result.get("secure_url")
            
            # Update pura image
            response = await update_pura_image(id, image_url)
            if response:
                return {"message": "Image updated successfully", "image_url": image_url}
            else:
                raise HTTPException(404, f"Pura dengan ID {id} tidak ditemukan")
        except Exception as e:
            raise HTTPException(500, f"Error updating pura image: {str(e)}")

# Endpoint to update pura audio
@app.put("/api/pura-besakih/update-audio/{id}")
async def update_audio(
    id: str,
    audio_file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        try:
            contents = await audio_file.read()
            # Upload audio to cloudinary
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="pura_besakih_audio",
                resource_type="auto"
            )
            audio_url = upload_result.get("secure_url")
            
            # Update pura audio
            response = await update_pura_audio(id, audio_url)
            if response:
                return {"message": "Audio updated successfully", "audio_url": audio_url}
            else:
                raise HTTPException(404, f"Pura dengan ID {id} tidak ditemukan")
        except Exception as e:
            raise HTTPException(500, f"Error updating pura audio: {str(e)}")

# Endpoint to delete pura besakih
@app.delete("/api/pura-besakih/delete/{id}")
async def delete_pura(id: str, current_user: UserInDB = Depends(get_current_user)):
    if current_user:
        response = await delete_pura_data(id)
        if response:
            return {"message": f"Pura dengan ID {id} berhasil dihapus"}
        raise HTTPException(404, f"Pura dengan ID {id} tidak ditemukan")

# Endpoint to approve/change status pura besakih
@app.put("/api/pura-besakih/approval/{id}")
async def approve_pura(
    id: str,
    status_id: Annotated[str, Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await approval_pura_data(id, status_id)
        return {"message": response}

# Endpoint to filter pura by status
@app.post("/api/pura-besakih/filterstatus")
async def filter_pura_by_status(
    statusId: Annotated[list[str], Form()],
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        if not statusId:
            raise HTTPException(400, "Parameter statusId diperlukan")
        response = await fetch_pura_by_filter_status(statusId)
        if response:
            return response
        raise HTTPException(404, "Data tidak ditemukan untuk filter yang diberikan")

# Endpoint to search pura by name
@app.get("/api/pura-besakih/search")
async def search_pura(
    nama: str,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await fetch_pura_by_nama(nama)
        return response

# Endpoint to filter pura by golongan
@app.get("/api/pura-besakih/filter/golongan")
async def filter_by_golongan(
    golongan: str,
    current_user: UserInDB = Depends(get_current_user)
):
    if current_user:
        response = await fetch_pura_by_golongan(golongan)
        return response



# Virtual Tour End Point

@app.get("/api/virtualtourdata/getallvirtualtour")
async def get_all_virtual_tour_data():
    response = await fetch_all_virtual_tour()
    return response

@app.get("/api/virtualtourdata/getonevirtualtour/{id}")
async def get_one_virtual_tour_data(id: str):
    response = await fetch_one_virtual_tour(id)
    if response:
        return response
    raise HTTPException(404, f"Virtual tour dengan ID {id} tidak ditemukan")

@app.get("/api/virtualtourdata/search/{name}")
async def search_virtual_tour_by_name_data(name: str):
    response = await fetch_virtual_tour_by_name(name)
    return response

@app.get("/api/virtualtourdata/bypuraid/{pura_id}")
async def get_virtual_tour_by_pura_id_data(pura_id: str):
    response = await fetch_virtual_tour_by_pura_id(pura_id)
    return response

@app.post("/api/virtualtourdata/createvirtualtour")
async def create_virtual_tour_data_endpoint(
    nama_virtual_path: str = Form(...),
    description_area: str = Form(...),
    panorama: UploadFile = File(...),
    thumbnail: UploadFile = File(...),
    pura_id: str = Form(""),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tidak terautentikasi"
        )

    try:
        # Upload panorama ke Cloudinary
        panorama_result = cloudinary.uploader.upload(
            panorama.file,
            folder="virtual-tour",
            resource_type="auto"
        )
        panorama_url = panorama_result.get("secure_url")

        # Upload thumbnail ke Cloudinary
        thumbnail_result = cloudinary.uploader.upload(
            thumbnail.file,
            folder="virtual-tour-thumbnails",
            resource_type="auto"
        )
        thumbnail_url = thumbnail_result.get("secure_url")

        # Buat virtual tour di database (TANPA kirim order_index lagi)
        response = await create_virtual_tour_data(
            nama_virtual_path,
            description_area,
            panorama_url,
            thumbnail_url,
            pura_id
        )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membuat virtual tour: {str(e)}"
        )

@app.put("/api/virtualtourdata/updatevirtualtour/{id}")
async def update_virtual_tour_data_endpoint(
    id: str, 
    nama_virtual_path: Optional[str] = Form(None), 
    description_area: Optional[str] = Form(None),
    order_index: Optional[str] = Form(None),
    pura_id: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    virtual_tour = await fetch_one_virtual_tour(id)
    if not virtual_tour:
        raise HTTPException(404, f"Virtual tour dengan ID {id} tidak ditemukan")
    
    # Update data virtual tour
    response = await update_virtual_tour_data(id, nama_virtual_path, description_area, order_index, pura_id)
    
    # Ambil data virtual tour yang sudah diupdate
    updated_virtual_tour = await fetch_one_virtual_tour(id)
    return {"message": "Virtual tour berhasil diperbarui", "virtual_tour": updated_virtual_tour}

@app.put("/api/virtualtourdata/updatepanorama/{id}")
async def update_virtual_tour_panorama_endpoint(
    id: str, 
    panorama: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    virtual_tour = await fetch_one_virtual_tour(id)
    if not virtual_tour:
        raise HTTPException(404, f"Virtual tour dengan ID {id} tidak ditemukan")
    
    try:
        # Upload panorama baru ke cloudinary
        result = cloudinary.uploader.upload(
            panorama.file,
            folder="virtual-tour",
            resource_type="auto"
        )
        
        panorama_url = result.get("secure_url")
        
        # Update panorama virtual tour di database
        await update_virtual_tour_panorama(id, panorama_url)
        
        # Ambil data virtual tour yang sudah diupdate
        updated_virtual_tour = await fetch_one_virtual_tour(id)
        return {"message": "Panorama virtual tour berhasil diperbarui", "virtual_tour": updated_virtual_tour}
    except Exception as e:
        raise HTTPException(500, f"Gagal memperbarui panorama virtual tour: {str(e)}")

@app.put("/api/virtualtourdata/updatethumbnail/{id}")
async def update_virtual_tour_thumbnail_endpoint(
    id: str, 
    thumbnail: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    virtual_tour = await fetch_one_virtual_tour(id)
    if not virtual_tour:
        raise HTTPException(404, f"Virtual tour dengan ID {id} tidak ditemukan")
    
    try:
        # Upload thumbnail baru ke cloudinary
        result = cloudinary.uploader.upload(
            thumbnail.file,
            folder="virtual-tour-thumbnails",
            resource_type="auto"
        )
        
        thumbnail_url = result.get("secure_url")
        
        # Update thumbnail virtual tour di database
        await update_virtual_tour_thumbnail(id, thumbnail_url)
        
        # Ambil data virtual tour yang sudah diupdate
        updated_virtual_tour = await fetch_one_virtual_tour(id)
        return {"message": "Thumbnail virtual tour berhasil diperbarui", "virtual_tour": updated_virtual_tour}
    except Exception as e:
        raise HTTPException(500, f"Gagal memperbarui thumbnail virtual tour: {str(e)}")

@app.delete("/api/virtualtourdata/deletevirtualtour/{id}")
async def delete_virtual_tour_data_endpoint(id: str, current_user: UserInDB = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tidak terautentikasi")
        
    virtual_tour = await fetch_one_virtual_tour(id)
    if not virtual_tour:
        raise HTTPException(404, f"Virtual tour dengan ID {id} tidak ditemukan")
    
    success = await delete_virtual_tour_data(id)
    if success:
        return {"message": f"Virtual tour dengan ID {id} berhasil dihapus"}
    raise HTTPException(500, f"Gagal menghapus virtual tour dengan ID {id}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
