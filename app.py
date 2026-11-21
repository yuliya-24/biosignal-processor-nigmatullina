# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from signal_processor import process_biosignal
import uvicorn

app = FastAPI(
    title="Universal Bio-Signal Processing Server",
    description="REST API для фильтрации и извлечения параметров ЭКГ (вариант 7: pNN50).",
)


@app.post("/analyze", summary="Обработать загруженный файл сигнала")
async def analyze_signal(
    file: UploadFile = File(..., description="Файл .txt или .csv с отсчётами сигнала"),
    fs: float = Query(250.0, description="Частота дискретизации, Гц"),
):
    if not file.filename.endswith((".txt", ".csv")):
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

    analysis_result = process_biosignal(raw_signal, fs=fs)
    return {"status": "success", "fs": fs, **analysis_result}


if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=5050, reload=False)
