from fastapi import APIRouter, UploadFile, File, HTTPException , Request
import io
from PIL import Image
from secrets import token_urlsafe
import base64
import zmq 

image_router = APIRouter()


@image_router.post("/uploadfile/", summary="Upload an image file")
async def upload_image(request:Request , file: UploadFile = File(...)):
    """
    Receives an image file from the client, stores it in zeromq push queue,
    and return id.
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
        
        payload= {
                "id": img_uid,
                "data": base64.b64encode(image_bytes).decode('utf-8')
            }
        
        push_socket :zmq.Socket= request.app.state.zmq_socket
        
        await push_socket.send_json(payload)#type:ignore

        return {
            "s":"ok",
            "id":img_uid
        }
    except Exception as e:
        print(f"[ERROR] processing image upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")
