import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from config import (
    DEFAULT_FS, FILTER_LOW_HZ, FILTER_HIGH_HZ, FILTER_ORDER, NYQUIST_MARGIN,
    WINDOW_SEC, THRESHOLD_K, MIN_PEAK_DISTANCE_SEC, SMOOTH_WINDOW_SEC,
    REL_AMP_MIN, REL_AMP_MAX,
    PNN50_DIFF_MS, MIN_PEAKS_FOR_FEATURES, RR_MIN_MS, RR_MAX_MS,
    RR_MAX_DEVIATION, RR_REJECT_WARN_RATIO,
    MIN_FS_HZ, MAX_FS_HZ, MIN_SIGNAL_SEC,
)


def validate_input(raw_data: np.ndarray, fs: float) -> None:
    """Проверка входа. При ошибке бросает ValueError с понятным текстом."""
    if not np.isfinite(fs) or not (MIN_FS_HZ <= fs <= MAX_FS_HZ):
        raise ValueError(
            f"fs должна быть в диапазоне {MIN_FS_HZ}-{MAX_FS_HZ} Гц, получено {fs}"
        )
    if not np.all(np.isfinite(raw_data)):
        raise ValueError("Сигнал содержит NaN или бесконечные значения")
    min_samples = int(MIN_SIGNAL_SEC * fs)
    if len(raw_data) < min_samples:
        raise ValueError(
            f"Сигнал слишком короткий: {len(raw_data)} отсчётов, нужно не менее {min_samples} "
            f"({MIN_SIGNAL_SEC} с при fs={fs})"
        )


def filter_signal(raw_data: np.ndarray, fs: float, **kwargs) -> np.ndarray:
    """Полосовой фильтр Баттерворта 4-го порядка 0.5–150 Гц (вариант 7)."""
    low = kwargs.get("low", FILTER_LOW_HZ)
    high = kwargs.get("high", FILTER_HIGH_HZ)
    order = kwargs.get("order", FILTER_ORDER)

    nyq = 0.5 * fs
    # Нормируем частоты к частоте Найквиста
    high_norm = min(high / nyq, NYQUIST_MARGIN)  # защита, если верхняя граница выше Найквиста
    low_norm = low / nyq

    b, a = butter(order, [low_norm, high_norm], btype="band")
    # filtfilt = фильтрация без фазового сдвига (важно для ЭКГ!)
    filtered = filtfilt(b, a, raw_data)
    return filtered


def _moving_average(x: np.ndarray, n: int) -> np.ndarray:
    return np.convolve(x, np.ones(n) / n, mode="same")


def detect_events(filtered_data: np.ndarray, fs: float, **kwargs) -> list:
    """
    Детекция R-пиков: сглаживание -> кандидаты -> динамический порог
    Mean + K*Std (вариант 7) -> отбор по амплитуде относительно медианы R.
    """
    k = kwargs.get("k", THRESHOLD_K)
    n = len(filtered_data)

    # Сглаживание подавляет высокочастотный шум и острые выбросы
    smooth = _moving_average(filtered_data, max(1, int(SMOOTH_WINDOW_SEC * fs)))

    #Кандидаты: локальные максимумы не ближе физиологического минимума
    candidates, _ = find_peaks(smooth, distance=int(MIN_PEAK_DISTANCE_SEC * fs))

    #Первый проход: динамический порог Mean + K*Std в окне WINDOW_SEC
    half_win = int(WINDOW_SEC * fs) // 2
    first_pass = []
    for idx in candidates:
        window = smooth[max(0, idx - half_win):min(n, idx + half_win)]
        if smooth[idx] > np.mean(window) + k * np.std(window):
            first_pass.append(int(idx))

    if len(first_pass) < MIN_PEAKS_FOR_FEATURES:
        return first_pass

    # Второй проход: опорная амплитуда R = медиана пиков первого прохода.
    ref = float(np.median(smooth[first_pass]))
    return [int(i) for i in candidates if REL_AMP_MIN * ref <= smooth[i] <= REL_AMP_MAX * ref]


def extract_features(filtered_data: np.ndarray, event_indices: list, fs: float) -> dict:
    """Расчёт pNN50 и вспомогательных признаков (вариант 7)."""
    features = {
        "mean_amplitude": float(np.mean(filtered_data)),
        "std_amplitude": float(np.std(filtered_data)),
        "n_r_peaks": len(event_indices),
        "pNN50": None,
        "mean_hr_bpm": None,
        "mean_rr_ms": None,
        "n_rr_rejected": 0,
        "warnings": [],
    }

    if len(event_indices) < MIN_PEAKS_FOR_FEATURES:
        features["warnings"].append("Найдено слишком мало R-пиков для расчёта ЧСС и pNN50")
        return features

    rr_ms = np.diff(event_indices) / fs * 1000.0

    # Фильтр физиологичности RR: диапазон + отклонение от медианы
    median_rr = np.median(rr_ms)
    valid = (
        (rr_ms >= RR_MIN_MS) & (rr_ms <= RR_MAX_MS)
        & (np.abs(rr_ms - median_rr) <= RR_MAX_DEVIATION * median_rr)
    )
    features["n_rr_rejected"] = int(np.sum(~valid))
    
    if np.mean(~valid) > RR_REJECT_WARN_RATIO:
        features["warnings"].append(
            f"Отброшено {features['n_rr_rejected']} из {len(rr_ms)} RR-интервалов: "
            "возможны шум или артефакты, результаты ненадёжны"
        )

    if not np.any(valid):
        features["warnings"].append("Нет ни одного допустимого RR-интервала")
        return features

    # pNN50: только по соседним парам, где оба RR допустимы
    pair_ok = valid[:-1] & valid[1:]
    diffs_ms = np.abs(np.diff(rr_ms))[pair_ok]
    if len(diffs_ms) > 0:
        features["pNN50"] = float(np.sum(diffs_ms > PNN50_DIFF_MS) / len(diffs_ms) * 100.0)

    mean_rr = float(np.mean(rr_ms[valid]))
    features["mean_rr_ms"] = mean_rr
    features["mean_hr_bpm"] = float(60000.0 / mean_rr)

    return features


def process_biosignal(raw_signal_list: list, fs: float = DEFAULT_FS) -> dict:
    """Центральный конвейер обработки. Бросает ValueError при некорректном входе."""
    raw_np = np.array(raw_signal_list, dtype=float)
    
    validate_input(raw_np, fs)
    
    filtered_np = filter_signal(raw_np, fs)
    events = detect_events(filtered_np, fs)
    features = extract_features(filtered_np, events, fs)

    if FILTER_HIGH_HZ > NYQUIST_MARGIN * fs / 2:
        features["warnings"].append(
            f"Верхняя граница фильтра {FILTER_HIGH_HZ} Гц выше предела для fs={fs}; "
            f"использовано {NYQUIST_MARGIN * fs / 2:.1f} Гц"
        )

    return {
        "raw_signal": raw_np.tolist(),
        "filtered_signal": filtered_np.tolist(),
        "detected_events": events,
        "calculated_features": features,
    }