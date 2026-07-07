import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials
import os
import json
import time
from datetime import datetime

# --- ЗАГРУЗКА КОНФИГУРАЦИИ ---
def load_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Ошибка чтения config.json: {e}")
    return {}

config = load_config()

# Настройка страницы
page_title = config.get("company_name", "Tootmise arvestus / Учёт производства / Production Tracking")
st.set_page_config(layout="wide", page_title=page_title)

# --- СЛОВАРЬ ПЕРЕВОДОВ (ЛОКАЛИЗАЦИЯ) ---
LANGUAGES = {
    "RU": {
        "title": "🏭 Система учёта заказов и технологических операций",
        "sidebar_mgmt": "➕ Ввод новых данных",
        "new_order": "1. Новый заказ",
        "order_num": "Номер заказа",
        "order_desc": "Клиент",
        "order_deadline": "Общий дедлайн заказа",
        "btn_create_order": "Создать заказ",
        "msg_order_success": "Заказ {} успешно добавлен!",
        "new_op": "2. Добавить операцию",
        "select_order": "Выберите заказ",
        "op_label": "Операция",
        "op_period": "Период выполнения операции",
        "btn_add_op": "Добавить в график",
        "msg_op_success": "Операция '{}' добавлена к заказу {}!",
        "info_add_order_first": "Сначала добавьте хотя бы один заказ, чтобы планировать операции.",
        
        # Вкладки
        "tab_view": "🗓 График и Таблица",
        "tab_manage": "⚙️ Управление и Удаление",
        
        # Главная панель (Просмотр)
        "gantt_title": " Календарный график выполнения работ",
        "gantt_subtitle": "Загрузка производства по дням",
        "xaxis_title": "Дата",
        "yaxis_title": "Заказы",
        "table_title": "📊 Сводная таблица по всем операциям",
        "info_empty_db": "База данных пока пуста. Используйте левую панель для ввода первого заказа.",
        
        # Названия операций
        "operations_list": ["Лазер", "Распиловка", "Гибка", "Сверловка", "Зачистка", "Сборка", "Сварка", "Сборка/Сварка", "Покраска", "Цинк", "Комплектовка"],
        
        # Названия колонок для таблицы
        "col_order": "Номер заказа",
        "col_desc": "Клиент",
        "col_op": "Операция",
        "col_start": "Старт",
        "col_finish": "Финиш",
        "col_status": "Статус операции",
        "col_deadline": "Дедлайн заказа",
        "today_label": "Сегодня",
        "comments_table_title": "📝 ЗАКАЗЫ",
        "comments_label": "Заказ",
        "notes_label": "Комментарии",

        # Раздел Управления
        "manage_ops_header": "🔄 Изменение статуса операций",
        "select_op_to_change": "Выберите операцию для изменения",
        "current_status": "Текущий статус: {}",
        "new_status_label": "Выберите новый статус",
        "btn_update_status": "Обновить статус",
        "msg_status_updated": "Статус операции успешно обновлен!",
        
        "danger_zone": "🗑 Опасная зона (Удаление данных)",
        "delete_op_label": "Удалить конкретную операцию",
        "btn_delete_op": "❌ Удалить операцию",
        "msg_op_deleted": "Операция успешно удалена!",
        
        "delete_order_label": "Удалить заказ целиком (Внимание: удалит и все его операции!)",
        "btn_delete_order": "🔥 Удалить заказ",
        "msg_order_deleted": "Заказ и все его операции успешно удалены!",
        
        # Статусы
        "statuses": {"Pending": "Ожидание", "In progress": "В работе", "Done": "Готово", "Paused": "Приостановлено"},
        
        # Ошибки
        "err_date_range": "Пожалуйста, выберите диапазон дат (дату начала и окончания)!",
        "err_duplicate_order": "Заказ с таким номером уже существует!",

        # Учёт деталей
        "parts_sidebar_header": "📊 Учёт готовых деталей",
        "part_name_label": "Название детали",
        "part_qty_label": "Количество деталей",
        "part_target_label": "Целевое количество (Цель)",
        "part_completed_label": "Сделано деталей всего",
        "part_remaining_label": "Осталось до цели",
        "direction_up": "Вверх (накопление)",
        "direction_down": "Вниз (обратный отсчёт)",
        "direction_label": "Направление графика",
        "select_part_to_view": "Выберите деталь для просмотра графика",
        "plan_label": "План (цель)",
        "fact_label": "Факт (прогресс)",
        "last_updated_label": "Дата обновления",
        "new_part": "3. Создать новую деталь",
        "btn_create_part": "Создать деталь",
        "parts_table_title": "🔧 Редактор и удаление деталей",
        "add_output_label": "Внести",
        "btn_delete_part": "Удалить деталь",
        "history_title": "История внесения",
        "history_added_label": "Внесено (+)",
        "history_total_label": "Всего",
        "part_settings_title": "Редактирование и управление",
        "btn_save": "Сохранить",
        "msg_save_success": "Изменения сохранены!",
        "msg_no_changes": "Нет изменений для сохранения.",
        "edit_deadlines_header": "📅 Редактирование дедлайнов заказа",
        "select_order_to_edit_deadlines": "Выберите заказ для редактирования дедлайнов",
        "btn_save_deadlines": "Сохранить дедлайны",
        "msg_deadlines_saved": "Дедлайны заказа успешно обновлены!",
        "deadline_date_label": "Дата дедлайна",
        "deadline_name_label": "Название этапа/дедлайна",
        "btn_add_deadline": "➕ Добавить дедлайн",
        "import_excel_header": "📥 Импорт из Excel",
        "import_excel_descr": "Выберите Excel-файл (.xlsx) с листами 'orders' (Заказы) и 'operations' (Операции). Лист 'orders' должен содержать колонку 'order_number'. Лист 'operations' должен содержать колонки 'order_number', 'op_name', 'start_date', 'end_date'.",
        "import_excel_btn": "Загрузить Excel файл",
        "clear_before_import_label": "Очистить базу перед импортом?",
        "btn_do_import": "Импортировать данные",
        "msg_import_success": "Данные успешно импортированы! Добавлено заказов: {}, операций: {}."
    },
    "EE": {
        "title": "🏭 Tellimuste ja tehnoloogiliste operatsioonide arvestussüsteem",
        "sidebar_mgmt": "➕ Uute andmete sisestamine",
        "new_order": "1. Uus tellimus",
        "order_num": "Tellimuse number",
        "order_desc": "KLIENT",
        "order_deadline": "Tellimuse üldine tähtaeg",
        "btn_create_order": "Loo tellimus",
        "msg_order_success": "Tellimus {} on edukalt lisatud!",
        "new_op": "2. Lisa operatsioon",
        "select_order": "Vali tellimus",
        "op_label": "Operatsioon",
        "op_period": "Operatsiooni teostamise periood",
        "btn_add_op": "Lisa graafikusse",
        "msg_op_success": "Operatsioon '{}' on lisatud tellimusele {}!",
        "info_add_order_first": "Esmalt lisage vähemalt üks tellimus, et planeerida operatsioone.",
        
        # Вкладки
        "tab_view": "🗓 Graafik ja Tabel",
        "tab_manage": "⚙️ Haldamine ja Kustutamine",
        
        # Главная панель
        "gantt_title": " Tööde täitmise kalenderplaan",
        "gantt_subtitle": "Tootmise koormus päevade kaupa",
        "xaxis_title": "Kuupäev",
        "yaxis_title": "Tellimused",
        "table_title": "📊 Kõikide operatsioonide koondtabel",
        "info_empty_db": "Andmebaas on veel tühi. Kasutage tellimuse sisestamiseks vasakut paneeli.",
        
        "operations_list": ["Laser", "Saagimine", "Painutamine", "Puurimine", "Puhastus", "Kokkupanek", "Keevitamine", "Kokkupanek/Keevitamine", "Värvimine", "Tsinkimine", "Komplekteerimine"],
        
        "col_order": "TELLIMUS",
        "col_desc": "KLIENT",
        "col_op": "Operatsioon",
        "col_start": "Algus",
        "col_finish": "Lõpp",
        "col_status": "Operatsiooni staatus",
        "col_deadline": "TARNE",
        "today_label": "Täna",
        "comments_table_title": "📝 TELLIMUSED",
        "comments_label": "PROJEKT",
        "notes_label": "KOMMENTAAR",

        # Раздел Управления
        "manage_ops_header": "🔄 Operatsiooni staatuse muutmine",
        "select_op_to_change": "Vali operatsioon muutmiseks",
        "current_status": "Praegune staatus: {}",
        "new_status_label": "Vali uus staatus",
        "btn_update_status": "Uuenda staatust",
        "msg_status_updated": "Operatsiooni staatus on edukalt uuendatud!",
        
        "danger_zone": "🗑 Ohutsoon (Andmete kustutamine)",
        "delete_op_label": "Kustuta konkreetne operatsioon",
        "btn_delete_op": "❌ Kustuta operatsioon",
        "msg_op_deleted": "Operatsioon on edukalt kustutatud!",
        
        "delete_order_label": "Kustuta kogu tellimus (Tähelepanu: kustutab ka kõik selle operatsioonid!)",
        "btn_delete_order": "🔥 Kustuta tellimus",
        "msg_order_deleted": "Tellimus ja kõik selle operatsioonid on edukalt kustutatud!",
        
        "statuses": {"Pending": "Ootel", "In progress": "Töös", "Done": "Tehtud", "Paused": "Peatatud"},
        
        # Vead
        "err_date_range": "Palun vali kuupäevade vahemik (algus- ja lõppkuupäev)!",
        "err_duplicate_order": "Sellise numbriga tellimus on juba olemas!",

        # Detailide arvestus
        "parts_sidebar_header": "📊 Detailide arvestus",
        "part_name_label": "Detaili nimetus",
        "part_qty_label": "Kogus",
        "part_target_label": "Sihtkogus (Eesmärk)",
        "part_completed_label": "Tehtud detaile kokku",
        "part_remaining_label": "Jäänud eesmärgini",
        "direction_up": "Üles (kogumine)",
        "direction_down": "Alla (tagasilugemine)",
        "direction_label": "Graafiku suund",
        "select_part_to_view": "Vali detail graafiku kuvamiseks",
        "plan_label": "Eesmärk",
        "fact_label": "Fakt",
        "last_updated_label": "Uuendamise kuupäev",
        "new_part": "3. Loo uus detail",
        "btn_create_part": "Loo detail",
        "parts_table_title": "🔧 Detailide muutmine ja kustutamine",
        "add_output_label": "Lisa",
        "btn_delete_part": "Kustuta detail",
        "history_title": "Toodangu sisestamise ajalugu",
        "history_added_label": "Lisatud (+)",
        "history_total_label": "Kokku",
        "part_settings_title": "Muutmine ja haldamine",
        "btn_save": "Salvesta",
        "msg_save_success": "Muudatused salvestatud!",
        "msg_no_changes": "Salvestamiseks puuduvad muudatused.",
        "edit_deadlines_header": "📅 Tellimuse tähtaegade muutmine",
        "select_order_to_edit_deadlines": "Vali tellimus tähtaegade muutmiseks",
        "btn_save_deadlines": "Salvesta tähtajad",
        "msg_deadlines_saved": "Tellimuse tähtajad on edukalt uuendatud!",
        "deadline_date_label": "Tähtaja kuupäev",
        "deadline_name_label": "Etapi/tähtaja nimetus",
        "btn_add_deadline": "➕ Lisa tahtaeg",
        "import_excel_header": "📥 Importimine Excelist",
        "import_excel_descr": "Valige Exceli fail (.xlsx) lehtedega 'orders' (Tellimused) ja 'operations' (Operatsioonid). Leht 'orders' peab sisaldama veergu 'order_number'. Leht 'operations' peab sisaldama veerge 'order_number', 'op_name', 'start_date', 'end_date'.",
        "import_excel_btn": "Laadi üles Exceli fail",
        "clear_before_import_label": "Tühjenda andmebaas enne importimist?",
        "btn_do_import": "Impordi andmed",
        "msg_import_success": "Andmed edukalt imporditud! Lisatud tellimusi: {}, operatsioone: {}."
    },
    "EN": {
        "title": "🏭 Order Tracking and Technological Operations System",
        "sidebar_mgmt": "➕ Data Input",
        "new_order": "1. New Order",
        "order_num": "Order number",
        "order_desc": "Client",
        "order_deadline": "Overall order deadline",
        "btn_create_order": "Create order",
        "msg_order_success": "Order {} has been successfully added!",
        "new_op": "2. Add Operation",
        "select_order": "Select order",
        "op_label": "Operation",
        "op_period": "Operation timeframe",
        "btn_add_op": "Add to schedule",
        "msg_op_success": "Operation '{}' added to order {}!",
        "info_add_order_first": "Please add at least one order first to plan operations.",
        
        # Вкладки
        "tab_view": "🗓 Schedule & Table",
        "tab_manage": "⚙️ Management & Deletion",
        
        "gantt_title": " Production Schedule",
        "gantt_subtitle": "Production load by days",
        "xaxis_title": "Date",
        "yaxis_title": "Orders",
        "table_title": "📊 Summary Table of All Operations",
        "info_empty_db": "The database is empty. Use the left panel to insert the first order.",
        
        "operations_list": ["Laser", "Sawing", "Bending", "Drilling", "Deburring", "Assembly", "Welding", "Assembly/Welding", "Painting", "Zinc Plating", "Kitting"],
        
        "col_order": "Order number",
        "col_desc": "Client",
        "col_op": "Operation",
        "col_start": "Start",
        "col_finish": "Finish",
        "col_status": "Operation status",
        "col_deadline": "Order deadline",
        "today_label": "Today",
        "comments_table_title": "📝 ORDERS",
        "comments_label": "Order Name",
        "notes_label": "Comments",

        # Раздел Управления
        "manage_ops_header": "🔄 Change Operation Status",
        "select_op_to_change": "Select operation to modify",
        "current_status": "Current status: {}",
        "new_status_label": "Select new status",
        "btn_update_status": "Update Status",
        "msg_status_updated": "Operation status updated successfully!",
        
        "danger_zone": "🗑 Danger Zone (Data Deletion)",
        "delete_op_label": "Delete specific operation",
        "btn_delete_op": "❌ Delete Operation",
        "msg_op_deleted": "Operation deleted successfully!",
        
        "delete_order_label": "Delete entire order (Warning: this will delete all its operations!)",
        "btn_delete_order": "🔥 Delete Order",
        "msg_order_deleted": "Order and all its operations deleted successfully!",
        
        "statuses": {"Pending": "Pending", "In progress": "In Progress", "Done": "Done", "Paused": "Paused"},
        
        # Errors
        "err_date_range": "Please select a date range (start and end date)!",
        "err_duplicate_order": "An order with this number already exists!",

        # Parts tracking
        "parts_sidebar_header": "📊 Parts Tracking",
        "part_name_label": "Part Name",
        "part_qty_label": "Quantity",
        "part_target_label": "Target Quantity (Goal)",
        "part_completed_label": "Total completed parts",
        "part_remaining_label": "Remaining to goal",
        "direction_up": "Up (accumulation)",
        "direction_down": "Down (countdown)",
        "direction_label": "Chart direction",
        "select_part_to_view": "Select part to view timeline",
        "plan_label": "Plan (target)",
        "fact_label": "Fact (progress)",
        "last_updated_label": "Last updated",
        "new_part": "3. Create New Part",
        "btn_create_part": "Create part",
        "parts_table_title": "🔧 Edit and delete parts",
        "add_output_label": "Add",
        "btn_delete_part": "Delete part",
        "history_title": "Output input history",
        "history_added_label": "Added (+)",
        "history_total_label": "Total",
        "part_settings_title": "Edit and manage",
        "btn_save": "Save",
        "msg_save_success": "Changes saved!",
        "msg_no_changes": "No changes to save.",
        "edit_deadlines_header": "📅 Edit Order Deadlines",
        "select_order_to_edit_deadlines": "Select order to edit deadlines",
        "btn_save_deadlines": "Save Deadlines",
        "msg_deadlines_saved": "Order deadlines updated successfully!",
        "deadline_date_label": "Deadline date",
        "deadline_name_label": "Stage/deadline name",
        "btn_add_deadline": "➕ Add Deadline",
        "import_excel_header": "📥 Import from Excel",
        "import_excel_descr": "Select Excel file (.xlsx) with 'orders' and 'operations' sheets. 'orders' sheet must contain 'order_number' column. 'operations' sheet must contain 'order_number', 'op_name', 'start_date', 'end_date' columns.",
        "import_excel_btn": "Upload Excel File",
        "clear_before_import_label": "Clear database before import?",
        "btn_do_import": "Import Data",
        "msg_import_success": "Data imported successfully! Added orders: {}, operations: {}."
    }
}

