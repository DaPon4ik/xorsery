import cv2
import numpy as np
import base64
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hmac

CANON_SIZE = 64
CANON_BLUR = 3
CANON_HASH_SIZE = 32


def _imread_safe(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, 'rb') as f:
        raw = f.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Не удалось декодировать изображение: {path}")
    return img


def _normalize_image(img):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    small = cv2.resize(gray, (CANON_SIZE, CANON_SIZE), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(small, (CANON_BLUR, CANON_BLUR), 0)
    normalized = cv2.equalizeHist(blurred)
    quantized = (normalized // 4) * 4
    return quantized.tobytes()


def _derive_encryption_key(canon_bytes, password):
    base = hashlib.sha256(canon_bytes).digest()
    return hmac.new(base, password.encode('utf-8'), hashlib.sha256).digest()[:CANON_HASH_SIZE]


def _aes_ctr_encrypt(data, key):
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return nonce + ciphertext


def _aes_ctr_decrypt(encrypted_data, key):
    nonce = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def encode(public_path, secret_path, quality=50, password=""):
    pub = _imread_safe(public_path)
    sec = _imread_safe(secret_path)

    if pub.shape[:2] != sec.shape[:2]:
        sec = cv2.resize(sec, (pub.shape[1], pub.shape[0]))

    h, w = pub.shape[:2]
    scale = quality / 100.0

    small_w = max(16, int(w * scale))
    small_h = max(16, int(h * scale))

    pub_small = cv2.resize(pub, (small_w, small_h), interpolation=cv2.INTER_AREA)
    sec_small = cv2.resize(sec, (small_w, small_h), interpolation=cv2.INTER_AREA)

    noise_small = cv2.bitwise_xor(pub_small, sec_small)
    _, buffer = cv2.imencode('.jpg', noise_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
    noise_bytes = buffer.tobytes()

    canon_bytes = _normalize_image(pub)
    enc_key = _derive_encryption_key(canon_bytes, password)
    encrypted_noise = _aes_ctr_encrypt(noise_bytes, enc_key)

    return base64.urlsafe_b64encode(encrypted_noise).decode()


def decode(public_path, key, password="", output_path=None):
    pub = _imread_safe(public_path)

    key_clean = key.strip()
    missing_padding = len(key_clean) % 4
    if missing_padding:
        key_clean += '=' * (4 - missing_padding)

    encrypted_noise = base64.urlsafe_b64decode(key_clean.encode())
    canon_bytes = _normalize_image(pub)
    enc_key = _derive_encryption_key(canon_bytes, password)
    noise_bytes = _aes_ctr_decrypt(encrypted_noise, enc_key)

    noise_array = np.frombuffer(noise_bytes, dtype=np.uint8)
    noise_small = cv2.imdecode(noise_array, cv2.IMREAD_COLOR)

    if noise_small is None:
        h, w = pub.shape[:2]
        noise_small = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)

    noise = cv2.resize(noise_small, (pub.shape[1], pub.shape[0]), interpolation=cv2.INTER_LINEAR)
    secret = cv2.bitwise_xor(pub, noise)

    if output_path:
        cv2.imwrite(output_path, secret)
        return output_path
    return secret


def estimate_key_length(image_shape, quality):
    scale = quality / 100.0
    small_w = max(16, int(image_shape[1] * scale))
    small_h = max(16, int(image_shape[0] * scale))
    pixels = small_w * small_h

    bytes_per_pixel = 1.2
    raw_bytes = int(pixels * bytes_per_pixel)
    encrypted_bytes = raw_bytes + 16
    return int(encrypted_bytes * 1.4)