import os 
from dotenv import load_dotenv 
from PIL import Image
from pix2tex.cli import LatexOCR
import io 
import base64
import zmq 
import redis 
import redis.exceptions
from multiprocessing import Process

load_dotenv()

NUM_WORKERS = int(os.getenv("NUM_WORKERS"))#type:ignore


def worker():
    
    context = zmq.Context()
    
    socket = context.socket(zmq.PULL)
    socket.connect("tcp://localhost:5555")
    model = LatexOCR()
    try:
        redis_con = redis.Redis(decode_responses=True)
        
        redis_con.ping()
    except redis.exceptions.ConnectionError:
        print("[ERROR] Cant Connect to Redis server!")
        exit()
         
    while True:
        try:
            
            task :dict = socket.recv_json()#type:ignore
            img_uid = task["id"]
            
            img_b64_string = task["data"]
            try:
                img_bytes = base64.b64decode(img_b64_string)
                img_stream = io.BytesIO(img_bytes)
                img = Image.open(img_stream)
                result = model(img)
                img_stream.close()
                
                redis_con.set(img_uid,f"Result:{str(result)}")
            except Exception as ex:
                redis_con.set(img_uid,f"Error:{ex}")
            finally:
                continue
            
                
            
                 
        except Exception as e:
            print("[ERROR] Unexpected Error while processing image: ",e)
            
            
def runworker():
    t = [Process(target=worker) for _ in range(NUM_WORKERS)]
    
    for i in t:
        i.start()
        
    for i in t:
        i.join()
        
