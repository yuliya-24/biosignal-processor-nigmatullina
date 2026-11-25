# Параметры фильтрации для варианта 7
DEFAULT_FS = 250.0                 # частота дискретизации по умолчанию, Гц
FILTER_LOW_HZ = 0.5                # нижняя граница полосового фильтра
FILTER_HIGH_HZ = 150.0             # верхняя граница полосового фильтра
FILTER_ORDER = 4                   # порядок фильтра Баттерворта

# Детекция R-пиков
WINDOW_SEC = 2.0                   # длина скользящего окна, сек
THRESHOLD_K = 2.5                  
PNN50_DIFF_MS = 50.0               # порог разницы RR-интервалов, мс

NYQUIST_MARGIN = 0.99              

# Параметры детектора
MIN_PEAK_DISTANCE_SEC = 0.25       
SMOOTH_WINDOW_SEC = 0.04           
REL_AMP_MIN = 0.6                 
REL_AMP_MAX = 2.0                 

# Ограничения для признаков
MIN_PEAKS_FOR_FEATURES = 3         
RR_MIN_MS = 300.0                
RR_MAX_MS = 2000.0                 
RR_MAX_DEVIATION = 0.4            
RR_REJECT_WARN_RATIO = 0.1        

# Проверка входных данных
MIN_FS_HZ = 100.0                  
MAX_FS_HZ = 10000.0               
MIN_SIGNAL_SEC = 2.0              