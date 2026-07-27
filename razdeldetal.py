import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from tkcalendar import Calendar
import ezdxf
from ezdxf.enums import TextEntityAlignment
import datetime
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# Настройка внешнего вида интерфейса
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

LINE_TYPES_RU = {"Сплошная": "CONTINUOUS", "Штриховая": "DASHED", "Штрихпунктирная": "DASHDOT", "Пунктирная": "DIVIDE"}
PATTERNS_RU = {"Сплошная (SOLID)": "SOLID", "Линии (ANSI31)": "ANSI31", "Кирпич (ANSI33)": "ANSI33", "Сетка (NET)": "NET", "Крестики (CROSS)": "CROSS", "Сетка диаг. (ANSI37)": "ANSI37", "Соты (HONEY)": "HONEY"}
MPL_LTYPES = {"Сплошная": "-", "Штриховая": "--", "Штрихпунктирная": "-.", "Пунктирная": ":"}

def clean_date_str(date_val):
    if pd.isna(date_val): return ""
    if isinstance(date_val, (datetime.datetime, pd.Timestamp)):
        return date_val.strftime("%d.%m.%Y")
    s = str(date_val).strip()
    if " " in s: s = s.split(" ")[0]
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return s[:10]

class StreamRow(ctk.CTkFrame):
    def __init__(self, master, delete_callback, update_preview_callback, default_data=None, **kwargs):
        super().__init__(master, **kwargs)
        self.update_callback = update_preview_callback
        
        self.name_entry = ctk.CTkEntry(self, width=150, placeholder_text="Название работы")
        self.name_entry.grid(row=0, column=0, padx=5, pady=5)
        
        self.start_var = ctk.StringVar()
        self.end_var = ctk.StringVar()
        self.start_var.trace_add("write", self.validate_dates)
        self.end_var.trace_add("write", self.validate_dates)
        
        self.start_entry = ctk.CTkEntry(self, width=85, textvariable=self.start_var, placeholder_text="ДД.ММ.ГГГГ")
        self.start_entry.grid(row=0, column=1, padx=(5,0), pady=5)
        ctk.CTkButton(self, text="📅", width=30, command=lambda: self.open_calendar(self.start_var)).grid(row=0, column=2, padx=(0,5))
        
        self.end_entry = ctk.CTkEntry(self, width=85, textvariable=self.end_var, placeholder_text="ДД.ММ.ГГГГ")
        self.end_entry.grid(row=0, column=3, padx=(5,0), pady=5)
        ctk.CTkButton(self, text="📅", width=30, command=lambda: self.open_calendar(self.end_var)).grid(row=0, column=4, padx=(0,5))
        
        self.w_entry = ctk.CTkEntry(self, width=50, placeholder_text="Чел.")
        self.w_entry.grid(row=0, column=5, padx=5, pady=5)
        
        self.v_entry = ctk.CTkEntry(self, width=50, placeholder_text="Шт.")
        self.v_entry.grid(row=0, column=6, padx=5, pady=5)
        
        self.color_var = ctk.StringVar(value="Желтый")
        self.color_menu = ctk.CTkOptionMenu(self, values=["Красный", "Желтый", "Зеленый", "Голубой", "Синий", "Фиолетовый", "Оранжевый", "Серый", "Темно-серый"], variable=self.color_var, width=110)
        self.color_menu.grid(row=0, column=7, padx=5, pady=5)

        self.ltype_var = ctk.StringVar(value="Сплошная")
        self.ltype_menu = ctk.CTkOptionMenu(self, values=list(LINE_TYPES_RU.keys()), variable=self.ltype_var, width=130)
        self.ltype_menu.grid(row=0, column=8, padx=5, pady=5)

        self.pattern_var = ctk.StringVar(value="Сплошная (SOLID)")
        self.pattern_menu = ctk.CTkOptionMenu(self, values=list(PATTERNS_RU.keys()), variable=self.pattern_var, width=130)
        self.pattern_menu.grid(row=0, column=9, padx=5, pady=5)
        
        self.del_btn = ctk.CTkButton(self, text="X", width=30, fg_color="#ff4a4a", hover_color="#cc0000", command=lambda: delete_callback(self))
        self.del_btn.grid(row=0, column=10, padx=5, pady=5)

        if default_data:
            self.name_entry.insert(0, default_data["name"])
            self.start_var.set(clean_date_str(default_data["start"]))
            self.end_var.set(clean_date_str(default_data["end"]))
            self.w_entry.insert(0, str(default_data["w"]))
            self.v_entry.insert(0, str(default_data["v"]))
            self.color_var.set(default_data["c_name"])
            self.ltype_var.set(default_data["ltype"])
            self.pattern_var.set(default_data["pattern"])

    def validate_dates(self, *args):
        try:
            s_date = datetime.datetime.strptime(self.start_var.get().strip()[:10], "%d.%m.%Y")
            e_date = datetime.datetime.strptime(self.end_var.get().strip()[:10], "%d.%m.%Y")
            if e_date < s_date:
                self.end_entry.configure(text_color="red")
            else:
                self.end_entry.configure(text_color=["black", "white"])
        except ValueError:
            pass

    def open_calendar(self, target_var):
        top = ctk.CTkToplevel(self)
        top.title("Выберите дату")
        top.geometry("250x250")
        top.attributes('-topmost', True)
        cal = Calendar(top, selectmode='day', date_pattern='dd.mm.yyyy')
        cal.pack(padx=10, pady=10)
        def set_date():
            target_var.set(cal.get_date())
            top.destroy()
        ctk.CTkButton(top, text="Применить", command=set_date).pack(pady=5)

class LKGGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LKG AutoGen Ultimate")
        self.geometry("1300x800")
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_editor = self.tabview.add("Редактор Данных")
        self.tab_preview = self.tabview.add("Предпросмотр & PDF")

        self.setup_editor_tab()
        self.setup_preview_tab()
        self.load_default_data()

    def setup_editor_tab(self):
        self.param_frame = ctk.CTkFrame(self.tab_editor)
        self.param_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.param_frame, text="Длина (км):").grid(row=0, column=0, padx=5, pady=5)
        self.length_entry = ctk.CTkEntry(self.param_frame, width=70)
        self.length_entry.insert(0, "7.192")
        self.length_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(self.param_frame, text="Старт проекта:").grid(row=0, column=2, padx=5, pady=5)
        self.global_start_entry = ctk.CTkEntry(self.param_frame, width=100)
        self.global_start_entry.insert(0, "05.04.2026")
        self.global_start_entry.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(self.param_frame, text="Материалы:").grid(row=0, column=4, padx=5, pady=5)
        self.mat_entry = ctk.CTkEntry(self.param_frame, width=500)
        self.mat_entry.insert(0, "ПГС - 7 990 м³   Щебень - 5 115 м³   А/б нижн. - 1 765 т   А/б верхн. - 1 281 т   Обочины - 669 м³")
        self.mat_entry.grid(row=0, column=5, padx=5, pady=5)
        
        self.headers_frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        self.headers_frame.pack(fill="x", padx=15, pady=(10, 0))
        headers =[("Название", 150), ("Начало", 120), ("Окончание", 120), ("Рабочие", 50), ("Машины", 50), ("Цвет", 110), ("Тип линии", 130), ("Штриховка", 130)]
        for i, (text, width) in enumerate(headers):
            ctk.CTkLabel(self.headers_frame, text=text, width=width, anchor="w", font=("Arial", 12, "bold")).grid(row=0, column=i, padx=5)

        self.streams_frame = ctk.CTkScrollableFrame(self.tab_editor)
        self.streams_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.stream_rows =[]
        
        self.btn_frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.btn_frame, text="+ Добавить", command=lambda: self.add_stream_row()).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="📥 Импорт Excel", fg_color="#17a2b8", command=self.import_excel).pack(side="left", padx=20)
        ctk.CTkButton(self.btn_frame, text="📤 Экспорт Excel", fg_color="#ffc107", text_color="black", command=self.export_excel).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="Сгенерировать DXF", font=("Arial", 14, "bold"), fg_color="#28a745", command=self.generate_dxf).pack(side="right", padx=5)

    def setup_preview_tab(self):
        btn_frame = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="🔄 Обновить Предпросмотр", command=self.update_preview).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📄 Сохранить график в PDF", fg_color="#dc3545", command=self.export_pdf).pack(side="right", padx=10)

        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.fig.patch.set_facecolor('#2b2b2b') 
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_preview)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def get_date_str(self, start_date, offset_days):
        return (start_date + datetime.timedelta(days=offset_days)).strftime("%d.%m.%Y")

    def load_default_data(self):
        base = datetime.datetime.strptime("05.04.2026", "%d.%m.%Y")
        ds = lambda offset: self.get_date_str(base, offset)
        defaults =[
            {"name": "Подгот. период", "start": ds(0), "end": ds(30), "w": 5, "v": 0, "c_name": "Серый", "ltype": "Сплошная", "pattern": "Сплошная (SOLID)"},
            {"name": "Земляное полотно", "start": ds(31), "end": ds(45), "w": 3, "v": 3, "c_name": "Темно-серый", "ltype": "Сплошная", "pattern": "Линии (ANSI31)"}, 
            {"name": "Основание ПГС", "start": ds(33), "end": ds(47), "w": 14, "v": 120, "c_name": "Фиолетовый", "ltype": "Штриховая", "pattern": "Сетка (NET)"}, 
            {"name": "Основание Щебень", "start": ds(35), "end": ds(49), "w": 8, "v": 69, "c_name": "Синий", "ltype": "Штрихпунктирная", "pattern": "Кирпич (ANSI33)"}, 
            {"name": "Подготовка к а/б", "start": ds(37), "end": ds(51), "w": 2, "v": 2, "c_name": "Голубой", "ltype": "Сплошная", "pattern": "Сплошная (SOLID)"}, 
            {"name": "А/б нижний слой", "start": ds(39), "end": ds(53), "w": 13, "v": 23, "c_name": "Зеленый", "ltype": "Штриховая", "pattern": "Крестики (CROSS)"}, 
            {"name": "А/б верхний слой", "start": ds(41), "end": ds(55), "w": 14, "v": 19, "c_name": "Красный", "ltype": "Пунктирная", "pattern": "Сетка диаг. (ANSI37)"}, 
            {"name": "Обочины (щебень)", "start": ds(43), "end": ds(57), "w": 2, "v": 11, "c_name": "Голубой", "ltype": "Штрихпунктирная", "pattern": "Соты (HONEY)"}, 
            {"name": "Обустройство", "start": ds(58), "end": ds(88), "w": 6, "v": 0, "c_name": "Желтый", "ltype": "Сплошная", "pattern": "Сплошная (SOLID)"}
        ]
        for data in defaults:
            self.add_stream_row(data)
        self.update_preview()

    def add_stream_row(self, default_data=None):
        row = StreamRow(self.streams_frame, self.delete_stream_row, self.update_preview, default_data)
        row.pack(fill="x", pady=2)
        self.stream_rows.append(row)

    def delete_stream_row(self, row):
        row.pack_forget()
        row.destroy()
        self.stream_rows.remove(row)

    def export_excel(self):
        try:
            data =[{"Работа": r.name_entry.get(), "Начало": r.start_var.get(), "Конец": r.end_var.get(), "Рабочие": r.w_entry.get(), "Машины": r.v_entry.get(), "Цвет": r.color_var.get(), "Тип линии": r.ltype_var.get(), "Штриховка": r.pattern_var.get()} for r in self.stream_rows]
            pd.DataFrame(data).to_excel(filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")]), index=False)
        except Exception: pass

    def import_excel(self):
        try:
            filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
            if not filepath: return
            df = pd.read_excel(filepath)
            for r in self.stream_rows: r.pack_forget(); r.destroy()
            self.stream_rows.clear()
            for _, row in df.iterrows():
                self.add_stream_row({"name": str(row["Работа"]), "start": clean_date_str(row["Начало"]), "end": clean_date_str(row["Конец"]), "w": str(row["Рабочие"]), "v": str(row["Машины"]), "c_name": str(row["Цвет"]), "ltype": str(row["Тип линии"]), "pattern": str(row["Штриховка"])})
            self.update_preview()
            messagebox.showinfo("Успех", "Данные загружены из Excel!")
        except Exception as e: messagebox.showerror("Ошибка", f"Ошибка импорта: {e}")

    def update_preview(self):
        self.ax.clear()
        try: length_km = float(self.length_entry.get().replace(',', '.'))
        except: return

        color_map = {"Красный": "#ff4a4a", "Желтый": "#ffc107", "Зеленый": "#28a745", "Голубой": "#17a2b8", "Синий": "#007bff", "Фиолетовый": "#6f42c1", "Оранжевый": "#fd7e14", "Серый": "#adb5bd", "Темно-серый": "#6c757d"}
        has_data = False
        
        for r in self.stream_rows:
            name = r.name_entry.get()
            if not name: continue
            try:
                s_date = datetime.datetime.strptime(r.start_var.get().strip()[:10], "%d.%m.%Y")
                e_date = datetime.datetime.strptime(r.end_var.get().strip()[:10], "%d.%m.%Y")
                hex_color = color_map.get(r.color_var.get(), "#ffffff")
                ls = MPL_LTYPES.get(r.ltype_var.get(), "-")
                if "Подгот" in name or "Обустройство" in name:
                    self.ax.fill_between([0, length_km], [s_date, s_date], [e_date, e_date], color=hex_color, alpha=0.3, label=name)
                else:
                    self.ax.plot([0, length_km], [s_date, e_date], color=hex_color, linewidth=2.5, linestyle=ls, label=name)
                has_data = True
            except: continue

        if not has_data: return

        self.ax.set_xlim(0, length_km)
        self.ax.xaxis.set_major_formatter('{x:.1f} км')
        self.ax.yaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        self.ax.set_title("Схема линейного календарного графика", color='white', pad=10)
        self.ax.grid(True, linestyle='--', color='gray', alpha=0.4)

        self.fig.subplots_adjust(left=0.08, right=0.70, top=0.9, bottom=0.1)
        self.ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
        self.canvas.draw()

    def export_pdf(self):
        self.update_preview()
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if filepath:
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.tick_params(colors='black')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.set_title("Схема линейного календарного графика", color='black', pad=10)
            self.ax.grid(True, linestyle='--', color='gray', alpha=0.5)

            legend = self.ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor('white')
                legend.get_frame().set_edgecolor('black')
                for text in legend.get_texts(): text.set_color('black')

            self.fig.savefig(filepath, format='pdf', bbox_inches='tight')
            self.update_preview()
            messagebox.showinfo("Успех", "График сохранен в PDF!")

    def get_color_index(self, color_name):
        colors = {"Красный": 1, "Желтый": 2, "Зеленый": 3, "Голубой": 4, "Синий": 5, "Фиолетовый": 6, "Оранжевый": 30, "Серый": 8, "Темно-серый": 32}
        return colors.get(color_name, 7)

    def generate_dxf(self):
        try:
            length_km = float(self.length_entry.get().replace(',', '.'))
            global_start = datetime.datetime.strptime(clean_date_str(self.global_start_entry.get()), "%d.%m.%Y")
            mat_text = self.mat_entry.get()
            
            streams =[]
            max_end_idx = 0 
            for row in self.stream_rows:
                name = row.name_entry.get()
                if not name: continue
                s_date = datetime.datetime.strptime(row.start_var.get().strip()[:10], "%d.%m.%Y")
                e_date = datetime.datetime.strptime(row.end_var.get().strip()[:10], "%d.%m.%Y")
                start_idx = (s_date - global_start).days
                end_idx = (e_date - global_start).days
                if start_idx < 0 or end_idx < start_idx: raise ValueError(f"Ошибки в датах: {name}")
                max_end_idx = max(max_end_idx, end_idx)
                streams.append({"name": name, "start": start_idx, "end": end_idx, "w": int(row.w_entry.get()), "v": int(row.v_entry.get()), "color": self.get_color_index(row.color_var.get()), "ltype": LINE_TYPES_RU[row.ltype_var.get()], "pattern": PATTERNS_RU[row.pattern_var.get()]})
            
            filepath = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("AutoCAD DXF", "*.dxf")])
            if not filepath: return
            self.create_dxf_file(filepath, length_km, max_end_idx + 1, global_start, mat_text, streams)
            messagebox.showinfo("Успех!", f"Чертеж сгенерирован!\nФайл: {filepath}")
        except Exception as e: messagebox.showerror("Ошибка", f"Проверьте данные.\n{e}")

    def create_dxf_file(self, filepath, LEN_KM, TOTAL_DAYS, global_start, mat_text, streams):
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Обычный прямой текст Arial, никаких курсивов, никаких глюков в AutoCAD
        doc.styles.add('style1', font='arial.ttf')

        def add_dxf_text(text, x, y, height=3.5, color=7, align=TextEntityAlignment.LEFT, rotation=0):
            msp.add_text(str(text), dxfattribs={'style': 'style1', 'height': float(height), 'color': int(color), 'rotation': float(rotation)}).set_placement((float(x), float(y)), align=align)

        # Типы линий загружаем с увеличенным масштабом, чтобы на длинных отрезках они смотрелись лучше
        doc.linetypes.add("DASHED", pattern=[10.0, 5.0, -5.0])
        doc.linetypes.add("DASHDOT", pattern=[16.0, 10.0, -2.0, 2.0, -2.0])
        doc.linetypes.add("DIVIDE", pattern=[29.0, 10.0, -5.0, 2.0, -5.0, 2.0, -5.0])

        SCALE_X, SCALE_Y = 70.0, 4.0
        TOTAL_X, TOTAL_Y = LEN_KM * SCALE_X, TOTAL_DAYS * SCALE_Y
        SCALE_WORKERS, SCALE_VEHICLES = 1.0, 0.5  
        X_DATES, X_MONTHS, X_WORKERS_START = -25, -45, -60 

        month_names_ru = {1:"ЯНВАРЬ", 2:"ФЕВРАЛЬ", 3:"МАРТ", 4:"АПРЕЛЬ", 5:"МАЙ", 6:"ИЮНЬ", 7:"ИЮЛЬ", 8:"АВГУСТ", 9:"СЕНТЯБРЬ", 10:"ОКТЯБРЬ", 11:"НОЯБРЬ", 12:"ДЕКАБРЬ"}
        months_dict = {}
        for day in range(TOTAL_DAYS):
            current = global_start + datetime.timedelta(days=day)
            m_name = month_names_ru[current.month]
            if m_name not in months_dict: months_dict[m_name] = [day, day]
            else: months_dict[m_name][1] = day
        months = [(k, v[0], v[1]+1) for k, v in months_dict.items()]

        def add_bar(x1, x2, y1, y2, color, pattern):
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={'color': 7})
            h = msp.add_hatch(color=color)
            if pattern == "SOLID": h.set_solid_fill(color=color)
            else: h.set_pattern_fill(pattern, color=color, scale=0.4)
            h.paths.add_polyline_path(pts, is_closed=True)

        msp.add_line((0, 0), (0, TOTAL_Y), dxfattribs={'color': 7})
        msp.add_line((X_DATES, 0), (X_DATES, TOTAL_Y), dxfattribs={'color': 7})
        msp.add_line((X_MONTHS, 0), (X_MONTHS, TOTAL_Y), dxfattribs={'color': 7})

        for m_name, d_start, d_end in months:
            y_s, y_e = d_start * SCALE_Y, d_end * SCALE_Y
            msp.add_line((X_MONTHS, y_s), (TOTAL_X, y_s), dxfattribs={'color': 7})
            add_dxf_text(m_name, X_MONTHS + 10, y_s + (y_e - y_s)/2, height=5, align=TextEntityAlignment.MIDDLE_CENTER, rotation=90)

        unique_days = sorted(list(set([s["start"] for s in streams] + [s["end"] for s in streams])))
        for d in unique_days:
            if d > TOTAL_DAYS: continue
            y = d * SCALE_Y
            date_str = (global_start + datetime.timedelta(days=d)).strftime("%d.%m")
            add_dxf_text(date_str, X_DATES + 20, y + 1, height=2.5, align=TextEntityAlignment.BOTTOM_RIGHT)
            msp.add_line((X_DATES, y), (TOTAL_X, y), dxfattribs={'color': 8, 'linetype': 'DASHED'})

        for km in range(int(LEN_KM) + 1):
            x = km * SCALE_X
            msp.add_line((x, 0), (x, TOTAL_Y), dxfattribs={'color': 8})
            msp.add_line((x, 0), (x, -3), dxfattribs={'color': 7})
            add_dxf_text(str(km), x, -7, height=3.5, align=TextEntityAlignment.MIDDLE_CENTER)

        msp.add_line((TOTAL_X, 0), (TOTAL_X, TOTAL_Y), dxfattribs={'color': 7})
        msp.add_line((TOTAL_X, 0), (TOTAL_X, -3), dxfattribs={'color': 7})
        add_dxf_text(f"{LEN_KM:.2f}", TOTAL_X, -7, height=3.5, align=TextEntityAlignment.MIDDLE_CENTER)

        for s in streams:
            y1, y2 = s["start"] * SCALE_Y, s["end"] * SCALE_Y
            if "Подгот" in s["name"] or "Обустройство" in s["name"]: 
                msp.add_line((0, y1), (0, y2), dxfattribs={'color': s["color"], 'linetype': s["ltype"]})
                msp.add_line((TOTAL_X, y1), (TOTAL_X, y2), dxfattribs={'color': s["color"], 'linetype': s["ltype"]})
                msp.add_line((0, y1), (TOTAL_X, y2), dxfattribs={'color': s["color"], 'linetype': s["ltype"]})
            else:
                msp.add_line((0, y1), (TOTAL_X, y2), dxfattribs={'color': s["color"], 'linetype': s["ltype"]})

        w_totals, v_totals = [0] * TOTAL_DAYS, [0] * TOTAL_DAYS
        for day in range(TOTAL_DAYS):
            y_base, y_top = day * SCALE_Y, day * SCALE_Y + SCALE_Y
            x_w, x_v = X_WORKERS_START, TOTAL_X
            c_w, c_v = 0, 0
            for s in streams:
                if s["start"] <= day < s["end"]:
                    c_w += s["w"]
                    c_v += s["v"]
                    if s["w"] > 0:
                        dx_w = s["w"] * SCALE_WORKERS
                        add_bar(x_w - dx_w, x_w, y_base, y_top, s["color"], s["pattern"])
                        x_w -= dx_w
                    if s["v"] > 0:
                        dx_v = s["v"] * SCALE_VEHICLES
                        add_bar(x_v, x_v + dx_v, y_base, y_top, s["color"], s["pattern"])
                        x_v += dx_v
            w_totals[day], v_totals[day] = c_w, c_v

        def draw_smart_labels(totals, is_left):
            start = 0
            while start < TOTAL_DAYS:
                val = totals[start]
                if val == 0:
                    start += 1; continue
                end = start
                while end < TOTAL_DAYS and totals[end] == val: end += 1
                y_c = (start + end - 1) / 2 * SCALE_Y + (SCALE_Y / 2)
                if is_left: add_dxf_text(str(val), X_WORKERS_START - (val * SCALE_WORKERS) - 4, y_c, height=3.5, align=TextEntityAlignment.MIDDLE_RIGHT)
                else: add_dxf_text(str(val), TOTAL_X + (val * SCALE_VEHICLES) + 4, y_c, height=3.5, align=TextEntityAlignment.MIDDLE_LEFT)
                start = end

        draw_smart_labels(w_totals, is_left=True)
        draw_smart_labels(v_totals, is_left=False)

        Y_SCALES = -15
        max_w = max(w_totals) if w_totals else 10
        max_w_scale = math.ceil(max_w / 10) * 10
        msp.add_line((X_WORKERS_START, Y_SCALES), (X_WORKERS_START - (max_w_scale*SCALE_WORKERS) - 5, Y_SCALES), dxfattribs={'color': 7})
        for w in range(0, max_w_scale + 1, 10):
            xx = X_WORKERS_START - (w * SCALE_WORKERS)
            msp.add_line((xx, Y_SCALES), (xx, Y_SCALES - 2), dxfattribs={'color': 7})
            add_dxf_text(str(w), xx, Y_SCALES - 5, height=2.5, align=TextEntityAlignment.MIDDLE_CENTER)

        max_v = max(v_totals) if v_totals else 20
        max_v_scale = math.ceil(max_v / 20) * 20
        scale_length = max_v_scale * SCALE_VEHICLES + 5
        msp.add_line((TOTAL_X, Y_SCALES), (TOTAL_X + scale_length, Y_SCALES), dxfattribs={'color': 7})
        for v in range(0, max_v_scale + 1, 20):
            xx = TOTAL_X + (v * SCALE_VEHICLES)
            msp.add_line((xx, Y_SCALES), (xx, Y_SCALES - 2), dxfattribs={'color': 7})
            add_dxf_text(str(v), xx, Y_SCALES - 5, height=2.5, align=TextEntityAlignment.MIDDLE_CENTER)

        Y_TAB1, Y_TAB2, Y_TAB3 = -25, -40, -55
        msp.add_line((X_MONTHS, Y_TAB1), (TOTAL_X, Y_TAB1), dxfattribs={'color': 7})
        msp.add_line((X_MONTHS, Y_TAB2), (TOTAL_X, Y_TAB2), dxfattribs={'color': 7})
        msp.add_line((X_MONTHS, Y_TAB3), (TOTAL_X, Y_TAB3), dxfattribs={'color': 7})
        msp.add_line((X_MONTHS, Y_TAB1), (X_MONTHS, Y_TAB3), dxfattribs={'color': 7})
        msp.add_line((0, Y_TAB1), (0, Y_TAB3), dxfattribs={'color': 7})
        msp.add_line((TOTAL_X, Y_TAB1), (TOTAL_X, Y_TAB3), dxfattribs={'color': 7})

        add_dxf_text("Схематический", X_MONTHS + 22.5, Y_TAB1 - 6, height=3.0, align=TextEntityAlignment.MIDDLE_CENTER)
        add_dxf_text("план трассы", X_MONTHS + 22.5, Y_TAB1 - 11, height=3.0, align=TextEntityAlignment.MIDDLE_CENTER)
        add_dxf_text("Расход материалов", X_MONTHS + 22.5, Y_TAB2 - 6, height=3.0, align=TextEntityAlignment.MIDDLE_CENTER)
        add_dxf_text("на 1 км", X_MONTHS + 22.5, Y_TAB2 - 11, height=3.0, align=TextEntityAlignment.MIDDLE_CENTER)
        add_dxf_text(mat_text, TOTAL_X / 2, Y_TAB2 - 7.5, height=3.5, align=TextEntityAlignment.MIDDLE_CENTER)

        ROUTE_Y = Y_TAB1 - 7.5 
        msp.add_line((0, ROUTE_Y), (TOTAL_X, ROUTE_Y), dxfattribs={'color': 7, 'linetype': 'DASHDOT'})
        for km in range(int(LEN_KM) + 1):
            x = km * SCALE_X
            msp.add_line((x, ROUTE_Y - 2), (x, ROUTE_Y + 2), dxfattribs={'color': 7})
            add_dxf_text(f"ПК {km}0", x, ROUTE_Y + 3, height=2.5, align=TextEntityAlignment.BOTTOM_CENTER)
        
        msp.add_line((TOTAL_X, ROUTE_Y - 2), (TOTAL_X, ROUTE_Y + 2), dxfattribs={'color': 7})
        frac_km = int((LEN_KM - int(LEN_KM)) * 100)
        add_dxf_text(f"ПК {int(LEN_KM)}+{frac_km:02d}", TOTAL_X, ROUTE_Y + 3, height=2.5, align=TextEntityAlignment.BOTTOM_CENTER)

        # ================= ЛЕГЕНДЫ СТРОГО ВНИЗУ В 3 БЛОКА =================
        LEG_Y = Y_TAB3 - 25
        
        # 1. СЛЕВА (Эпюра рабочих)
        # Выравниваем по линии X_MONTHS (-45), чтобы всё было аккуратно
        left_x = X_MONTHS
        add_dxf_text("Эпюра потребности в рабочих:", left_x, LEG_Y, height=4.5)
        streams_w = [s for s in streams if s["w"] > 0]
        for i, s in enumerate(streams_w):
            col, row = i % 2, i // 2
            x_pos = left_x + col * 75
            y_pos = LEG_Y - 8 - (row * 9)
            add_bar(x_pos, x_pos + 8, y_pos - 2.5, y_pos + 2.5, s["color"], s["pattern"])
            add_dxf_text(f"- {s['name'][:18]}", x_pos + 12, y_pos - 1.5, height=3.5)

        # 2. ЦЕНТР (Условные обозначения линий)
        # Защита от наложений: вычисляем центр, но сдвигаем если мешает левому блоку
        mid_x = TOTAL_X / 2 - 120
        if mid_x < left_x + 160: mid_x = left_x + 160
        add_dxf_text("Условные обозначения линий графиков:", mid_x, LEG_Y, height=4.5)
        for i, s in enumerate(streams):
            col, row = i % 2, i // 2
            x_pos = mid_x + col * 120 # Расширил до 120 чтобы текст не наезжал на длинные линии
            y_pos = LEG_Y - 8 - (row * 9)
            # УДЛИНЕННАЯ ЛИНИЯ (40 единиц), чтобы четко видеть штрихпунктиры
            msp.add_line((x_pos, y_pos), (x_pos + 40, y_pos), dxfattribs={'color': s["color"], 'linetype': s["ltype"]})
            add_dxf_text(f"- {s['name'][:18]}", x_pos + 45, y_pos - 1.5, height=3.5)

        # 3. СПРАВА (Эпюра машин)
        # Защита от наложений: сдвигаем вправо, но проверяем, чтобы не налезло на центр
        right_x = TOTAL_X - 160
        if right_x < mid_x + 250: right_x = mid_x + 250
        add_dxf_text("Эпюра потребности в машинах:", right_x, LEG_Y, height=4.5)
        streams_v = [s for s in streams if s["v"] > 0]
        for i, s in enumerate(streams_v):
            col, row = i % 2, i // 2
            x_pos = right_x + col * 75
            y_pos = LEG_Y - 8 - (row * 9)
            add_bar(x_pos, x_pos + 8, y_pos - 2.5, y_pos + 2.5, s["color"], s["pattern"])
            add_dxf_text(f"- {s['name'][:18]}", x_pos + 12, y_pos - 1.5, height=3.5)

        doc.saveas(filepath)

if __name__ == "__main__":
    app = LKGGeneratorApp()
    app.mainloop()
