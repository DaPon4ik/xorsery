<div align="center">

![logo](images/xorsery.png)


# Xorsery 🦎
![Version](https://img.shields.io/badge/version-1.0.2-blue.svg)

[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
![XOR](https://img.shields.io/badge/XOR-encryption-ff6b6b?style=for-the-badge)
![AES-CTR](https://img.shields.io/badge/AES--CTR-256_bit-4ecdc4?style=for-the-badge)
[![Python](https://img.shields.io/bage/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54&style=flat-square)](https://www.python.org/)


##### Xorsery — инструмент для сокрытия изображений с использованием XOR и AES-CTR шифрования.

</div>

## Принцип работы:
- Публичное и секретное изображения приводятся к одному размеру
- Вычисляется XOR разница между ними
- Полученный шум шифруется AES-CTR с ключом, производным от публичного изображения (SHA256)
- Результат возвращается в виде base64 строки

Для восстановления требуются оригинальное публичное изображение и ключ.

<img src="images/screenshot1.png" alt="screen1" width="300"/>
<img src="images/screenshot2.png" alt="screen2" width="250"/>

---

## Использование

### Способ 1 — как библиотека:

```
from algorithm import encode, decode

key = encode("public.jpg", "secret.jpg", quality=50)
decode("public.jpg", key, output_path="restored.png")

```

### Способ 2 — через графический интерфейс:

Использовать пример gui-обёртки или сделать свою.

---

## API

encode(public_path, secret_path, quality=50)
- quality (1-100) — влияет на размер ключа и степень сжатия
- Возвращает: base64 ключ

decode(public_path, key, output_path=None)
- Возвращает: numpy array или путь к файлу

---

## Важно

- Из-за JPEG-сжатия восстановленное изображение теряет качество
- Для сохранения результата рекомендуется использовать PNG
- Для расшифровки требуется публичное изображение идентичное тому, которое использовалось при кодировании. Это не обязательно должен быть тот же файл, но изображение должно быть точно таким же.

---

## От себя

Я специально не стал делать кучу проверок if/else, которые можно просто вырезать из кода. Вместо этого я завязал расшифровку на саму картинку: ключ считается из неё, и если картинка левая или проверки сломаны — ключ получается неправильный, и секрет никак не достать. Отдельная проверка файлов спрятана так, что без неё внутрь попадёт каша из байтов, и код всё равно упадёт. Короче, просто удалить условия и обойти защиту не выйдет — всё развалится само.


А ещё можно было алгоритм развернуть в обратную сторону: вычесть ключ из секретных картинок и получить кучу публичных, которые расшифровываются одним и тем же ключом.