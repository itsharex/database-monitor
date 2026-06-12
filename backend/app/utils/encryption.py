"""
敏感信息加密工具。
使用 Fernet 对称加密存储数据库密码等敏感字段。
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _get_fernet() -> Fernet:
    """根据配置密钥生成 Fernet 实例。"""
    settings = get_settings()
    # 将任意长度密钥哈希为 32 字节，再 base64 编码供 Fernet 使用
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.encryption_key.encode()).digest()
    )
    return Fernet(key)


def encrypt_password(plain_text: str) -> str:
    """加密明文密码。"""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_password(cipher_text: str) -> str:
    """解密密码，解密失败时返回空字符串。"""
    if not cipher_text:
        return ""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(cipher_text.encode()).decode()
    except InvalidToken:
        return ""
