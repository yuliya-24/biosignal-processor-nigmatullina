# biosignal-processor: REST API для фильтрации ЭКГ и расчёта pNN50

Веб-сервер на FastAPI: принимает файл с отсчётами ЭКГ, фильтрует сигнал, находит R-пики и считает pNN50 (вариант 7).

## Структура проекта

- `app.py` — сервер и маршруты, валидация входа
- `signal_processor.py` — фильтрация, поиск R-пиков, расчёт признаков 
- `config.py` — все параметры и пороги
- `test_data/` — `raw_signal.txt`, `noisy_signal.txt`, `artifact_signal.txt`, `test_client.py`
- `test_all_signals.py`, `generate_signal.py` — автотест и генератор данных

## Развёртывание

```bash
git clone https://github.com/yuliya-24/biosignal-processor-nigmatullina.git
cd biosignal-processor-nigmatullina
git checkout dev
python -m venv venv
venv\Scripts\activate        
pip install -r requirements.txt
python app.py
```

Сервер доступен по адресу http://localhost:5050.

## Алгоритм

1. Полосовой фильтр Баттерворта 4-го порядка, 0,5–150 Гц, `filtfilt`.
2. Сглаживание скользящим средним 40 мс, поиск локальных максимумов не ближе 0,25 с.
3. Порог Mean + 2,5·Std в окне 2 с; затем отбор пиков с амплитудой 0,6–2,0 от медианы R (отсекает шум и артефакты).
4. RR-интервалы вне 300–2000 мс и дальше 40 % от медианы отбрасываются.
5. pNN50 = доля соседних пар RR, различающихся более чем на 50 мс, в процентах.

Все числа заданы в `config.py`.

## Тестирование

```bash
python generate_signal.py     # создаёт три тестовых файла (seed = 42)
python test_all_signals.py    # проверяет ЧСС и обработку ошибок
python test_data/test_client.py   # при запущенном сервере, строит графики
```


