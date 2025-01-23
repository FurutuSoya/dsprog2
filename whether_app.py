import flet as ft
import requests
import sqlite3
from datetime import datetime

# 気象庁APIエンドポイント
AREA_LIST_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


# データベースの初期化
DB_FILE = "weather_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # エリア情報テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    # 天気予報テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            weather TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            FOREIGN KEY (area_code) REFERENCES areas (code)
        )
    """)
    conn.commit()
    conn.close()

# DB操作: エリア情報保存
def save_areas_to_db(areas):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for code, details in areas.items():
        cur.execute("INSERT OR IGNORE INTO areas (code, name) VALUES (?, ?)", (code, details["name"]))
    conn.commit()
    conn.close()

# DB操作: 天気予報保存
def save_weather_to_db(area_code, forecasts):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    fetched_at = datetime.now().isoformat()
    for forecast in forecasts:
        forecast_date = forecast["date"]
        weather = forecast["weathers"][0]
        cur.execute("""
            INSERT INTO weather_forecasts (area_code, forecast_date, weather, fetched_at)
            VALUES (?, ?, ?, ?)
        """, (area_code, forecast_date, weather, fetched_at))
    conn.commit()
    conn.close()

# DB操作: 天気予報取得
def get_weather_from_db(area_code, selected_date=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if selected_date:
        cur.execute("""
            SELECT forecast_date, weather FROM weather_forecasts
            WHERE area_code = ? AND forecast_date = ?
        """, (area_code, selected_date))
    else:
        cur.execute("""
            SELECT forecast_date, weather FROM weather_forecasts
            WHERE area_code = ?
        """, (area_code,))
    rows = cur.fetchall()
    conn.close()
    return rows

def main(page: ft.Page):
    page.title = "天気予報アプリ (改良版)"
    page.scroll = ft.ScrollMode.AUTO

    init_db()  # データベース初期化

    # UI Components
    region_dropdown = ft.Dropdown(
        hint_text="地域を選択してください",
        width=400,
        on_change=lambda e: load_weather_from_db(e.control.value),
    )
    date_picker_label = ft.Text("日付を選択してください", size=16)
    date_picker = ft.DatePicker(
        on_change=lambda e: load_weather_from_db(region_dropdown.value, e.control.value),
    )
    weather_info = ft.Text(value="", width=400)

    # エリア情報を取得
    def fetch_regions():
        try:
            response = requests.get(AREA_LIST_URL)
            response.raise_for_status()
            data = response.json()
            areas = data["offices"]
            save_areas_to_db(areas)  # エリア情報をDBに保存

            # ドロップダウンにエリア情報を追加
            region_dropdown.options.clear()
            for code, details in areas.items():
                region_dropdown.options.append(ft.dropdown.Option(key=code, text=details["name"]))
            page.update()
        except Exception as e:
            weather_info.value = f"地域リストの取得中にエラーが発生しました: {e}"
            page.update()

    # 天気予報を取得して保存
    def fetch_and_save_weather(region_code):
        if not region_code:
            return
        try:
            response = requests.get(FORECAST_URL.format(region_code))
            response.raise_for_status()
            weather_data = response.json()

            # 天気情報をDBに保存
            save_weather_to_db(region_code, weather_data[0]["timeSeries"][0]["areas"])
            load_weather_from_db(region_code)
        except Exception as e:
            weather_info.value = f"天気予報の取得中にエラーが発生しました: {e}"
            page.update()

    # DBから天気予報を読み込む
    def load_weather_from_db(region_code, selected_date=None):
        if not region_code:
            return
        rows = get_weather_from_db(region_code, selected_date)
        if rows:
            weather_info.value = "\n".join(f"{row[0]}: {row[1]}" for row in rows)
        else:
            weather_info.value = "指定されたデータはありません。"
        page.update()

    # レイアウト
    page.add(
        ft.Column([
            ft.Text("気象庁 天気予報アプリ (改良版)", size=24, weight="bold"),
            ft.ElevatedButton("地域リストを読み込む", on_click=lambda _: fetch_regions()),
            region_dropdown,
            ft.ElevatedButton("天気予報を取得", on_click=lambda _: fetch_and_save_weather(region_dropdown.value)),
            date_picker_label,  # 日付選択用のラベル
            date_picker,
            weather_info,
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

ft.app(target=main)