# --- ИНТЕГРАЦИЯ КОНФИГУРАЦИИ И ЛОКАЛИЗАЦИЯ ЛОГИНА ---
login_translations = {
    "RU": {
        "login_header": "🔑 Авторизация",
        "login_pass_label": "Введите пароль",
        "btn_login": "Войти",
        "msg_login_err": "Неверный пароль!",
        "msg_login_success": "Успешный вход!"
    },
    "EE": {
        "login_header": "🔑 Sisselogimine",
        "login_pass_label": "Sisesta parool",
        "btn_login": "Logi sisse",
        "msg_login_err": "Vale parool!",
        "msg_login_success": "Sisselogimine õnnestus!"
    },
    "EN": {
        "login_header": "🔑 Authorization",
        "login_pass_label": "Enter password",
        "btn_login": "Login",
        "msg_login_err": "Incorrect password!",
        "msg_login_success": "Successful login!"
    }
}

for l_code in LANGUAGES:
    if l_code in login_translations:
        LANGUAGES[l_code].update(login_translations[l_code])
    if "company_name" in config:
        LANGUAGES[l_code]["title"] = "🏭 " + config["company_name"]
    cfg_ops = config.get("operations_list", {}).get(l_code)
    if cfg_ops:
        LANGUAGES[l_code]["operations_list"] = cfg_ops

# --- ВЫБОР ЯЗЫКА ---
languages_list = ["RU", "EE", "EN"]
default_lang = config.get("default_language", "EN")
default_index = 0
if default_lang in languages_list:
    default_index = languages_list.index(default_lang)

lang = st.sidebar.selectbox("Language / Keel / Язык", languages_list, index=default_index)
t = LANGUAGES[lang]

# --- ЭКРАН АВТОРИЗАЦИИ (БЕЗОПАСНОСТЬ) ---
import hashlib

