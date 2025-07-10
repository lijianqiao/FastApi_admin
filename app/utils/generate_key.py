"""
@Author         : li
@FileName       : generate_key.py
@Email          : lijianqiao2906@live.com
@DateTime       : 2025/01/16 11:27:53
@Version        : 1.0
@Docs           : 生成密钥
"""

import base64
import secrets


def generate_secret_key(length: int = 32) -> str:
    """
    生成随机密钥

    参数:
        length: 密钥长度, 默认32位

    返回:
        str: base64编码的密钥字符串
    """
    return base64.b64encode(secrets.token_bytes(length)).decode()


if __name__ == "__main__":
    # 生成并打印密钥
    secret_key1 = generate_secret_key()
    secret_key2 = generate_secret_key()
    print("\n=== 生成的SECRET_KEY1 ===")
    print(secret_key1)
    print("\n=== 生成的SECRET_KEY2 ===")
    print(secret_key2)
    print("======================\n")
    print("请将此密钥复制到.env文件的SECRET_KEY中")
