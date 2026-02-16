"""
安全与加密工具：密码哈希与简易 JWT（HS256）
"""
import os
import binascii
import hashlib
import hmac
import json
import base64
import datetime
from typing import Dict, Any
import threading
from app.config import AUTH_FAIL_THRESHOLD, AUTH_FAIL_WINDOW_MINUTES, AUTH_BAN_MINUTES, AUTH_BAN_LOG, AUTH_BAN_STATE

def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    if salt_hex is None:
        salt = os.urandom(16)
        salt_hex = binascii.hexlify(salt).decode("utf-8")
    else:
        salt = binascii.unhexlify(salt_hex.encode("utf-8"))
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return h, salt_hex

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))

def jwt_encode(payload: Dict[str, Any], secret: str, alg: str = "HS256") -> str:
    header = {"alg": alg, "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    if alg != "HS256":
        raise ValueError("Unsupported alg")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def jwt_decode(token: str, secret: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Invalid token")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise ValueError("Invalid signature")
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None:
        # exp 为 Unix 秒时间戳
        now = int(datetime.datetime.utcnow().timestamp())
        if now >= int(exp):
            raise ValueError("Token expired")
    return payload

def create_access_token(sub: str, minutes: int, secret: str) -> str:
    now = int(datetime.datetime.utcnow().timestamp())
    exp = now + minutes * 60
    payload = {"sub": sub, "type": "access", "iat": now, "exp": exp}
    return jwt_encode(payload, secret)

def create_refresh_token(sub: str, days: int, secret: str) -> str:
    now = int(datetime.datetime.utcnow().timestamp())
    exp = now + days * 24 * 60 * 60
    payload = {"sub": sub, "type": "refresh", "iat": now, "exp": exp}
    return jwt_encode(payload, secret)

class BanManager:
    def __init__(self, threshold: int, window_minutes: int, ban_minutes: int, log_path: str, state_path: str):
        self.threshold = threshold
        self.window_seconds = window_minutes * 60
        self.ban_seconds = ban_minutes * 60
        self.log_path = log_path
        self.state_path = state_path
        self.lock = threading.Lock()
        self.failures: Dict[str, list[int]] = {}
        self.banned: Dict[str, int] = {}
        self._load_state()

    def _now(self) -> int:
        return int(datetime.datetime.utcnow().timestamp())

    def prune(self):
        now = self._now()
        with self.lock:
            for ip, until in list(self.banned.items()):
                if until <= now:
                    del self.banned[ip]
            self._save_state()
            for ip, times in list(self.failures.items()):
                self.failures[ip] = [t for t in times if now - t <= self.window_seconds]
                if not self.failures[ip]:
                    del self.failures[ip]

    def is_banned(self, ip: str) -> bool:
        self.prune()
        with self.lock:
            until = self.banned.get(ip)
            if until and until > self._now():
                return True
            return False

    def record_failure(self, ip: str):
        now = self._now()
        with self.lock:
            arr = self.failures.get(ip, [])
            arr.append(now)
            self.failures[ip] = [t for t in arr if now - t <= self.window_seconds]
            if len(self.failures[ip]) >= self.threshold:
                self.banned[ip] = now + self.ban_seconds
                try:
                    os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
                    with open(self.log_path, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.datetime.utcnow().isoformat()} BAN {ip} for {self.ban_seconds}s\n")
                except:
                    pass
                self._save_state()

    def reset(self, ip: str):
        with self.lock:
            self.failures.pop(ip, None)
            self._save_state()

    def _load_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            if os.path.exists(self.state_path):
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                b = data.get("banned") or {}
                now = self._now()
                self.banned = {ip: until for ip, until in b.items() if until > now}
        except:
            self.banned = {}

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump({"banned": self.banned}, f)
        except:
            pass

ban_manager = BanManager(AUTH_FAIL_THRESHOLD, AUTH_FAIL_WINDOW_MINUTES, AUTH_BAN_MINUTES, AUTH_BAN_LOG, AUTH_BAN_STATE)
