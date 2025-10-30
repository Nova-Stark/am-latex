import zmq
import zmq.asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from RequestsHandle import image_router  

context = zmq.asyncio.Context()

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("FastAPI starting up...")
    
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind("tcp://*:5555")
    
    app.state.zmq_socket = push_socket
    print("ZMQ PUSH socket bound to tcp://*:5555")
    
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
