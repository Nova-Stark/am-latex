import zmq
import zmq.asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from RequestsHandle import image_router  
import redis.asyncio as redis 
import redis.exceptions 

context = zmq.asyncio.Context()

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("FastAPI starting up...")
    
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind("tcp://*:5555")
    
    try:
        redis_con = redis.Redis(decode_responses=True)
        
        redis_con.ping()
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
    return {"message": "Image PUSH server is running. POST images to /images/uploadfile/"}
