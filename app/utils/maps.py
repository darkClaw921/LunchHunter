from typing import Optional
from urllib.parse import quote

def get_yandex_maps_url(address: str, name: Optional[str] = None) -> str:
    """
    Создает URL для Яндекс.Карт с заданным адресом и названием
    
    Args:
        address: Адрес заведения
        name: Название заведения (опционально)
    
    Returns:
        str: URL для Яндекс.Карт
    """
    query = address
    if name:
        query = f"{name}, {address}"
    
    encoded_query = quote(query)
    return f"https://yandex.ru/maps/?text={encoded_query}" 