import matplotlib.pyplot as plt
from signal_processor import process_biosignal
import os

FILES_TO_TEST = [
    ("test_data/raw_signal.txt", "Нормальный ритм (75 уд/мин)"),
    ("test_data/noisy_signal.txt", "Высокий уровень шума"),
    ("test_data/artifact_signal.txt", "Артефакт движения")
]

FS = 250.0

fig, axes = plt.subplots(3, 1, figsize=(12, 12))

for i, (filepath, title) in enumerate(FILES_TO_TEST):
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден!")
        continue
        
    print(f"\nОбработка: {title}")
    
    # Чтение
    raw_signal = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                raw_signal.append(float(line))
                
    # Обработка
    result = process_biosignal(raw_signal, fs=FS)
    features = result["calculated_features"]
    events = result["detected_events"]
    
    print(f"  Найдено R-пиков: {features['n_r_peaks']}")
    print(f"  ЧСС: {features.get('mean_hr_bpm', 0):.1f} уд/мин")
    print(f"  pNN50: {features.get('pNN50', 0):.1f} %")
    
    # Построение
    ax = axes[i]
    ax.plot(result["filtered_signal"], color="blue", linewidth=0.7, alpha=0.7)
    if events:
        filt = result["filtered_signal"]
        ax.plot(events, [filt[j] for j in events], "r.", markersize=6, label="R-пики")
    
    ax.set_title(f"{title} (найдено: {len(events)})")
    ax.legend(loc="upper right")

plt.tight_layout()
plt.show()