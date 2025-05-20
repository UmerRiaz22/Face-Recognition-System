import os
import cv2
import numpy as np
import face_recognition
import psycopg2
import io
import base64
from fastapi import FastAPI, UploadFile, File, Form, Response
from PIL import Image
import uvicorn
import matplotlib
matplotlib.use('agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
from Helper import FaceDBManager


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

face_manager = FaceDBManager()

@app.post("/register")
async def register_user_endpoint(secret: str = Form(...), username: str = Form(...), file: UploadFile = File(...)):
    if secret != "99tech3344":
        return {"message": "Invalid secret key"}
    file_bytes = await file.read()
    img = Image.open(io.BytesIO(file_bytes))
    img_np = np.array(img)
    encoded_img = face_manager.register_user(img_np, username, return_image=True)
    if encoded_img == "No face found in image":
        return {"message": "No face detected in the image. Please try another—ensure the face is clearly visible."}
    if encoded_img is None:
        return {"message": "User already registered."}
    return Response(content=encoded_img, media_type="image/jpeg")

@app.post("/verify")
async def verify_user_endpoint(secret: str = Form(...), file: UploadFile = File(...), tolerance: float = Form(default=0.6)):
    if secret != "99tech3344":
        return {"message": "Invalid secret key"}
    file_bytes = await file.read()
    img = Image.open(io.BytesIO(file_bytes))
    img_np = np.array(img)
    encoded_img = face_manager.verify_user(img_np, tolerance=tolerance, return_image=True)
    if encoded_img is None:
        return {"message": "No face found in image."}
    return Response(content=encoded_img, media_type="image/jpeg")

@app.get("/list-users")
def list_users_endpoint(secret: str = Form(...)):
    if secret != "99tech3344":
        return {"message": "Invalid secret key"}
    users = face_manager.list_users()
    return users



@app.delete("/delete-user/{user_id}")
def delete_user_endpoint(secret: str = Form(...), user_id: int = Form(...)):
    if secret != "99tech3344":
        return {"message": "Invalid secret key"}
    face_manager.delete_user(user_id)
    return {"message": f"User with ID {user_id} deleted."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)