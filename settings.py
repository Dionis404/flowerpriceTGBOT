# settings.py
import json
import logging
import os

logger = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"
GROUPS_FILE = "groups.json"


def load_settings():
    """Загружает настройки из файла settings.json"""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Файл настроек не найден")
        # Возвращаем настройки по умолчанию
        return {
            "price_change_threshold": 15.0,
            "check_interval": 60
        }
    except Exception as e:
        logger.error("Ошибка при загрузке настроек: %s", e)
        # Возвращаем настройки по умолчанию
        return {
            "price_change_threshold": 15.0,
            "check_interval": 60
        }


def save_settings(settings):
    """Сохраняет настройки в файл settings.json"""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.warning("Ошибка при сохранении настроек: %s", e)


def load_groups():
    """Загружает информацию о группах из файла groups.json"""
    try:
        logger.debug("Попытка загрузки файла групп: %s", GROUPS_FILE)
        if not os.path.exists(GROUPS_FILE):
            logger.warning("Файл групп не существует: %s", GROUPS_FILE)
            # Возвращаем структуру по умолчанию
            default_groups = {
                "admin_ids": [],
                "group_chats": []
            }
            logger.debug("Возвращаем структуру групп по умолчанию: %s", default_groups)
            return default_groups
            
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug("Файл групп загружен успешно: %s", data)
            return data
    except FileNotFoundError:
        logger.warning("Файл групп не найден: %s", GROUPS_FILE)
        # Возвращаем структуру по умолчанию
        default_groups = {
            "admin_ids": [],
            "group_chats": []
        }
        logger.debug("Возвращаем структуру групп по умолчанию: %s", default_groups)
        return default_groups
    except Exception as e:
        logger.error("Ошибка при загрузке групп: %s", e)
        # Возвращаем структуру по умолчанию
        default_groups = {
            "admin_ids": [],
            "group_chats": []
        }
        logger.debug("Возвращаем структуру групп по умолчанию из-за ошибки: %s", default_groups)
        return default_groups


def save_groups(groups):
    """Сохраняет информацию о группах в файл groups.json"""
    try:
        logger.debug("Сохранение групп в файл: %s", groups)
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, indent=2, ensure_ascii=False)
        logger.debug("Группы успешно сохранены в файл: %s", GROUPS_FILE)
    except Exception as e:
        logger.warning("Ошибка при сохранении групп: %s", e)


def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    try:
        groups = load_groups()
        if groups and "admin_ids" in groups:
            # Если список администраторов пуст, то первый пользователь становится администратором
            if not groups["admin_ids"]:
                logger.info("Список администраторов пуст, добавляем первого пользователя %s как администратора", user_id)
                add_admin(user_id)
                return True
            return user_id in groups["admin_ids"]
        return False
    except Exception as e:
        logger.error("Ошибка при проверке прав администратора: %s", e)
        return False


def add_admin(user_id):
    """Добавляет пользователя в список администраторов"""
    try:
        groups = load_groups()
        if not groups:
            groups = {"admin_ids": [], "group_chats": []}
        
        if "admin_ids" not in groups:
            groups["admin_ids"] = []
        
        if user_id not in groups["admin_ids"]:
            groups["admin_ids"].append(user_id)
            save_groups(groups)
            return True
        return False
    except Exception:
        return False


def remove_admin(user_id):
    """Удаляет пользователя из списка администраторов"""
    try:
        groups = load_groups()
        if not groups or "admin_ids" not in groups:
            return False
        
        if user_id in groups["admin_ids"]:
            groups["admin_ids"].remove(user_id)
            save_groups(groups)
            return True
        return False
    except Exception:
        return False


def add_group(group_id, group_name):
    """Добавляет новую группу в список"""
    try:
        logger.info("Попытка добавления группы: ID=%s, имя=%s", group_id, group_name)
        groups = load_groups()
        if not groups:
            groups = {"admin_ids": [], "group_chats": []}
        
        if "group_chats" not in groups:
            groups["group_chats"] = []
        
        # Проверяем, что группа еще не добавлена
        if any(group["id"] == group_id for group in groups["group_chats"]):
            logger.warning("Группа с ID=%s уже существует", group_id)
            return False
        
        groups["group_chats"].append({
            "id": group_id,
            "name": group_name
        })
        save_groups(groups)
        logger.info("Группа добавлена успешно: ID=%s, имя=%s", group_id, group_name)
        logger.info("Текущий список групп: %s", groups["group_chats"])
        return True
    except Exception as e:
        logger.error("Ошибка при добавлении группы: %s", e)
        return False


def remove_group(group_id):
    """Удаляет группу из списка"""
    try:
        groups = load_groups()
        if not groups or "group_chats" not in groups:
            return False
        
        # Находим и удаляем группу
        for i, group in enumerate(groups["group_chats"]):
            if group["id"] == group_id:
                del groups["group_chats"][i]
                save_groups(groups)
                return True
        return False
    except Exception:
        return False


def get_group_ids():
    """Возвращает список ID всех групп"""
    try:
        groups = load_groups()
        logger.debug("Загруженные группы: %s", groups)
        if groups and "group_chats" in groups:
            group_ids = [group["id"] for group in groups["group_chats"]]
            logger.debug("Список ID групп: %s", group_ids)
            return group_ids
        logger.debug("Группы не найдены")
        return []
    except Exception as e:
        logger.error("Ошибка при получении списка групп: %s", e)
        return []