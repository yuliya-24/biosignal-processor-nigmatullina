# signal_processor.py
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from config import (
    DEFAULT_FS, FILTER_LOW_HZ, FILTER_HIGH_HZ, FILTER_ORDER,
    WINDOW_SEC, THRESHOLD_K, PNN50_DIFF_MS,
)


def filter_signal(raw_data: np.ndarray, fs: float, **kwargs) -> np.ndarray:
    """Полосовой фильтр Баттерворта 4-го порядка 0.5–150 Гц (вариант 7)."""
    low = kwargs.get("low", FILTER_LOW_HZ)
    high = kwargs.get("high", FILTER_HIGH_HZ)
    order = kwargs.get("order", FILTER_ORDER)

    nyq = 0.5 * fs
    # Нормируем частоты к частоте Найквиста
    high_norm = min(high / nyq, 0.99)  # защита от ошибки, если fs мала
    low_norm = low / nyq

    b, a = butter(order, [low_norm, high_norm], btype="band")
    # filtfilt = фильтрация без фазового сдвига (важно для ЭКГ!)
    filtered = filtfilt(b, a, raw_data)
    return filtered


def detect_events(filtered_data: np.ndarray, fs: float, **kwargs) -> list:
    """
    Детекция R-пиков по динамическому порогу Mean + K*Std
    в скользящем окне WINDOW_SEC секунд (вариант 7).
    """
    window_len = int(WINDOW_SEC * fs)
    k = kwargs.get("k", THRESHOLD_K)

    # 1. Огрублённый поиск кандидатов: локальные максимумы
    #    distance ~ 0.25 сек — физиологический минимум между ударами
    min_distance = int(0.25 * fs)
    candidates, _ = find_peaks(filtered_data, distance=min_distance)

    # 2. Для каждого кандидата проверяем, превышает ли он динамический порог
    r_peaks = []
    half_win = window_len // 2
    n = len(filtered_data)
    for idx in candidates:
        left = max(0, idx - half_win)
        right = min(n, idx + half_win)
        window = filtered_data[left:right]
        threshold = np.mean(window) + k * np.std(window)
        if filtered_data[idx] > threshold:
            r_peaks.append(int(idx))

    return r_peaks


def extract_features(filtered_data: np.ndarray, event_indices: list, fs: float) -> dict:
    """Расчёт pNN50 и вспомогательных признаков (вариант 7)."""
    features = {
        "mean_amplitude": float(np.mean(filtered_data)),
        "std_amplitude": float(np.std(filtered_data)),
        "n_r_peaks": len(event_indices),
    }

    if len(event_indices) < 3:
        features["pNN50"] = None
        features["mean_hr_bpm"] = None
        return features

    # RR-интервалы в секундах, затем в миллисекундах
    rr_sec = np.diff(event_indices) / fs
    rr_ms = rr_sec * 1000.0

    # pNN50: % последовательных пар RR, различающихся > 50 мс
    diffs_ms = np.abs(np.diff(rr_ms))
    pnn50 = float(np.sum(diffs_ms > PNN50_DIFF_MS) / len(diffs_ms) * 100.0)

    # Средняя ЧСС
    mean_hr = float(60.0 / np.mean(rr_sec)) if np.mean(rr_sec) > 0 else None

    features["pNN50"] = pnn50
    features["mean_hr_bpm"] = mean_hr
    features["mean_rr_ms"] = float(np.mean(rr_ms))
    return features


def process_biosignal(raw_signal_list: list, fs: float = DEFAULT_FS) -> dict:
    """Центральный конвейер обработки."""
    raw_np = np.array(raw_signal_list, dtype=float)

    filtered_np = filter_signal(raw_np, fs)
    events = detect_events(filtered_np, fs)
    features = extract_features(filtered_np, events, fs)

    return {
        "raw_signal": raw_np.tolist(),
        "filtered_signal": filtered_np.tolist(),
        "detected_events": events,
        "calculated_features": features,
    }
    