def check_password(password, hashed_password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed_password

security_config = config.get("security", {})

# Проверяем настройки авторизации сначала из secrets (для облака), затем из config.json
enable_login = False
expected_hash = ""

try:
    if "enable_login" in st.secrets:
        enable_login = st.secrets["enable_login"]
    if "simple_password_hash" in st.secrets:
        expected_hash = st.secrets["simple_password_hash"]
except Exception:
    pass

if not enable_login:
    enable_login = security_config.get("enable_login", False)
if not expected_hash:
    expected_hash = security_config.get("simple_password_hash", "")

if enable_login:
    from streamlit_cookies_controller import CookieController
    cookies = CookieController()
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Если в текущей сессии еще не авторизован, проверяем сохраненную куку
    if not st.session_state["authenticated"]:
        try:
            saved_token = cookies.get("auth_token")
        except Exception:
            saved_token = None
            
        if saved_token == expected_hash:
            st.session_state["authenticated"] = True
            st.rerun()

    if not st.session_state["authenticated"]:
        st.title(t["login_header"])
        password_input = st.text_input(t["login_pass_label"], type="password")
        if st.button(t["btn_login"]):
            if check_password(password_input, expected_hash):
                st.session_state["authenticated"] = True
                # Записываем токен авторизации в куки на 1 день (24 часа = 86400 секунд)
                try:
                    cookies.set("auth_token", expected_hash, max_age=86400)
                except Exception:
                    pass
                st.success(t["msg_login_success"])
                st.rerun()
            else:
                st.error(t["msg_login_err"])
        st.stop()
        
    # Кнопка Выхода в сайдбаре
    if st.sidebar.button("🚪 Выйти / Log out / Logi välja"):
        st.session_state["authenticated"] = False
        try:
            cookies.remove("auth_token")
        except Exception:
            pass
        st.rerun()

st.title(t["title"])

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def parse_deadlines(deadline_val):
    if not deadline_val or pd.isna(deadline_val):
        return []
    val_str = str(deadline_val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            return json.loads(val_str)
        except Exception:
            pass
            
    # Determine separator: semicolon if present, otherwise comma if present, else fallback
    separator = None
    if ";" in val_str:
        separator = ";"
    elif "," in val_str:
        separator = ","
        
    if separator:
        parts = val_str.split(separator)
        result = []
        for p in parts:
            p = p.strip()
            if p:
                label = ""
                date_part = p
                if "(" in p and p.endswith(")"):
                    date_part, label = p.split("(", 1)
                    label = label.rstrip(")").strip()
                elif '"' in p:
                    p_clean = p.strip()
                    if p_clean.endswith('"'):
                        first_quote_idx = p_clean.find('"')
                        if first_quote_idx != -1 and first_quote_idx < len(p_clean) - 1:
                            date_part = p_clean[:first_quote_idx].strip()
                            label = p_clean[first_quote_idx+1:-1].strip()
                
                result.append({"date": date_part.strip(), "label": label})
        return result
        
    label = ""
    date_part = val_str
    if "(" in val_str and val_str.endswith(")"):
        date_part, label = val_str.split("(", 1)
        label = label.rstrip(")").strip()
    elif '"' in val_str:
        p_clean = val_str.strip()
        if p_clean.endswith('"'):
            first_quote_idx = p_clean.find('"')
            if first_quote_idx != -1 and first_quote_idx < len(p_clean) - 1:
                date_part = p_clean[:first_quote_idx].strip()
                label = p_clean[first_quote_idx+1:-1].strip()
                
    return [{"date": date_part.strip(), "label": label}]

def get_main_deadline(deadline_val):
    deadlines = parse_deadlines(deadline_val)
    if not deadlines:
        return None
    valid_dates = []
    for d in deadlines:
        try:
            dt = pd.to_datetime(d["date"]).date()
            valid_dates.append(dt)
        except Exception:
            pass
    if valid_dates:
        return max(valid_dates)
    return None

# --- ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS ---
def run_with_retry(func, *args, retries=6, delay=2.0, **kwargs):
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            status_code = None
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            
            # Retry on rate limits (429, 403) and server errors (500, 502, 503, 504)
            is_transient = (status_code in [403, 429, 500, 502, 503, 504]) or \
                           any(term in str(e).lower() for term in [
                               "429", "403", "500", "502", "503", "504",
                               "quota", "rate limit", "limit exceeded", "exhausted", "temp", "timeout"
                           ])
            
            if is_transient and i < retries - 1:
                time.sleep(delay * (2 ** i))
                continue
            raise e
        except Exception as e:
            # Retry on network connection issues / timeouts
            is_conn_error = any(term in str(e).lower() for term in ["connection", "timeout", "disconnected", "reset"])
            if is_conn_error and i < retries - 1:
                time.sleep(delay * (2 ** i))
                continue
            raise e

@st.cache_resource(show_spinner=False)
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_info = None
    # 1. Сначала проверяем config.json
    db_config = config.get("database", {})
    creds_file = db_config.get("credentials_file")
    if creds_file and os.path.exists(creds_file):
        try:
            with open(creds_file, "r", encoding="utf-8") as f:
                creds_info = json.load(f)
        except Exception as e:
            st.warning(f"Ошибка загрузки credentials_file из config.json: {e}")
            
    # 2. Если нет в конфиге или файл не найден, проверяем secrets (безопасно, чтобы не вызывать ошибку StreamlitSecretNotFoundError)
    if not creds_info:
        try:
            if "gcp_service_account" in st.secrets:
                creds_info = dict(st.secrets["gcp_service_account"])
        except Exception:
            pass
        
    # 3. Если нет в secrets, проверяем дефолтный service_account.json в рабочей папке
    if not creds_info and os.path.exists("service_account.json"):
        try:
            with open("service_account.json", "r", encoding="utf-8") as f:
                creds_info = json.load(f)
        except Exception as e:
            pass
            
    if not creds_info:
        st.error("Google Sheets credentials not found! Пожалуйста, настройте credentials_file в config.json, service_account.json или secrets.")
        st.stop()
        
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_resource(ttl=600, show_spinner=False)
def get_spreadsheet():
    client = get_gspread_client()
    
    sheet_url = None
    # 1. Проверяем config.json
    db_config = config.get("database", {})
    sheet_url = db_config.get("spreadsheet_url")
    
    # 2. Если нет в конфиге, проверяем secrets (безопасно)
    if not sheet_url:
        try:
            if "spreadsheet_url" in st.secrets:
                sheet_url = st.secrets["spreadsheet_url"]
        except Exception:
            pass
        
    # 3. Если нет в secrets, проверяем spreadsheet_url.txt
    if not sheet_url and os.path.exists("spreadsheet_url.txt"):
        try:
            with open("spreadsheet_url.txt", "r", encoding="utf-8") as f:
                sheet_url = f.read().strip()
        except Exception:
            pass
            
    if not sheet_url:
        st.error("Google Spreadsheet URL not found! Пожалуйста, добавьте spreadsheet_url в config.json, secrets или в файл spreadsheet_url.txt.")
        st.stop()
        
    try:
        return run_with_retry(client.open_by_url, sheet_url)
    except Exception as e:
        import traceback
        st.error("Не удалось открыть Google Таблицу по ссылке. Убедитесь, что вы поделились таблицей с email сервисного аккаунта!")
        st.code(f"Тип ошибки: {type(e).__name__}\nОписание: {str(e)}\n\nСлед (Traceback):\n{traceback.format_exc()}")
        st.stop()

@st.cache_resource(show_spinner=False)
def get_worksheet(sheet_name):
    sh = get_spreadsheet()
    return run_with_retry(sh.worksheet, sheet_name)

@st.cache_data(ttl=60, show_spinner=False)
def get_worksheet_as_df(sheet_name):
    try:
        worksheet = get_worksheet(sheet_name)
        data = run_with_retry(worksheet.get_all_records)
    except Exception as e:
        import traceback
        st.error(f"Ошибка при чтении листа '{sheet_name}'!")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            st.code(f"Тип ошибки: {type(e).__name__}\nОтвет API: {e.response.text}\n\nСлед:\n{traceback.format_exc()}")
        else:
            st.code(f"Тип ошибки: {type(e).__name__}\nОписание: {str(e)}\n\nСлед:\n{traceback.format_exc()}")
        st.stop()
    if not data:
        if sheet_name == "orders":
            return pd.DataFrame(columns=["id", "order_number", "description", "deadline", "status", "comments", "notes"])
        elif sheet_name == "operations":
            return pd.DataFrame(columns=["id", "order_id", "op_name", "start_date", "end_date", "status"])
        elif sheet_name == "parts":
            return pd.DataFrame(columns=["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"])
        elif sheet_name == "parts_log":
            return pd.DataFrame(columns=["id", "part_id", "date", "quantity_added", "total_completed_after"])
    df_res = pd.DataFrame(data)
    if "order_number" in df_res.columns:
        df_res["order_number"] = df_res["order_number"].apply(
            lambda x: str(x)[:-2] if str(x).endswith(".0") else str(x)
        )
    return df_res

def init_db():
    sh = get_spreadsheet()
    worksheets = [w.title for w in run_with_retry(sh.worksheets)]
    
    if "orders" not in worksheets:
        run_with_retry(sh.add_worksheet, title="orders", rows="100", cols="20")
        worksheet = run_with_retry(sh.worksheet, "orders")
        run_with_retry(worksheet.append_row, ["id", "order_number", "description", "deadline", "status", "comments", "notes"])
    else:
        worksheet = run_with_retry(sh.worksheet, "orders")
        headers = run_with_retry(worksheet.row_values, 1)
        if "comments" not in headers:
            run_with_retry(worksheet.update_cell, 1, len(headers) + 1, "comments")
        headers = run_with_retry(worksheet.row_values, 1)
        if "notes" not in headers:
            run_with_retry(worksheet.update_cell, 1, len(headers) + 1, "notes")
        
    if "operations" not in worksheets:
        run_with_retry(sh.add_worksheet, title="operations", rows="1000", cols="20")
        worksheet = run_with_retry(sh.worksheet, "operations")
        run_with_retry(worksheet.append_row, ["id", "order_id", "op_name", "start_date", "end_date", "status"])


    if "parts" not in worksheets:
        try:
            run_with_retry(sh.add_worksheet, title="parts", rows=1000, cols=8)
            worksheet = run_with_retry(sh.worksheet, "parts")
            run_with_retry(worksheet.append_row, ["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"])
        except Exception as e:
            st.error(f"Ошибка при инициализации листа parts: {e}")
    else:
        try:
            worksheet = run_with_retry(sh.worksheet, "parts")
            headers = run_with_retry(worksheet.row_values, 1)
            if "last_updated" not in headers or "completed_quantity" not in headers or "direction" not in headers:
                df = run_with_retry(worksheet.get_all_records)
                new_rows = []
                today_str = datetime.today().strftime('%d.%m.%Y')
                for row in df:
                    qty = row.get("quantity", row.get("completed_quantity", 0))
                    target = row.get("target_quantity", qty if qty > 0 else 100)
                    last_up = row.get("last_updated", today_str)
                    if not last_up: last_up = today_str
                    direction = row.get("direction", "up")
                    if not direction: direction = "up"
                    new_rows.append([row.get("id", ""), row.get("part_name", ""), target, qty, last_up, direction])
                run_with_retry(worksheet.clear)
                run_with_retry(worksheet.update, "A1", [["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"]] + new_rows)
        except Exception as e:
            st.error(f"Ошибка при миграции листа parts: {e}")

    if "parts_log" not in worksheets:
        try:
            run_with_retry(sh.add_worksheet, title="parts_log", rows=10000, cols=5)
            log_ws = run_with_retry(sh.worksheet, "parts_log")
            run_with_retry(log_ws.append_row, ["id", "part_id", "date", "quantity_added", "total_completed_after"])
            
            parts_ws = run_with_retry(sh.worksheet, "parts")
            parts_records = run_with_retry(parts_ws.get_all_records)
            if parts_records:
                new_rows = []
                log_id = 1
                today_str = datetime.today().strftime('%d.%m.%Y')
                for r in parts_records:
                    p_id = r.get("id")
                    qty = r.get("completed_quantity", r.get("quantity", 0))
                    last_up = r.get("last_updated", today_str)
                    if not last_up: last_up = today_str
                    new_rows.append([log_id, int(p_id), str(last_up), int(qty), int(qty)])
                    log_id += 1
                if new_rows:
                    run_with_retry(log_ws.append_rows, new_rows)
        except Exception as e:
            st.error(f"Ошибка при инициализации листа parts_log: {e}")

def get_parts():
    df = get_worksheet_as_df("parts")
    if df.empty:
        return pd.DataFrame(columns=["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"])
    
    # Создаем копию для безопасности
    df = df.copy()
    
    # Если это старая схема (есть quantity, но нет completed_quantity)
    if "quantity" in df.columns and "completed_quantity" not in df.columns:
        df["completed_quantity"] = df["quantity"]
        df["target_quantity"] = df["quantity"].apply(lambda q: q if q > 0 else 100)
        
    for col in ["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"]:
        if col not in df.columns:
            df[col] = ""
            
    today_str = datetime.today().strftime('%d.%m.%Y')
    df["id"] = df["id"].fillna("").astype(str)
    df["part_name"] = df["part_name"].fillna("").astype(str)
    df["last_updated"] = df["last_updated"].fillna(today_str).apply(lambda x: today_str if str(x).strip() == "" else str(x))
    df["direction"] = df["direction"].fillna("up").apply(lambda x: "up" if str(x).strip() == "" else str(x))
    df["target_quantity"] = pd.to_numeric(df["target_quantity"], errors="coerce").fillna(100).astype(int)
    df["completed_quantity"] = pd.to_numeric(df["completed_quantity"], errors="coerce").fillna(0).astype(int)
    return df[["id", "part_name", "target_quantity", "completed_quantity", "last_updated", "direction"]]

def add_part(part_name, target_quantity, completed_quantity=0, last_updated=None, direction="up"):
    get_worksheet_as_df.clear()
    if not last_updated:
        last_updated = datetime.today().strftime('%d.%m.%Y')
    try:
        worksheet = get_worksheet("parts")
        df = get_worksheet_as_df("parts")
        
        new_id = 1
        if not df.empty:
            ids = pd.to_numeric(df["id"], errors="coerce").dropna().astype(int)
            if not ids.empty:
                new_id = int(ids.max() + 1)
                
        run_with_retry(worksheet.append_row, [new_id, str(part_name), int(target_quantity), int(completed_quantity), str(last_updated), str(direction)])
        
        # Запишем начальную точку в лог!
        log_production(new_id, completed_quantity, completed_quantity, last_updated)
        
        get_worksheet_as_df.clear()
        return True
    except Exception as e:
        st.error(f"Ошибка при добавлении детали: {e}")
        get_worksheet_as_df.clear()
        return False

def delete_part(part_id):
    get_worksheet_as_df.clear()
    try:
        # 1. Удаляем деталь
        worksheet = get_worksheet("parts")
        df = get_worksheet_as_df("parts")
        if not df.empty:
            match_idx = df[df["id"].astype(str) == str(part_id)].index
            if len(match_idx) > 0:
                row_num = int(match_idx[0]) + 2
                run_with_retry(worksheet.delete_rows, row_num)
        
        # 2. Удаляем связанные логи из parts_log
        log_ws = get_worksheet("parts_log")
        log_df = get_worksheet_as_df("parts_log")
        if not log_df.empty:
            matching_rows = log_df[log_df["part_id"].astype(str) == str(part_id)].index.tolist()
            for idx in sorted(matching_rows, reverse=True):
                row_num = idx + 2
                run_with_retry(log_ws.delete_rows, row_num)
    except Exception as e:
        st.error(f"Ошибка при удалении детали: {e}")
    get_worksheet_as_df.clear()

def update_part(part_id, part_name, target_quantity, completed_quantity, last_updated=None, direction=None):
    get_worksheet_as_df.clear()
    if not last_updated:
        last_updated = datetime.today().strftime('%d.%m.%Y')
    try:
        worksheet = get_worksheet("parts")
        df = get_worksheet_as_df("parts")
        if not df.empty:
            match_idx = df[df["id"].astype(str) == str(part_id)].index
            if len(match_idx) > 0:
                row_num = int(match_idx[0]) + 2
                if not direction:
                    direction = df.loc[match_idx[0], "direction"] if "direction" in df.columns else "up"
                run_with_retry(worksheet.update, f"B{row_num}:F{row_num}", [[str(part_name), int(target_quantity), int(completed_quantity), str(last_updated), str(direction)]])
    except Exception as e:
        st.error(f"Ошибка при обновлении детали: {e}")
    get_worksheet_as_df.clear()


def log_production(part_id, quantity_added, total_completed_after, date_str=None):
    if not date_str:
        date_str = datetime.today().strftime('%d.%m.%Y')
    try:
        worksheet = get_worksheet("parts_log")
        df = get_worksheet_as_df("parts_log")
        new_id = 1
        if not df.empty:
            ids = pd.to_numeric(df["id"], errors="coerce").dropna().astype(int)
            if not ids.empty:
                new_id = int(ids.max() + 1)
        run_with_retry(worksheet.append_row, [new_id, int(part_id), str(date_str), int(quantity_added), int(total_completed_after)])
    except Exception as e:
        st.warning(f"Не удалось записать историю изменения детали: {e}")

def delete_production_log(log_id):
    try:
        log_ws = get_worksheet("parts_log")
        all_logs_df = get_worksheet_as_df("parts_log")
        if not all_logs_df.empty:
            match_idx = all_logs_df[pd.to_numeric(all_logs_df["id"], errors="coerce") == pd.to_numeric(log_id, errors="coerce")].index
            if len(match_idx) > 0:
                row_num = int(match_idx[0]) + 2  # +2 для заголовка и 1-based index
                run_with_retry(log_ws.delete_rows, row_num)
                get_worksheet_as_df.clear()
                return True
    except Exception as e:
        st.warning(f"Не удалось удалить запись из лога: {e}")
    return False

def recalculate_and_save_part_logs(part_id, updated_part_logs_df):
    get_worksheet_as_df.clear()
    try:
        # 1. Сортируем переданные логи по дате
        # Сначала преобразуем дату для сортировки
        updated_part_logs_df = updated_part_logs_df.copy()
        updated_part_logs_df["parsed_date"] = pd.to_datetime(updated_part_logs_df["date"], dayfirst=True, errors="coerce")
        updated_part_logs_df = updated_part_logs_df.dropna(subset=["parsed_date"])
        updated_part_logs_df = updated_part_logs_df.sort_values(by="parsed_date")
        
        # 2. Пересчитываем накопительный итог (total_completed_after)
        cumulative_total = 0
        final_rows = []
        latest_date = datetime.today().strftime('%d.%m.%Y')
        
        for idx, row in updated_part_logs_df.iterrows():
            qty_added = int(row["quantity_added"])
            cumulative_total += qty_added
            date_str = str(row["date"])
            latest_date = date_str
            final_rows.append({
                "id": int(row["id"]),
                "part_id": int(part_id),
                "date": date_str,
                "quantity_added": qty_added,
                "total_completed_after": cumulative_total
            })
            
        # 3. Сохраняем в лист parts_log в Google Sheets
        # Читаем все записи из parts_log
        log_ws = get_worksheet("parts_log")
        all_logs_df = get_worksheet_as_df("parts_log")
        
        # Обновляем строки для этой детали в общем списке
        for updated_row in final_rows:
            log_id = updated_row["id"]
            if not all_logs_df.empty:
                match_idx = all_logs_df[pd.to_numeric(all_logs_df["id"], errors="coerce") == pd.to_numeric(log_id, errors="coerce")].index
                if len(match_idx) > 0:
                    row_num = int(match_idx[0]) + 2 # +2 для заголовка и 1-based index
                    run_with_retry(log_ws.update, f"A{row_num}:E{row_num}", [[
                        int(log_id),
                        int(part_id),
                        str(updated_row["date"]),
                        int(updated_row["quantity_added"]),
                        int(updated_row["total_completed_after"])
                    ]])
                    
        # 4. Обновляем общее количество в таблице parts
        parts_ws = get_worksheet("parts")
        parts_df = get_worksheet_as_df("parts")
        if not parts_df.empty:
            part_match = parts_df[parts_df["id"].astype(str) == str(part_id)].index
            if len(part_match) > 0:
                part_row_num = int(part_match[0]) + 2
                current_part_name = str(parts_df.loc[part_match[0], "part_name"])
                current_target = int(parts_df.loc[part_match[0], "target_quantity"])
                current_dir = str(parts_df.loc[part_match[0], "direction"])
                run_with_retry(parts_ws.update, f"A{part_row_num}:F{part_row_num}", [[
                    int(part_id),
                    current_part_name,
                    current_target,
                    int(cumulative_total),
                    str(latest_date),
                    current_dir
                ]])
        get_worksheet_as_df.clear()
        return True
    except Exception as e:
        st.error(f"Ошибка при пересчете логов: {e}")
        get_worksheet_as_df.clear()
        return False

def get_production_logs(part_id=None):
    df = get_worksheet_as_df("parts_log")
    if df.empty:
        return pd.DataFrame(columns=["id", "part_id", "date", "quantity_added", "total_completed_after"])
    df = df.copy()
    
    for col in ["id", "part_id", "date", "quantity_added", "total_completed_after"]:
        if col not in df.columns:
            df[col] = ""
            
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    df["part_id"] = pd.to_numeric(df["part_id"], errors="coerce").fillna(0).astype(int)
    df["quantity_added"] = pd.to_numeric(df["quantity_added"], errors="coerce").fillna(0).astype(int)
    df["total_completed_after"] = pd.to_numeric(df["total_completed_after"], errors="coerce").fillna(0).astype(int)
    df["date"] = df["date"].fillna("").astype(str)
    
    if part_id is not None:
        df = df[df["part_id"] == int(part_id)]
        
    return df



def order_exists(number):
    df = get_worksheet_as_df("orders")
    if df.empty:
        return False
    return str(number) in df["order_number"].astype(str).values

def add_order(number, desc, deadline, comments="", notes=""):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("orders")
    df = get_worksheet_as_df("orders")
    
    new_id = 1
    if not df.empty:
        ids = pd.to_numeric(df["id"], errors="coerce").dropna().astype(int)
        if not ids.empty:
            new_id = int(ids.max() + 1)
            
    headers = run_with_retry(worksheet.row_values, 1)
    row_data = [new_id, str(number), str(desc), str(deadline), "In production", str(comments)]
    if "notes" in headers:
        row_data.append(str(notes))
    run_with_retry(worksheet.append_row, row_data)
    get_worksheet_as_df.clear()

def add_operation(order_id, op_name, start, end):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("operations")
    df = get_worksheet_as_df("operations")
    
    new_id = 1
    if not df.empty:
        ids = pd.to_numeric(df["id"], errors="coerce").dropna().astype(int)
        if not ids.empty:
            new_id = int(ids.max() + 1)
            
    run_with_retry(worksheet.append_row, [new_id, int(order_id), str(op_name), str(start), str(end), "Pending"])
    get_worksheet_as_df.clear()

def update_operation_status(op_id, new_status):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("operations")
    df = get_worksheet_as_df("operations")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(op_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            run_with_retry(worksheet.update_cell, row_num, 6, new_status)
    get_worksheet_as_df.clear()

def update_operation(op_id, op_name, start, end, status):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("operations")
    df = get_worksheet_as_df("operations")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(op_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            # Обновляем диапазон C{row_num}:F{row_num} (колонки op_name, start_date, end_date, status)
            run_with_retry(worksheet.update, f"C{row_num}:F{row_num}", [[str(op_name), str(start), str(end), str(status)]])
    get_worksheet_as_df.clear()

def delete_operation(op_id):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("operations")
    df = get_worksheet_as_df("operations")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(op_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            run_with_retry(worksheet.delete_rows, row_num)
    get_worksheet_as_df.clear()

def delete_order(order_id):
    get_worksheet_as_df.clear()
    
    # 1. Удаляем все связанные операции
    ops_worksheet = get_worksheet("operations")
    ops_df = get_worksheet_as_df("operations")
    if not ops_df.empty:
        matching_rows = ops_df[ops_df["order_id"].astype(str) == str(order_id)].index.tolist()
        for idx in sorted(matching_rows, reverse=True):
            row_num = idx + 2
            run_with_retry(ops_worksheet.delete_rows, row_num)
            
    # 2. Удаляем сам заказ
    orders_worksheet = get_worksheet("orders")
    orders_df = get_worksheet_as_df("orders")
    if not orders_df.empty:
        match_idx = orders_df[orders_df["id"].astype(str) == str(order_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            run_with_retry(orders_worksheet.delete_rows, row_num)
    get_worksheet_as_df.clear()

def update_order_description(order_id, new_desc):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("orders")
    df = get_worksheet_as_df("orders")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(order_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            run_with_retry(worksheet.update_cell, row_num, 3, str(new_desc))  # Колонка 3 - description
    get_worksheet_as_df.clear()

def update_order_comments(order_id, new_comments):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("orders")
    df = get_worksheet_as_df("orders")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(order_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            headers = run_with_retry(worksheet.row_values, 1)
            if "comments" in headers:
                col_idx = headers.index("comments") + 1
                run_with_retry(worksheet.update_cell, row_num, col_idx, str(new_comments))
    get_worksheet_as_df.clear()

def update_order_deadline(order_id, new_deadline):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("orders")
    df = get_worksheet_as_df("orders")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(order_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            run_with_retry(worksheet.update_cell, row_num, 4, str(new_deadline))
    get_worksheet_as_df.clear()

def update_order_notes(order_id, new_notes):
    get_worksheet_as_df.clear()
    worksheet = get_worksheet("orders")
    df = get_worksheet_as_df("orders")
    
    if not df.empty:
        match_idx = df[df["id"].astype(str) == str(order_id)].index
        if len(match_idx) > 0:
            row_num = int(match_idx[0]) + 2
            headers = run_with_retry(worksheet.row_values, 1)
            if "notes" not in headers:
                run_with_retry(worksheet.update_cell, 1, len(headers) + 1, "notes")
                headers.append("notes")
            col_idx = headers.index("notes") + 1
            run_with_retry(worksheet.update_cell, row_num, col_idx, str(new_notes))
    get_worksheet_as_df.clear()

def get_orders_list():
    df = get_worksheet_as_df("orders")
    if df.empty:
        return pd.DataFrame(columns=["id", "order_number", "comments"])
    df_sorted = df.sort_values(by="order_number", key=lambda x: x.astype(str))
    cols = ["id", "order_number"]
    if "comments" in df_sorted.columns:
        cols.append("comments")
    return df_sorted[cols]

def get_merged_data():
    orders_df = get_worksheet_as_df("orders")
    ops_df = get_worksheet_as_df("operations")
    
    if orders_df.empty:
        return pd.DataFrame(columns=[
            "op_id", "order_id", "order_number", "description", 
            "deadline", "op_name", "start_date", "end_date", "status", "comments"
        ])
        
    orders_df["id"] = orders_df["id"].astype(str)
    
    if ops_df.empty:
        merged = orders_df.copy()
        merged = merged.rename(columns={"id": "order_id"})
        merged["op_id"] = None
        merged["op_name"] = None
        merged["start_date"] = None
        merged["end_date"] = None
        merged["status"] = None
    else:
        ops_df["order_id"] = ops_df["order_id"].astype(str)
        ops_df = ops_df.rename(columns={"id": "op_id"})
        # Делаем LEFT JOIN, чтобы сохранить заказы без операций
        merged = pd.merge(orders_df, ops_df, left_on="id", right_on="order_id", how="left")
        merged = merged.drop(columns=["order_id"])
        merged = merged.rename(columns={"id": "order_id", "status_y": "status"})
        
    columns_to_keep = [
        "op_id", "order_id", "order_number", "description", 
        "deadline", "op_name", "start_date", "end_date", "status", "comments", "notes"
    ]
    # Дозаполняем колонки, если их нет
    for col in columns_to_keep:
        if col not in merged.columns:
            merged[col] = None
            
    merged = merged[columns_to_keep]
    return merged

init_db()

def get_col_width(df, col_name, min_w=100, max_w=1000):
    if df.empty or col_name not in df.columns:
        return min_w
    max_len = max(
        df[col_name].astype(str).map(len).max(),
        len(str(col_name))
    )
    return int(max(min_w, min(max_w, max_len * 9.5 + 25)))

# --- БОКОВАЯ ПАНЕЛЬ (ВВОД ДАННЫХ) ---
st.sidebar.markdown("---")
st.sidebar.header(t["sidebar_mgmt"])

if st.session_state.get("new_order_success_msg"):
    st.sidebar.success(st.session_state["new_order_success_msg"])
    del st.session_state["new_order_success_msg"]

# Форма 1: Создание заказа
with st.sidebar.expander(t["new_order"], expanded=False):
    if st.session_state.get("clear_new_order_flag"):
        for key in ["new_order_num", "new_order_desc", "new_order_comments", "new_order_notes"]:
            st.session_state[key] = ""
        st.session_state["new_order_deadlines"] = [{"date": datetime.today(), "label": ""}]
        for key in list(st.session_state.keys()):
            if key.startswith("new_order_dl_date_") or key.startswith("new_order_dl_lbl_"):
                del st.session_state[key]
        st.session_state["clear_new_order_flag"] = False

    order_num = st.text_input(t["order_num"], key="new_order_num")
    order_desc = st.text_input(t["order_desc"], key="new_order_desc")
    order_comments = st.text_area(t["comments_label"], key="new_order_comments")
    order_notes = st.text_area(t["notes_label"], key="new_order_notes")
    
    st.write(f"**{t['col_deadline']}**")
    if "new_order_deadlines" not in st.session_state:
        st.session_state["new_order_deadlines"] = [{"date": datetime.today(), "label": ""}]
        
    col_hdr_date, col_hdr_lbl, col_hdr_btn = st.columns([0.45, 0.45, 0.1])
    with col_hdr_date:
        st.caption(t.get("deadline_date_label", "Дата"))
    with col_hdr_lbl:
        st.caption(t.get("deadline_name_label", "Этап"))
        
    updated_deadlines = []
    for idx, dl in enumerate(st.session_state["new_order_deadlines"]):
        col_date, col_lbl, col_btn = st.columns([0.45, 0.45, 0.1])
        with col_date:
            d_val = st.date_input(
                f"date_{idx}", 
                dl["date"], 
                format="DD.MM.YYYY", 
                key=f"new_order_dl_date_{idx}",
                label_visibility="collapsed"
            )
        with col_lbl:
            l_val = st.text_input(
                f"lbl_{idx}", 
                dl["label"], 
                key=f"new_order_dl_lbl_{idx}", 
                placeholder="Лазер...",
                label_visibility="collapsed"
            )
        with col_btn:
            if st.button("×", key=f"new_order_dl_del_{idx}"):
                st.session_state["new_order_deadlines"].pop(idx)
                st.rerun()
        updated_deadlines.append({"date": d_val, "label": l_val})
        
    st.session_state["new_order_deadlines"] = updated_deadlines
    
    if st.button(t.get("btn_add_deadline", "➕ Добавить дедлайн"), key="new_order_dl_add"):
        st.session_state["new_order_deadlines"].append({"date": datetime.today(), "label": ""})
        st.rerun()
        
    if st.button(t["btn_create_order"], key="btn_create_order_submit", type="primary", use_container_width=True):
        if not order_num:
            st.error("Введите номер заказа!" if lang == "RU" else "Sisesta tellimuse number!" if lang == "EE" else "Enter order number!")
        elif order_exists(order_num):
            st.error(t["err_duplicate_order"])
        else:
            # Serialize deadlines to our human-readable format
            dl_strings = []
            for dl in st.session_state["new_order_deadlines"]:
                d_str = dl["date"].strftime('%Y-%m-%d')
                lbl = dl["label"].strip()
                if lbl:
                    dl_strings.append(f"{d_str} ({lbl})")
                else:
                    dl_strings.append(d_str)
            serialized_deadlines = ", ".join(dl_strings)
            
            add_order(order_num, order_desc, serialized_deadlines, order_comments, order_notes)
            
            # Set flag to clear inputs and save success message for the next run
            st.session_state["clear_new_order_flag"] = True
            st.session_state["new_order_success_msg"] = t["msg_order_success"].format(order_num)
            st.rerun()

# Форма 2: Добавление операции
df_available_orders = get_orders_list()

if not df_available_orders.empty:
    with st.sidebar.expander(t["new_op"], expanded=False):
        with st.form("operation_form", clear_on_submit=True):
            order_options = {}
            for _, row in df_available_orders.iterrows():
                num = str(row['order_number'])
                name = str(row['comments']).strip() if 'comments' in row and pd.notna(row['comments']) and str(row['comments']).strip() else ""
                label = f"{num} — {name}" if name else num
                order_options[label] = (num, row['id'])
            selected_order_label = st.selectbox(t["select_order"], list(order_options.keys()))
            selected_order_num, selected_order_id = order_options[selected_order_label]
            
            op_name = st.selectbox(t["op_label"], t["operations_list"])
            op_dates = st.date_input(t["op_period"], [datetime.today(), datetime.today()], format="DD.MM.YYYY")
            
            submit_op = st.form_submit_button(t["btn_add_op"])
            if submit_op:
                if len(op_dates) == 2:
                    add_operation(selected_order_id, op_name, op_dates[0], op_dates[1])
                    st.success(t["msg_op_success"].format(op_name, selected_order_num))
                    st.rerun()
                else:
                    st.error(t["err_date_range"])
else:
    st.sidebar.info(t["info_add_order_first"])

# Форма 3: Добавление детали (parts)
with st.sidebar.expander(t.get("new_part", "3. Создать новую деталь"), expanded=False):
    with st.form("part_form", clear_on_submit=True):
        new_part_name = st.text_input(t.get("part_name_label", "Название детали"))
        new_part_target = st.number_input(
            t.get("part_target_label", "План"), 
            min_value=1, 
            step=1, 
            value=None, 
            placeholder="Введите количество..." if lang == "RU" else ("Sisesta kogus..." if lang == "EE" else "Enter quantity...")
        )
        
        # Selection for direction (Up/Down)
        new_part_direction_label = st.selectbox(
            t.get("direction_label", "Направление графика"), 
            options=[t["direction_up"], t["direction_down"]]
        )
        
        submit_part = st.form_submit_button(t.get("btn_create_part", "Создать деталь" if lang == "RU" else ("Loo detail" if lang == "EE" else "Create part")))
        
        if submit_part and new_part_name:
            if new_part_target is None:
                st.error("Пожалуйста, введите количество (План)!" if lang == "RU" else "Palun sisesta kogus (Plaan)!" if lang == "EE" else "Please enter the quantity (Plan)!")
            else:
                dir_map_to_db = {t["direction_up"]: "up", t["direction_down"]: "down"}
                db_direction = dir_map_to_db.get(new_part_direction_label, "up")
                
                # Добавляем в базу
                success = add_part(new_part_name, int(new_part_target), 0, direction=db_direction)
                if success:
                    st.success(f"Деталь '{new_part_name}' успешно создана!" if lang == "RU" else f"Detail '{new_part_name}' loodud!" if lang == "EE" else f"Part '{new_part_name}' created!")
                    st.rerun()

# Форма 4: Импорт из Excel (умный авто-маппинг колонок)
with st.sidebar.expander(t.get("import_excel_header", "📥 Импорт из Excel"), expanded=False):

    # Словарь псевдонимов для каждого поля (RU + EE + EN + возможные варианты)
    FIELD_ALIASES = {
        # --- ЗАКАЗЫ ---
        "order_number": [
            "order_number", "order number", "номер заказа", "номер", "заказ", "zakaz",
            "tellimuse number", "tellimus", "tellimus (номер заказа)", "order no", "order#",
            "order №", "№", "nomer", "order_no", "ordernumber", "order_num", "заказ №",
            "nr", "tellimuse nr"
        ],
        "description": [
            "description", "клиент", "client", "klient", "customer", "заказчик",
            "kliendi nimi", "company", "компания", "kontragent", "контрагент",
            "desc", "name", "имя", "назв"
        ],
        "deadline": [
            "deadline", "дедлайн", "срок", "срок сдачи", "tähtaeg", "tähtaeg (üldine)",
            "lähetusaeg", "due date", "due", "srok", "deadline_date", "end", "конечная дата",
            "tarne"
        ],
        "comments": [
            "comments", "название заказа", "название",
            "наименование", "заказ", "note",
            "comment", "заказ (название)", "наим", "order name", "name",
            "projekt"
        ],
        "notes": [
            "notes", "заметки", "заметка", "примечания", "märkused", "notes_label",
            "extra", "доп", "дополнительно", "additional", "info", "информация",
            "kommentaar", "kommentaarid", "комментарий", "комментарии", "примечание"
        ],
        # --- ОПЕРАЦИИ ---
        "op_name": [
            "op_name", "operation", "операция", "operatsioon", "op name", "тип операции",
            "вид операции", "операции", "operation name", "op", "работа", "вид работы",
            "тип работы", "op_type", "operation_type", "process"
        ],
        "start_date": [
            "start_date", "start date", "начало", "дата начала", "algus", "alguskuupäev",
            "start", "from", "от", "с", "начало операции", "date start", "startdate",
            "begin", "begin_date", "begindate"
        ],
        "end_date": [
            "end_date", "end date", "конец", "окончание", "дата окончания", "lõpp",
            "lõppkuupäev", "end", "to", "до", "по", "финиш", "finish", "finish_date",
            "date end", "enddate", "завершение"
        ],
        "status": [
            "status", "статус", "staatus", "state", "состояние", "текущий статус",
            "op_status", "operation_status"
        ]
    }

    # Альтернативные названия листов
    ORDERS_SHEET_ALIASES = ["orders", "заказы", "tellimused", "order", "zakazy", "заказ"]
    OPS_SHEET_ALIASES = ["operations", "операции", "operatsioonid", "ops", "operacii", "операция"]

    def fuzzy_match_column(col_name, field_aliases, threshold=0.6):
        """Возвращает имя поля БД для данного имени колонки Excel."""
        import difflib
        col_lower = str(col_name).strip().lower()
        for field, aliases in field_aliases.items():
            if col_lower in [a.lower() for a in aliases]:
                return field  # Точное совпадение
        # Нечёткий поиск среди всех псевдонимов
        all_aliases = [(field, alias) for field, aliases in field_aliases.items() for alias in aliases]
        alias_strings = [a.lower() for _, a in all_aliases]
        matches = difflib.get_close_matches(col_lower, alias_strings, n=1, cutoff=threshold)
        if matches:
            matched_alias = matches[0]
            for field, alias in all_aliases:
                if alias.lower() == matched_alias:
                    return field
        return None

    def find_sheet(sheet_names, aliases):
        """Ищет лист по псевдонимам (без учёта регистра)."""
        for alias in aliases:
            for sheet in sheet_names:
                if sheet.strip().lower() == alias.lower():
                    return sheet
        return None

    def detect_and_normalize(df_raw):
        """
        Нормализует Excel в стандартный табличный формат.
        Поддерживает 2 формата:
          1. Стандартный: заголовки в одной строке, данные ниже (множество записей)
          2. Разбросанный/транспонированный: пары поле→значение (ячейка справа)
             в произвольных местах листа — одна запись на весь лист
        """
        if df_raw is None or df_raw.empty:
            return pd.DataFrame()
        import difflib

        # Словарь псевдоним (нижний регистр) → название поля
        alias_map = {}
        for field, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                if isinstance(alias, str):
                    alias_map[alias.strip().lower()] = field
        all_aliases = list(alias_map.keys())

        def cell_str(v):
            """Возвращает строку или None если пусто/NaN."""
            if v is None:
                return None
            try:
                if isinstance(v, float) and pd.isna(v):
                    return None
            except Exception:
                pass
            s = str(v).strip()
            return None if s.lower() in ('', 'nan') else s

        def match_field(v):
            """Возвращает имя поля БД если значение — псевдоним поля, иначе None."""
            s = cell_str(v)
            if not s:
                return None
            sl = s.lower()
            if sl in alias_map:
                return alias_map[sl]
            sl2 = sl.rstrip('.,;: ')
            if sl2 in alias_map:
                return alias_map[sl2]
            hits = difflib.get_close_matches(sl2, all_aliases, n=1, cutoff=0.65)
            return alias_map[hits[0]] if hits else None

        n_rows, n_cols = df_raw.shape

        # ── Стратегия 1: Стандартный табличный формат ────────────────────────
        # Ищем строку, где ≥3 ячейки в одной строке — псевдонимы полей
        # (≥3 чтобы не спутать с заголовком одиночного поля в разбросанном формате)
        for ri in range(min(15, n_rows)):
            row = df_raw.iloc[ri]
            known = [match_field(v) for v in row]
            if sum(1 for f in known if f) >= 3:
                new_cols = [cell_str(v) or f'_c{i}' for i, v in enumerate(row)]
                df_out = df_raw.iloc[ri + 1:].copy()
                df_out.columns = new_cols
                df_out = df_out.reset_index(drop=True)
                return df_out

        # ── Стратегия 2: Разбросанный/транспонированный формат ───────────────
        # Полный скан листа: ячейка = псевдоним → значение из соседней (право/низ)
        records = {}
        matched_fields = set()
        for ri in range(n_rows):
            for ci in range(n_cols):
                v = df_raw.iloc[ri, ci]
                field = match_field(v)
                if field and field not in matched_fields:
                    val = None
                    # Приоритет: ячейка справа
                    if ci + 1 < n_cols:
                        right = cell_str(df_raw.iloc[ri, ci + 1])
                        if right and not match_field(right):
                            val = right
                    # Иначе: ячейка снизу
                    if val is None and ri + 1 < n_rows:
                        down = cell_str(df_raw.iloc[ri + 1, ci])
                        if down and not match_field(down):
                            val = down
                    if val is not None:
                        records[str(v).strip()] = val
                        matched_fields.add(field)

        if records:
            return pd.DataFrame([records])

        return df_raw



    if "import_result_logs" in st.session_state:
        with st.container():
            st.success("📊 Результат последнего импорта:")
            for log in st.session_state["import_result_logs"][:15]:
                st.caption(log)
            if len(st.session_state["import_result_logs"]) > 15:
                st.caption(f"... и еще {len(st.session_state['import_result_logs']) - 15} записей")
            if st.button("Очистить лог", key="clear_import_logs_btn"):
                del st.session_state["import_result_logs"]
                st.rerun()
        st.write("---")

    excel_file = st.file_uploader(
        t.get("import_excel_btn", "Загрузить Excel файл"),
        type=["xlsx"],
        key="excel_import_uploader",
        label_visibility="collapsed"
    )



    if excel_file is not None:
        try:
            xls = pd.ExcelFile(excel_file)
            sheet_names = xls.sheet_names

            # Ищем лист с заказами; если не найден — берём первый лист
            orders_sheet_name = find_sheet(sheet_names, ORDERS_SHEET_ALIASES)
            if not orders_sheet_name:
                orders_sheet_name = sheet_names[0]
                st.info(f"ℹ️ Лист с заказами определён автоматически: **{orders_sheet_name}**")

            ops_sheet_name = find_sheet(sheet_names, OPS_SHEET_ALIASES)

            df_raw_orders = pd.read_excel(xls, orders_sheet_name, header=None)
            df_excel_orders = detect_and_normalize(df_raw_orders)

            if ops_sheet_name:
                df_raw_ops = pd.read_excel(xls, ops_sheet_name, header=None)
                df_excel_ops = detect_and_normalize(df_raw_ops)
            else:
                df_excel_ops = pd.DataFrame()

            # Строим маппинг колонок заказов
            order_col_map = {}
            for col in df_excel_orders.columns:
                field = fuzzy_match_column(col, {k: v for k, v in FIELD_ALIASES.items() if k in ["order_number","description","deadline","comments","notes"]})
                if field:
                    order_col_map[col] = field

            # Если авто-маппинг по именам колонок не нашёл номер заказа, применяем эвристический анализ содержимого
            if "order_number" not in order_col_map.values():
                def heuristic_classify_columns(df):
                    mapping = {}
                    n_rows = len(df)
                    if n_rows == 0:
                        return mapping

                    # 1. Поиск дедлайна (даты)
                    deadline_col = None
                    for col in df.columns:
                        non_empty = df[col].dropna()
                        if len(non_empty) == 0:
                            continue
                        parsed_dates = 0
                        for v in non_empty:
                            try:
                                if isinstance(v, (int, float)) and v > 50000:
                                    continue
                                dt = pd.to_datetime(v, errors='raise')
                                if 2020 <= dt.year <= 2100:
                                    parsed_dates += 1
                            except Exception:
                                pass
                        if parsed_dates / len(non_empty) >= 0.7:
                            deadline_col = col
                            break

                    # 2. Поиск номеров заказов
                    order_col = None
                    for col in df.columns:
                        if col == deadline_col:
                            continue
                        non_empty = df[col].dropna()
                        if len(non_empty) == 0:
                            continue
                        valid_orders = 0
                        for v in non_empty:
                            try:
                                s = str(v).strip()
                                if s.endswith('.0'):
                                    s = s[:-2]
                                val = int(s)
                                if 1000 <= val <= 999999:
                                    valid_orders += 1
                            except Exception:
                                pass
                        if valid_orders / len(non_empty) >= 0.7:
                            order_col = col
                            break

                    # 3. Поиск текстовых колонок (заполнено >= 50%)
                    remaining_cols = [c for c in df.columns if c not in (deadline_col, order_col)]
                    text_cols_stats = []
                    for col in remaining_cols:
                        non_empty = df[col].dropna()
                        if len(non_empty) / n_rows < 0.5:
                            continue
                        non_empty_str = non_empty.astype(str).str.strip()
                        non_empty_str = non_empty_str[non_empty_str != '']
                        if len(non_empty_str) == 0:
                            continue
                        avg_len = non_empty_str.map(len).mean()
                        text_cols_stats.append((col, avg_len))

                    text_cols_stats.sort(key=lambda x: x[1])

                    desc_col = None
                    if text_cols_stats:
                        desc_col = text_cols_stats[0][0]

                    comments_col = None
                    if len(text_cols_stats) > 1:
                        comments_col = text_cols_stats[1][0]

                    notes_col = None
                    if len(text_cols_stats) > 2:
                        notes_col = text_cols_stats[2][0]

                    if order_col is not None:
                        mapping[order_col] = 'order_number'
                    if desc_col is not None:
                        mapping[desc_col] = 'description'
                    if deadline_col is not None:
                        mapping[deadline_col] = 'deadline'
                    if comments_col is not None:
                        mapping[comments_col] = 'comments'
                    if notes_col is not None:
                        mapping[notes_col] = 'notes'
                    return mapping

                heuristic_map = heuristic_classify_columns(df_excel_orders)
                for col, field in heuristic_map.items():
                    order_col_map[col] = field

            # Строим маппинг колонок операций
            ops_col_map = {}
            if not df_excel_ops.empty:
                for col in df_excel_ops.columns:
                    field = fuzzy_match_column(col, {k: v for k, v in FIELD_ALIASES.items() if k in ["order_number","op_name","start_date","end_date","status"]})
                    if field:
                        ops_col_map[col] = field



            # Показываем превью маппинга
            st.markdown("**🔍 Определённые колонки:**")

            field_labels = {
                "order_number": "Номер заказа ✅",
                "description": "Клиент",
                "deadline": "Дедлайн",
                "comments": "Название заказа",
                "notes": "Заметки",
                "op_name": "Операция ✅",
                "start_date": "Дата начала ✅",
                "end_date": "Дата окончания ✅",
                "status": "Статус"
            }

            preview_rows = []
            for excel_col, db_field in order_col_map.items():
                preview_rows.append({"Excel колонка": excel_col, "→ Поле": field_labels.get(db_field, db_field)})
            for excel_col, db_field in ops_col_map.items():
                preview_rows.append({"Excel колонка": excel_col, "→ Поле": field_labels.get(db_field, db_field)})

            if preview_rows:
                st.dataframe(pd.DataFrame(preview_rows), hide_index=True, use_container_width=True)

            # Проверяем обязательные колонки
            mapped_order_fields = set(order_col_map.values())
            mapped_ops_fields = set(ops_col_map.values())

            missing_order = []
            if "order_number" not in mapped_order_fields:
                missing_order.append("order_number (Номер заказа)")

            missing_ops = []
            if not df_excel_ops.empty:
                for req in ["order_number", "op_name", "start_date", "end_date"]:
                    if req not in mapped_ops_fields:
                        missing_ops.append(field_labels.get(req, req))

            if missing_order:
                st.error(f"❌ Не удалось найти обязательные колонки в листе заказов: {', '.join(missing_order)}")
            elif missing_ops:
                st.warning(f"⚠️ В листе операций не хватает колонок: {', '.join(missing_ops)}. Операции будут пропущены.")

            can_import = "order_number" in mapped_order_fields

            if can_import:
                if st.button(t.get("btn_do_import", "Импортировать данные"), key="btn_do_import_submit", type="primary", use_container_width=True):
                    try:
                        df_orders_mapped = df_excel_orders.rename(columns=order_col_map)
                        df_ops_mapped = df_excel_ops.rename(columns=ops_col_map) if not df_excel_ops.empty else pd.DataFrame()

                        with st.spinner("Загрузка данных в Google Sheets..."):
                            sh = get_spreadsheet()
                            gs_orders = sh.worksheet("orders")
                            gs_ops = sh.worksheet("operations")

                            existing_orders = get_worksheet_as_df("orders")
                            existing_ops = get_worksheet_as_df("operations")

                            def clean_val(val):
                                if isinstance(val, pd.Series):
                                    val = val.iloc[0] if not val.empty else ""
                                if pd.isna(val):
                                    return ""
                                v = str(val).strip()
                                return "" if v.lower() == "nan" else v

                            def norm_num(v):
                                if isinstance(v, pd.Series):
                                    v = v.iloc[0] if not v.empty else ""
                                s = str(v).strip()
                                return s[:-2] if s.endswith('.0') else s

                            # Получаем все значения листа orders, чтобы знать индексы строк для обновления
                            existing_raw_orders = gs_orders.get_all_values()
                            id_to_row_idx = {}
                            if len(existing_raw_orders) > 1:
                                for idx, r in enumerate(existing_raw_orders[1:], start=2):
                                    if r:
                                        id_to_row_idx[str(r[0]).strip()] = idx

                            order_num_to_id = {}
                            existing_comments = set()
                            next_order_id = 1
                            if not existing_orders.empty:
                                for _, row in existing_orders.iterrows():
                                    order_num_to_id[norm_num(row["order_number"])] = int(row["id"])
                                    comm = clean_val(row.get("comments", ""))
                                    if comm:
                                        existing_comments.add(comm.strip().lower())
                                max_id = pd.to_numeric(existing_orders["id"], errors="coerce").max()
                                next_order_id = int(max_id + 1) if pd.notna(max_id) else 1

                            orders_to_append = []
                            import_logs = []
                            added_count = 0
                            updated_count = 0

                            for _, row in df_orders_mapped.iterrows():
                                ord_num = norm_num(row.get("order_number", ""))
                                if not ord_num:
                                    continue
                                desc = clean_val(row.get("description", ""))
                                deadline = clean_val(row.get("deadline", ""))
                                comments = clean_val(row.get("comments", ""))
                                notes = clean_val(row.get("notes", ""))

                                # Если название заказа (comments) совпадает с уже существующим — пропускаем импорт
                                if comments and comments.strip().lower() in existing_comments:
                                    import_logs.append(f"⚠️ Пропущен дубликат названия: '{comments}' (Заказ {ord_num})")
                                    continue

                                # Если заказ уже существует по номеру заказа, ОБНОВЛЯЕМ его в Google Sheet
                                if ord_num in order_num_to_id:
                                    ord_id = order_num_to_id[ord_num]
                                    row_idx = id_to_row_idx.get(str(ord_id))
                                    if row_idx:
                                        gs_orders.update(f"C{row_idx}:D{row_idx}", [[desc, deadline]])
                                        gs_orders.update(f"F{row_idx}:G{row_idx}", [[comments, notes]])
                                        if comments:
                                            existing_comments.add(comments.strip().lower())
                                        import_logs.append(f"🔄 Обновлен существующий заказ {ord_num} ({desc})")
                                        updated_count += 1
                                    else:
                                        # Если индекс строки не найден, добавляем как новый
                                        order_num_to_id[ord_num] = next_order_id
                                        orders_to_append.append([next_order_id, ord_num, desc, deadline, "In production", comments, notes])
                                        if comments:
                                            existing_comments.add(comments.strip().lower())
                                        import_logs.append(f"✅ Добавлен заказ {ord_num} ({desc})")
                                        next_order_id += 1
                                        added_count += 1
                                else:
                                    # Добавляем новый заказ
                                    order_num_to_id[ord_num] = next_order_id
                                    orders_to_append.append([next_order_id, ord_num, desc, deadline, "In production", comments, notes])
                                    if comments:
                                        existing_comments.add(comments.strip().lower())
                                    import_logs.append(f"✅ Добавлен заказ {ord_num} ({desc})")
                                    next_order_id += 1
                                    added_count += 1

                            if orders_to_append:
                                gs_orders.append_rows(orders_to_append)

                            next_op_id = 1
                            if not existing_ops.empty:
                                max_op_id = pd.to_numeric(existing_ops["id"], errors="coerce").max()
                                next_op_id = int(max_op_id + 1) if pd.notna(max_op_id) else 1

                            ops_to_append = []
                            ops_added_count = 0
                            if not df_ops_mapped.empty and "order_number" in df_ops_mapped.columns:
                                for _, row in df_ops_mapped.iterrows():
                                    ord_num = norm_num(row.get("order_number", ""))
                                    if ord_num not in order_num_to_id:
                                        continue
                                    ord_id = order_num_to_id[ord_num]
                                    op_name = clean_val(row.get("op_name", ""))
                                    try:
                                        start_date = pd.to_datetime(row["start_date"]).strftime('%Y-%m-%d')
                                        end_date = pd.to_datetime(row["end_date"]).strftime('%Y-%m-%d')
                                    except Exception:
                                        continue
                                    status = clean_val(row.get("status", "Pending"))
                                    if status not in ["Pending", "In progress", "Done", "Paused"]:
                                        status = "Pending"
                                    ops_to_append.append([next_op_id, ord_id, op_name, start_date, end_date, status])
                                    import_logs.append(f"⚙️ Добавлена операция '{op_name}' для заказа {ord_num}")
                                    next_op_id += 1
                                    ops_added_count += 1

                            if ops_to_append:
                                gs_ops.append_rows(ops_to_append)

                            get_worksheet_as_df.clear()
                            
                            # Сохраняем логи в session_state для отображения пользователю
                            st.session_state["import_result_logs"] = import_logs
                            
                            # Формируем сообщение об успешности
                            success_msg = f"Импорт завершен! Добавлено новых заказов: {added_count}, обновлено: {updated_count}, операций: {ops_added_count}."
                            st.success(success_msg)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при импорте: {str(e)}")

        except Exception as e:
            st.error(f"Ошибка при чтении Excel файла: {str(e)}")







def translate_operation(op_name, target_lang):
    if pd.isna(op_name) or not op_name:
        return op_name
    
    ops_ru = LANGUAGES["RU"]["operations_list"]
    ops_ee = LANGUAGES["EE"]["operations_list"]
    ops_en = LANGUAGES["EN"]["operations_list"]
    
    idx = -1
    for ops in [ops_ru, ops_ee, ops_en]:
        cleaned_ops = [str(x).strip().lower() for x in ops]
        cleaned_val = str(op_name).strip().lower()
        if cleaned_val in cleaned_ops:
            idx = cleaned_ops.index(cleaned_val)
            break
            
    if idx != -1:
        return LANGUAGES[target_lang]["operations_list"][idx]
    return op_name

df_raw = get_merged_data()

if not df_raw.empty:
    df_raw['op_name'] = df_raw['op_name'].apply(lambda x: translate_operation(x, lang))
    df_raw['translated_status'] = df_raw['status'].map(t["statuses"])

    tab_view, tab_manage = st.tabs([t["tab_view"], t["tab_manage"]])

    with tab_view:
        today_date = datetime.today().date()
        expired_orders = set()
        df_deadlines_raw = df_raw[["order_number", "deadline"]].drop_duplicates()
        for _, row in df_deadlines_raw.iterrows():
            ord_num = str(row["order_number"])
            dl_str = row["deadline"]
            if pd.notna(dl_str) and dl_str != "":
                try:
                    dl_date = get_main_deadline(dl_str)
                    if dl_date and dl_date < today_date:
                        expired_orders.add(ord_num)
                except Exception:
                    pass

        def get_sort_key(row):
            ord_num = str(row["order_number"])
            dl_str = row["deadline"]
            
            if pd.isna(dl_str) or str(dl_str).strip() == "":
                group = 1
                dl_date = pd.Timestamp.max.date()
            else:
                group = 0
                try:
                    dl_date = get_main_deadline(dl_str)
                    if dl_date is None:
                        dl_date = pd.Timestamp.max.date()
                        group = 1
                except Exception:
                    dl_date = pd.Timestamp.max.date()
                    group = 1
                
            return (group, dl_date, ord_num)

        sort_keys = df_raw.apply(get_sort_key, axis=1)
        df_raw_copy = df_raw.copy()
        df_raw_copy["_sort_group"] = [x[0] for x in sort_keys]
        df_raw_copy["_sort_date"] = [x[1] for x in sort_keys]
        df_raw_copy["_sort_order"] = [x[2] for x in sort_keys]
        
        df_sorted = df_raw_copy.sort_values(
            by=["_sort_group", "_sort_date", "_sort_order"], 
            ascending=[True, True, True]
        ).drop(columns=["_sort_group", "_sort_date", "_sort_order"])

        df_display = df_sorted.rename(columns={
            "order_number": t["col_order"],
            "description": t["col_desc"],
            "comments": t["comments_label"],
            "op_name": t["col_op"],
            "start_date": t["col_start"],
            "end_date": t["col_finish"],
            "translated_status": t["col_status"]
        })

        df_display[t["col_order"]] = df_display[t["col_order"]].astype(str)
        df_display[t["comments_label"]] = df_display[t["comments_label"]].fillna("—").apply(lambda val: "—" if str(val).strip() == "" else str(val))
        df_display[t["col_desc"]] = df_display[t["col_desc"]].fillna("—").apply(lambda val: "—" if str(val).strip() == "" else str(val))
        def format_deadline_for_row(dl_val):
            dls = parse_deadlines(dl_val)
            if not dls:
                return "—"
            parts = []
            for d in dls:
                try:
                    formatted_date = pd.to_datetime(d["date"]).strftime('%d.%m.%Y')
                    if d["label"]:
                        parts.append(f"{formatted_date} {d['label']}")
                    else:
                        parts.append(formatted_date)
                except Exception:
                    parts.append(str(d['date']))
            return ", ".join(parts)

        df_display[t["col_deadline"]] = df_sorted['deadline'].apply(format_deadline_for_row)
        
        start_dt = pd.to_datetime(df_sorted['start_date'])
        end_dt = pd.to_datetime(df_sorted['end_date'])
        df_display['duration_ms'] = (end_dt - start_dt).dt.total_seconds() * 1000 + 86400000
        df_display['raw_start'] = df_sorted['start_date']

        valid_start = start_dt.dropna()
        valid_end = end_dt.dropna()
        
        today_dt = pd.to_datetime(datetime.today().date())
        min_date = today_dt
        max_date = valid_end.max() if not valid_end.empty else today_dt
        
        main_deadlines = df_sorted['deadline'].apply(get_main_deadline).dropna()
        max_deadline = pd.to_datetime(main_deadlines).max() if not main_deadlines.empty else pd.NaT
        if pd.notna(max_deadline):
            max_date = max(max_date, max_deadline)
            
        if max_date < min_date:
            max_date = min_date
            
        max_date = max_date + pd.Timedelta(days=1)
        
        all_days = pd.date_range(start=min_date, end=max_date, freq='D')
        date_boundaries = all_days
        date_midpoints = all_days + pd.Timedelta(hours=12)
        
        today_date = datetime.today().date()
        today_str = today_date.strftime('%d.%m.%Y')
        date_labels = []
        for day in all_days:
            day_formatted = day.strftime('%d.%m.%Y')
            is_weekend = day.weekday() >= 5
            label = day_formatted
            if is_weekend:
                label = f"<span style='color: #FF6B6B;'>{label}</span>"
            if day_formatted == today_str:
                label = f"<b><span style='color: #FF5252;'>{day_formatted}</span></b>"
            date_labels.append(label)
            
        # ── Zoom In / Zoom Out ──────────────────────────────────────────────
        total_days = int((max_date - min_date).days) or 1
        zoom_step = 10  # шаг зума — 10 дней

        if "gantt_zoom_days" not in st.session_state or st.session_state["gantt_zoom_days"] > total_days:
            st.session_state["gantt_zoom_days"] = total_days

        zoom_days = st.session_state["gantt_zoom_days"]

        # Вычисляем отображаемый диапазон дат
        zoom_max_date = min_date + pd.Timedelta(days=zoom_days)
        if zoom_max_date > max_date:
            zoom_max_date = max_date

        title_col, zoom_col1, zoom_col2 = st.columns([12, 0.45, 0.45])
        
        st.markdown("""
        <style>
        div[data-testid="column"]:has(.zoom-btn-marker) button {
            width: 32px !important;
            height: 28px !important;
            min-height: 28px !important;
            max-width: 32px !important;
            padding: 0px !important;
            font-size: 12px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 4px !important;
            margin-top: 10px !important;
        }
        div[data-testid="column"]:has(.zoom-btn-marker) button p {
            font-size: 12px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        with title_col:
            st.subheader(t["gantt_title"])

        with zoom_col1:
            st.markdown('<div class="zoom-btn-marker"></div>', unsafe_allow_html=True)
            if st.button("🔍+", key="zoom_in_btn", help="Zoom In — показать меньше дней", use_container_width=True):
                new_days = max(zoom_step, zoom_days - zoom_step)
                st.session_state["gantt_zoom_days"] = new_days
                st.rerun()
        with zoom_col2:
            st.markdown('<div class="zoom-btn-marker"></div>', unsafe_allow_html=True)
            if st.button("🔎−", key="zoom_out_btn", help="Zoom Out — показать больше дней", use_container_width=True):
                new_days = min(total_days, zoom_days + zoom_step)
                st.session_state["gantt_zoom_days"] = new_days
                st.rerun()
        # ───────────────────────────────────────────────────────────────────

        fig = go.Figure()
        
        operation_styles = {
            "Лазер": {"fill": "rgba(255, 107, 107, 0.35)", "line": "#FF6B6B"},
            "Распиловка": {"fill": "rgba(77, 150, 255, 0.35)", "line": "#4D96FF"},
            "Гибка": {"fill": "rgba(107, 203, 119, 0.35)", "line": "#6BCB77"},
            "Сверловка": {"fill": "rgba(255, 217, 61, 0.35)", "line": "#FFD93D"},
            "Зачистка": {"fill": "rgba(244, 115, 185, 0.35)", "line": "#F473B9"},
            "Сборка": {"fill": "rgba(56, 229, 77, 0.35)", "line": "#38E54D"},
            "Сварка": {"fill": "rgba(255, 139, 19, 0.35)", "line": "#FF8B13"},
            "Сборка/Сварка": {"fill": "rgba(156, 39, 176, 0.35)", "line": "#9C27B0"},
            "Покраска": {"fill": "rgba(0, 201, 167, 0.35)", "line": "#00C9A7"},
            "Цинк": {"fill": "rgba(142, 152, 168, 0.35)", "line": "#8E98A8"},
            "Комплектовка": {"fill": "rgba(210, 180, 140, 0.35)", "line": "#D2B48C"},
            "Laser": {"fill": "rgba(255, 107, 107, 0.35)", "line": "#FF6B6B"},
            "Saagimine": {"fill": "rgba(77, 150, 255, 0.35)", "line": "#4D96FF"},
            "Painutamine": {"fill": "rgba(107, 203, 119, 0.35)", "line": "#6BCB77"},
            "Puurimine": {"fill": "rgba(255, 217, 61, 0.35)", "line": "#FFD93D"},
            "Puhastus": {"fill": "rgba(244, 115, 185, 0.35)", "line": "#F473B9"},
            "Kokkupanek": {"fill": "rgba(56, 229, 77, 0.35)", "line": "#38E54D"},
            "Keevitamine": {"fill": "rgba(255, 139, 19, 0.35)", "line": "#FF8B13"},
            "Kokkupanek/Keevitamine": {"fill": "rgba(156, 39, 176, 0.35)", "line": "#9C27B0"},
            "Värvimine": {"fill": "rgba(0, 201, 167, 0.35)", "line": "#00C9A7"},
            "Tsinkimine": {"fill": "rgba(142, 152, 168, 0.35)", "line": "#8E98A8"},
            "Komplekteerimine": {"fill": "rgba(210, 180, 140, 0.35)", "line": "#D2B48C"},
            "Sawing": {"fill": "rgba(77, 150, 255, 0.35)", "line": "#4D96FF"},
            "Bending": {"fill": "rgba(107, 203, 119, 0.35)", "line": "#6BCB77"},
            "Drilling": {"fill": "rgba(255, 217, 61, 0.35)", "line": "#FFD93D"},
            "Deburring": {"fill": "rgba(244, 115, 185, 0.35)", "line": "#F473B9"},
            "Assembly": {"fill": "rgba(56, 229, 77, 0.35)", "line": "#38E54D"},
            "Welding": {"fill": "rgba(255, 139, 19, 0.35)", "line": "#FF8B13"},
            "Assembly/Welding": {"fill": "rgba(156, 39, 176, 0.35)", "line": "#9C27B0"},
            "Painting": {"fill": "rgba(0, 201, 167, 0.35)", "line": "#00C9A7"},
            "Zinc Plating": {"fill": "rgba(142, 152, 168, 0.35)", "line": "#8E98A8"},
            "Kitting": {"fill": "rgba(210, 180, 140, 0.35)", "line": "#D2B48C"},
        }
        
        df_bars = df_display.dropna(subset=[t["col_op"]])
        unique_ops = df_bars[t["col_op"]].unique() if not df_bars.empty else []
        
        for op in unique_ops:
            df_op = df_bars[df_bars[t["col_op"]] == op]
            custom_data = df_op[[t["col_desc"], t["col_op"], t["col_start"], t["col_finish"], t["col_deadline"], t["comments_label"], t["col_status"]]].values
            
            style = operation_styles.get(op, {"fill": "rgba(142, 152, 168, 0.35)", "line": "#8E98A8"})
            
            fig.add_trace(go.Bar(
                x=df_op[t["col_order"]],
                y=df_op['duration_ms'],
                base=df_op['raw_start'],
                name=op,
                marker_color=style["fill"],
                customdata=custom_data,
                hovertemplate=(
                    f"{t['comments_label']}: %{{customdata[5]}}<br>"
                    f"{t['col_op']}: %{{customdata[1]}}<extra></extra>"
                )
            ))
            
        # Добавление маркера дедлайна для каждого заказа (красная линия на одной линии с числом)
        deadline_points = []
        df_deadlines_unique = df_sorted[["order_number", "description", "deadline", "comments"]].drop_duplicates(subset=["order_number"])
        for _, row in df_deadlines_unique.iterrows():
            ord_num = str(row["order_number"])
            desc = str(row["description"]) if pd.notna(row["description"]) else "—"
            comments = str(row["comments"]) if pd.notna(row["comments"]) else "—"
            dls = parse_deadlines(row["deadline"])
            for d in dls:
                date_str = d["date"]
                label = d["label"]
                try:
                    dt = pd.to_datetime(date_str)
                    deadline_points.append({
                        "order_number": ord_num,
                        "description": desc,
                        "date": dt,
                        "label": label,
                        "comments": comments
                    })
                except Exception:
                    pass

        if deadline_points:
            df_dl_points = pd.DataFrame(deadline_points)
            dl_custom = df_dl_points[["description", "comments", "label", "date"]].copy()
            dl_custom["date_formatted"] = pd.to_datetime(dl_custom["date"]).dt.strftime('%d.%m.%Y')
            
            fig.add_trace(go.Scatter(
                x=df_dl_points["order_number"].astype(str),
                y=pd.to_datetime(df_dl_points["date"]) + pd.Timedelta(hours=12),  # Смещение на 12:00 для выравнивания с текстом даты
                mode="markers",
                marker=dict(symbol="line-ew", size=32, line=dict(width=4, color="red")),
                name=t["col_deadline"],
                customdata=dl_custom[["description", "comments", "label", "date_formatted"]].values,
                hovertemplate=(
                    "Срок: <b>%{customdata[3]} %{customdata[2]}</b><br>"
                    f"{t['col_desc']}: %{{customdata[0]}}<br>"
                    f"{t['comments_label']}: %{{customdata[1]}}<extra></extra>"
                )
            ))
        
        # Подсветка текущего дня (сегодня) - горизонтальная полоса
        today_start = datetime.today().strftime('%Y-%m-%d')
        tomorrow_start = (datetime.today() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        fig.add_hrect(
            y0=today_start,
            y1=tomorrow_start,
            fillcolor="#43A047",  # Насыщенный зелёный
            opacity=0.25,
            line_width=2,
            line_color="#2E7D32",
            line_dash="solid"
        )
        
        # Применяем диапазон зума к оси Y
        zoom_days_current = st.session_state.get("gantt_zoom_days", total_days)
        zoom_range_end = min_date + pd.Timedelta(days=zoom_days_current)
        if zoom_range_end > max_date:
            zoom_range_end = max_date

        fig.update_yaxes(
            type="date",
            range=[min_date.strftime('%Y-%m-%d'), zoom_range_end.strftime('%Y-%m-%d')],  # Диапазон с учётом зума
            tickvals=date_midpoints,
            ticktext=date_labels,
            showgrid=False,  # Скрываем сетку по центру текста (основные тики)
            minor=dict(
                tickvals=date_boundaries,  # Разделительные линии на границах дней
                showgrid=True,
                gridcolor="#E0E0E0",  # Приятный светло-серый цвет разделителей
                gridwidth=1
            )
        )
        
        unique_orders = list(df_display[t["col_order"]].unique())
        
        # Добавляем невидимый след для всех заказов, чтобы принудительно отобразить их на оси X
        if unique_orders:
            fig.add_trace(go.Scatter(
                x=unique_orders,
                y=[min_date + pd.Timedelta(hours=12)] * len(unique_orders),
                mode="markers",
                marker=dict(opacity=0),
                showlegend=False,
                hoverinfo="skip"
            ))
            
        tick_text = []
        for x in unique_orders:
            clean_x = str(x).replace(" 🔴", "").strip()
            if clean_x in expired_orders:
                tick_text.append(f"<span style='color: red; font-size: 9px;'>{clean_x}</span>")
            else:
                tick_text.append(f"<span style='font-size: 9px;'>{clean_x}</span>")
                
        fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=unique_orders,
            tickvals=unique_orders,
            ticktext=tick_text,
            tickangle=0,  # Строго горизонтально
            tickfont=dict(size=9, color="black"),  # Уменьшаем размер номеров заказов до 9px во избежание наложения
            fixedrange=True  # Запрещаем изменение масштаба оси X (всегда фиксированная ширина и отступы)
        )
        
        # Добавляем вертикальные разделительные линии между заказами (колонками)
        for i in range(len(unique_orders) - 1):
            fig.add_vline(
                x=i + 0.5,
                line=dict(color="#CCCCCC", width=1.5, dash="solid")
            )
            
        # Заполняем выходные дни (суббота и воскресенье) легким красным фоном - горизонтальные полосы
        for day in all_days:
            if day.weekday() == 5:  # Суббота
                fig.add_hrect(
                    y0=day.strftime('%Y-%m-%d'),
                    y1=(day + pd.Timedelta(days=2)).strftime('%Y-%m-%d'),
                    fillcolor="#FF6B6B",
                    opacity=0.12,  # Мягкий, слегка красный цвет
                    line_width=0,
                    layer="below"
                )
            elif day.weekday() == 6 and day == all_days[0]:  # Если первый день графика — воскресенье
                fig.add_hrect(
                    y0=day.strftime('%Y-%m-%d'),
                    y1=(day + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                    fillcolor="#FF6B6B",
                    opacity=0.12,
                    line_width=0,
                    layer="below"
                )
        
        # Вычисляем размеры графика динамически для оптимальной плотности и прокрутки
        chart_width = max(1000, len(unique_orders) * 150 + 150)
        # Высота графика зависит от текущего zoom-диапазона (количества видимых дней)
        visible_days_count = int((zoom_range_end - min_date).days)
        chart_height = max(400, visible_days_count * 20 + 120)

        fig.update_layout(
            xaxis_title=t["xaxis_title"],  # "Номер заказа" на горизонтальной оси
            yaxis_title=t["yaxis_title"],  # "Дата" на вертикальной оси
            barmode="group",
            bargap=0.30,  # Отступ между заказами (увеличен в 2 раза)
            bargroupgap=0.05,  # Отступ между операциями внутри одного заказа
            width=chart_width,
            height=chart_height,
            font=dict(family="Arial, Helvetica, sans-serif", size=12),  # Унифицированный шрифт для всех надписей
            hoverlabel=dict(font_size=15),  # Увеличенный размер шрифта во всплывающих подсказках
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.06,
                xanchor="left",
                x=0.0
            ),
            margin=dict(l=20, r=20, t=40, b=80)  # b=80: уменьшен отступ под легенду (промежуток вдвое меньше)
        )
        
        # CSS для стилизации контейнера графика с прокруткой по бокам и скрытия пустого отступа снизу
        st.markdown("""
        <style>
        /* Скрываем пустые контейнеры Streamlit, содержащие только теги style (убирает невидимые отступы) */
        div[data-testid="element-container"]:has(style) {
            display: none !important;
        }
        /* Ограничиваем внешний контейнер графика по высоте и убираем внешний отступ снизу */
        div[data-testid="element-container"]:has(div[data-testid="stPlotlyChart"]) {
            max-height: none !important;
            height: auto !important;
            margin-bottom: 0px !important;
        }
        div[data-testid="stPlotlyChart"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
            overflow-y: visible !important;
            max-height: none !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0px !important;
        }
        /* Фиксируем курсор — не меняем его при наведении на график */
        div[data-testid="stPlotlyChart"] *,
        div[data-testid="stPlotlyChart"] svg *,
        div[data-testid="stPlotlyChart"] .nsewdrag,
        div[data-testid="stPlotlyChart"] .drag,
        div[data-testid="stPlotlyChart"] canvas {
            cursor: default !important;
        }
        /* Значки управления графиком — правый нижний угол, на уровне легенды */
        div.modebar-container {
            top: auto !important;
            bottom: 56px !important;
            right: 10px !important;
        }
        /* Отступ перед таблицами-экспандерами после графика */
        div[data-testid="stExpander"] {
            margin-top: 14px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Принудительно задаем внутреннему блоку графика вычисленную ширину, чтобы он не сжимался
        st.markdown(f"""
        <style>
        div[data-testid="stPlotlyChart"] > div,
        div[data-testid="stPlotlyChart"] > div > div,
        div[data-testid="stPlotlyChart"] > div > div > div,
        div[data-testid="stPlotlyChart"] .js-plotly-plot,
        div[data-testid="stPlotlyChart"] .plot-container,
        div[data-testid="stPlotlyChart"] .main-svg,
        div[data-testid="stPlotlyChart"] svg.main-svg {{
            width: {chart_width}px !important;
            min-width: {chart_width}px !important;
            max-width: none !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        st.plotly_chart(fig, use_container_width=False)
        
        # CSS: приглушённый (прозрачный) стиль для первой колонки № в таблице ЗАКАЗЫ
        st.markdown("""
        <style>
        /* Первая ячейка каждой строки данных — колонка № */
        div[data-testid="stDataEditor"] [aria-colindex="1"] > div {
            color: rgba(0, 0, 0, 0.25) !important;
            font-size: 11px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Новая таблица: ЗАКАЗЫ (с комментариями)
        with st.expander(t["comments_table_title"], expanded=False):
            orders_df = get_worksheet_as_df("orders")
            if not orders_df.empty:
                df_with_comments = orders_df.copy()
                if not df_with_comments.empty:
                    df_with_comments = df_with_comments.copy()
                    # Сортируем по возрастанию дедлайна (от самых ранних к самым поздним), пустые уносим в конец
                    df_with_comments["parsed_deadline"] = df_with_comments["deadline"].apply(get_main_deadline)
                    df_with_comments["sort_deadline"] = df_with_comments["parsed_deadline"].apply(lambda d: d if pd.notna(d) else pd.Timestamp.max.date())
                    df_with_comments = df_with_comments.sort_values(by="sort_deadline", ascending=True).drop(columns=["parsed_deadline", "sort_deadline"]).reset_index(drop=True)
                    
                    if "notes" not in df_with_comments.columns:
                        df_with_comments["notes"] = ""
                    
                    df_comments_display = df_with_comments[["description", "comments", "deadline", "order_number", "notes"]].copy()
                    df_comments_display["notes"] = df_comments_display["notes"].fillna("").astype(str)
                    df_comments_display["comments"] = df_comments_display["comments"].fillna("").astype(str)
                    df_comments_display["description"] = df_comments_display["description"].fillna("").astype(str)
                    df_comments_display["order_number"] = df_comments_display["order_number"].fillna("").astype(str)
                    df_comments_display["deadline_display"] = df_comments_display["deadline"].apply(format_deadline_for_row)
                    
                    df_comments_display = df_comments_display.rename(columns={
                        "order_number": t["col_order"],
                        "description": t["order_desc"],
                        "deadline_display": t["col_deadline"],
                        "comments": t["comments_label"],
                        "notes": t["notes_label"]
                    })
                    
                    df_comments_display[t["col_order"]] = df_comments_display[t["col_order"]].apply(
                        lambda x: f"{x} 🔴" if str(x) in expired_orders else x
                    )
                    
                    # Встроенный индекс с 1 — отображается приглушённым серым Streamlit-ом автоматически
                    df_comments_display.index = range(1, len(df_comments_display) + 1)
                    
                    comments_table_height = max(120, (len(df_comments_display) + 1) * 28 + 45)

                    # Вычисляем ширины колонок по самой длинной строке
                    w_order    = 120
                    w_desc     = get_col_width(df_comments_display, t["order_desc"], 100, 600)
                    w_deadline = get_col_width(df_comments_display, t["col_deadline"], 100, 300)
                    w_comments = get_col_width(df_comments_display, t["comments_label"], 100, 600)
                    w_notes    = get_col_width(df_comments_display, t["notes_label"], 100, 600)

                    edited_comments = st.data_editor(
                        df_comments_display[[t["col_order"], t["order_desc"], t["col_deadline"], t["comments_label"], t["notes_label"]]],
                        use_container_width=False,
                        num_rows="fixed",
                        key="comments_editor",
                        height=comments_table_height,
                        row_height=28,
                        disabled=[t["col_order"], t["col_deadline"]],
                        hide_index=False,
                        column_config={
                            t["comments_label"]: st.column_config.TextColumn(width=w_comments),
                            t["order_desc"]:     st.column_config.TextColumn(width=w_desc),
                            t["col_deadline"]:   st.column_config.TextColumn(width=w_deadline),
                            t["col_order"]:      st.column_config.TextColumn(alignment="left", width=w_order),
                            t["notes_label"]:    st.column_config.TextColumn(width=w_notes),
                        }
                    )
                    
                    if "comments_editor" in st.session_state:
                        comm_changes = st.session_state["comments_editor"]
                        if comm_changes.get("edited_rows"):
                            for idx_str, edited_cols in comm_changes["edited_rows"].items():
                                idx = int(idx_str)
                                if idx < len(df_with_comments):
                                    order_id = str(df_with_comments.iloc[idx]['id'])
                                    if t["order_desc"] in edited_cols:
                                        new_desc = edited_cols[t["order_desc"]]
                                        update_order_description(order_id, new_desc)
                                    if t["comments_label"] in edited_cols:
                                        new_comm = edited_cols[t["comments_label"]]
                                        update_order_comments(order_id, new_comm)
                                    if t["notes_label"] in edited_cols:
                                        new_notes = edited_cols[t["notes_label"]]
                                        update_order_notes(order_id, new_notes)
                            del st.session_state["comments_editor"]
                            st.rerun()
                else:
                    st.info("Нет заказов в базе данных." if lang == "RU" else ("Andmebaasis puuduvad tellimused." if lang == "EE" else "No orders in database."))
            else:
                st.info("Нет заказов в базе данных." if lang == "RU" else ("Andmebaasis puuduvad tellimused." if lang == "EE" else "No orders in database."))

        # Сводная таблица по всем операциям
        with st.expander(t["table_title"], expanded=False):
            # В таблице показываем только те заказы, у которых есть запланированные операции
            df_table_display = df_display.dropna(subset=[t["col_op"]])
            df_sorted_clean = df_sorted.dropna(subset=["op_name"])
            
            df_table = df_table_display.copy()
            df_table[t["col_start"]] = pd.to_datetime(df_sorted_clean['start_date']).dt.date
            df_table[t["col_finish"]] = pd.to_datetime(df_sorted_clean['end_date']).dt.date
            df_table[t["col_deadline"]] = pd.to_datetime(df_sorted_clean['deadline'], errors="coerce").dt.date
            df_table[t["col_order"]] = df_table[t["col_order"]].apply(
                lambda x: f"{x} 🔴" if str(x) in expired_orders else x
            )
            
            cols_to_show = [t["comments_label"], t["col_op"], t["col_start"], t["col_finish"], t["col_status"]]
            
            op_table_height = max(200, (len(df_table) + 1) * 28 + 45)
            edited_df = st.data_editor(
                df_table[cols_to_show],
                use_container_width=False,
                num_rows="dynamic",
                key="op_editor",
                height=op_table_height,
                row_height=28,
                disabled=[],
                column_config={
                    t["col_order"]: st.column_config.TextColumn(alignment="left"),
                    t["col_desc"]: st.column_config.TextColumn(),
                    t["comments_label"]: st.column_config.TextColumn(width=get_col_width(df_table, t["comments_label"], 150, 1000)),
                    t["col_deadline"]: st.column_config.DateColumn(format="DD.MM.YYYY"),
                    t["col_op"]: st.column_config.SelectboxColumn(options=t["operations_list"], width=150),
                    t["col_start"]: st.column_config.DateColumn(format="DD.MM.YYYY", width=120),
                    t["col_finish"]: st.column_config.DateColumn(format="DD.MM.YYYY", width=120),
                    t["col_status"]: st.column_config.SelectboxColumn(options=list(t["statuses"].values()), width=150),
                }
            )
            
            # Обработка изменений из редактора таблицы
            if "op_editor" in st.session_state:
                changes = st.session_state["op_editor"]
                
                # 1. Удаление строк
                if changes.get("deleted_rows"):
                    for idx in changes["deleted_rows"]:
                        if idx < len(df_sorted_clean):
                            op_id = int(df_sorted_clean.iloc[idx]['op_id'])
                            delete_operation(op_id)
                    # Clear stale editor state before rerun to avoid index errors
                    del st.session_state["op_editor"]
                    st.rerun()
                    
                # 2. Редактирование строк
                if changes.get("edited_rows"):
                    for idx_str, edited_cols in changes["edited_rows"].items():
                        idx = int(idx_str)
                        if idx < len(df_sorted_clean):
                            op_id = int(df_sorted_clean.iloc[idx]['op_id'])
                            order_id = str(df_sorted_clean.iloc[idx]['order_id'])
                            
                            # Получаем текущие значения для обновления
                            current_op_name = df_sorted_clean.iloc[idx]['op_name']
                            current_start = df_sorted_clean.iloc[idx]['start_date']
                            current_end = df_sorted_clean.iloc[idx]['end_date']
                            current_status = df_sorted_clean.iloc[idx]['status']
                            
                            op_changed = False
                            if t["col_op"] in edited_cols:
                                current_op_name = edited_cols[t["col_op"]]
                                op_changed = True
                            if t["col_start"] in edited_cols:
                                current_start = str(edited_cols[t["col_start"]])
                                op_changed = True
                            if t["col_finish"] in edited_cols:
                                current_end = str(edited_cols[t["col_finish"]])
                                op_changed = True
                            if t["col_status"] in edited_cols:
                                inv_statuses = {v: k for k, v in t["statuses"].items()}
                                current_status = inv_statuses.get(edited_cols[t["col_status"]], current_status)
                                op_changed = True
                                
                            if op_changed:
                                update_operation(op_id, current_op_name, current_start, current_end, current_status)
                                
                            # Если изменено Описание (Название заказа)
                            if t["col_desc"] in edited_cols:
                                new_desc = edited_cols[t["col_desc"]]
                                update_order_description(order_id, new_desc)
                                
                            # Если изменен Комментарий
                            if t["comments_label"] in edited_cols:
                                new_comm = edited_cols[t["comments_label"]]
                                update_order_comments(order_id, new_comm)
                                
                    # Clear stale editor state before rerun to avoid index errors
                    del st.session_state["op_editor"]
                    st.rerun()

    # --- ВКЛАДКА 2: УПРАВЛЕНИЕ СТАТУСАМИ И УДАЛЕНИЕ ---
    with tab_manage:
        # 1. Редактирование операций
        with st.expander(t["manage_ops_header"], expanded=False):
            # Фильтруем строки, чтобы показывать только те, где есть операции
            df_manage_sorted = df_raw.dropna(subset=["op_name"]).sort_values(by="order_number", ascending=True, key=lambda x: x.astype(str))
            
            op_options = {}
            for _, row in df_manage_sorted.iterrows():
                fmt_start = datetime.strptime(row['start_date'], '%Y-%m-%d').strftime('%d.%m.%Y')
                fmt_end = datetime.strptime(row['end_date'], '%Y-%m-%d').strftime('%d.%m.%Y')
                label = f"{row['order_number']} — {row['op_name']} [{fmt_start} - {fmt_end}] ({t['statuses'].get(row['status'], row['status'])})"
                op_options[label] = row
                
            if not op_options:
                st.info(t["info_add_order_first"])
            else:
                selected_op_label = st.selectbox(t["select_op_to_change"], list(op_options.keys()))
            
                if selected_op_label:
                    selected_op_data = op_options[selected_op_label]
                    current_eng_status = selected_op_data['status']
                    current_id = selected_op_data['op_id']
                    
                    st.info(t["current_status"].format(t["statuses"].get(current_eng_status, current_eng_status)))
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        inv_statuses = {v: k for k, v in t["statuses"].items()}
                        new_status_name = st.selectbox(t["new_status_label"], list(inv_statuses.keys()))
                        v_status_to_save = inv_statuses[new_status_name]
                    
                    with col2:
                        st.write(" ")
                        st.write(" ")
                        if st.button(t["btn_update_status"], use_container_width=True):
                            update_operation_status(current_id, v_status_to_save)
                            st.success(t["msg_status_updated"])
                            st.rerun()
                    
                    st.markdown("---")
                    st.subheader(t["danger_zone"])
                    
                    col_del1, col_del2 = st.columns([2, 1])
                    with col_del1:
                        st.write(t["delete_op_label"])
                    with col_del2:
                        if st.button(t["btn_delete_op"], use_container_width=True, type="secondary"):
                            delete_operation(current_id)
                            st.success(t["msg_op_deleted"])
                            st.rerun()
                        
        # 2. Редактирование дедлайнов заказа
        with st.expander(t["edit_deadlines_header"], expanded=False):
            df_orders_for_edit = get_orders_list()
            if not df_orders_for_edit.empty:
                order_edit_options = {}
                for _, row in df_orders_for_edit.iterrows():
                    ord_num = str(row['order_number'])
                    ord_name = str(row.get('comments', '')).strip()
                    label = f"{ord_num} — {ord_name}" if ord_name else ord_num
                    order_edit_options[label] = row['id']
                selected_order_to_edit = st.selectbox(t["select_order_to_edit_deadlines"], list(order_edit_options.keys()), key="edit_dl_order_select")
                
                if selected_order_to_edit:
                    selected_order_id = order_edit_options[selected_order_to_edit]
                    
                    orders_df = get_worksheet_as_df("orders")
                    order_row = orders_df[orders_df["id"].astype(str) == str(selected_order_id)]
                    
                    if not order_row.empty:
                        current_dl_str = order_row.iloc[0]["deadline"]
                        
                        state_key = f"edit_deadlines_{selected_order_id}"
                        if state_key not in st.session_state:
                            parsed = parse_deadlines(current_dl_str)
                            for item in parsed:
                                try:
                                    item["date"] = pd.to_datetime(item["date"]).date()
                                except Exception:
                                    item["date"] = datetime.today().date()
                            st.session_state[state_key] = parsed
                            
                        col_hdr_date, col_hdr_lbl, col_hdr_btn = st.columns([0.45, 0.45, 0.1])
                        with col_hdr_date:
                            st.caption(t['deadline_date_label'])
                        with col_hdr_lbl:
                            st.caption(t['deadline_name_label'])
                            
                        edited_dls = []
                        for idx, dl in enumerate(st.session_state[state_key]):
                            col_date, col_lbl, col_btn = st.columns([0.45, 0.45, 0.1])
                            with col_date:
                                d_val = st.date_input(
                                    f"edit_date_{idx}", 
                                    dl["date"], 
                                    format="DD.MM.YYYY", 
                                    key=f"edit_dl_date_{selected_order_id}_{idx}",
                                    label_visibility="collapsed"
                                )
                            with col_lbl:
                                l_val = st.text_input(
                                    f"edit_lbl_{idx}", 
                                    dl["label"], 
                                    key=f"edit_dl_lbl_{selected_order_id}_{idx}", 
                                    placeholder="Лазер...",
                                    label_visibility="collapsed"
                                )
                            with col_btn:
                                if st.button("×", key=f"edit_dl_del_{selected_order_id}_{idx}"):
                                    st.session_state[state_key].pop(idx)
                                    st.rerun()
                            edited_dls.append({"date": d_val, "label": l_val})
                            
                        st.session_state[state_key] = edited_dls
                        
                        if st.button(t["btn_add_deadline"], key=f"edit_dl_add_{selected_order_id}"):
                            st.session_state[state_key].append({"date": datetime.today().date(), "label": ""})
                            st.rerun()
                            
                        if st.button(t["btn_save_deadlines"], key=f"edit_dl_save_{selected_order_id}", type="primary", use_container_width=True):
                            dl_strings = []
                            for dl in st.session_state[state_key]:
                                if hasattr(dl["date"], "strftime"):
                                    d_str = dl["date"].strftime('%Y-%m-%d')
                                else:
                                    d_str = str(dl["date"])
                                lbl = dl["label"].strip()
                                if lbl:
                                    dl_strings.append(f"{d_str} ({lbl})")
                                else:
                                    dl_strings.append(d_str)
                            serialized_dl = ", ".join(dl_strings)
                            
                            update_order_deadline(selected_order_id, serialized_dl)
                            if state_key in st.session_state:
                                del st.session_state[state_key]
                            st.success(t["msg_deadlines_saved"])
                            st.rerun()
                            
        # 3. Удаление заказа
        with st.expander(t["delete_order_label"], expanded=False):
            # Bug 4 fix: refresh orders list here to avoid stale data after rerun
            df_orders_for_delete = get_orders_list()
            if not df_orders_for_delete.empty:
                order_del_options = {}
                for _, row in df_orders_for_delete.iterrows():
                    ord_num = str(row['order_number'])
                    ord_name = str(row.get('comments', '')).strip()
                    label = f"{ord_num} — {ord_name}" if ord_name else ord_num
                    order_del_options[label] = row['id']
                col_ord_del1, col_ord_del2 = st.columns([2, 1])
                with col_ord_del1:
                    selected_order_to_del = st.selectbox(t["delete_order_label"], list(order_del_options.keys()))
                with col_ord_del2:
                    st.write(" ")
                    st.write(" ")
                    if st.button(t["btn_delete_order"], use_container_width=True, type="primary"):
                        delete_order(order_del_options[selected_order_to_del])
                        st.success(t["msg_order_deleted"])
                        st.rerun()

else:
    st.info(t["info_empty_db"])

df_parts = get_parts()
st.markdown("---")
st.markdown(
    """
    <style>
    /* Скрываем кнопку "Manage app" / Streamlit Badge в нижнем правом углу */
    div[data-testid="stViewerBadge"],
    .viewerBadge,
    [data-testid="manage-app-button"],
    div[class*="viewerBadge"] {
        display: none !important;
    }
    
    /* Скрыть полосы прокрутки во всем приложении и таблицах */
    ::-webkit-scrollbar {
        display: none !important;
        width: 0px !important;
        height: 0px !important;
    }
    * {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    
    /* Global styles for parts section to increase font sizes */
    .parts-title {
        font-size: 28px !important;
        font-weight: bold;
        color: #2C3E50;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    .parts-history-title {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #2C3E50;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    /* Style Streamlit expander headers globally */
    .streamlit-expanderHeader,
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] details summary p {
        font-size: 16px !important;
        font-weight: normal !important;
    }
    /* Style bold text in expander headers to be large and very bold */
    div[data-testid="stExpander"] details summary strong,
    div[data-testid="stExpander"] details summary b {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #2C3E50 !important;
    }
    /* Increase font sizes for inputs, buttons and text in streamlit data editor wrapper */
    div[data-testid="stDataEditor"] {
        font-size: 15px !important;
    }
    div[data-testid="stMarkdownContainer"] p {
        font-size: 15px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(f"<div class='parts-title'>{t['parts_sidebar_header']}</div>", unsafe_allow_html=True)

# Строим Plotly Charts (по одному графику для каждой детали)
if df_parts.empty:
    fig_parts = go.Figure()
    # Отображаем пустой график с красивым текстовым уведомлением по центру
    fig_parts.add_trace(go.Bar(
        x=[],
        y=[],
        marker_color="#FF6B6B"
    ))
    fig_parts.update_layout(
        annotations=[dict(
            text=t.get("no_parts_data", "No parts data"),
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )]
    )
    st.plotly_chart(fig_parts, use_container_width=True)
else:
    # Переводим направление для UI
    dir_map_to_ui = {
        "up": t["direction_up"], 
        "down": t["direction_down"],
        t["direction_up"]: t["direction_up"],
        t["direction_down"]: t["direction_down"]
    }
    dir_map_to_db = {
        t["direction_up"]: "up", 
        t["direction_down"]: "down",
        "up": "up",
        "down": "down"
    }

    # Загружаем все логи деталей
    all_logs = get_production_logs()
    
    # Преобразуем дату для парсинга и сортировки
    if not all_logs.empty:
        all_logs["parsed_date"] = pd.to_datetime(all_logs["date"], format="%d.%m.%Y", errors="coerce")
        all_logs = all_logs.dropna(subset=["parsed_date"])
        all_logs = all_logs.sort_values(by="parsed_date")
    
    # Цветовая палитра для линий разных деталей
    colors_palette = ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF"]
    
    for i, (_, part_row) in enumerate(df_parts.iterrows()):
        part_id = part_row["id"]
        part_name = part_row["part_name"]
        direction = part_row["direction"]
        target = int(part_row["target_quantity"])
        
        dir_text = t["direction_up"] if direction == "up" else t["direction_down"]
        with st.expander(f"**📦 {part_name}** | {t['plan_label']}: {target} | {dir_text}", expanded=False):
        
            # Получаем логи для этой конкретной детали
            if not all_logs.empty:
                part_logs = all_logs[all_logs["part_id"] == int(part_id)]
            else:
                part_logs = pd.DataFrame()
            
            if part_logs.empty:
                # Свежесозданная деталь без логов выпуска - показываем начальную точку
                part_logs = pd.DataFrame([{
                    "id": 1,
                    "part_id": part_id,
                    "date": part_row["last_updated"],
                    "quantity_added": part_row["completed_quantity"],
                    "total_completed_after": part_row["completed_quantity"],
                    "parsed_date": pd.to_datetime(part_row["last_updated"], format="%d.%m.%Y", errors="coerce")
                }])
            else:
                part_logs = part_logs.copy()
                part_logs["parsed_date"] = pd.to_datetime(part_logs["date"], format="%d.%m.%Y", errors="coerce")
                part_logs = part_logs.dropna(subset=["parsed_date"])
                part_logs = part_logs.sort_values(by="parsed_date")
            
            # Группируем логи по датам
            grouped = part_logs.groupby("parsed_date").agg({
                "date": "first",
                "quantity_added": "sum",
                "total_completed_after": "last"
            }).reset_index()
            grouped = grouped.sort_values(by="parsed_date")
        
            # Построение массивов Плана и Факта
            y_plan = []
            y_fact = []
            colors = []
        
            for idx, row in grouped.iterrows():
                completed = int(row["total_completed_after"])
                remaining_val = max(0, target - completed)
            
                if direction == "down":
                    y_plan.append(0)
                    y_fact.append(remaining_val)
                    is_success = (remaining_val == 0)
                else:
                    y_plan.append(target)
                    y_fact.append(completed)
                    is_success = (completed >= target)
                
                colors.append("rgba(46, 204, 113, 0.25)" if is_success else "rgba(231, 76, 60, 0.25)")
            
            bases = [min(p, f) for p, f in zip(y_plan, y_fact)]
            heights = [abs(p - f) for p, f in zip(y_plan, y_fact)]
        
            # Вычисляем позиции текста
            plan_positions = []
            fact_positions = []
            for p, f in zip(y_plan, y_fact):
                if f >= p:
                    plan_positions.append("bottom center")
                    fact_positions.append("top center")
                else:
                    plan_positions.append("top center")
                    fact_positions.append("bottom center")
                
            custom_data_all = pd.DataFrame({
                "target": [target] * len(grouped),
                "completed": grouped["total_completed_after"],
                "remaining": [max(0, target - int(c)) for c in grouped["total_completed_after"]],
                "pct": [round(int(c) / target * 100) for c in grouped["total_completed_after"]],
                "updated": grouped["date"],
                "direction_type": [direction] * len(grouped)
            }).values
        
            # Вычисляем максимальное значение для автоматического Y-диапазона с запасом 15%, чтобы цифры наверху не обрезались
            max_y_val = max(target, max(y_fact))
            y_max_range = max_y_val + max(1, int(max_y_val * 0.15))
        
            # Название детали над графиком отдельным заголовком 18px
        
            fig = go.Figure()
            color = colors_palette[i % len(colors_palette)]
        
            # 2. Линия План (цель) красного цвета
            fig.add_trace(go.Scatter(
                x=grouped["date"],
                y=y_plan,
                mode="lines+markers+text",
                name=t["plan_label"],
                line=dict(color="#E74C3C", width=3),
                marker=dict(size=8, color="#E74C3C", symbol="circle"),
                text=[str(v) for v in y_plan],
                textposition=plan_positions,
                textfont=dict(size=14, color="black", family="Arial"),
                cliponaxis=False,
                customdata=custom_data_all,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{t['plan_label']}: %{{y}}<br>"
                    f"{t['part_target_label']}: %{{customdata[0]}}<br>"
                    f"{t['last_updated_label']}: %{{customdata[4]}}<extra></extra>"
                )
            ))
        
            # 3. Линия Факт (выпуск/остаток)
            fig.add_trace(go.Scatter(
                x=grouped["date"],
                y=y_fact,
                mode="lines+markers+text",
                name=t["fact_label"],
                line=dict(color=color, width=3),
                marker=dict(size=8, color=color, symbol="circle"),
                text=[str(v) for v in y_fact],
                textposition=fact_positions,
                textfont=dict(size=14, color="black", family="Arial"),
                cliponaxis=False,
                customdata=custom_data_all,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{t['fact_label']}: %{{y}}<br>"
                    f"{t['part_completed_label']}: %{{customdata[1]}}<br>"
                    f"{t['part_remaining_label']}: %{{customdata[2]}}<br>"
                    "Прогресс: %{customdata[3]}%<br>"
                    f"{t['last_updated_label']}: %{{customdata[4]}}<extra></extra>"
                )
            ))
        
            dir_text = t["direction_up"] if direction == "up" else t["direction_down"]
            fig.update_layout(
                title=dict(
                    text=f"{t['plan_label']}: {target}  |  {dir_text}",
                    font=dict(size=13, color="#7F8C8D")
                ),
                plot_bgcolor="white",
                height=400,
                margin=dict(l=20, r=20, t=60, b=80),
                xaxis=dict(
                    type="category", 
                    categoryorder="array",
                    categoryarray=grouped["date"].tolist(),
                    title=dict(
                        text=t["last_updated_label"],
                        font=dict(size=15, color="black")
                    ),
                    tickfont=dict(size=13, color="black"),
                    showgrid=True,
                    gridcolor="#E5E5E5",
                    linecolor="#CCCCCC"
                ),
                yaxis=dict(
                    title=dict(
                        text=t["part_qty_label"],
                        font=dict(size=15, color="black")
                    ),
                    tickfont=dict(size=13, color="black"),
                    range=[0, y_max_range],
                    showgrid=True,
                    gridcolor="#E5E5E5",
                    linecolor="#CCCCCC"
                ),
                hovermode="closest",
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="left",
                    x=0.0,
                    font=dict(size=13, color="black")
                )
            )
        
            st.plotly_chart(fig, use_container_width=True, key=f"fig_part_{part_id}")
        
            # --- БЛОК НАСТРОЕК И ИСТОРИИ ДЛЯ КОНКРЕТНОЙ ДЕТАЛИ ---
            with st.expander(f"⚙️ {t['part_settings_title']}: {part_name}", expanded=False):
                # 1. Редактор одной строки
                editor_key = f"editor_part_{part_id}"
            
                df_single = df_parts[df_parts["id"].astype(str) == str(part_id)].copy()
                df_single["direction"] = df_single["direction"].map(dir_map_to_ui).fillna(t["direction_up"])
                df_single["add_output"] = None
            
                # Принудительное приведение типов для стабильности st.data_editor
                df_single["part_name"] = df_single["part_name"].fillna("").astype(str)
                df_single["target_quantity"] = pd.to_numeric(df_single["target_quantity"], errors="coerce").fillna(100).astype(int)
                # Внести выпуск оставляем пустым (None) по умолчанию
                df_single["add_output"] = df_single["add_output"].astype(object)
                df_single["direction"] = df_single["direction"].fillna(t["direction_up"]).astype(str)
            
                # Дата обновления по умолчанию всегда сегодняшняя актуальная дата
                df_single["last_updated"] = datetime.today().date()
            
                edited_single = st.data_editor(
                    df_single[["part_name", "target_quantity", "add_output", "last_updated", "direction"]],
                    use_container_width=False,
                    num_rows="fixed",
                    key=editor_key,
                    column_config={
                        "part_name": st.column_config.TextColumn(t["part_name_label"], required=True, width=get_col_width(df_single, "part_name", 150, 1000)),
                        "target_quantity": st.column_config.NumberColumn(t["part_target_label"], min_value=1, step=10, required=True, width=120),
                        "add_output": st.column_config.NumberColumn(t["add_output_label"], min_value=0, step=1, required=True, width=120),
                        "last_updated": st.column_config.DateColumn(
                            t["last_updated_label"],
                            format="DD.MM.YYYY",
                            required=True,
                            width=120
                        ),
                        "direction": st.column_config.SelectboxColumn(
                            t["direction_label"],
                            options=[t["direction_up"], t["direction_down"]],
                            required=True,
                            width=150
                        )
                    }
                )
            
                # Добавлена кнопка Сохранить для ручного сохранения изменений и удаления автоматического внесения
                if st.button(t["btn_save"], key=f"save_btn_{part_id}", type="primary", use_container_width=True):
                    has_changes = False
                    if editor_key in st.session_state:
                        changes = st.session_state[editor_key]
                        if changes.get("edited_rows"):
                            has_changes = True
                            for idx_str, edited_cols in changes["edited_rows"].items():
                                current_name = df_single.iloc[0]["part_name"]
                                current_target = df_single.iloc[0]["target_quantity"]
                                current_completed = int(df_parts[df_parts["id"].astype(str) == str(part_id)]["completed_quantity"].values[0])
                                current_dir = df_parts[df_parts["id"].astype(str) == str(part_id)]["direction"].values[0]
                            
                                # Получаем текущую дату записи
                                current_date_val = df_single.iloc[0]["last_updated"]
                                if hasattr(current_date_val, "strftime"):
                                    current_date_str = current_date_val.strftime('%d.%m.%Y')
                                else:
                                    current_date_str = str(current_date_val)
                                
                                # Если пользователь отредактировал дату
                                if "last_updated" in edited_cols:
                                    new_date_val = edited_cols["last_updated"]
                                    if hasattr(new_date_val, "strftime"):
                                        current_date_str = new_date_val.strftime('%d.%m.%Y')
                                    else:
                                        try:
                                            current_date_str = pd.to_datetime(new_date_val).strftime('%d.%m.%Y')
                                        except:
                                            current_date_str = str(new_date_val)
                                        
                                if "part_name" in edited_cols:
                                    current_name = edited_cols["part_name"]
                                if "target_quantity" in edited_cols:
                                    current_target = edited_cols["target_quantity"]
                                if "direction" in edited_cols:
                                    current_dir = dir_map_to_db.get(edited_cols["direction"], "up")
                            
                                # Если пользователь добавил выпуск (обрабатываем пустые и некорректные значения безопасно)
                                if "add_output" in edited_cols:
                                    val = edited_cols["add_output"]
                                    try:
                                        if val is None or pd.isna(val) or str(val).strip() == "":
                                            added_val = 0
                                        else:
                                            added_val = int(float(val))
                                    except:
                                        added_val = 0
                                    
                                    if added_val > 0:
                                        current_completed += added_val
                                        # Логируем изменения с указанной датой
                                        log_production(part_id, added_val, current_completed, current_date_str)
                                    
                                update_part(part_id, current_name, current_target, current_completed, current_date_str, current_dir)
                        
                            # Очищаем состояние редактора
                            if editor_key in st.session_state:
                                del st.session_state[editor_key]
                            st.success(t["msg_save_success"])
                            st.rerun()
                
                    if not has_changes:
                        st.info(t["msg_no_changes"])
                        
                # 2. Список истории (слева) и кнопка удаления (справа, сдвинута к правому краю и уменьшена)
                col_history, col_actions = st.columns([2.5, 1.5])
            
                with col_history:
                    # История помещена в st.expander, свернутый по умолчанию (теперь слева)
                    with st.expander(f"📋 {t['history_title']}", expanded=False):
                        # Фильтруем логи только для этой детали, где количество > 0
                        if not part_logs.empty:
                            # Исключаем технические нулевые записи
                            history_df = part_logs[part_logs["quantity_added"] > 0].copy()
                        else:
                            history_df = pd.DataFrame()
                        
                        if not history_df.empty:
                            history_df = history_df.sort_values(by="parsed_date", ascending=True)
                        
                            df_editor_history = history_df.copy().reset_index(drop=True)
                            df_editor_history["date"] = pd.to_datetime(df_editor_history["date"], format="%d.%m.%Y", errors="coerce").dt.date
                        
                            history_editor_key = f"history_editor_part_{part_id}"
                        
                            history_table_height = max(120, (len(df_editor_history) + 1) * 28 + 45)
                            edited_history = st.data_editor(
                                df_editor_history[["date", "quantity_added"]],
                                use_container_width=False,
                                num_rows="dynamic", # Разрешаем добавление и удаление строк для полного редактирования
                                key=history_editor_key,
                                height=history_table_height,
                                column_config={
                                    "date": st.column_config.DateColumn(t["last_updated_label"], format="DD.MM.YYYY", required=True, width=120),
                                    "quantity_added": st.column_config.NumberColumn(t["history_added_label"], min_value=1, step=1, required=True, width=120)
                                }
                            )
                            st.caption("Выделите строку и нажмите Delete (или значок корзины) для удаления, либо используйте пустую строку внизу для добавления." if lang == "RU" else ("Vali rida ja vajuta Delete kustutamiseks või kasuta alumist rida lisamiseks." if lang == "EE" else "Select row and press Delete to remove, or use the bottom blank row to add."))
                        
                            # Обработка изменений в истории (полное управление: добавление, изменение, удаление)
                            if history_editor_key in st.session_state:
                                hist_changes = st.session_state[history_editor_key]
                                change_happened = False
                            
                                # 1. Обработка удалений
                                if hist_changes.get("deleted_rows"):
                                    for idx in hist_changes["deleted_rows"]:
                                        if idx < len(df_editor_history):
                                            log_row_id = df_editor_history.iloc[idx]["id"]
                                            delete_production_log(log_row_id)
                                            # Удаляем из локального датафрейма для последующего пересчета
                                            part_logs = part_logs[pd.to_numeric(part_logs["id"], errors="coerce") != pd.to_numeric(log_row_id, errors="coerce")]
                                            change_happened = True
                                        
                                # 2. Обработка редактирования
                                if hist_changes.get("edited_rows"):
                                    for idx_str, edited_cols in hist_changes["edited_rows"].items():
                                        idx = int(idx_str)
                                        log_row_id = df_editor_history.iloc[idx]["id"]
                                        match_idx = part_logs[pd.to_numeric(part_logs["id"], errors="coerce") == pd.to_numeric(log_row_id, errors="coerce")].index
                                        if len(match_idx) > 0:
                                            if "date" in edited_cols:
                                                new_d = edited_cols["date"]
                                                if hasattr(new_d, "strftime"):
                                                    date_str = new_d.strftime('%d.%m.%Y')
                                                else:
                                                    try:
                                                        date_str = pd.to_datetime(new_d).strftime('%d.%m.%Y')
                                                    except:
                                                        date_str = str(new_d)
                                                part_logs.loc[match_idx, "date"] = date_str
                                            if "quantity_added" in edited_cols:
                                                val = edited_cols["quantity_added"]
                                                try:
                                                    if val is None or pd.isna(val) or str(val).strip() == "":
                                                        new_qty = 0
                                                    else:
                                                        new_qty = int(float(val))
                                                except:
                                                    new_qty = 0
                                                part_logs.loc[match_idx, "quantity_added"] = new_qty
                                            change_happened = True
                                        
                                # 3. Обработка добавлений
                                if hist_changes.get("added_rows"):
                                    all_logs_df = get_worksheet_as_df("parts_log")
                                    max_id = 1
                                    if not all_logs_df.empty:
                                        ids = pd.to_numeric(all_logs_df["id"], errors="coerce").dropna().astype(int)
                                        if not ids.empty:
                                            max_id = int(ids.max())
                                        
                                    for new_row_data in hist_changes["added_rows"]:
                                        max_id += 1
                                    
                                        # Парсим дату
                                        new_d = new_row_data.get("date", datetime.today().date())
                                        if hasattr(new_d, "strftime"):
                                            date_str = new_d.strftime('%d.%m.%Y')
                                        else:
                                            try:
                                                date_str = pd.to_datetime(new_d).strftime('%d.%m.%Y')
                                            except:
                                                date_str = datetime.today().strftime('%d.%m.%Y')
                                            
                                        # Парсим количество
                                        val = new_row_data.get("quantity_added", 0)
                                        try:
                                            qty = int(float(val))
                                        except:
                                            qty = 0
                                        
                                        if qty > 0:
                                            # Создаем новую запись в таблице parts_log в Google Sheets
                                            log_production(part_id, qty, qty, date_str)
                                        
                                            # Добавляем в локальный датафрейм для пересчета
                                            new_row_df = pd.DataFrame([{
                                                "id": max_id,
                                                "part_id": part_id,
                                                "date": date_str,
                                                "quantity_added": qty,
                                                "total_completed_after": qty,
                                                "parsed_date": pd.to_datetime(date_str, format="%d.%m.%Y", errors="coerce")
                                            }])
                                            part_logs = pd.concat([part_logs, new_row_df], ignore_index=True)
                                            change_happened = True
                                        
                                # Пересчитываем накопительный итог и сохраняем, если были изменения
                                if change_happened:
                                    if recalculate_and_save_part_logs(part_id, part_logs):
                                        del st.session_state[history_editor_key]
                                        st.rerun()
                        else:
                            st.info("История пуста." if lang == "RU" else "Ajalugu on tühi." if lang == "EE" else "History is empty.")
                        
                with col_actions:
                    # Внедряем CSS для сильного уменьшения шрифта и размера кнопок удаления (теперь в правой колонке)
                    st.markdown("""
                    <style>
                    div[data-testid="column"]:nth-of-type(2) button {
                        font-size: 10px !important;
                        height: 24px !important;
                        line-height: 1 !important;
                        padding: 0px 6px !important;
                        background-color: #fdfefe !important;
                        color: #95a5a6 !important;
                        border: 1px solid #e5e8e8 !important;
                    }
                    div[data-testid="column"]:nth-of-type(2) button:hover {
                        color: #c0392b !important;
                        border-color: #f5b7b1 !important;
                        background-color: #fdf2f2 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                
                    confirm_key = f"confirm_del_{part_id}"
                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False
                    
                    if not st.session_state[confirm_key]:
                        st.write("") # Отступ
                        if st.button(t["btn_delete_part"], key=f"del_btn_{part_id}", type="secondary", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Удалить деталь?" if lang == "RU" else "Kustuta detail?" if lang == "EE" else "Delete part?")
                        col_yes, col_no = st.columns([1, 1])
                        with col_yes:
                            if st.button("Да" if lang == "RU" else "Jah" if lang == "EE" else "Yes", key=f"yes_del_{part_id}", type="primary", use_container_width=True):
                                if delete_part(part_id):
                                    del st.session_state[confirm_key]
                                    st.success("Деталь удалена!" if lang == "RU" else "Detail kustutatud!" if lang == "EE" else "Part deleted!")
                                    st.rerun()
                        with col_no:
                            if st.button("Нет" if lang == "RU" else "Ei" if lang == "EE" else "No", key=f"no_del_{part_id}", type="secondary", use_container_width=True):
                                st.session_state[confirm_key] = False
                                st.rerun()

