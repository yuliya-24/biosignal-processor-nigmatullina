import numpy as np
import os

os.makedirs("test_data", exist_ok=True)

def generate_ecg(hr_base, duration=30, fs=250, noise_level=0.05, artifact=False, path="test_data/file.txt"):
    t = np.arange(0, duration, 1/fs)
    signal = np.zeros_like(t)
    rr_base = 60 / hr_base
    
    current_time = 0.5
    while current_time < duration:
        # Добавляем вариабельность (jitter) для pNN50
        jitter = np.random.uniform(-0.015, 0.015)
        beat = current_time + jitter
        idx = int(beat * fs)
        
        if 0 < idx < len(signal) - 10:
            signal[idx:idx+10] += np.hanning(10) * 1.0
            
        current_time += rr_base

    # Добавляем шум и дрейф изолинии
    noise = np.random.normal(0, noise_level, len(signal))
    baseline_wander = 0.2 * np.sin(2 * np.pi * 0.3 * t)
    
    final_signal = signal + noise + baseline_wander
    
    # Если нужно добавить артефакт (высокоамплитудный выброс)
    if artifact:
        artifact_idx = int(duration * fs / 2)
        final_signal[artifact_idx:artifact_idx+50] += np.random.normal(0, 2.0, 50)
        
    np.savetxt(path, final_signal, fmt="%.6f")
    print(f"Создан файл: {path} (HR={hr_base} уд/мин)")

# 1. Нормальный ритм (базовый)
generate_ecg(hr_base=75, noise_level=0.05, path="test_data/raw_signal.txt")

# 2. Сигнал с высоким уровнем шума (проверка фильтра)
generate_ecg(hr_base=60, noise_level=0.3, path="test_data/noisy_signal.txt")

# 3. Сигнал с артефактом движения (проверка устойчивости детектора)
generate_ecg(hr_base=90, noise_level=0.05, artifact=True, path="test_data/artifact_signal.txt")

print("\nВсе тестовые файлы успешно сгенерированы!")