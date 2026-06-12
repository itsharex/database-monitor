"""
加密模块单元测试。
"""

from app.utils.encryption import decrypt_password, encrypt_password


def test_encrypt_decrypt_roundtrip():
    """测试加密解密往返。"""
    original = "my_secret_password_123"
    encrypted = encrypt_password(original)
    assert encrypted != original
    decrypted = decrypt_password(encrypted)
    assert decrypted == original


def test_encrypt_empty_string():
    """测试空字符串加密。"""
    assert encrypt_password("") == ""
    assert decrypt_password("") == ""


def test_decrypt_invalid_token():
    """测试解密无效令牌。"""
    assert decrypt_password("invalid_token") == ""
