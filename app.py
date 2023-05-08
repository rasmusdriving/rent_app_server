from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime
from rent_utils import extract_info_from_pdf, create_new_rent_increase_pdf
import uvicorn


app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    with open("index.html", "r") as f:
        content = f.read()
    return content

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.filename != "":
        upload_dir = os.path.join("uploaded_files")
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, file.filename), "wb") as f:
            f.write(await file.read())
    response = {
        "filename": file.filename
    }
    return JSONResponse(response)


@app.post("/generate")
async def generate(data: dict):
    try:
        filename = data["filename"]
        new_rent = data["new_rent"]
        application_date = datetime.strptime(data["application_date"], "%Y-%m-%d")

        print(f"filename: {filename}, new_rent: {new_rent}, application_date: {application_date}")  # Debugging line

        current_dir = os.getcwd()
        upload_dir = os.path.join(current_dir, "uploaded_files")
        template_path = os.path.join(current_dir, "template.docx")

        print("Upload directory:", upload_dir)
        print("Template path:", template_path)

        pdf_path = os.path.join(upload_dir, filename)
        landlord_name, tenant_name, address, transaction_id, current_rent = extract_info_from_pdf(pdf_path)

        print(f"Extracted info: {landlord_name}, {tenant_name}, {address}, {transaction_id}, {current_rent}")  # Debugging line

        output_folder = os.path.join(current_dir, "output")
        os.makedirs(output_folder, exist_ok=True)
        output_file_name = f"Rent_Increase_{transaction_id}.docx"
        output_path = os.path.join(output_folder, output_file_name)

        print("Output folder:", output_folder)
        print("Output path:", output_path)

        service_fee = new_rent * 0.0495

        create_new_rent_increase_pdf(template_path, landlord_name, tenant_name, application_date, current_rent, new_rent, service_fee, address, transaction_id, output_path)
        os.remove(pdf_path)
        print(f"Generated file: {output_file_name} at {output_path}")  # Debugging line

        response = {
            "status": "success",
            "output_path": output_file_name
        }
        return JSONResponse(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}", include_in_schema=False)
async def download(filename: str):
    current_dir = os.getcwd()
    output_folder = os.path.join(current_dir, "output")
    file_path = os.path.join(output_folder, filename)
    return FileResponse(file_path)


if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
