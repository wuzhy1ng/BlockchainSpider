"""
工具函数模块
"""
from typing import Dict, Any, List
from datetime import datetime
import json


def convert_item_to_dict(item, field_mapping: Dict[str, str] = None) -> Dict[str, Any]:
    """
    转换 Scrapy Item 为字典格式
    
    Args:
        item: Scrapy Item 对象
        field_mapping: 字段映射字典
        
    Returns:
        转换后的字典
    """
    data = dict(item)
    
    # 应用字段映射
    if field_mapping:
        for old_field, new_field in field_mapping.items():
            if old_field in data:
                data[new_field] = data.pop(old_field)
    
    # 移除 None 值（可选）
    # data = {k: v for k, v in data.items() if v is not None}
    
    return data


def handle_jsonb_fields(data: Dict[str, Any], jsonb_fields: List[str]) -> Dict[str, Any]:
    """
    处理 JSONB 字段
    
    Args:
        data: 数据字典
        jsonb_fields: JSONB 字段列表
        
    Returns:
        处理后的数据字典
    """
    for field in jsonb_fields:
        if field in data:
            value = data[field]
            
            # 如果是字符串，尝试解析为 JSON
            if isinstance(value, str):
                try:
                    data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # 如果是列表或字典，保持不变
            elif isinstance(value, (list, dict)):
                pass
            
            # 其他类型转换为 JSON 字符串
            else:
                data[field] = json.dumps(value) if value is not None else None
    
    return data


def normalize_address(address: str) -> str:
    """
    标准化地址格式
    
    Args:
        address: 地址字符串
        
    Returns:
        标准化后的地址
    """
    if not address:
        return address
    
    # 转换为小写
    address = address.lower()
    
    # 确保以太坊地址以 0x 开头
    if len(address) == 40 and not address.startswith('0x'):
        address = '0x' + address
    
    return address


def convert_value_to_numeric(value: Any) -> Any:
    """
    转换值为数值类型
    
    Args:
        value: 原始值
        
    Returns:
        转换后的数值
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return value
    
    if isinstance(value, str):
        try:
            # 尝试转换为整数
            if value.startswith('0x'):
                return int(value, 16)
            else:
                return int(value)
        except ValueError:
            try:
                # 尝试转换为浮点数
                return float(value)
            except ValueError:
                return value
    
    return value


def safe_get(data: Dict, key: str, default=None):
    """
    安全获取字典值
    
    Args:
        data: 数据字典
        key: 键名
        default: 默认值
        
    Returns:
        获取的值或默认值
    """
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default


def timestamp_to_datetime(timestamp: Any) -> datetime:
    """
    时间戳转换为 datetime
    
    Args:
        timestamp: 时间戳（秒或毫秒）
        
    Returns:
        datetime 对象
    """
    if timestamp is None:
        return None
    
    if isinstance(timestamp, datetime):
        return timestamp
    
    try:
        timestamp = int(timestamp)
        
        # 判断是秒还是毫秒
        if timestamp > 10000000000:  # 毫秒
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp)
        
    except (ValueError, TypeError, OSError):
        return None


def batch_split(data_list: List, batch_size: int) -> List[List]:
    """
    将列表分批
    
    Args:
        data_list: 数据列表
        batch_size: 批次大小
        
    Returns:
        分批后的列表
    """
    batches = []
    for i in range(0, len(data_list), batch_size):
        batches.append(data_list[i:i + batch_size])
    return batches


def clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理数据
    
    Args:
        data: 原始数据字典
        
    Returns:
        清理后的数据字典
    """
    cleaned = {}
    
    for key, value in data.items():
        # 跳过 None 值
        if value is None:
            cleaned[key] = value
            continue
        
        # 字符串类型：去除首尾空格
        if isinstance(value, str):
            value = value.strip()
        
        # 地址类型：标准化
        if 'address' in key.lower():
            value = normalize_address(value)
        
        # 数值类型：转换
        if key in ['value', 'gas', 'gas_price', 'nonce', 'block_number']:
            value = convert_value_to_numeric(value)
        
        cleaned[key] = value
    
    return cleaned 