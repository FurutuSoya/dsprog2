import flet as ft
import requests
import json

AREA_LIST_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO

    # UI Components
    region_dropdown = ft.Dropdown(
        hint_text="地域を選択してください",
        width=400,
        on_change=lambda e: fetch_weather(e.control.value),
    )
    weather_info = ft.Text(value="", width=400)

    # Fetch and populate region dropdown
    def fetch_regions():
        try:
            response = requests.get(AREA_LIST_URL)
            response.raise_for_status()
            data = response.json()
            areas = data["offices"]
            for code, details in areas.items():
                region_dropdown.options.append(ft.dropdown.Option(key=code, text=details["name"]))
            page.update()
        except Exception as e:
            weather_info.value = f"地域リストの取得中にエラーが発生しました: {e}"
            page.update()

    # Fetch weather information for selected region
    def fetch_weather(region_code):
        if not region_code:
            return
        try:
            response = requests.get(FORECAST_URL.format(region_code))
            response.raise_for_status()
            weather_data = response.json()

            # Format weather information for display
            forecast_text = "天気予報:\n"
            for forecast in weather_data[0]["timeSeries"][0]["areas"]:
                forecast_text += f"{forecast['date']}: {forecast['weathers'][0]}\n"
            weather_info.value = forecast_text
        except Exception as e:
            weather_info.value = f"天気予報の取得中にエラーが発生しました: {e}"
        page.update()

    # Layout
    page.add(
        ft.Column([
            ft.Text("気象庁 天気予報アプリ", size=24, weight="bold"),
            region_dropdown,
            ft.ElevatedButton(text="地域リストを読み込む", on_click=lambda _: fetch_regions()),
            weather_info,
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

ft.app(target=main)
