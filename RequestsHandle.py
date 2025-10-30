from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict
import asyncio
import io
from PIL import Image
from secrets import token_urlsafe

image_router = APIRouter()

uploaded_images_queue: List[Dict] = []
queue_lock = asyncio.Lock() # make list operations safe in async environment

@image_router.post("/uploadfile/", summary="Upload an image file")
async def upload_image(file: UploadFile = File(...)):
    """
    Receives an image file from the client, stores it in an in-memory queue,
    and returns a confirmation message.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only image files are allowed. Use jpg/png."
        )

    try:
        image_bytes = await file.read()

        try:
            Image.open(io.BytesIO(image_bytes)).verify() 
        except Exception:
            raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only image files are allowed. Use jpg/png."
        )

        img_uid = token_urlsafe(32)
        
        async with queue_lock:
            uploaded_images_queue.append({
                "id": img_uid,
                "data": image_bytes #raw bytes
            })

        return {
            "s":"ok",
            "id":img_uid
        }
    except Exception as e:
        print(f"[ERROR] processing image upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")



@image_router.get("/queue_status/", summary="Get the current status of the image queue")
async def get_queue_status():
    """
    Returns the number of images currently in the in-memory queue.
    """
    async with queue_lock:
        return {"queue_size": len(uploaded_images_queue)}

# Optional: A route to "process" and clear items from the queue
@image_router.post("/process_next_image/", summary="Simulate processing the next image in the queue")
async def process_next_image():
    """
    Simulates taking the next image from the queue for processing.
    In a real app, this would involve actual image processing, database storage, etc.
    """
    async with queue_lock:
        if not uploaded_images_queue:
            raise HTTPException(status_code=404, detail="Image queue is empty.")

        next_image = uploaded_images_queue.pop(0) # Get and remove the first item

    # Simulate some async processing
    await asyncio.sleep(1) # e.g., for image resizing, analysis, etc.

    return {
        "message": f"Successfully processed image '{next_image['filename']}'",
        "details": {
            "filename": next_image['filename'],
            "content_type": next_