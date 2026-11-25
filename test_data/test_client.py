import requests
import matplotlib.pyplot as plt

FILE_PATH = "test_data/raw_signal.txt"
FS = 250.0
URL = "http://localhost:5050/analyze"

print(f"Отправка файла {FILE_PATH} на сервер...")

try:
    with open(FILE_PATH, "rb") as f:
        files = {"file": (FILE_PATH.split("/")[-1], f, "text/plain")}
        params = {"fs": FS}
        resp = requests.post(URL, files=files, params=params)

    print("HTTP статус:", resp.status_code)

    if resp.status_code == 200:
        data = resp.json()
        print("Рассчитанные признаки:", data["calculated_features"])

        raw = data["raw_signal"]
        filt = data["filtered_signal"]
        events = data["detected_events"]

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        axes[0].plot(raw, color="gray", linewidth=0.7)
        axes[0].set_title("Исходный сигнал (сгенерированный)")
        
        axes[1].plot(filt, color="blue", linewidth=0.9)
        if events:
            axes[1].plot(events, [filt[i] for i in events], "r.", markersize=8, label="R-пики")
        
        axes[1].set_title(f"Отфильтрованный сигнал + R-пики (найдено: {len(events)})")
        axes[1].legend()
        
        plt.tight_layout()
        plt.show()
    else:
        print("Ошибка сервера:", resp.text)

except FileNotFoundError:
    print(f"ОШИБКА: Файл {FILE_PATH} не найден. Сначала запустите generate_signal.py!")