from fastapi import APIRouter, UploadFile, File, HTTPException , Request
import io
from PIL import Image
from secrets import token_urlsafe
import base64
import zmq 
import redis.asyncio as redis
import redis.exceptions

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
        r_con :redis.Redis = request.app.redis_connection
        
        await push_socket.send_json(payload)#type:ignore
        try:
            await r_con.set(payload["id"],"Pending: ")
        except redis.exceptions.ConnectionError:
            print("[ERROR] Redis connection Error!")
        
        return {
            "s":"ok",
            "id":img_uid
        }
    except Exception as e:
        print(f"[ERROR] processing image upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")

@image_router.get("/result/{img_uid}",summary="Get reult.")
async def get_result(img_uid:str ,request:Request):
    """
    Hanlde polling and getting back result.!
    """
    try:
        r_con :redis.Redis = request.app.redis_connection
        
        result = await r_con.get(img_uid)
        if result is None:
            #here i think we can add a mechanism for stopping ddos attack!
            raise HTTPException(status_code=404, detail="Invalid Img_UID!")
        
        code = str(result).split(":")[0]
        
        match code:
            case "Pending":
                return {"status":"pending"}
            case "Result":
                return {"status":"done","result":code[-1]}
            case "Error":
                return {"status":"error","e":code[-1]}
            case _:
                return {"status":"unknown"}
            
    except redis.exceptions.ConnectionError as e:
        print("[ERROR] Redis connection error:",e)
        raise HTTPException(status_code=500, detail="Redis connection error")
    except Exception as e:
        print("[ERROR] Something unexpected went wrong!:",e)
        raise HTTPException(status_code=500, detail="Internal Server error")
    