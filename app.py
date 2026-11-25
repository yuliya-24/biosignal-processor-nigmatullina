from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from signal_processor import process_biosignal
from config import DEFAULT_FS
import uvicorn

app = FastAPI(
    title="Universal Bio-Signal Processing Server",
    description="REST API для фильтрации и извлечения параметров ЭКГ (вариант 7: pNN50).",
)

# Все ошибки возвращаются в едином формате 
@app.exception_handler(HTTPException)
async def http_error_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"status": "error", "detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422,
                        content={"status": "error", "detail": "Некорректные параметры запроса"})

@app.post("/analyze", summary="Обработать загруженный файл сигнала")
async def analyze_signal(
    file: UploadFile = File(..., description="Файл .txt или .csv с отсчётами сигнала"),
    fs: float = Query(DEFAULT_FS, description="Частота дискретизации, Гц"),
):
    if not (file.filename or "").lower().endswith((".txt", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Разрешены только .txt и .csv",
        )
    try:
        contents = await file.read()
        lines = contents.decode("utf-8").strip().splitlines()
        raw_signal = [float(line.strip()) for line in lines if line.strip()]
        if not raw_signal:
            raise ValueError("Файл пуст или не содержит числовых данных")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при парсинге файла: {e}")

    try:
        analysis_result = process_biosignal(raw_signal, fs=fs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"status": "success", "fs": fs, **analysis_result}

if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=5050, reload=False)