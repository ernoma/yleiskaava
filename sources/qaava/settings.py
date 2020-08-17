from os.path import join
from typing import Optional, Union

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsSettings


def plugin_name():
    return "yleiskaava_tyokalu"

def setting_key(*args) -> str:
    """
    Get QGIS setting key

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    """
    return join("/", plugin_name(), *map(str, args))


def get_setting(key: str, default: Optional[any] = None,
                typehint: type = None, internal: bool = True) -> Union[QVariant, str]:
    """
    Get QGIS setting value plugin

    :param key: Key for the setting
    :param default: Optional default value
    :param typehint:
    :param internal: Whether to search from only plugin settings or all
    """
    s = QgsSettings()
    return s.value(setting_key(key) if internal else key, defaultValue=default, type=typehint)


def set_setting(key: str, value: Union[str, int, float, bool], internal: bool = True) -> bool:
    """
    Set a value in the QgsSetting

    :param key: Key for the setting
    :param value: Value for the setting
    :param internal: Whether to search from only plugin settings or all
    """
    qs = QgsSettings()
    return qs.setValue(setting_key(key) if internal else key, value)


def parse_value(value: Union[QVariant, str]) -> Union[None, str, bool]:
    """
    Parse QSettings value

    :param value: QVariant
    """
    str_value = str(value)
    val = str_value
    if str_value == "NULL":
        val = None
    elif str_value == "true":
        val = True
    elif str_value == "false":
        val = False
    return val
