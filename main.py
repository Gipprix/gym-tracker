import flet as ft
import pandas as pd
import os

def main(page: ft.Page):
    page.title = "D1 Gym Tracker Offline"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "auto"
    page.window_width = 360
    page.window_height = 800

    # --- XỬ LÝ DỮ LIỆU (Giống hệt code cũ) ---
    try:
        # Lưu ý: Khi đóng gói APK, đường dẫn file sẽ khác. 
        # Code này tạm thời chạy trên máy tính.
        df = pd.read_excel('LichTap.xlsx')
        
        # Xử lý merged cells
        if 'Thứ' in df.columns:
            df['Thứ'] = df['Thứ'].ffill()

        # Đổi tên cột
        rename_map = {
            'Bài tập / Drill': 'name',
            'Sets × Reps': 'sets_reps',
            'Nghỉ': 'rest',
            'Tư duy D1 & Mục tiêu': 'notes',
            'Trọng tâm': 'focus',
            'Mô tả cách thực hiện (Action)': 'description'
        }
        # Lọc cột tồn tại
        valid_map = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=valid_map)
        
        # Tách sets/reps
        def split_sets_reps(val):
            val = str(val).lower()
            if '×' in val: parts = val.split('×')
            elif 'x' in val: parts = val.split('x')
            else: return val, "-"
            if len(parts) >= 2: return parts[0].strip(), parts[1].strip()
            return val, "-"

        if 'sets_reps' in df.columns:
            df[['sets', 'reps']] = df['sets_reps'].apply(lambda x: pd.Series(split_sets_reps(x)))
        else:
            df['sets'] = "N/A"; df['reps'] = "N/A"
            
        df = df.fillna("")

    except Exception as e:
        page.add(ft.Text(f"Lỗi đọc file: {e}", color="red"))
        return

    # --- GIAO DIỆN ---
    
    # Biến lưu trạng thái
    current_day = None
    current_exercises = []
    current_idx = 0

    def build_workout_view(e):
        nonlocal current_idx
        page.clean()
        
        if current_idx >= len(current_exercises):
            page.add(
                ft.Column([
                    ft.Icon(ft.icons.CELEBRATION, size=50, color="green"),
                    ft.Text("Hoàn thành buổi tập!", size=24, weight="bold"),
                    ft.ElevatedButton("Về trang chủ", on_click=go_home)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            page.update()
            return

        ex = current_exercises[current_idx]
        
        # Giao diện bài tập
        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK, on_click=go_home),
                    ft.Text(f"Bài {current_idx + 1}/{len(current_exercises)}")
                ]),
                ft.Container(
                    content=ft.Text("🏋️", size=60, text_align="center"),
                    alignment=ft.alignment.center
                ),
                ft.Text(ex.get('name', 'Bài tập'), size=20, weight="bold", text_align="center"),
                
                ft.Row([
                    ft.Column([ft.Text(str(ex.get('sets', '-')), size=20, weight="bold"), ft.Text("SETS")], horizontal_alignment="center"),
                    ft.Column([ft.Text(str(ex.get('reps', '-')), size=20, weight="bold"), ft.Text("REPS")], horizontal_alignment="center"),
                    ft.Column([ft.Text(str(ex.get('rest', '-')), size=20, weight="bold"), ft.Text("NGHỈ")], horizontal_alignment="center"),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                
                ft.Divider(),
                
                # Hướng dẫn
                ft.Container(
                    content=ft.Column([
                        ft.Text("🛠️ Hướng dẫn:", weight="bold"),
                        ft.Text(ex.get('description', 'Không có mô tả'))
                    ]),
                    bgcolor=ft.colors.BLUE_50, padding=10, border_radius=5
                ) if ex.get('description') else ft.Container(),
                
                ft.Container(height=10),
                
                ft.ElevatedButton("Tiếp theo ➡️", on_click=next_exercise, width=300, height=50, bgcolor="blue", color="white")
            ], scroll="auto")
        )
        page.update()

    def next_exercise(e):
        nonlocal current_idx
        current_idx += 1
        build_workout_view(None)

    def start_workout(day):
        nonlocal current_day, current_exercises, current_idx
        current_day = day
        current_idx = 0
        # Lọc bài tập
        data = df[df['Thứ'] == day].reset_index(drop=True)
        current_exercises = data.to_dict('records')
        build_workout_view(None)

    def go_home(e):
        page.clean()
        page.add(ft.Text("📅 Chọn Ngày Tập D1", size=24, weight="bold"))
        
        days = df['Thứ'].unique()
        for day in days:
            focus = df[df['Thứ'] == day]['focus'].iloc[0] if 'focus' in df.columns else ""
            
            # Tạo thẻ ngày tập
            card = ft.Container(
                content=ft.Column([
                    ft.Text(day, size=18, weight="bold"),
                    ft.Text(focus, size=12, color="grey"),
                    ft.ElevatedButton("Bắt đầu", on_click=lambda e, d=day: start_workout(d))
                ]),
                padding=15,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=10,
                margin=5
            )
            page.add(card)
        page.update()

    # Khởi chạy màn hình chính
    go_home(None)

ft.app(target=main)
