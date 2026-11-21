import numpy as np
import os

# Создаем папку test_data, если ее нет
os.makedirs("test_data", exist_ok=True)

# Параметры
fs = 250
duration = 30  # 30 секунд записи
t = np.arange(0, duration, 1/fs)
signal = np.zeros_like(t)

# Генерируем удары сердца (примерно 75 уд/мин)
hr = 75
rr = 60 / hr

# Добавляем небольшую вариабельность ритма (чтобы pNN50 было не 0)
for beat in np.arange(0.5, duration, rr):
    # случайное отклонение в 10 мс
    jitter = np.random.uniform(-0.01, 0.01) 
    idx = int((beat + jitter) * fs)
    
    if idx < len(signal) and idx + 10 < len(signal):
        # Форма QRS-комплекса (треугольный импульс)
        signal[idx:idx+10] += np.hanning(10) * 1.0

# Добавляем шум и дрейф изолинии (как в реальной ЭКГ)
noise = np.random.normal(0, 0.05, len(signal))
baseline_wander = 0.2 * np.sin(2 * np.pi * 0.3 * t)

final_signal = signal + noise + baseline_wander

# Сохраняем в файл
np.savetxt("test_data/raw_signal.txt", final_signal, fmt="%.6f")
print(f"Файл test_data/raw_signal.txt успешно создан! ({len(final_signal)} отсчетов)")