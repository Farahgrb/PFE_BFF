import os
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import requests
import tempfile
import json
import uuid
import arabic_reshaper
from bidi.algorithm import get_display
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiohttp import ClientResponse, FormData, ClientSession, ClientConnectorError, ContentTypeError
from pydantic import BaseModel
from typing import Optional, Generic,TypeVar
from pydantic.generics import GenericModel


app = FastAPI()





class id_text(BaseModel):
    id:Optional[str]=None
T = TypeVar("T")
class Response(GenericModel, Generic[T]):
    code: str
    status: str
    message: str
    result: Optional[T]

origins = [
    "http://localhost",
    "http://localhost:3000",  # Update with your React app's URL
    # Add more origins if needed
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

asr_microservice_url = os.getenv("ASR_MICROSERVICE_URL", "http://127.0.0.1:9001")
classification_microservice_url = os.getenv("CLASSIFICATION_MICROSERVICE_URL", "http://127.0.0.1:9002")



class TextInput(BaseModel):
    text: str

async def file_to_data(payload_obj) -> FormData:
    """
    Args:
        payload_obj: convert file to aio http form data so it can be send in the request
    Returns: aiohttp FormData that could be used on async methods
    """
    temp = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    temp.name = payload_obj.filename
    data = FormData()
    try:
        temp.writelines(payload_obj.file)
        temp.seek(0)
        data.add_field('wav', temp.read(), filename=payload_obj.filename)
        temp.close()
    except Exception as exception:
      print("hi")
    return data


import arabic_reshaper
from bidi.algorithm import get_display


@app.get('/')
async def Home():
    return "welcome from BFF"

# @app.post("/transcribe")
# async def transcribe(file: UploadFile = File(...), device="cpu"):
#     print(file)

#     async with ClientSession() as session:
#         request = getattr(session, "post")
#         async with request(
#                 url=f"{asr_microservice_url}/transcribe",
#                 data=await file_to_data(file),
#         ) as response:
#             response_text = await response.text(encoding='utf-8')
#             transcription = json.loads(response_text)

#             reshaped_text = arabic_reshaper.reshape(transcription.get("Transcription"))
#             display_text = get_display(reshaped_text)

#         async with ClientSession() as session2:
#             print(display_text)
#             async with session2.post(
#                     url=f"{classification_microservice_url}/classify",
#                     json={"text": display_text},
#             ) as response1:
#                 response1_text = await response1.text(encoding='utf-8')
#                 print(response1_text)
#                 label = json.loads(response1_text)
     
        

#         return {"Transcription": transcription["Transcription"], "label": label["label"]}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), device="cpu"):
    try:
        async with ClientSession() as session:
            # Transcribe the audio file using ASR microservice
            async with session.post(
                url=f"{asr_microservice_url}/transcribe",
                data=await file_to_data(file),
            ) as response:
                response.raise_for_status()
                transcription = await response.json()
                reshaped_text = arabic_reshaper.reshape(transcription.get("Transcription"))
                display_text = get_display(reshaped_text)

            # Classify the transcribed text using classification microservice
            async with session.post(
                url=f"{classification_microservice_url}/detection/classify_create",
                json={"text": reshaped_text},
            ) as response1:
                response1.raise_for_status()
                label = await response1.json()

        return {"Transcription": transcription["Transcription"], "label": label["label"]}
    
    except Exception as e:
        return {"error": str(e)}


@app.post("/file-upload")
async def file_upload(file: UploadFile):
    # Save the uploaded file to a desired location
    with open(file.filename, "wb") as f:
        contents = await file.read()
        f.write(contents)

    # Return a response indicating the successful upload
    return {"message": "File uploaded successfully"}
    
@app.post('/classifytext')
async def classify_text(text_input: dict):
    try:
        
        # text_input = await request.json()
     
        response = requests.post(f"{classification_microservice_url}/detection/classify_create", json=text_input)
        response.raise_for_status()
        print(text_input)
        result = response.text

        api_response_dict = json.loads(result)
      
        return api_response_dict
    except requests.exceptions.RequestException as e:
        # Handle errors from the classification microservice
        print("Error: ", e)
        return None

@app.delete('/delete')
def delete_row(request:id_text):
    db_response_del = requests.delete(f"{classification_microservice_url}/detection/delete", json=request.dict())
    return Response(status="Ok", code="200", message="Success delete data").dict(exclude_none=True)

@app.patch("/update")
async def update_detection_bff(request: dict):

    try:
        response = requests.patch(f"{classification_microservice_url}/detection/update", json=request)
        response.raise_for_status()
        return Response(status="Ok", code="200", message="Success delete data").dict(exclude_none=True)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Error communicating with the microservice")
@app.get("/fetch")
def get_rows():
    response = requests.get(f"{classification_microservice_url}/detection/all")

    # Check if the request was successful (status code 200)
    try:
        db_response = response.json()  # Assuming the response is in JSON format
       
        return db_response
    except requests.exceptions.RequestException as e:
        return e



if __name__ == '__main__':
    uvicorn.run("main:app", host='127.0.0.1', port=9000, reload=True)
