import os
import matplotlib
matplotlib.use("Agg")  # без окна: график сохраняется в файл
import matplotlib.pyplot as plt
from signal_processor import process_biosignal

FS = 250.0

CASES = [
    ("test_data/raw_signal.txt", "Нормальный ритм (75 уд/мин)", 75, 2),
    ("test_data/noisy_signal.txt", "Высокий уровень шума (60 уд/мин)", 60, 3),
    ("test_data/artifact_signal.txt", "Артефакт движения (90 уд/мин)", 90, 4),
]

def load(path):
    with open(path) as f:
        return [float(line) for line in f if line.strip()]

fig, axes = plt.subplots(len(CASES), 1, figsize=(12, 10))

for ax, (path, title, true_hr, tol) in zip(axes, CASES):
    assert os.path.exists(path), f"Файл {path} не найден (запустите generate_signal.py)"
    result = process_biosignal(load(path), fs=FS)
    
    feats = result["calculated_features"]
    events = result["detected_events"]
    filt = result["filtered_signal"]
    
    print(f"{title}: пиков={feats['n_r_peaks']}, ЧСС={feats['mean_hr_bpm']}, pNN50={feats['pNN50']}")
    
    # Проверки
    assert feats["mean_hr_bpm"] is not None, "ЧСС не рассчитана"
    assert abs(feats["mean_hr_bpm"] - true_hr) <= tol, \
        f"ЧСС {feats['mean_hr_bpm']:.1f} отличается от {true_hr} больше чем на {tol}"
    assert feats["pNN50"] is not None and 0 <= feats["pNN50"] <= 100
    
    ax.plot(filt, color="blue", linewidth=0.7, alpha=0.7)
    ax.plot(events, [filt[i] for i in events], "r.", markersize=6, label="R-пики")
    ax.set_title(f"{title} (найдено: {len(events)})")
    ax.legend(loc="upper right")

# Проверка обработки некорректного входа
for bad_signal, bad_fs in [([1, 2, 3, 4, 5], FS), (load(CASES[0][0]), 0.0)]:
    try:
        process_biosignal(bad_signal, fs=bad_fs)
        raise AssertionError("Ожидался ValueError")
    except ValueError:
        pass

print("\nВСЕ ПРОВЕРКИ ПРОЙДЕНЫ. График сохранен в test_data/all_signals.png")
plt.tight_layout()
plt.savefig("test_data/all_signals.png", dpi=120)
