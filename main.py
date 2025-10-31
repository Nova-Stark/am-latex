import zmq
import zmq.asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from RequestsHandle import image_router  
import redis.asyncio as aredis 
import redis.exceptions 
from worker import runworker,Process
import uvicorn
import os 
from dotenv import load_dotenv
load_dotenv()

context = zmq.asyncio.Context()

INFO = bool(os.getenv("INFO"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("FastAPI starting up...")
    
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind("tcp://*:5555")
    
    try:
        redis_con = aredis.Redis(decode_responses=True)
        
        await redis_con.ping()#type:ignore
    except redis.exceptions.ConnectionError:
        print("[ERROR] Cant Connect to Redis server!")
        exit()
    app.state.zmq_socket = push_socket
    print("ZMQ PUSH socket bound to tcp://*:5555")
    app.state.redis_connection = redis_con
    
    yield  
    
    print("FastAPI shutting down...")
    app.state.zmq_socket.close()
    context.term()
    print("ZMQ socket and FastAPI closed.")

app = FastAPI(lifespan=lifespan)

app.include_router(image_router, prefix="/images")

@app.get("/")
async def root():
    if INFO:
        print("[INFO] root initiated!")
    return {"message": "Image PUSH server is running. POST images to /images/uploadfile/"}


if __name__=="__main__":
    
    child_controller_pro = Process(target=runworker)
    
    try:
        
        child_controller_pro.start()
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False 
        )
        
    except KeyboardInterrupt:
        print("Shutting Down from Keyboard Interrupt")
    finally:
        if child_controller_pro.is_alive():
            child_controller_pro.terminate()
            child_controller_pro.join()
            
        print("Closing...")
        
