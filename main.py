import flet as ft
import pandas as pd
import os

def main(page: ft.Page):
    page.title = "D1 Gym Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "auto"
    page.window_width = 360
    page.window_height = 800

    # --- XỬ LÝ DỮ LIỆU ---
    # Lưu ý: Khi chạy trên điện thoại, file Excel phải nằm cùng thư mục
    # GitHub Actions sẽ copy file này vào đúng chỗ khi build
    try:
        df = pd.read_excel('LichTap.xlsx')
        
        # Xử lý ô gộp (Merged cells)
        if 'Thứ' in df.columns:
            df['Thứ'] = df['Thứ'].ffill()

        # Đổi tên cột cho khớp logic
        rename_map = {
            'Bài tập / Drill': 'name',
            'Sets × Reps': 'sets_reps',
            'Nghỉ': 'rest',
            'Tư duy D1 & Mục tiêu': 'notes',
            'Trọng tâm': 'focus',
            'Mô tả cách thực hiện (Action)': 'description'
        }
        # Chỉ đổi tên những cột có thật
        valid_map = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=valid_map)
        
        # Tách Sets/Reps
        def split_sets_reps(val):
            val = str(val).lower()
            if '×' in val: parts = val.split('×')
            elif 'x' in val: parts = val.split('x')
            else: return val, "-"
            
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
            return val, "-"

        if 'sets_reps' in df.columns:
            df[['sets', 'reps']] = df['sets_reps'].apply(lambda x: pd.Series(split_sets_reps(x)))
        else:
            df['sets'] = "N/A"
            df['reps'] = "N/A"
            
        df = df.fillna("")

    except Exception as e:
        page.add(ft.Text(f"Lỗi đọc dữ liệu: {e}", color="red"))
        return

    # --- UI COMPONENTS ---
    
    def get_stickman():
        return ft.Text("🏋️", size=60, text_align="center")

    # Biến lưu trạng thái
    current_exercises = []
    current_idx = 0

    def build_workout_view():
        page.clean()
        
        if current_idx >= len(current_exercises):
            page.add(
                ft.Column([
                    ft.Icon(ft.icons.CELEBRATION, size=60, color="green"),
                    ft.Text("HOÀN THÀNH!", size=30, weight="bold", color="green"),
                    ft.Text("Bạn đã hoàn thành buổi tập hôm nay.", text_align="center"),
                    ft.Container(height=20),
                    ft.ElevatedButton("Về trang chủ", on_click=lambda e: go_home(), height=50, width=200)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            )
            page.update()
            return

        ex = current_exercises[current_idx]
        
        # Giao diện bài tập
        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: go_home()),
                    ft.Text(f"Bài {current_idx + 1} / {len(current_exercises)}", weight="bold")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(content=get_stickman(), alignment=ft.alignment.center, margin=10),
                
                ft.Text(ex.get('name', 'Bài tập'), size=22, weight="bold", text_align="center"),
                
                ft.Container(height=10),
                
                # Thông số
                ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(str(ex.get('sets', '-')), size=24, weight="bold", color="blue"), ft.Text("SETS", size=10)], horizontal_alignment="center"),
                        ft.Column([ft.Text(str(ex.get('reps', '-')), size=24, weight="bold", color="blue"), ft.Text("REPS", size=10)], horizontal_alignment="center"),
                        ft.Column([ft.Text(str(ex.get('rest', '-')), size=24, weight="bold", color="blue"), ft.Text("NGHỈ", size=10)], horizontal_alignment="center"),
                    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                    padding=10,
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=10
                ),
                
                ft.Divider(),
                
                # Hướng dẫn (Action)
                ft.Text("🛠️ Hướng dẫn:", weight="bold") if ex.get('description') else ft.Container(),
                ft.Container(
                    content=ft.Text(str(ex.get('description', '')), italic=True),
                    bgcolor=ft.colors.GREY_100, padding=10, border_radius=5, width=float('inf')
                ) if ex.get('description') else ft.Container(),
                
                # Tư duy (Notes)
                ft.Container(height=10),
                ft.Text("💡 Tư duy:", weight="bold") if ex.get('notes') else ft.Container(),
                ft.Text(str(ex.get('notes', '')), size=12) if ex.get('notes') else ft.Container(),
                
                ft.Container(height=20),
                
                ft.ElevatedButton("TIẾP THEO ➡️", on_click=lambda e: next_exercise(), width=300, height=50, style=ft.ButtonStyle(bgcolor="blue", color="white"))
            ], scroll="auto", expand=True, padding=10)
        )
        page.update()

    def next_exercise():
        nonlocal current_idx
        current_idx += 1
        build_workout_view()

    def start_workout(day):
        nonlocal current_exercises, current_idx
        current_idx = 0
        # Lọc bài tập
        data = df[df['Thứ'] == day].reset_index(drop=True)
        current_exercises = data.to_dict('records')
        if not current_exercises:
            page.snack_bar = ft.SnackBar(ft.Text("Không có bài tập nào!"))
            page.snack_bar.open = True
            page.update()
            return
        build_workout_view()

    def go_home():
        page.clean()
        page.add(ft.Text("📅 Lịch Tập D1", size=28, weight="bold", text_align="center"))
        
        if 'Thứ' not in df.columns:
            page.add(ft.Text("Lỗi file Excel: Thiếu cột 'Thứ'", color="red"))
            return

        days = df['Thứ'].unique()
        
        lv = ft.ListView(expand=True, spacing=10)
        
        for day in days:
            focus = ""
            if 'focus' in df.columns:
                f_row = df[df['Thứ'] == day]['focus']
                if not f_row.empty: focus = str(f_row.iloc[0])
            
            card = ft.Container(
                content=ft.Column([
                    ft.Text(str(day), size=20, weight="bold"),
                    ft.Text(focus, size=14, color="grey"),
                    ft.ElevatedButton("Bắt đầu tập", on_click=lambda e, d=day: start_workout(d))
                ]),
                padding=20,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=15,
                bgcolor="white",
                on_click=lambda e, d=day: start_workout(d) # Bấm vào thẻ cũng start luôn
            )
            lv.controls.append(card)
            
        page.add(lv)
        page.update()

    # Khởi chạy
    go_home()

ft.app(target=main)
