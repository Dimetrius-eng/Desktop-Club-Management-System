import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager
from datetime import datetime
import re
import tkinter.font as tkfont


class ResponsiveWindowMixin:
    def init_responsive_ui(self, base_width, base_height):
        self.base_width = base_width
        self.base_height = base_height
        self._base_font_sizes = {}
        self._responsive_fonts = {}
        self._tree_base_widths = {}
        self._responsive_style = ttk.Style(self.root)
        self._last_scale = None
        self._responsive_after_id = None
        self._responsive_force_refresh = True
        self._responsive_updating = False
        self.root.bind('<Configure>', self.queue_responsive_update)
        self.root.after(100, self.apply_responsive_scale)

    def queue_responsive_update(self, event=None):
        if getattr(self, '_responsive_updating', False):
            return

        if event is not None and event.widget != self.root:
            return

        self._responsive_force_refresh = True

        if self._responsive_after_id:
            self.root.after_cancel(self._responsive_after_id)

        self._responsive_after_id = self.root.after(60, self.apply_responsive_scale)

    def get_responsive_scale(self):
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        width_scale = width / self.base_width
        height_scale = height / self.base_height
        return max(0.85, min(1.35, min(width_scale, height_scale)))

    def apply_responsive_scale(self):
        self._responsive_after_id = None
        scale = round(self.get_responsive_scale(), 2)

        if scale == self._last_scale and not self._responsive_force_refresh:
            return

        self._last_scale = scale
        self._responsive_force_refresh = False
        self._responsive_updating = True

        try:
            self.update_ttk_responsive_style(scale)
            self.update_widget_fonts(self.root, scale)
            self.update_treeviews(self.root, scale)
        finally:
            self._responsive_updating = False

    def update_ttk_responsive_style(self, scale):
        base_font = max(9, int(round(10 * scale)))
        heading_font = max(9, int(round(11 * scale)))
        tab_font = max(9, int(round(10 * scale)))
        row_height = max(22, int(round(24 * scale)))

        self._responsive_style.configure('Treeview', font=('Arial', base_font), rowheight=row_height)
        self._responsive_style.configure('Treeview.Heading', font=('Arial', heading_font, 'bold'))
        self._responsive_style.configure('TNotebook.Tab', font=('Arial', tab_font))
        self._responsive_style.configure('TCombobox', font=('Arial', base_font))

    def update_widget_fonts(self, widget, scale):
        try:
            current_font = widget.cget('font')
            widget_id = str(widget)

            if widget_id not in self._base_font_sizes:
                original_font = tkfont.Font(root=self.root, font=current_font)
                self._base_font_sizes[widget_id] = max(8, abs(int(original_font.cget('size'))))
                self._responsive_fonts[widget_id] = tkfont.Font(root=self.root, font=current_font)
                widget.configure(font=self._responsive_fonts[widget_id])

            new_size = max(8, int(round(self._base_font_sizes[widget_id] * scale)))
            self._responsive_fonts[widget_id].configure(size=new_size)
        except (tk.TclError, ValueError):
            pass

        for child in widget.winfo_children():
            self.update_widget_fonts(child, scale)

    def update_treeviews(self, widget, scale):
        if isinstance(widget, ttk.Treeview):
            widget_id = str(widget)
            columns = widget['columns']

            if widget_id not in self._tree_base_widths:
                self._tree_base_widths[widget_id] = {}
                for col in columns:
                    self._tree_base_widths[widget_id][col] = int(widget.column(col, 'width'))

            for col, base_width in self._tree_base_widths[widget_id].items():
                scaled_width = max(40, int(round(base_width * scale)))
                widget.column(col, width=scaled_width, minwidth=max(30, int(round(scaled_width * 0.6))), stretch=True)

        for child in widget.winfo_children():
            self.update_treeviews(child, scale)

class MainWindow(ResponsiveWindowMixin):
    def __init__(self, root, db, role, username, full_name=""):
        self.root = root
        self.db = db
        self.role = role
        self.username = username
        self.full_name = full_name  # Зберігаємо ПІБ у класі (раптом знадобиться десь ще)

        # 1. Словник для гарного перекладу ролей
        role_display_names = {
            'Admin': 'Адміністратор',
            'Manager': 'Менеджер',
            'Trainer': 'Тренер',
            'Client': 'Клієнт'
        }
        # Дістаємо українську назву ролі (якщо раптом ролі немає в словнику, виведе оригінал)
        display_role = role_display_names.get(self.role, self.role)

        # 2. Ставимо РОЛЬ у заголовок вікна
        self.root.title(f"Інформаційна система - Спортивні секції міста | {display_role}")
        self.root.geometry("850x550")

        # --- ВЕРХНЯ ПАНЕЛЬ (HEADER) ---
        header_frame = tk.Frame(self.root, bg="#2b2b2b", height=40)
        header_frame.pack(fill='x', side='top')

        # 3. Залишаємо ІМ'Я у привітанні
        tk.Label(header_frame, text=f"👤 {self.full_name}", font=("Arial", 12, "bold"), bg="#2b2b2b",
                 fg="white").pack(
            side="left", padx=15)

        # Наша кнопка виходу
        tk.Button(header_frame, text="🚪 Вийти", bg="#f44336", fg="white", relief="flat", borderwidth=0, cursor="hand2",
                  command=self.logout).pack(side='right', padx=15, pady=5)
        # ------------------------------

        self.root.resizable(True, True)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.setup_tabs()
        self.init_responsive_ui(850, 550)

    def logout(self):
        import tkinter as tk
        from tkinter import messagebox

        if messagebox.askyesno("Вихід", "Ви дійсно хочете вийти з облікового запису?"):
            # 1. Повністю закриваємо поточне вікно і зупиняємо його процеси
            self.root.destroy()

            # 2. Створюємо абсолютно нове, чисте "полотно" (root)
            new_root = tk.Tk()

            # 3. Передаємо це нове полотно у твій клас логіну
            LoginWindow(new_root)

            # 4. Запускаємо програму по новій
            new_root.mainloop()

    def setup_tabs(self):
        if self.role == 'Admin':
            self.tab_sections = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_sections, text="Довідник: Секції")
            self.load_admin_sections()


            self.tab_trainers = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_trainers, text="Довідник: Тренери")
            self.load_admin_trainers()

            self.tab_admin_schedule = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_admin_schedule, text="Розклад тренувань")
            self.load_admin_schedule()

            self.tab_reports = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_reports, text="Фінанси та Звіти")
            self.load_admin_reports()

        elif self.role == 'Manager':
            self.tab_registry = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_registry, text="Реєстратура (Клієнти та Продажі)")
            self.load_manager_registry()

        elif self.role == 'Trainer':
            self.tab_schedule = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_schedule, text="Мій розклад (Тренер)")
            self.load_trainer_schedule()

        elif self.role == 'Client':
            self.tab_client = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_client, text="Мої абонементи")
            self.load_client_data()

    def is_valid_date(self, date_str):
        from datetime import datetime
        try:
            # Пробуємо перетворити рядок у справжній об'єкт дати
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            # Якщо виникла помилка (наприклад, 13 місяць або 30 лютого) — дата хибна
            return False

    def is_valid_time(self, time_str):
        # Перевірка формату ГГ:ХХ (від 00:00 до 23:59)
        return bool(re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str))

    def is_valid_phone(self, phone_str):
        # Перевірка українського мобільного номера (+380 та коректний код оператора)
        return bool(re.match(r'^\+380(39|50|63|66|67|68|73|89|91|92|93|94|95|96|97|98|99)\d{7}$', phone_str))

    # ==========================================
    # 1. АДМІНІСТРАТОР: ЗВІТИ ТА АНАЛІТИКА (З ПЕРІОДАМИ)
    # ==========================================
    def load_admin_reports(self):
        for widget in self.tab_reports.winfo_children():
            widget.destroy()

        tk.Label(self.tab_reports, text="Панель керівника (Аналітика та Зарплата)",
                 font=("Arial", 16, "bold")).pack(pady=5)

        # --- БЛОК: НАЛАШТУВАННЯ ПЕРІОДУ ---
        period_frame = tk.LabelFrame(self.tab_reports, text="Налаштування періоду для звітів",
                                     font=("Arial", 10, "bold"))
        period_frame.pack(fill='x', padx=20, pady=5)

        from datetime import datetime
        import calendar

        today = datetime.today()
        first_day = today.strftime('%Y-%m-01')
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day = today.replace(day=last_day_num).strftime('%Y-%m-%d')

        tk.Label(period_frame, text="Період З (РРРР-ММ-ДД):").pack(side='left', padx=5)
        self.entry_report_start = tk.Entry(period_frame, width=12)
        self.entry_report_start.insert(0, first_day)
        self.entry_report_start.pack(side='left', padx=5)

        tk.Label(period_frame, text="ПО:").pack(side='left', padx=5)
        self.entry_report_end = tk.Entry(period_frame, width=12)
        self.entry_report_end.insert(0, last_day)
        self.entry_report_end.pack(side='left', padx=5)

        # Додаємо поле для пошуку по клієнту
        tk.Label(period_frame, text="Пошук (ПІБ або Телефон):").pack(side='left', padx=5)
        self.entry_report_search_client = tk.Entry(period_frame, width=20)
        self.entry_report_search_client.pack(side='left', padx=5)

        # tk.Label(period_frame, fg="gray", font=("Arial", 9, "italic")).pack( side='left', padx=20)

        # --- КНОПКИ ЗВІТІВ ---
        btn_frame = tk.Frame(self.tab_reports)
        btn_frame.pack(fill='x', padx=20, pady=5)

        tk.Button(btn_frame, text="1. Дохід за період", font=("Arial", 10), bg="#FF9800", fg="white",
                  width=32, command=self.generate_revenue_report).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(btn_frame, text="2. Розрахувати ЗП тренерам", font=("Arial", 10), bg="#9C27B0", fg="white",
                  width=32, command=self.generate_payroll_report).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(btn_frame, text="3. Клієнти по тренерам", font=("Arial", 10), bg="#00BCD4", fg="white",
                  width=32, command=self.generate_trainer_clients_report).grid(row=1, column=0, padx=5, pady=5)

        tk.Button(btn_frame, text="4. Абонементи закінчуються", font=("Arial", 10), bg="#E91E63", fg="white",
                  width=32, command=self.generate_expiring_report).grid(row=1, column=1, padx=5, pady=5)

        tk.Button(btn_frame, text="5. Аналіз пікових годин", font=("Arial", 10, "bold"), bg="#3F51B5", fg="white",
                  width=32, command=self.generate_peak_hours_report).grid(row=2, column=0, padx=5, pady=5)

        tk.Button(btn_frame, text="6. Рейтинг популярності секцій", font=("Arial", 10, "bold"), bg="#607D8B",
                  fg="white",
                  width=32, command=self.generate_sections_popularity_report).grid(row=2, column=1, padx=5, pady=5)

        # --- ЗАГАЛЬНИЙ КОНТЕЙНЕР ДЛЯ ВІДОБРАЖЕННЯ БУДЬ-ЯКОГО ЗВІТУ ---
        self.lbl_report_title = tk.Label(self.tab_reports, text="Оберіть звіт для відображення", font=("Arial", 14),
                                         fg="#333")
        self.lbl_report_title.pack(pady=5)

        # Кнопка Експорту (притиснута до низу)
        export_frame = tk.Frame(self.tab_reports)
        export_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        tk.Button(export_frame, text="📊 Експортувати поточний звіт в Excel", bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.export_to_excel).pack(side='right')

        # Універсальна таблиця для всіх звітів
        self.tree_reports = ttk.Treeview(self.tab_reports, show='headings')
        self.tree_reports.pack(side='top', fill='both', expand=True, padx=20, pady=5)

    # --- ДОПОМІЖНА ФУНКЦІЯ: Налаштування колонок таблиці ---
    def setup_report_tree(self, columns, headings):
        for row in self.tree_reports.get_children(): self.tree_reports.delete(row)
        self.tree_reports['columns'] = columns
        for col, head in zip(columns, headings):
            self.tree_reports.heading(col, text=head)
            self.tree_reports.column(col, anchor='center')
        self.tree_reports.column(columns[0], anchor='w', width=200)

    # ==========================================
    # ЛОГІКА 6 ЗВІТІВ
    # ==========================================
    def get_valid_report_dates(self):
        """Допоміжна функція: перевіряє формат і логіку дат перед генерацією звіту"""
        from datetime import datetime
        from tkinter import messagebox

        start_date = self.entry_report_start.get().strip()
        end_date = self.entry_report_end.get().strip()

        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end = datetime.strptime(end_date, '%Y-%m-%d')

            # Захист від "Мандрівників у часі"
            if dt_start > dt_end:
                messagebox.showerror("Логічна помилка",
                                     "Початкова дата 'З' не може бути пізнішою за кінцеву дату 'ПО'!")
                return None, None

            return start_date, end_date
        except ValueError:
            # Якщо ввели "привіт" або "01.03.2026" замість 2026-03-01
            messagebox.showerror("Помилка формату",
                                 "Неправильний формат дати!\n\nБудь ласка, введіть дати у форматі РРРР-ММ-ДД\n(наприклад: 2026-03-01)")
            return None, None

    def generate_revenue_report(self):
        dates = self.get_valid_report_dates()
        if not dates[0]: return  # Зупиняємо звіт, якщо дати криві
        s_date, e_date = dates

        self.lbl_report_title.config(text=f"Дохід з {s_date} по {e_date}")
        self.setup_report_tree(
            ('date', 'amount', 'sales_count', 'total_amount', 'total_count'),
            ('Дата', 'Дохід за день', 'Продано за день', 'ЗАГАЛЬНИЙ ДОХІД', 'ВСЬОГО АБОНЕМЕНТІВ')
        )
        self.tree_reports.tag_configure('highlight', background='#FFF9C4')

        query = "SELECT sale_date, SUM(total_paid) as daily_total, COUNT(id_sale) as daily_count FROM Sales WHERE sale_date BETWEEN %s AND %s GROUP BY sale_date ORDER BY sale_date"
        data = self.db.fetch_data(query, (s_date, e_date)) or []

        if data:
            grand_total = sum(float(r['daily_total']) for r in data)
            grand_count = sum(int(r['daily_count']) for r in data)
            self.tree_reports.insert('', 'end', values=("ПІДСУМОК ЗА ПЕРІОД:", "", "", f"{grand_total:.2f} грн",
                                                        f"{grand_count} шт."), tags=('highlight',))
            for r in data:
                self.tree_reports.insert('', 'end',
                                         values=(r['sale_date'], f"{float(r['daily_total']):.2f}", r['daily_count'],
                                                 "", ""))
        else:
            self.tree_reports.insert('', 'end', values=("Немає продажів", "", "", "", ""))

    def generate_payroll_report(self):
        dates = self.get_valid_report_dates()
        if not dates[0]: return
        s_date, e_date = dates

        self.lbl_report_title.config(text=f"Зарплати тренерів з {s_date} по {e_date}")
        self.setup_report_tree(('trainer', 'indiv', 'group', 'salary'),
                               ('Тренер', 'Індивід. (шт)', 'Групові (шт)', 'До виплати (грн)'))

        # --- МАГІЯ REVENUE SHARE (Відсоток від реального чека) ---
        query = """
            SELECT t.full_name,
                COUNT(CASE WHEN sec.section_type = 'Індивідуальна' THEN a.id_attendance END) as indiv_clients,
                COUNT(CASE WHEN sec.section_type IN ('Групова', 'ТЗ') THEN a.id_attendance END) as group_clients,
                COALESCE(SUM(
                    CASE 
                        WHEN a.id_attendance IS NOT NULL AND sec.section_type = 'Індивідуальна' THEN 
                            -- Формула: (Реальна ціна чека / К-ть занять) * 60
                            -- NULLIF захищає від ділення на нуль
                            -- COALESCE захищає старі записи: якщо id_sale ще порожній, беремо стару фіксовану t.indiv_rate
                            COALESCE((sl.total_paid / NULLIF(m.visits_limit, 0)) * 0.60, t.indiv_rate)

                        WHEN a.id_attendance IS NOT NULL AND sec.section_type IN ('Групова', 'ТЗ') THEN 
                            t.group_rate 

                        ELSE 0 
                    END
                ), 0) as total_salary
            FROM Trainers t
            LEFT JOIN Schedule s ON t.id_trainer = s.id_trainer AND s.class_date BETWEEN %s AND %s
            LEFT JOIN Sections sec ON s.id_section = sec.id_section
            LEFT JOIN Attendance a ON s.id_schedule = a.id_schedule AND a.presence_status LIKE 'Присутній%%'
            -- ПРИЄДНУЄМО ТАБЛИЦІ ЧЕКІВ ТА АБОНЕМЕНТІВ ДЛЯ МАТЕМАТИКИ:
            LEFT JOIN Sales sl ON a.id_sale = sl.id_sale
            LEFT JOIN Memberships m ON sl.id_membership = m.id_membership
            GROUP BY t.id_trainer, t.full_name 
            ORDER BY total_salary DESC
        """
        for r in self.db.fetch_data(query, (s_date, e_date)) or []:
            self.tree_reports.insert('', 'end', values=(r['full_name'], r['indiv_clients'], r['group_clients'],
                                                        f"{float(r['total_salary']):.2f}"))

    def generate_trainer_clients_report(self):
        dates = self.get_valid_report_dates()
        if not dates[0]: return
        s_date, e_date = dates

        # Зчитуємо текст із нового поля пошуку (якщо воно існує)
        search_val = ""
        if hasattr(self, 'entry_report_search_client'):
            search_val = self.entry_report_search_client.get().strip()

        # 1. Оновлюємо заголовок та колонки
        if search_val:
            self.lbl_report_title.config(text=f"Пошук '{search_val}': Клієнти та Тренери (з {s_date} по {e_date})")
        else:
            self.lbl_report_title.config(text=f"Деталізація: Клієнти та Тренери з {s_date} по {e_date}")

        self.setup_report_tree(
            ('client', 'phone', 'trainer', 'date', 'section'),
            ('ПІБ Клієнта', 'Телефон', 'Тренер', 'Дата і Час', 'Напрямок')
        )

        # 2. Будуємо розширений SQL-запит
        query = """
            SELECT c.full_name as client_name, c.phone, t.full_name as trainer_name, 
                   s.class_date, s.start_time, sec.section_name
            FROM Clients c
            JOIN Attendance a ON c.id_client = a.id_client
            JOIN Schedule s ON a.id_schedule = s.id_schedule
            JOIN Trainers t ON s.id_trainer = t.id_trainer
            JOIN Sections sec ON s.id_section = sec.id_section
            WHERE s.class_date BETWEEN %s AND %s
        """
        params = [s_date, e_date]

        # 3. Якщо користувач щось ввів у пошук - додаємо фільтр (LIKE)
        if search_val:
            query += " AND (c.full_name LIKE %s OR c.phone LIKE %s)"
            search_pattern = f"%{search_val}%"
            # Передаємо патерн двічі: для ПІБ і для Телефону
            params.extend([search_pattern, search_pattern])

        # Сортуємо від найновіших до найстаріших тренувань
        query += " ORDER BY s.class_date DESC, s.start_time DESC"

        # 4. Виконуємо запит та заповнюємо таблицю
        data = self.db.fetch_data(query, tuple(params)) or []

        if data:
            for r in data:
                datetime_str = f"{r['class_date']} {r['start_time']}"
                self.tree_reports.insert('', 'end', values=(
                    r['client_name'],
                    r['phone'],
                    r['trainer_name'],
                    datetime_str,
                    r['section_name']
                ))
        else:
            self.tree_reports.insert('', 'end', values=("Записів не знайдено", "", "", "", ""))

    def generate_expiring_report(self):
        # Зчитуємо текст із нашого універсального поля пошуку
        search_val = ""
        if hasattr(self, 'entry_report_search_client'):
            search_val = self.entry_report_search_client.get().strip()

        # 1. Оновлюємо заголовок
        if search_val:
            self.lbl_report_title.config(text=f"Пошук '{search_val}': Абонементи, що закінчуються (7 днів)")
        else:
            self.lbl_report_title.config(text="Абонементи, що закінчуються у найближчі 7 днів")

        self.setup_report_tree(
            ('client', 'phone', 'package', 'exp_date'),
            ('ПІБ Клієнта', 'Телефон', 'Абонемент', 'Діє до')
        )

        # 2. Базовий SQL-запит (від сьогодні + 7 днів)
        query = """
            SELECT c.full_name, c.phone, m.package_name, DATE_ADD(sl.sale_date, INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY) as exp_date
            FROM Sales sl 
            JOIN Clients c ON sl.id_client = c.id_client 
            JOIN Memberships m ON sl.id_membership = m.id_membership
            WHERE DATE_ADD(sl.sale_date, INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """
        params = []

        # 3. Якщо користувач щось ввів у пошук - додаємо фільтр
        if search_val:
            query += " AND (c.full_name LIKE %s OR c.phone LIKE %s)"
            search_pattern = f"%{search_val}%"
            params.extend([search_pattern, search_pattern])

        # Сортуємо, щоб ті, що згорають найшвидше, були зверху
        query += " ORDER BY exp_date ASC"

        # 4. Виконуємо запит
        if params:
            data = self.db.fetch_data(query, tuple(params)) or []
        else:
            data = self.db.fetch_data(query) or []

        # 5. Виводимо результат
        if data:
            for r in data:
                self.tree_reports.insert('', 'end',
                                         values=(r['full_name'], r['phone'], r['package_name'], r['exp_date']))
        else:
            self.tree_reports.insert('', 'end', values=("Записів не знайдено", "", "", ""))

    def generate_peak_hours_report(self):
        dates = self.get_valid_report_dates()
        if not dates[0]: return
        s_date, e_date = dates

        self.lbl_report_title.config(text=f"Пікові години з {s_date} по {e_date}")
        self.setup_report_tree(('time', 'visits'), ('Час початку тренування', 'Кількість клієнтів (Присутні)'))

        query = """
            SELECT s.start_time, COUNT(a.id_attendance) as total
            FROM Schedule s JOIN Attendance a ON s.id_schedule = a.id_schedule
            WHERE a.presence_status LIKE 'Присутній%%' AND s.class_date BETWEEN %s AND %s
            GROUP BY s.start_time ORDER BY total DESC
        """
        for r in self.db.fetch_data(query, (s_date, e_date)) or []:
            self.tree_reports.insert('', 'end', values=(r['start_time'], r['total']))

    def generate_sections_popularity_report(self):
        dates = self.get_valid_report_dates()
        if not dates[0]: return
        s_date, e_date = dates

        self.lbl_report_title.config(text=f"Популярність секцій з {s_date} по {e_date}")
        self.setup_report_tree(('section', 'visits'), ('Секція (Напрямок)', 'Кількість відвідувань'))

        query = """
            SELECT sec.section_name, COUNT(a.id_attendance) as total
            FROM Sections sec JOIN Schedule s ON sec.id_section = s.id_section
            JOIN Attendance a ON s.id_schedule = a.id_schedule
            WHERE a.presence_status LIKE 'Присутній%%' AND s.class_date BETWEEN %s AND %s
            GROUP BY sec.section_name ORDER BY total DESC
        """
        for r in self.db.fetch_data(query, (s_date, e_date)) or []:
            self.tree_reports.insert('', 'end', values=(r['section_name'], r['total']))

    # ==========================================
    # УНІВЕРСАЛЬНИЙ ЕКСПОРТ В EXCEL
    # ==========================================
    def export_to_excel(self):
        import csv
        from tkinter import filedialog, messagebox

        # Перевіряємо, чи є взагалі дані в таблиці
        if not self.tree_reports.get_children():
            return messagebox.showwarning("Увага", "Спочатку згенеруйте звіт, який хочете експортувати!")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV (Excel)", "*.csv")],
            title="Зберегти звіт..."
        )
        if not file_path: return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')

                # Автоматично беремо назви колонок поточного звіту
                headers = [self.tree_reports.heading(c)['text'] for c in self.tree_reports['columns']]
                writer.writerow(headers)

                # Пишемо рядки
                for row_id in self.tree_reports.get_children():
                    writer.writerow(self.tree_reports.item(row_id)['values'])

            messagebox.showinfo("Успіх", f"Звіт збережено:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл:\n{e}")

    def show_report_table(self, title, columns_text, data, dict_keys):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x300")
        tk.Label(dialog, text=title, font=("Arial", 12, "bold")).pack(pady=10)
        if not data:
            tk.Label(dialog, text="Немає даних за цей період.", fg="red").pack(pady=20)
            return
        cols = tuple(range(len(columns_text)))
        tree = ttk.Treeview(dialog, columns=cols, show='headings')
        for i, col_name in enumerate(columns_text):
            tree.heading(i, text=col_name)
            tree.column(i, anchor='center', width=180 if i == 0 else 120)
        tree.pack(expand=True, fill='both', padx=10, pady=10)
        for row in data:
            values = [row[key] for key in dict_keys]
            tree.insert('', 'end', values=values)

    # ==========================================
    # 2. АДМІНІСТРАТОР: УПРАВЛІННЯ СЕКЦІЯМИ
    # ==========================================
    def load_admin_sections(self):
        btn_frame = tk.Frame(self.tab_sections)
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame, text="Додати", bg="#4CAF50", fg="white", width=12, command=self.add_section).pack(
            side='left', padx=5)
        tk.Button(btn_frame, text="Редагувати", bg="#2196F3", fg="white", width=12, command=self.edit_section).pack(
            side='left', padx=5)
        tk.Button(btn_frame, text="Видалити", bg="#f44336", fg="white", width=12, command=self.delete_section).pack(
            side='left', padx=5)

        # --- ДОДАНО КОЛОНКУ 'capacity' ---
        columns = ('id', 'name', 'type', 'age', 'capacity')
        self.tree = ttk.Treeview(self.tab_sections, columns=columns, show='headings')
        self.tree.heading('id', text='ID', command=lambda: self.sort_treeview(self.tree, 'id', False))
        self.tree.heading('name', text='Назва напрямку', command=lambda: self.sort_treeview(self.tree, 'name', False))
        self.tree.heading('type', text='Тип заняття', command=lambda: self.sort_treeview(self.tree, 'type', False))
        self.tree.heading('age', text='Вікове обмеження', command=lambda: self.sort_treeview(self.tree, 'age', False))
        self.tree.heading('capacity', text='Кількість місць',
                          command=lambda: self.sort_treeview(self.tree, 'capacity', False))

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('name', width=200, anchor='w')
        self.tree.column('type', width=120, anchor='center')
        self.tree.column('age', width=120, anchor='center')
        self.tree.column('capacity', width=100, anchor='center')
        self.tree.pack(expand=True, fill='both', pady=5, padx=10)
        self.refresh_sections_table()

    def refresh_sections_table(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        sections = self.db.fetch_data("SELECT * FROM Sections")
        if sections:
            for s in sections:
                # Вставляємо дані, включаючи capacity
                self.tree.insert('', 'end',
                                 values=(s['id_section'], s['section_name'], s['section_type'], s['age_limit'],
                                         s.get('capacity', 1)))

    def add_section(self):
        # Додали capacity у запит
        self.open_section_dialog("Додати секцію",
                                 "INSERT INTO Sections (section_name, section_type, age_limit, capacity) VALUES (%s, %s, %s, %s)")

    def edit_section(self):
        selected = self.tree.selection()
        if not selected: return messagebox.showwarning("Увага", "Оберіть запис!")
        item = self.tree.item(selected[0])['values']
        # Додали capacity у запит та передаємо item[4]
        self.open_section_dialog("Редагувати",
                                 "UPDATE Sections SET section_name = %s, section_type = %s, age_limit = %s, capacity = %s WHERE id_section = %s",
                                 item[0], item[1], item[2], item[3], item[4])

    def open_section_dialog(self, title, query, item_id=None, current_name="", current_type="Групова", current_age="",
                            current_capacity="15"):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x320")

        tk.Label(dialog, text="Назва:").pack(pady=2)
        entry_name = tk.Entry(dialog, width=30)
        entry_name.insert(0, current_name)
        entry_name.pack(pady=2)

        tk.Label(dialog, text="Вікове обмеження:").pack(pady=2)
        entry_age = tk.Entry(dialog, width=30)
        entry_age.insert(0, str(current_age))
        entry_age.pack(pady=2)

        tk.Label(dialog, text="Тип заняття:").pack(pady=2)
        combo_type = ttk.Combobox(dialog, values=["Групова", "Індивідуальна"], state="readonly", width=27)
        combo_type.set(current_type)
        combo_type.pack(pady=2)

        # --- СПЕЦІАЛЬНИЙ ФРЕЙМ-КОНТЕЙНЕР ДЛЯ МІСТКОСТІ ---
        # Він фіксує місце рівно під випадаючим списком і над кнопкою "Зберегти"
        frame_capacity = tk.Frame(dialog)
        frame_capacity.pack(fill='x', pady=2)

        lbl_capacity = tk.Label(frame_capacity, text="Кількість місць:")
        entry_capacity = tk.Entry(frame_capacity, width=30)
        entry_capacity.insert(0, str(current_capacity))

        def toggle_capacity(event=None):
            # Перемикаємо видимість елементів ТІЛЬКИ всередині нашого фрейму
            if combo_type.get() == "Групова":
                lbl_capacity.pack(pady=2)
                entry_capacity.pack(pady=2)
            else:
                lbl_capacity.pack_forget()
                entry_capacity.pack_forget()

        # Прив'язуємо перемикач і викликаємо одразу для стартового налаштування
        combo_type.bind("<<ComboboxSelected>>", toggle_capacity)
        toggle_capacity()

        # --------------------------------------------------

        def save_data():
            c_type = combo_type.get()

            # Визначаємо місткість
            if c_type == 'Індивідуальна':
                capacity_val = 1
            else:
                try:
                    capacity_val = int(entry_capacity.get())
                except ValueError:
                    capacity_val = 15  # Значення за замовчуванням

            if item_id:
                self.db.execute_query(query, (entry_name.get(), c_type, int(entry_age.get()), capacity_val, item_id))
            else:
                self.db.execute_query(query, (entry_name.get(), c_type, int(entry_age.get()), capacity_val))

            self.refresh_sections_table()
            dialog.destroy()

        # Кнопка збереження тепер надійно зафіксована внизу
        tk.Button(dialog, text="Зберегти", bg="#4CAF50", fg="white", command=save_data).pack(pady=15)

    def delete_section(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть запис для видалення!")
            return
        item_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Підтвердження", "Ви дійсно хочете видалити цю секцію?"):
            if self.db.execute_query("DELETE FROM Sections WHERE id_section = %s", (item_id,)):
                self.refresh_sections_table()

    # ==========================================
    # НОВИЙ БЛОК: УПРАВЛІННЯ ТРЕНЕРАМИ (АДМІН)
    # ==========================================
    def load_admin_trainers(self):
        btn_frame = tk.Frame(self.tab_trainers)
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame, text="Додати тренера", bg="#4CAF50", fg="white", width=15,
                  command=self.add_trainer).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Звільнити (Видалити)", bg="#f44336", fg="white", width=20,
                  command=self.delete_trainer).pack(side='left', padx=5)

        # --- ОНОВЛЕНІ КОЛОНКИ: ТЕПЕР ЇХ ДВІ ДЛЯ СТАВОК ---
        cols = ('id', 'name', 'indiv_rate', 'group_rate')
        self.tree_trainers = ttk.Treeview(self.tab_trainers, columns=cols, show='headings')
        self.tree_trainers.heading('id', text='ID')
        self.tree_trainers.heading('name', text='ПІБ Тренера')
        self.tree_trainers.heading('indiv_rate', text='Ставка індивід. (грн)')
        self.tree_trainers.heading('group_rate', text='Ставка групові (грн/люд)')

        self.tree_trainers.column('id', width=40, anchor='center')
        self.tree_trainers.column('name', width=250, anchor='w')
        self.tree_trainers.column('indiv_rate', width=130, anchor='center')
        self.tree_trainers.column('group_rate', width=150, anchor='center')
        self.tree_trainers.pack(expand=True, fill='both', pady=5, padx=10)

        self.refresh_trainers_table()

    def refresh_trainers_table(self):
        for row in self.tree_trainers.get_children():
            self.tree_trainers.delete(row)

        # --- ОНОВЛЕНИЙ ЗАПИТ: ТЯГНЕМО ОБИДВІ СТАВКИ ---
        trainers = self.db.fetch_data("SELECT id_trainer, full_name, indiv_rate, group_rate FROM Trainers")
        if trainers:
            for t in trainers:
                self.tree_trainers.insert('', 'end',
                                          values=(t['id_trainer'], t['full_name'], t['indiv_rate'], t['group_rate']))

    def add_trainer(self):
        from tkinter import messagebox
        dialog = tk.Toplevel(self.root)
        dialog.title("Реєстрація тренера")
        dialog.geometry("300x350")
        dialog.grab_set()

        tk.Label(dialog, text="ПІБ Тренера:").pack(pady=2)
        entry_name = tk.Entry(dialog, width=30)
        entry_name.pack()

        # --- ПРОСИМО ВВЕСТИ ТІЛЬКИ ІНДИВІДУАЛЬНУ СТАВКУ ---
        tk.Label(dialog, text="Ставка за індивідуальне (грн):").pack(pady=2)
        entry_rate = tk.Entry(dialog, width=30)
        entry_rate.pack()

        tk.Label(dialog, text="Логін для входу:").pack(pady=2)
        entry_login = tk.Entry(dialog, width=30)
        entry_login.pack()
        tk.Label(dialog, text="Пароль:").pack(pady=2)
        entry_pass = tk.Entry(dialog, width=30)
        entry_pass.pack()

        def save():
            name = entry_name.get()
            rate = entry_rate.get()
            login = entry_login.get()
            password = entry_pass.get()

            if not name or not rate or not login or not password:
                messagebox.showwarning("Увага", "Заповніть всі поля!", parent=dialog)
                return

            try:
                rate_val = float(rate)
            except ValueError:
                messagebox.showerror("Помилка", "Ставка має бути числом!", parent=dialog)
                return

            # 1. Створюємо обліковий запис
            if not self.db.execute_query(
                    "INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, 'Trainer')",
                    (login, password)):
                messagebox.showerror("Помилка", "Такий логін вже існує!", parent=dialog)
                return

            user_id = self.db.fetch_data("SELECT id_user FROM Users WHERE username = %s", (login,))[0]['id_user']

            # --- 2. Створюємо фізичного тренера (GROUP_RATE = 50.00 ТУТ) ---
            if self.db.execute_query(
                    "INSERT INTO Trainers (full_name, indiv_rate, group_rate, id_user) VALUES (%s, %s, 50.00, %s)",
                    (name, rate_val, user_id)):
                self.refresh_trainers_table()
                dialog.destroy()
                messagebox.showinfo("Успіх",
                                    "Тренера додано!\n\nСтавка за людину в групі (50 грн) призначена автоматично.")
            else:
                self.db.execute_query("DELETE FROM Users WHERE id_user = %s", (user_id,))
                messagebox.showerror("Помилка", "Помилка бази даних!", parent=dialog)

        tk.Button(dialog, text="Зберегти", bg="#4CAF50", fg="white", command=save).pack(pady=15)

    def delete_trainer(self):
        from tkinter import messagebox
        selected = self.tree_trainers.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть тренера для звільнення!")
            return

        t_id = self.tree_trainers.item(selected[0])['values'][0]

        if messagebox.askyesno("Підтвердження", "Ви дійсно хочете видалити цього тренера?"):

            # --- НОВИЙ БЛОК: ПЕРЕВІРКА ЗАЛЕЖНОСТЕЙ В БАЗІ ДАНИХ ---
            # 1. Перевіряємо, чи є у нього записи в розкладі (минулі або майбутні)
            sched_check = self.db.fetch_data("SELECT COUNT(*) as count FROM Schedule WHERE id_trainer = %s", (t_id,))
            sched_count = sched_check[0]['count'] if sched_check else 0

            # 2. Перевіряємо, чи прив'язані до нього продані індивідуальні абонементи
            sales_check = self.db.fetch_data("SELECT COUNT(*) as count FROM Sales WHERE id_trainer = %s", (t_id,))
            sales_count = sales_check[0]['count'] if sales_check else 0

            # Якщо знайдено хоча б один "хвіст" - блокуємо видалення і пояснюємо чому
            if sched_count > 0 or sales_count > 0:
                msg = "Неможливо звільнити цього тренера, оскільки він є в історії клубу!\n\n"
                if sched_count > 0:
                    msg += f"🏋️ Проведено/Заплановано занять: {sched_count} шт.\n"
                if sales_count > 0:
                    msg += f"💰 Продано індивідуальних абонементів: {sales_count} шт.\n"
                msg += "\nПорада: Ви не можете видалити його повністю, щоб не зламати фінансові звіти."
                return messagebox.showerror("Блокування видалення", msg)
            # --------------------------------------------------------

            # Якщо залежностей немає (тренера тільки створили і він ще нічого не робив) - видаляємо!
            user_data = self.db.fetch_data("SELECT id_user FROM Trainers WHERE id_trainer = %s", (t_id,))

            if self.db.execute_query("DELETE FROM Trainers WHERE id_trainer = %s", (t_id,)):
                if user_data:
                    self.db.execute_query("DELETE FROM Users WHERE id_user = %s", (user_data[0]['id_user'],))
                self.refresh_trainers_table()
                messagebox.showinfo("Успіх", "Тренера успішно звільнено та видалено з бази.")
            else:
                messagebox.showerror("Помилка", "Сталася невідома помилка при видаленні.")

    # ==========================================
    # 3. АДМІНІСТРАТОР: РОЗКЛАД
    # ==========================================
    def load_admin_schedule(self):
        filter_frame = tk.LabelFrame(self.tab_admin_schedule, text="Пошук та Фільтрація")
        filter_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(filter_frame, text="Дата (РРРР-ММ-ДД):").pack(side='left', padx=5)
        self.entry_sched_date = tk.Entry(filter_frame, width=12)
        self.entry_sched_date.pack(side='left', padx=5)

        tk.Label(filter_frame, text="Секція:").pack(side='left', padx=5)
        self.entry_sched_sec = tk.Entry(filter_frame, width=15)
        self.entry_sched_sec.pack(side='left', padx=5)

        tk.Button(filter_frame, text="🔍 Знайти", bg="#2196F3", fg="white", command=self.refresh_schedule_table).pack(
            side='left', padx=10)
        tk.Button(filter_frame, text="Скинути", command=self.reset_schedule_filter).pack(side='left', padx=5)

        # --- НОВИЙ ЕЛЕМЕНТ: Чекбокс для приховування минулого ---
        self.show_past_var = tk.BooleanVar(value=False)  # За замовчуванням False (ховаємо минулі)
        tk.Checkbutton(filter_frame, text="Показувати архівні (минулі) заняття",
                       variable=self.show_past_var, command=self.refresh_schedule_table).pack(side='left', padx=20)
        # --------------------------------------------------------

        btn_frame = tk.Frame(self.tab_admin_schedule)
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame, text="Додати заняття", bg="#4CAF50", fg="white", width=15,
                  command=self.add_schedule_dialog).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Видалити", bg="#f44336", fg="white", width=15, command=self.delete_schedule).pack(
            side='left', padx=5)

        columns = ('id', 'date', 'time', 'section', 'trainer')
        self.tree_schedule = ttk.Treeview(self.tab_admin_schedule, columns=columns, show='headings')
        self.tree_schedule.heading('id', text='ID', command=lambda: self.sort_treeview(self.tree_schedule, 'id', False))
        self.tree_schedule.heading('date', text='Дата',
                                   command=lambda: self.sort_treeview(self.tree_schedule, 'date', False))
        self.tree_schedule.heading('time', text='Час',
                                   command=lambda: self.sort_treeview(self.tree_schedule, 'time', False))
        self.tree_schedule.heading('section', text='Секція',
                                   command=lambda: self.sort_treeview(self.tree_schedule, 'section', False))
        self.tree_schedule.heading('trainer', text='Тренер',
                                   command=lambda: self.sort_treeview(self.tree_schedule, 'trainer', False))

        self.tree_schedule.column('id', width=40, anchor='center')
        self.tree_schedule.column('date', width=100, anchor='center')
        self.tree_schedule.column('time', width=80, anchor='center')
        self.tree_schedule.column('section', width=150, anchor='w')
        self.tree_schedule.column('trainer', width=200, anchor='w')
        self.tree_schedule.pack(expand=True, fill='both', pady=5, padx=10)

        self.refresh_schedule_table()

    def reset_schedule_filter(self):
        self.entry_sched_date.delete(0, tk.END)
        self.entry_sched_sec.delete(0, tk.END)
        self.refresh_schedule_table()

    def refresh_schedule_table(self):
        for row in self.tree_schedule.get_children():
            self.tree_schedule.delete(row)

        d_filt = self.entry_sched_date.get().strip() if hasattr(self, 'entry_sched_date') else ""
        s_filt = self.entry_sched_sec.get().strip() if hasattr(self, 'entry_sched_sec') else ""

        query = """
            SELECT s.id_schedule, s.class_date, s.start_time, sec.section_name, t.full_name 
            FROM Schedule s 
            JOIN Sections sec ON s.id_section = sec.id_section 
            JOIN Trainers t ON s.id_trainer = t.id_trainer 
            WHERE 1=1
        """
        params = []

        # --- РОЗУМНЕ ПРИХОВУВАННЯ МИНУЛИХ ТРЕНУВАНЬ ---
        if hasattr(self, 'show_past_var') and not self.show_past_var.get():
            # Якщо галочка НЕ стоїть, перетворюємо дату+час на об'єкт DATETIME і порівнюємо з поточною секундою NOW()
            query += " AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) >= NOW()"
        # ----------------------------------------------

        if d_filt:
            query += " AND s.class_date = %s"
            params.append(d_filt)
        if s_filt:
            query += " AND sec.section_name LIKE %s"
            params.append(f"%{s_filt}%")

        query += " ORDER BY s.class_date DESC, s.start_time DESC"

        schedule = self.db.fetch_data(query, tuple(params))
        if schedule:
            for s in schedule:
                self.tree_schedule.insert('', 'end',
                                          values=(s['id_schedule'], s['class_date'], s['start_time'], s['section_name'],
                                                  s['full_name']))

    def add_schedule_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати заняття у розклад")
        dialog.geometry("350x380")
        dialog.grab_set()
        sections = self.db.fetch_data("SELECT id_section, section_name FROM Sections")
        trainers = self.db.fetch_data("SELECT id_trainer, full_name FROM Trainers")
        if not sections or not trainers:
            messagebox.showerror("Помилка", "Додайте хоча б одну секцію та тренера!", parent=dialog)
            dialog.destroy()
            return
        tk.Label(dialog, text="Оберіть секцію:").pack(pady=5)
        combo_sec = ttk.Combobox(dialog, state="readonly", width=35)
        combo_sec['values'] = [f"{s['id_section']} - {s['section_name']}" for s in sections]
        combo_sec.pack()
        tk.Label(dialog, text="Оберіть тренера:").pack(pady=5)
        combo_tr = ttk.Combobox(dialog, state="readonly", width=35)
        combo_tr['values'] = [f"{t['id_trainer']} - {t['full_name']}" for t in trainers]
        combo_tr.pack()
        tk.Label(dialog, text="Дата (РРРР-ММ-ДД):").pack(pady=5)
        entry_date = tk.Entry(dialog, width=38)
        entry_date.pack()
        tk.Label(dialog, text="Час (ГГ:ХХ):").pack(pady=5)
        entry_time = tk.Entry(dialog, width=38)
        entry_time.pack()

        def save_schedule():
            from datetime import datetime
            from tkinter import messagebox

            sec_val = combo_sec.get()
            tr_val = combo_tr.get()
            date_val = entry_date.get().strip()
            time_val = entry_time.get().strip()

            if not sec_val or not tr_val or not date_val or not time_val:
                messagebox.showwarning("Увага", "Заповніть всі поля!", parent=dialog)
                return

            if not self.is_valid_date(date_val):
                messagebox.showerror("Помилка", "Дата має бути у форматі РРРР-ММ-ДД", parent=dialog)
                return
            if not self.is_valid_time(time_val):
                messagebox.showerror("Помилка", "Час має бути у форматі ГГ:ХХ", parent=dialog)
                return

            try:
                # Склеюємо введену дату і час та перетворюємо у справжній об'єкт часу Python
                class_dt = datetime.strptime(f"{date_val} {time_val}", "%Y-%m-%d %H:%M")

                # Перевірка на "Минулий час"
                if class_dt < datetime.now():
                    messagebox.showerror("Помилка", "Неможливо створити тренування у минулому часі!", parent=dialog)
                    return

                # --- НОВИЙ БЛОК: Перевірка робочих годин клубу (08:00 - 21:00) ---
                t = class_dt.time()
                if t < datetime.strptime('08:00', '%H:%M').time() or t > datetime.strptime('21:00', '%H:%M').time():
                    messagebox.showerror("Помилка",
                                         "Клуб зачинено в цей час!\nРобочі години: 08:00 - 22:00 (останній запис на 21:00).",
                                         parent=dialog)
                    return

            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка обробки часу: {e}", parent=dialog)
                return

            # Витягуємо ID
            sec_id = int(sec_val.split(' - ')[0])
            tr_id = int(tr_val.split(' - ')[0])

            # --- НОВИЙ БЛОК: Перевірка накладання тренувань ---
            sec_info = self.db.fetch_data("SELECT section_type FROM Sections WHERE id_section = %s", (sec_id,))
            if not sec_info:
                return
            new_sec_type = sec_info[0]['section_type']

            overlap_query = """
                SELECT sec.section_type 
                FROM Schedule s 
                JOIN Sections sec ON s.id_section = sec.id_section 
                WHERE s.id_trainer = %s AND s.class_date = %s AND s.start_time = %s
            """
            existing_classes = self.db.fetch_data(overlap_query, (tr_id, date_val, time_val))

            if existing_classes:
                if new_sec_type == 'Групова':
                    messagebox.showerror("Помилка",
                                         "Тренер вже має заняття на цей час!\nГрупове тренування не можна поєднувати з іншими записами.",
                                         parent=dialog)
                    return

                for ec in existing_classes:
                    if ec['section_type'] == 'Групова':
                        messagebox.showerror("Помилка",
                                             "У цей час тренер проводить Групове заняття!\nВи не можете поставити йому паралельне Індивідуальне.",
                                             parent=dialog)
                        return
            # --------------------------------------------------

            # Фінальне збереження
            query = "INSERT INTO Schedule (id_section, id_trainer, class_date, start_time) VALUES (%s, %s, %s, %s)"
            if self.db.execute_query(query, (sec_id, tr_id, date_val, time_val)):
                self.refresh_schedule_table()
                dialog.destroy()
            else:
                messagebox.showerror("Помилка", "Помилка бази даних.", parent=dialog)

        tk.Button(dialog, text="Зберегти", bg="#4CAF50", fg="white", command=save_schedule).pack(pady=20)

    def delete_schedule(self):
        selected = self.tree_schedule.selection()
        if not selected:
            return
        item_id = self.tree_schedule.item(selected[0])['values'][0]
        if messagebox.askyesno("Підтвердження", "Видалити це заняття?"):
            if self.db.execute_query("DELETE FROM Schedule WHERE id_schedule = %s", (item_id,)):
                self.refresh_schedule_table()

    # ==========================================
    # 4. МЕНЕДЖЕР: РЕЄСТРАТУРА, ПРОДАЖІ ТА ЗАПИС
    # ==========================================
    def load_manager_registry(self):
        # --- ВЕРХНЯ ЧАСТИНА (Реєстрація та Продаж) ---
        top_frame = tk.Frame(self.tab_registry)
        top_frame.pack(fill='x', padx=10, pady=5)

        frame_left = tk.LabelFrame(top_frame, text="Реєстрація нового клієнта", font=("Arial", 11, "bold"))
        frame_left.pack(side='left', expand=True, fill='both', padx=5, pady=5)

        frame_right = tk.LabelFrame(top_frame, text="Продаж абонемента", font=("Arial", 11, "bold"))
        frame_right.pack(side='right', expand=True, fill='both', padx=5, pady=5)

        # --- Форма реєстрації ---
        tk.Label(frame_left, text="ПІБ Клієнта:").grid(row=0, column=0, pady=2, sticky='e')
        self.entry_client_name = tk.Entry(frame_left, width=25)
        self.entry_client_name.grid(row=0, column=1, pady=2, padx=5)

        tk.Label(frame_left, text="Телефон (+380...):").grid(row=1, column=0, pady=2, sticky='e')
        self.entry_client_phone = tk.Entry(frame_left, width=25)
        self.entry_client_phone.grid(row=1, column=1, pady=2, padx=5)

        tk.Label(frame_left, text="Дата (РРРР-ММ-ДД):").grid(row=2, column=0, pady=2, sticky='e')
        self.entry_client_birth = tk.Entry(frame_left, width=25)
        self.entry_client_birth.grid(row=2, column=1, pady=2, padx=5)

        tk.Label(frame_left, text="Логін:").grid(row=3, column=0, pady=2, sticky='e')
        self.entry_client_login = tk.Entry(frame_left, width=25)
        self.entry_client_login.grid(row=3, column=1, pady=2, padx=5)

        tk.Label(frame_left, text="Пароль:").grid(row=4, column=0, pady=2, sticky='e')
        self.entry_client_pass = tk.Entry(frame_left, width=25)
        self.entry_client_pass.grid(row=4, column=1, pady=2, padx=5)

        tk.Button(frame_left, text="Зареєструвати", bg="#4CAF50", fg="white", command=self.register_client).grid(
            row=5, column=0, columnspan=2, pady=10)

        # --- Форма продажу (ОНОВЛЕНО З ПОШУКОМ) ---
        sale_search_frame = tk.Frame(frame_right)
        sale_search_frame.pack(fill='x', padx=5, pady=2)

        self.sale_client_mode = tk.IntVar(value=1)
        tk.Radiobutton(sale_search_frame, text="Активні", variable=self.sale_client_mode, value=1,
                       command=self.refresh_sale_clients_list).pack(side='left')
        tk.Radiobutton(sale_search_frame, text="Архів", variable=self.sale_client_mode, value=0,
                       command=self.refresh_sale_clients_list, fg="gray").pack(side='left')

        tk.Label(sale_search_frame, text=" 🔍:").pack(side='left')
        self.entry_sale_search = tk.Entry(sale_search_frame, width=15)
        self.entry_sale_search.pack(side='left', padx=2)
        self.entry_sale_search.bind('<KeyRelease>', lambda e: self.refresh_sale_clients_list())

        self.combo_clients = ttk.Combobox(frame_right, state="readonly", width=35)
        self.combo_clients.pack(pady=2)

        tk.Label(frame_right, text="Оберіть абонемент:").pack(pady=2)
        self.combo_memberships = ttk.Combobox(frame_right, state="readonly", width=35)
        self.combo_memberships.pack(pady=2)

        tk.Button(frame_right, text="Оформити продаж", bg="#FF9800", fg="white", command=self.sell_membership).pack(
            pady=10)

        # --- НОВИЙ СЕРЕДНІЙ БЛОК: ЗАПИС НА ТРЕНУВАННЯ (З ФІКСОМ ВІДОБРАЖЕННЯ) ---
        middle_frame = tk.LabelFrame(self.tab_registry, text="📅 Запис клієнта на тренування",
                                     font=("Arial", 11, "bold"))
        middle_frame.pack(fill='x', padx=10, pady=5)

        # Рядок 1: Пошук та вибір активного клієнта
        row1 = tk.Frame(middle_frame)
        row1.pack(fill='x', padx=5, pady=5)

        tk.Label(row1, text="🔍 Пошук:").pack(side='left', padx=(5, 5))
        self.entry_enroll_search = tk.Entry(row1, width=20)
        self.entry_enroll_search.pack(side='left', padx=5)
        self.entry_enroll_search.bind('<KeyRelease>', lambda e: self.refresh_enroll_clients_list())

        tk.Label(row1, text="Клієнт:").pack(side='left', padx=(15, 5))
        self.combo_enroll_client = ttk.Combobox(row1, state="readonly")
        self.combo_enroll_client.pack(side='left', expand=True, fill='x', padx=5)
        # Рядок 2: Вибір тренування та кнопка запису
        row2 = tk.Frame(middle_frame)
        row2.pack(fill='x', padx=5, pady=5)

        tk.Label(row2, text="Тренування:").pack(side='left', padx=5)
        self.combo_enroll_schedule = ttk.Combobox(row2, state="readonly")
        self.combo_enroll_schedule.pack(side='left', expand=True, fill='x', padx=5)

        # Кнопка притиснута до правого краю, щоб точно не загубилася
        tk.Button(row2, text="✅ Записати", bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                  command=self.enroll_client).pack(side='right', padx=10)

        # --- НИЖНЯ ЧАСТИНА: ПОШУК ТА VIP-СТАТУС (БЕЗ ЗМІН) ---
        bottom_frame = tk.LabelFrame(self.tab_registry, text="База клієнтів (Пошук та Система Лояльності)",
                                     font=("Arial", 11, "bold"))
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=5)

        search_frame = tk.Frame(bottom_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        tk.Button(search_frame, text="🗑 Відправити в архів", bg="#FF9800", fg="white",
                  command=self.archive_client).pack(side='left', padx=15)

        tk.Label(search_frame, text="Пошук (ПІБ або Телефон):").pack(side='left', padx=5)
        self.entry_search = tk.Entry(search_frame, width=30)
        self.entry_search.pack(side='left', padx=5)
        tk.Button(search_frame, text="Знайти", bg="#2196F3", fg="white", command=self.search_clients).pack(side='left',
                                                                                                           padx=5)
        tk.Button(search_frame, text="Показати всіх", command=self.load_all_clients).pack(side='left', padx=5)

        cols = ('id', 'name', 'phone', 'spent', 'vip')
        self.tree_clients = ttk.Treeview(bottom_frame, columns=cols, show='headings', height=5)
        self.tree_clients.heading('id', text='ID', command=lambda: self.sort_treeview(self.tree_clients, 'id', False))
        self.tree_clients.heading('name', text='ПІБ Клієнта',
                                  command=lambda: self.sort_treeview(self.tree_clients, 'name', False))
        self.tree_clients.heading('phone', text='Телефон')
        self.tree_clients.heading('spent', text='Сума покупок (грн)',
                                  command=lambda: self.sort_treeview(self.tree_clients, 'spent', True))
        self.tree_clients.heading('vip', text='Статус',
                                  command=lambda: self.sort_treeview(self.tree_clients, 'vip', False))

        self.tree_clients.column('id', width=40, anchor='center')
        self.tree_clients.column('name', width=250, anchor='w')
        self.tree_clients.column('phone', width=120, anchor='center')
        self.tree_clients.column('spent', width=120, anchor='center')
        self.tree_clients.column('vip', width=80, anchor='center')

        self.tree_clients.pack(fill='both', expand=True, padx=5, pady=5)

        self.refresh_manager_comboboxes()
        self.refresh_enrollment_data()
        self.load_all_clients()

        # Ініціалізуємо наші нові списки
        self.refresh_sale_clients_list()
        self.refresh_enroll_clients_list()

    def refresh_sale_clients_list(self, event=None):
        """Живий пошук клієнтів для поля продажу"""
        mode = self.sale_client_mode.get()
        search_val = self.entry_sale_search.get().strip()

        query = "SELECT id_client, full_name, phone FROM Clients WHERE is_active = %s"
        params = [mode]
        if search_val:
            query += " AND (full_name LIKE %s OR phone LIKE %s)"
            params.extend([f"%{search_val}%", f"%{search_val}%"])
        query += " ORDER BY full_name"

        clients = self.db.fetch_data(query, tuple(params))
        if clients:
            self.combo_clients['values'] = [f"{c['id_client']} - {c['full_name']} ({c['phone']})" for c in clients]
        else:
            self.combo_clients['values'] = ["Клієнтів не знайдено"]
        self.combo_clients.set('')

    def refresh_enroll_clients_list(self, event=None):
        """Живий пошук клієнтів ТІЛЬКИ серед активних (для поля запису)"""
        search_val = self.entry_enroll_search.get().strip()

        # Завжди шукаємо тільки активних клієнтів
        query = "SELECT id_client, full_name, phone FROM Clients WHERE is_active = 1"
        params = []

        if search_val:
            query += " AND (full_name LIKE %s OR phone LIKE %s)"
            params.extend([f"%{search_val}%", f"%{search_val}%"])

        query += " ORDER BY full_name"

        clients = self.db.fetch_data(query, tuple(params))
        if clients:
            self.combo_enroll_client['values'] = [f"{c['id_client']} - {c['full_name']} ({c['phone']})" for c in
                                                  clients]
        else:
            self.combo_enroll_client['values'] = ["Клієнтів не знайдено"]

        self.combo_enroll_client.set('')

    # --- НОВІ ФУНКЦІЇ ДЛЯ ЗАПИСУ НА ТРЕНУВАННЯ ---
    def refresh_enrollment_data(self):
        """Завантажує клієнтів та майбутній розклад із вільними місцями"""
        clients = self.db.fetch_data("SELECT id_client, full_name, phone FROM Clients WHERE is_active = 1")
        if clients:
            self.combo_enroll_client['values'] = [f"{c['id_client']} - {c['full_name']}" for c in clients]

        query = """
            SELECT 
                s.id_schedule, s.class_date, s.start_time, 
                sec.section_name, sec.section_type, sec.capacity,
                s.id_trainer,
                (SELECT COUNT(*) FROM Attendance a WHERE a.id_schedule = s.id_schedule) as occupied
            FROM Schedule s
            JOIN Sections sec ON s.id_section = sec.id_section
            WHERE CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) >= NOW()
            ORDER BY s.class_date, s.start_time
        """
        sched_data = self.db.fetch_data(query)

        self.enroll_map = {}
        vals = []

        if sched_data:
            for row in sched_data:
                occ = row['occupied']
                cap = row.get('capacity', 1)
                text = f"{row['id_schedule']} - {row['section_name']} ({row['class_date']} {row['start_time']}) - Місць: ({occ}/{cap})"
                vals.append(text)
                self.enroll_map[row['id_schedule']] = {'sec_type': row['section_type'], 'occupied': row['occupied'],
                                                       'capacity': row['capacity'], 'trainer_id': row['id_trainer']}

        self.combo_enroll_schedule['values'] = vals

    def enroll_client(self):
        from tkinter import messagebox

        c_val = self.combo_enroll_client.get()
        s_val = self.combo_enroll_schedule.get()

        if not c_val or not s_val or "не знайдено" in c_val:
            return messagebox.showwarning("Увага", "Оберіть клієнта та тренування!")

        c_id = int(c_val.split(' - ')[0])
        s_id = int(s_val.split(' - ')[0])

        sched_info = self.enroll_map.get(s_id)
        if not sched_info: return

        sec_type = sched_info['sec_type']
        target_trainer_id = sched_info.get('trainer_id')

        # --- БЛОК 0: ПЕРЕВІРКА ЗАМОРОЗКИ ТА БАНУ ---
        check_status = self.db.fetch_data(
            "SELECT IF(freeze_until >= CURDATE(), 1, 0) as is_frozen, freeze_until, IF(group_blocked_until >= NOW(), 1, 0) as is_banned, group_blocked_until FROM Clients WHERE id_client = %s",
            (c_id,))
        if check_status:
            if check_status[0]['is_frozen']: return messagebox.showerror("❄️ Заморозка",
                                                                         f"Профіль заморожено до {check_status[0]['freeze_until']}!")
            if check_status[0]['is_banned']: return messagebox.showerror("🚨 Блокування",
                                                                         f"Клієнт заблокований до {check_status[0]['group_blocked_until']}!")
        # =========================================================
        # --- БЛОК 0.5: ПЕРЕВІРКА ВІКУ (Захист від дітей на дорослих секціях) ---
        sec_query = "SELECT sec.age_limit FROM Schedule s JOIN Sections sec ON s.id_section = sec.id_section WHERE s.id_schedule = %s"
        sec_data = self.db.fetch_data(sec_query, (s_id,))

        if sec_data:
            age_limit = int(sec_data[0]['age_limit'])
            if age_limit > 0:  # Якщо є обмеження
                client_data = self.db.fetch_data("SELECT birth_date FROM Clients WHERE id_client = %s", (c_id,))
                if client_data:
                    from datetime import datetime, date
                    b_date = client_data[0]['birth_date']

                    # Безпечне конвертування дати
                    birth_dt = datetime.strptime(b_date, '%Y-%m-%d').date() if isinstance(b_date, str) else b_date
                    today = date.today()

                    # Точний розрахунок віку
                    age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))

                    if age < age_limit:
                        return messagebox.showerror("Обмеження віку",
                                                    f"Клієнту лише {age} років!\nЗапис заборонено: ця секція дозволена з {age_limit} років.")
        # =========================================================

        # --- БЛОК 1: ПЕРЕВІРКА ВІЛЬНИХ МІСЦЬ ---
        if sched_info['occupied'] >= sched_info['capacity']:
            return messagebox.showerror("Немає місць", "Увага! На це тренування всі місця вже зайняті.")

        # --- БЛОК 2: ПЕРЕВІРКА НА ДУБЛІКАТ ---
        if self.db.fetch_data("SELECT * FROM Attendance WHERE id_schedule = %s AND id_client = %s", (s_id, c_id)):
            return messagebox.showerror("Помилка", "Цей клієнт вже записаний на дане тренування!")

        # =========================================================
        # --- БЛОК 2.5: ПЕРЕВІРКА НА НАКЛАДАННЯ ЧАСУ (Телепортація) ---
        overlap_query = """
                SELECT a.id_attendance 
                FROM Attendance a
                JOIN Schedule s ON a.id_schedule = s.id_schedule
                WHERE a.id_client = %s 
                  AND a.presence_status IN ('Записаний', 'Присутній', 'Присутній (вручну)')
                  AND s.class_date = (SELECT class_date FROM Schedule WHERE id_schedule = %s)
                  AND s.start_time = (SELECT start_time FROM Schedule WHERE id_schedule = %s)
                  AND s.id_schedule != %s
            """
        # Передаємо c_id та тричі s_id (для підзапитів дати, часу та виключення поточного заняття)
        if self.db.fetch_data(overlap_query, (c_id, s_id, s_id, s_id)):
            return messagebox.showerror("Накладання часу",
                                        "Клієнт не може бути у двох місцях одночасно!\nВін вже записаний на інше тренування на цей самий час.")
        # =========================================================

        # --- БЛОК 3: ПЕРЕВІРКА АБОНЕМЕНТА ---
        mem_query = "SELECT sl.id_sale, m.package_name, sl.classes_left, sl.id_trainer FROM Sales sl JOIN Memberships m ON sl.id_membership = m.id_membership WHERE sl.id_client = %s AND sl.classes_left > 0 AND sl.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY) ORDER BY sl.sale_date ASC"
        valid_mems = self.db.fetch_data(mem_query, (c_id,))

        if not valid_mems: return messagebox.showerror("Блок",
                                                       "У клієнта немає дійсних абонементів із залишками занять!")

        valid_sale_id = None
        wrong_trainer_name = None

        for mem in valid_mems:
            p_name = mem['package_name']
            is_valid_type = False
            if sec_type == 'Групова' and p_name in ['Групові + Тренажерний зал', 'Тільки групові', 'Разове (Групове)']:
                is_valid_type = True
            elif sec_type == 'Індивідуальна' and p_name in ['Разове (З тренером)']:
                if mem['id_trainer'] == target_trainer_id:
                    is_valid_type = True
                else:
                    t_data = self.db.fetch_data("SELECT full_name FROM Trainers WHERE id_trainer = %s",
                                                (mem['id_trainer'],))
                    if t_data: wrong_trainer_name = t_data[0]['full_name']
                    continue
            elif sec_type == 'ТЗ' and p_name in ['Групові + Тренажерний зал', 'Тренажерний зал']:
                is_valid_type = True

            if is_valid_type:
                valid_sale_id = mem['id_sale']
                break

        if not valid_sale_id:
            if wrong_trainer_name and sec_type == 'Індивідуальна':
                return messagebox.showerror("Доступ", f"Абонемент виписаний на іншого тренера ({wrong_trainer_name})!")
            else:
                return messagebox.showerror("Доступ", f"У клієнта немає абонемента для секції '{sec_type}'!")

        # --- БЛОК 4: ЗАПИС ТА АВТО-РОЗАРХІВУВАННЯ ---
        # ТУТ ЗМІНЕНО: Явно вказуємо статус 'Записаний'
        insert_query = "INSERT INTO Attendance (id_schedule, id_client, id_sale, presence_status) VALUES (%s, %s, %s, 'Записаний')"

        if self.db.execute_query(insert_query, (s_id, c_id, valid_sale_id)):
            self.db.execute_query("UPDATE Sales SET classes_left = classes_left - 1 WHERE id_sale = %s",
                                  (valid_sale_id,))

            # Перевіряємо, чи був він в архіві
            client_status = self.db.fetch_data("SELECT is_active FROM Clients WHERE id_client = %s", (c_id,))
            if client_status and client_status[0]['is_active'] == 0:
                self.db.execute_query("UPDATE Clients SET is_active = 1 WHERE id_client = %s", (c_id,))
                messagebox.showinfo("Відновлення",
                                    "Клієнта успішно записано!\n\nОскільки він був в архіві, його автоматично відновлено в базі активних клієнтів.")
                self.load_all_clients()
                self.refresh_sale_clients_list()  # Оновлюємо список продажів
            else:
                messagebox.showinfo("Успіх",
                                    "Клієнта успішно записано на тренування! Одне заняття списано з абонемента.")

            self.refresh_enrollment_data()
            self.refresh_enroll_clients_list()
            self.combo_enroll_schedule.set('')

    # ------------------------------------------------

    def load_all_clients(self):
        for row in self.tree_clients.get_children():
            self.tree_clients.delete(row)

        search_val = self.entry_search_client.get().strip() if hasattr(self, 'entry_search_client') else ""

        query = """
            SELECT c.id_client, c.full_name, c.phone, c.birth_date, c.is_vip,
                   COALESCE(SUM(s.total_paid), 0) as total_spent
            FROM Clients c
            LEFT JOIN Sales s ON c.id_client = s.id_client
            WHERE c.is_active = 1 
        """
        params = []
        if search_val:
            query += " AND (c.full_name LIKE %s OR c.phone LIKE %s)"
            params.extend([f"%{search_val}%", f"%{search_val}%"])

        query += " GROUP BY c.id_client, c.full_name, c.phone, c.birth_date, c.is_vip"

        clients = self.db.fetch_data(query, tuple(params))
        if clients:
            for c in clients:
                status = "🌟 VIP" if c['is_vip'] else "Стандарт"
                self.tree_clients.insert('', 'end',
                                         values=(c['id_client'], c['full_name'], c['phone'], f"{c['total_spent']:.2f}",
                                                 status))

    def archive_client(self):
        from tkinter import messagebox
        selected = self.tree_clients.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть клієнта зі списку!")

        c_id = self.tree_clients.item(selected[0])['values'][0]
        c_name = self.tree_clients.item(selected[0])['values'][1]

        # --- ПЕРЕВІРКА 1: ЧИ Є МАЙБУТНІ ТРЕНУВАННЯ? ---
        future_classes_query = """
            SELECT COUNT(*) as count 
            FROM Attendance a 
            JOIN Schedule s ON a.id_schedule = s.id_schedule 
            WHERE a.id_client = %s 
              AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) >= NOW()
        """
        future_check = self.db.fetch_data(future_classes_query, (c_id,))

        if future_check and future_check[0]['count'] > 0:
            return messagebox.showerror("Блокування",
                                        f"Клієнт '{c_name}' має заплановані тренування ({future_check[0]['count']} шт)!\n\nБудь ласка, скасуйте його записи перед архівацією.")

        # --- ПЕРЕВІРКА 2: ЧИ Є АКТИВНІ АБОНЕМЕНТИ? ---
        active_mem_query = """
            SELECT m.package_name, sl.classes_left 
            FROM Sales sl 
            JOIN Memberships m ON sl.id_membership = m.id_membership 
            WHERE sl.id_client = %s 
              AND sl.classes_left > 0 
              AND sl.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY)
        """
        mem_check = self.db.fetch_data(active_mem_query, (c_id,))

        if mem_check:
            mem_list = "\n".join([f"- {m['package_name']} (залишок: {m['classes_left']} занять)" for m in mem_check])
            return messagebox.showerror("Блокування",
                                        f"Клієнт '{c_name}' має діючі абонементи:\n\n{mem_list}\n\nНеможливо відправити в архів клієнта з активним балансом!")

        # --- АРХІВАЦІЯ (Якщо перевірки пройдені) ---
        if messagebox.askyesno("Підтвердження",
                               f"Ви впевнені, що хочете відправити клієнта '{c_name}' в архів?\n\nВін зникне зі списку активних клієнтів, але його можна буде відновити під час наступного запису."):
            if self.db.execute_query("UPDATE Clients SET is_active = 0 WHERE id_client = %s", (c_id,)):
                messagebox.showinfo("Успіх", "Клієнта перенесено в архів.")
                self.load_all_clients()

                # Оновлюємо випадаючі списки, щоб клієнт зник з них
                if hasattr(self, 'refresh_sale_clients_list'):
                    self.refresh_sale_clients_list()
                if hasattr(self, 'refresh_enroll_clients_list'):
                    self.refresh_enroll_clients_list()

    def refresh_clients_combobox(self):
        clients = self.db.fetch_data("SELECT id_client, full_name FROM Clients WHERE is_active = 1")
        if clients and hasattr(self, 'combo_clients'):
            self.combo_clients['values'] = [f"{c['id_client']} - {c['full_name']}" for c in clients]
            self.combo_clients.set('')

    def search_clients(self):
        search_term = self.entry_search.get().strip()
        if not search_term:
            self.load_all_clients()
            return

        query = """
            SELECT c.id_client, c.full_name, c.phone, COALESCE(SUM(s.total_paid), 0) as total_spent
            FROM Clients c
            LEFT JOIN Sales s ON c.id_client = s.id_client
            WHERE c.full_name LIKE %s OR c.phone LIKE %s
            GROUP BY c.id_client, c.full_name, c.phone
        """
        wildcard = f"%{search_term}%"
        self.populate_client_table(query, (wildcard, wildcard))

    def populate_client_table(self, query, params):
        for row in self.tree_clients.get_children():
            self.tree_clients.delete(row)

        data = self.db.fetch_data(query, params)
        if data:
            for row in data:
                spent = float(row['total_spent'])
                vip_status = "🌟 VIP" if spent >= 3000 else "Стандарт"
                self.tree_clients.insert('', 'end',
                                         values=(row['id_client'], row['full_name'], row['phone'], spent, vip_status))

    def register_client(self):
        import re
        from datetime import datetime
        from tkinter import messagebox

        name = self.entry_client_name.get().strip()
        raw_phone = self.entry_client_phone.get().strip()
        birth = self.entry_client_birth.get().strip()
        login = self.entry_client_login.get().strip()
        password = self.entry_client_pass.get().strip()

        if not name or not raw_phone or not birth or not login or not password:
            messagebox.showwarning("Увага", "Заповніть всі поля!")
            return

        # ========================================================
        # --- РОЗУМНА ВАЛІДАЦІЯ ТА НОРМАЛІЗАЦІЯ ТЕЛЕФОНУ ---
        # ========================================================
        # 1. Залишаємо тільки цифри та знак '+'
        cleaned_phone = re.sub(r'[^\d+]', '', raw_phone)
        formatted_phone = None

        # 2. Аналізуємо та приводимо до стандарту +380...
        if cleaned_phone.startswith('0') and len(cleaned_phone) == 10 and cleaned_phone.isdigit():
            formatted_phone = f"+38{cleaned_phone}"
        elif cleaned_phone.startswith('380') and len(cleaned_phone) == 12 and cleaned_phone.isdigit():
            formatted_phone = f"+{cleaned_phone}"
        elif cleaned_phone.startswith('+380') and len(cleaned_phone) == 13 and cleaned_phone[1:].isdigit():
            formatted_phone = cleaned_phone

        # Якщо формат або код оператора неправильний - зупиняємо реєстрацію
        if not formatted_phone or not self.is_valid_phone(formatted_phone):
            return messagebox.showerror(
                "Помилка формату",
                "Неправильний формат телефону!\n\nДозволено лише український мобільний номер із коректним кодом оператора, наприклад:\n+380971234567\n0971234567"
            )
        # ========================================================

        if not self.is_valid_date(birth):
            messagebox.showerror("Помилка", "Дата народження має бути у форматі РРРР-ММ-ДД (наприклад, 1995-05-25)")
            return

        try:
            birth_dt = datetime.strptime(birth, '%Y-%m-%d').date()
            if birth_dt > datetime.today().date():
                messagebox.showerror("Помилка", "Клієнт ще не народився! Ви ввели дату з майбутнього.")
                return
        except ValueError:
            messagebox.showerror("Помилка", "Некоректна дата народження!")
            return

        # =========================================================
        # --- ПЕРЕВІРКА НА ДУБЛІКАТИ ДО ЗБЕРЕЖЕННЯ ---
        # =========================================================
        # 1. Перевірка логіна
        existing_user = self.db.fetch_data("SELECT id_user FROM Users WHERE username = %s", (login,))
        if existing_user:
            return messagebox.showerror("Помилка", "Такий логін вже існує! Оберіть інший.")

        # 2. Перевірка телефону (ВИКОРИСТОВУЄМО ВЖЕ НОРМАЛІЗОВАНИЙ НОМЕР)
        existing_phone = self.db.fetch_data("SELECT id_client FROM Clients WHERE phone = %s", (formatted_phone,))
        if existing_phone:
            return messagebox.showerror("Помилка", f"Клієнт з номером {formatted_phone} вже зареєстрований у базі!")
        # =========================================================

        # Якщо перевірки пройдені, зберігаємо користувача
        query_user = "INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, 'Client')"
        if self.db.execute_query(query_user, (login, password)):

            user_record = self.db.fetch_data("SELECT id_user FROM Users WHERE username = %s", (login,))
            if not user_record:
                return messagebox.showerror("Помилка", "Не вдалося отримати ID нового користувача.")

            new_user_id = user_record[0]['id_user']

            # ЗБЕРІГАЄМО КЛІЄНТА З НОРМАЛІЗОВАНИМ ТЕЛЕФОНОМ (formatted_phone)
            query_client = "INSERT INTO Clients (full_name, phone, birth_date, id_user) VALUES (%s, %s, %s, %s)"
            if self.db.execute_query(query_client, (name, formatted_phone, birth, new_user_id)):
                messagebox.showinfo("Успіх", "Клієнта успішно зареєстровано!")

                # Оновлюємо списки
                if hasattr(self, 'refresh_manager_comboboxes'):
                    self.refresh_manager_comboboxes()
                if hasattr(self, 'refresh_enrollment_data'):
                    self.refresh_enrollment_data()
                if hasattr(self, 'load_all_clients'):
                    self.load_all_clients()

                # Оновлюємо нові списки з "Живим пошуком", які ми додали в попередньому кроці!
                if hasattr(self, 'refresh_sale_clients_list'):
                    self.refresh_sale_clients_list()
                if hasattr(self, 'refresh_enroll_clients_list'):
                    self.refresh_enroll_clients_list()

                # --- Очищуємо поля форми після успіху ---
                self.entry_client_name.delete(0, 'end')
                self.entry_client_phone.delete(0, 'end')
                self.entry_client_birth.delete(0, 'end')
                self.entry_client_login.delete(0, 'end')
                self.entry_client_pass.delete(0, 'end')

            else:
                # Якщо клієнта не вдалося створити, видаляємо його логін, щоб не було "сиріт"
                self.db.execute_query("DELETE FROM Users WHERE id_user = %s", (new_user_id,))
                messagebox.showerror("Помилка", "Помилка бази даних при створенні профілю!")
        else:
            messagebox.showerror("Помилка", "Не вдалося створити користувача.")

    def refresh_manager_comboboxes(self):
        clients = self.db.fetch_data("SELECT id_client, full_name, phone FROM Clients")
        if clients:
            self.combo_clients['values'] = [f"{c['id_client']} - {c['full_name']} ({c['phone']})" for c in clients]
        memberships = self.db.fetch_data("SELECT id_membership, package_name, price FROM Memberships")
        if memberships:
            self.combo_memberships['values'] = [f"{m['id_membership']} - {m['package_name']} ({m['price']} грн)" for
                                                m in memberships]

    def sell_membership(self):
        from tkinter import messagebox

        selected_client = self.combo_clients.get()
        selected_membership = self.combo_memberships.get()

        if not selected_client or not selected_membership or "не знайдено" in selected_client:
            return messagebox.showwarning("Увага", "Оберіть клієнта та абонемент!")

        client_id = int(selected_client.split(' - ')[0])
        membership_id = int(selected_membership.split(' - ')[0])
        base_price = float(selected_membership.split('(')[-1].replace(' грн)', ''))

        mem_data = self.db.fetch_data("SELECT package_name FROM Memberships WHERE id_membership = %s", (membership_id,))
        if not mem_data: return

        selected_mem_name = mem_data[0]['package_name']

        # --- БЛОК 0: САНКЦІЇ ---
        check_status = self.db.fetch_data(
            "SELECT IF(freeze_until >= CURDATE(), 1, 0) as is_frozen, freeze_until, IF(group_blocked_until >= NOW(), 1, 0) as is_banned, group_blocked_until FROM Clients WHERE id_client = %s",
            (client_id,))
        if check_status:
            if check_status[0]['is_frozen']: return messagebox.showerror("❄️ Заморозка",
                                                                         f"Профіль заморожено до {check_status[0]['freeze_until']}.")
            group_mems = ['Групові + Тренажерний зал', 'Тільки групові', 'Разове (Групове)']
            if selected_mem_name in group_mems and check_status[0]['is_banned']: return messagebox.showerror(
                "🚨 Блокування", "Клієнт заблокований для групових занять.")

        # --- БЛОК 1: ДУБЛЮВАННЯ АБОНЕМЕНТІВ ---
        big_memberships = ['Групові + Тренажерний зал', 'Тільки групові', 'Тільки тренажерний зал']
        if selected_mem_name in big_memberships:
            active_big = self.db.fetch_data(
                "SELECT m.package_name FROM Sales s JOIN Memberships m ON s.id_membership = m.id_membership WHERE s.id_client = %s AND m.package_name IN ('Групові + Тренажерний зал', 'Тільки групові', 'Тільки тренажерний зал') AND s.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(s.frozen_days, 0)) DAY)",
                (client_id,))
            if active_big: return messagebox.showerror("Блок продажу",
                                                       f"У клієнта вже є активний абонемент: «{active_big[0]['package_name']}»!")

        if selected_mem_name == 'Разове (Групове)':
            active_group_mem = self.db.fetch_data(
                "SELECT m.package_name, s.classes_left FROM Sales s JOIN Memberships m ON s.id_membership = m.id_membership WHERE s.id_client = %s AND m.package_name IN ('Групові + Тренажерний зал', 'Тільки групові') AND s.classes_left > 0 AND s.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(s.frozen_days, 0)) DAY)",
                (client_id,))
            if active_group_mem: return messagebox.showerror("Блок продажу",
                                                             f"Ще є активний абонемент «{active_group_mem[0]['package_name']}» ({active_group_mem[0]['classes_left']} занять).")

        if selected_mem_name in ['Групові + Тренажерний зал', 'Тільки групові']:
            active_single = self.db.fetch_data(
                "SELECT m.package_name FROM Sales s JOIN Memberships m ON s.id_membership = m.id_membership WHERE s.id_client = %s AND m.package_name = 'Разове (Групове)' AND s.classes_left > 0 AND s.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(s.frozen_days, 0)) DAY)",
                (client_id,))
            if active_single: return messagebox.showerror("Блок продажу",
                                                          "У клієнта ще є невикористане «Разове (Групове)» тренування!")

        # --- БЛОК 1.7: ЗАБОРОНА КУПІВЛІ РАЗОВОГО ТЗ, ЯКЩО Є АКТИВНИЙ АБОНЕМЕНТ У ЗАЛ ---
        # УВАГА: Заміни 'Разове (Тренажерний зал)' на точну назву твого разового абонемента з бази даних!
        if selected_mem_name == 'Разове (Самостійно зал)':
            check_gym_query = """
                    SELECT m.package_name, s.classes_left 
                    FROM Sales s
                    JOIN Memberships m ON s.id_membership = m.id_membership
                    WHERE s.id_client = %s
                      AND m.package_name IN ('Групові + Тренажерний зал', 'Тільки тренажерний зал', 'Тренажерний зал')
                      AND s.classes_left > 0
                      AND s.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(frozen_days, 0)) DAY)
                """
            active_gym_mem = self.db.fetch_data(check_gym_query, (client_id,))

            if active_gym_mem:
                return messagebox.showerror("Блок продажу",
                                            f"У клієнта ще є активний абонемент «{active_gym_mem[0]['package_name']}» із доступом до залу ({active_gym_mem[0]['classes_left']} занять).\n\nКупівля разового відвідування ТЗ заборонена!")

        # --- БЛОК 1.8: ЗАБОРОНА КУПІВЛІ "ВЕЛИКОГО" АБОНЕМЕНТА В ЗАЛ, ЯКЩО Є АКТИВНЕ РАЗОВЕ В ТЗ ---
        if selected_mem_name in ['Групові + Тренажерний зал', 'Тільки тренажерний зал']:
            check_single_gym_query = """
                    SELECT m.package_name, s.classes_left 
                    FROM Sales s
                    JOIN Memberships m ON s.id_membership = m.id_membership
                    WHERE s.id_client = %s
                      AND m.package_name = 'Разове (Самостійно зал)'
                      AND s.classes_left > 0
                      AND s.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(frozen_days, 0)) DAY)
                """
            active_single_gym = self.db.fetch_data(check_single_gym_query, (client_id,))

            if active_single_gym:
                return messagebox.showerror("Блок продажу",
                                            f"У клієнта ще є невикористане «{active_single_gym[0]['package_name']}»!\n\nКупівля місячного абонемента з тренажерним залом заборонена, поки не вичерпано разовий ліміт.")

        # --- ФУНКЦІЯ АВТО-РОЗАРХІВУВАННЯ ---
        def restore_client_if_archived():
            c_status = self.db.fetch_data("SELECT is_active FROM Clients WHERE id_client = %s", (client_id,))
            if c_status and c_status[0]['is_active'] == 0:
                self.db.execute_query("UPDATE Clients SET is_active = 1 WHERE id_client = %s", (client_id,))
                messagebox.showinfo("Відновлення",
                                    "Клієнт був в архіві. Після купівлі його автоматично відновлено в активну базу!")
                self.load_all_clients()
                self.refresh_enroll_clients_list()
                self.refresh_sale_clients_list()

        # --- БЛОК 2: ІНДИВІДУАЛЬНІ ---
        if selected_mem_name == 'Разове (З тренером)':
            trainers = self.db.fetch_data("SELECT id_trainer, full_name, indiv_rate FROM Trainers")
            if not trainers: return messagebox.showerror("Помилка", "В базі немає тренерів!")

            dialog = tk.Toplevel(self.root)
            dialog.title("Оберіть тренера")
            dialog.geometry("350x150")
            tk.Label(dialog, text="До якого тренера йде клієнт?").pack(pady=10)

            from tkinter import ttk
            combo_tr = ttk.Combobox(dialog, state="readonly", width=40,
                                    values=[f"{t['id_trainer']} - {t['full_name']} ({t['indiv_rate']} грн)" for t in
                                            trainers])
            combo_tr.pack(pady=5)

            def confirm_sale():
                if not combo_tr.get(): return
                tr_val = combo_tr.get()
                tr_id = int(tr_val.split(' - ')[0])
                trainer_rate = float(tr_val.split('(')[-1].replace(' грн)', ''))

                client_data = self.db.fetch_data("SELECT birth_date FROM Clients WHERE id_client = %s", (client_id,))
                if client_data:
                    from datetime import datetime, date
                    b_date = client_data[0]['birth_date']
                    birth_dt = datetime.strptime(b_date, '%Y-%m-%d').date() if isinstance(b_date, str) else b_date
                    today = date.today()
                    client_age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))

                    age_check_query = """
                        SELECT sec.age_limit
                        FROM Sections sec
                        JOIN Schedule s ON sec.id_section = s.id_section
                        WHERE s.id_trainer = %s
                          AND sec.section_type = 'Індивідуальна'
                        GROUP BY sec.id_section, sec.age_limit
                    """
                    trainer_sections = self.db.fetch_data(age_check_query, (tr_id,)) or []

                    has_suitable_section = any(client_age >= int(sec['age_limit']) for sec in trainer_sections)
                    if not has_suitable_section:
                        return messagebox.showerror(
                            "Увага!",
                            "У цього тренера немає індивідуальних тренувань, які підходять клієнту за віком. Оберіть іншого фахівця"
                        )

                dialog.destroy()

                restore_client_if_archived()  # Розархівуємо
                self._process_sale(client_id, membership_id, trainer_rate, trainer_id=tr_id)

            tk.Button(dialog, text="Підтвердити", bg="#FF9800", fg="white", command=confirm_sale).pack(pady=10)
            return

        # Звичайний абонемент
        restore_client_if_archived()  # Розархівуємо
        self._process_sale(client_id, membership_id, base_price, trainer_id=None)

    def _process_sale(self, client_id, membership_id, base_price, trainer_id=None):
        limit_data = self.db.fetch_data("SELECT visits_limit FROM Memberships WHERE id_membership = %s",
                                        (membership_id,))
        classes_left = int(limit_data[0]['visits_limit']) if limit_data else 1

        vip_data = self.db.fetch_data(
            "SELECT COALESCE(SUM(total_paid), 0) as total_spent FROM Sales WHERE id_client = %s", (client_id,))
        total_spent = float(vip_data[0]['total_spent']) if vip_data else 0.0

        discount = 10 if total_spent >= 3000 else 0
        final_price = base_price - (base_price * (discount / 100))

        if self.db.execute_query(
                "INSERT INTO Sales (id_client, id_membership, sale_date, total_paid, classes_left, id_trainer) VALUES (%s, %s, CURDATE(), %s, %s, %s)",
                (client_id, membership_id, final_price, classes_left, trainer_id)):

            if total_spent + final_price >= 3000:
                self.db.execute_query("UPDATE Clients SET is_vip = 1 WHERE id_client = %s", (client_id,))

            msg = f"Продаж оформлено зі знижкою {discount}%!\nДо сплати: {final_price:.2f} грн.\nНараховано занять: {classes_left}" if discount > 0 else f"Продаж оформлено!\nДо сплати: {final_price:.2f} грн.\nНараховано занять: {classes_left}"

            from tkinter import messagebox
            messagebox.showinfo("Успіх", msg)
            self.load_all_clients()

            # Оновлюємо дані, бо змінилися залишки в абонементах
            self.refresh_enrollment_data()

    # ==========================================
    # 5. ТРЕНЕР: ЖУРНАЛ ВІДВІДУВАНЬ
    # ==========================================
    def load_trainer_schedule(self):
        tk.Label(self.tab_schedule, text="Мій розклад на найближчі дні:", font=("Arial", 14, "bold")).pack(pady=5)
        btn_frame = tk.Frame(self.tab_schedule)
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame, text="Відкрити журнал заняття", bg="#2196F3", fg="white", width=25,
                  command=self.open_trainer_journal).pack(side='left')

        columns = ('id', 'date', 'time', 'section')
        self.tree_trainer = ttk.Treeview(self.tab_schedule, columns=columns, show='headings')
        self.tree_trainer.heading('id', text='ID')
        self.tree_trainer.heading('date', text='Дата заняття')
        self.tree_trainer.heading('time', text='Час початку')
        self.tree_trainer.heading('section', text='Секція')
        self.tree_trainer.column('id', width=40, anchor='center')
        self.tree_trainer.pack(expand=True, fill='both', padx=10, pady=5)
        self.refresh_trainer_schedule()

    def refresh_trainer_schedule(self):
        for row in self.tree_trainer.get_children():
            self.tree_trainer.delete(row)
        t_query = "SELECT id_trainer FROM Trainers t JOIN Users u ON t.id_user = u.id_user WHERE u.username = %s"
        t_data = self.db.fetch_data(t_query, (self.username,))
        if t_data:
            t_id = t_data[0]['id_trainer']
            sched_query = "SELECT s.id_schedule, s.class_date, s.start_time, sec.section_name FROM Schedule s JOIN Sections sec ON s.id_section = sec.id_section WHERE s.id_trainer = %s AND s.class_date >= CURDATE() ORDER BY s.class_date, s.start_time"
            schedule = self.db.fetch_data(sched_query, (t_id,))
            if schedule:
                for row in schedule:
                    self.tree_trainer.insert('', 'end',
                                             values=(row['id_schedule'], row['class_date'], row['start_time'],
                                                     row['section_name']))

    def open_trainer_journal(self):
        from tkinter import messagebox
        from datetime import datetime, date

        sel = self.tree_trainer.selection()
        if not sel:
            messagebox.showwarning("Увага", "Оберіть заняття зі списку!")
            return

        s_id = self.tree_trainer.item(sel[0])['values'][0]

        # ЗМІНА: Додали s.class_date та s.start_time у запит
        sec_query = """
            SELECT s.class_date, s.start_time, sec.age_limit, sec.section_type, sec.capacity 
            FROM Schedule s 
            JOIN Sections sec ON s.id_section = sec.id_section 
            WHERE s.id_schedule = %s
        """
        sec_info = self.db.fetch_data(sec_query, (s_id,))[0]

        age_limit = int(sec_info['age_limit'])
        sec_type = sec_info['section_type']
        capacity = int(sec_info.get('capacity', 1))

        # Витягуємо дату і час для перевірки
        class_date = sec_info['class_date']
        start_time = sec_info['start_time']

        dialog = tk.Toplevel(self.root)
        dialog.geometry("600x650")  # Трішки збільшили вікно, щоб вліз гарний список пошуку
        dialog.title(f"Журнал (Місць: {capacity} | Вік від {age_limit} р.)")

        # --- НОВИЙ БЛОК: ЗАХИСТ ВІД ЯСНОВИДЦІВ (Часовий запобіжник) ---
        # Форматуємо час для порівняння
        if isinstance(class_date, str):
            class_dt_str = f"{class_date} {start_time}"
            class_datetime = datetime.strptime(class_dt_str,
                                               "%Y-%m-%d %H:%M:%S" if len(str(start_time)) > 5 else "%Y-%m-%d %H:%M")
        else:
            class_dt_str = f"{class_date} {start_time}"
            class_datetime = datetime.strptime(class_dt_str, "%Y-%m-%d %H:%M:%S")

        def is_class_started():
            """Перевіряє, чи вже настав час тренування"""
            if datetime.now() < class_datetime:
                messagebox.showwarning("Зарано!",
                                       f"Це заняття ще не почалося!\nВоно заплановане на {class_datetime.strftime('%H:%M')}.\n\nПерекличка та ручне додавання клієнтів будуть доступні лише після початку тренування.",
                                       parent=dialog)
                return False
            return True

        # ----------------------------------------------------------------

        # --- ТАБЛИЦЯ ВЖЕ ЗАПИСАНИХ КЛІЄНТІВ ---
        tk.Label(dialog, text="Записані клієнти:", font=("Arial", 10, "bold")).pack(pady=5)

        cols = ('id', 'client_name', 'status')
        tree_att = ttk.Treeview(dialog, columns=cols, show='headings', height=6)
        tree_att.heading('id', text='ID')
        tree_att.heading('client_name', text='ПІБ')
        tree_att.heading('status', text='Статус')
        tree_att.column('id', width=30, anchor='center')
        tree_att.column('client_name', width=250, anchor='w')
        tree_att.column('status', width=120, anchor='center')
        tree_att.pack(fill='x', padx=10, pady=5)

        def load_att():
            for r in tree_att.get_children(): tree_att.delete(r)

            query = """
                SELECT c.id_client, c.full_name, COALESCE(a.presence_status, 'Записаний') as p_status
                FROM Attendance a 
                JOIN Clients c ON a.id_client = c.id_client 
                WHERE a.id_schedule = %s
            """
            for r in self.db.fetch_data(query, (s_id,)):
                tree_att.insert('', 'end', values=(r['id_client'], r['full_name'], r['p_status']))

        load_att()

        # --- КНОПКИ КЕРУВАННЯ ВЖЕ ЗАПИСАНИМИ ---
        btn_frame_att = tk.Frame(dialog)
        btn_frame_att.pack(pady=5)

        def confirm_presence():
            if not is_class_started(): return  # <--- БЛОКУВАННЯ

            sel = tree_att.selection()
            if not sel: return messagebox.showwarning("Увага", "Оберіть клієнта зі списку вище!", parent=dialog)
            c_id = tree_att.item(sel[0])['values'][0]
            self.db.execute_query(
                "UPDATE Attendance SET presence_status = 'Присутній' WHERE id_schedule = %s AND id_client = %s",
                (s_id, c_id))
            load_att()

        def no_show_penalty():
            if not is_class_started(): return  # <--- БЛОКУВАННЯ

            sel = tree_att.selection()
            if not sel: return messagebox.showwarning("Увага", "Оберіть клієнта зі списку вище!", parent=dialog)
            c_id = tree_att.item(sel[0])['values'][0]

            if messagebox.askyesno("Штраф",
                                   "Клієнт не з'явився?\n\nВін отримає бан на 7 днів, а його майбутні записи на цей тиждень будуть скасовані.\nПродовжити?",
                                   parent=dialog):
                # 1. Відмічаємо як "Не з'явився" (ВИПРАВЛЕНО: передаємо статус через %s)
                self.db.execute_query(
                    "UPDATE Attendance SET presence_status = %s WHERE id_schedule = %s AND id_client = %s",
                    ("Не з'явився", s_id, c_id))

                # 2. Видаємо бан
                self.db.execute_query(
                    "UPDATE Clients SET group_blocked_until = DATE_ADD(NOW(), INTERVAL 7 DAY) WHERE id_client = %s",
                    (c_id,))

                # 3. Каскадне скасування майбутніх тренувань
                future_query = """
                    SELECT a.id_schedule, sec.section_type 
                    FROM Attendance a JOIN Schedule s ON a.id_schedule = s.id_schedule JOIN Sections sec ON s.id_section = sec.id_section
                    WHERE a.id_client = %s AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) > NOW()
                      AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) <= DATE_ADD(NOW(), INTERVAL 7 DAY)
                """
                futures = self.db.fetch_data(future_query, (c_id,))
                if futures:
                    for f in futures:
                        self.db.execute_query("DELETE FROM Attendance WHERE id_schedule = %s AND id_client = %s",
                                              (f['id_schedule'], c_id))
                        # Повертаємо заняття
                        active_mems = self.db.fetch_data(
                            "SELECT id_sale, classes_left FROM Sales WHERE id_client = %s ORDER BY sale_date DESC",
                            (c_id,))
                        if active_mems: self.db.execute_query(
                            "UPDATE Sales SET classes_left = classes_left + 1 WHERE id_sale = %s",
                            (active_mems[0]['id_sale'],))

                load_att()
                messagebox.showinfo("Штраф", "Клієнта оштрафовано та заблоковано на 7 днів.", parent=dialog)

        tk.Button(btn_frame_att, text="✅ Підтвердити присутність", bg="#4CAF50", fg="white",
                  command=confirm_presence).pack(side='left', padx=5)
        tk.Button(btn_frame_att, text="❌ Не з'явився (Штраф)", bg="#f44336", fg="white", command=no_show_penalty).pack(
            side='left', padx=5)

        # ========================================================
        # --- НОВИЙ БЛОК: ЖИВИЙ ПОШУК КЛІЄНТІВ "З ВУЛИЦІ" ---
        # ========================================================
        tk.Frame(dialog, height=2, bd=1, relief="sunken").pack(fill="x", pady=10)  # Розділювач
        tk.Label(dialog, text="Додати клієнта вручну (Пошук за ПІБ або Телефоном):", font=("Arial", 10, "bold")).pack(
            pady=(0, 5))

        # Поле для вводу тексту
        entry_search_client = tk.Entry(dialog, width=50)
        entry_search_client.pack(pady=2)

        # Список результатів
        listbox_clients = tk.Listbox(dialog, width=60, height=6)
        listbox_clients.pack(pady=5)

        def search_clients_live(event=None):
            """Функція динамічного пошуку в базі"""
            search_text = entry_search_client.get().strip()
            listbox_clients.delete(0, tk.END)  # Очищаємо список

            if not search_text:
                query = "SELECT id_client, full_name, phone FROM Clients WHERE is_active = 1 LIMIT 30"
                results = self.db.fetch_data(query)
            else:
                query = """
                    SELECT id_client, full_name, phone 
                    FROM Clients 
                    WHERE is_active = 1 AND (full_name LIKE %s OR phone LIKE %s)
                    LIMIT 30
                """
                search_pattern = f"%{search_text}%"
                results = self.db.fetch_data(query, (search_pattern, search_pattern))

            if results:
                for row in results:
                    # Форматуємо рядок для красивого виводу
                    client_info = f"ID:{row['id_client']} | {row['full_name']} | {row['phone']}"
                    listbox_clients.insert(tk.END, client_info)
            else:
                listbox_clients.insert(tk.END, "Клієнтів не знайдено...")

        # Прив'язуємо подію: відпускання клавіші викликає пошук
        entry_search_client.bind('<KeyRelease>', search_clients_live)

        # Викликаємо один раз при відкритті вікна, щоб заповнити список
        search_clients_live()

        # ========================================================

        def mark_manual():
            if not is_class_started(): return  # <--- БЛОКУВАННЯ

            # --- ЗМІНЕНО: Беремо клієнта з Listbox замість Combobox ---
            selected_index = listbox_clients.curselection()
            if not selected_index:
                return messagebox.showwarning("Увага", "Оберіть клієнта зі списку результатів пошуку!", parent=dialog)

            selected_text = listbox_clients.get(selected_index)
            if "не знайдено" in selected_text:
                return

            try:
                # Витягуємо ID з формату "ID:12 | Іванов | +38..."
                c_id = int(selected_text.split('|')[0].replace('ID:', '').strip())
            except ValueError:
                return messagebox.showerror("Помилка", "Некоректний вибір клієнта.", parent=dialog)
            # -----------------------------------------------------------

            # 1. ПЕРЕВІРКА НА БЛОКУВАННЯ ТА ЗАМОРОЗКУ (Жорстка!)
            check_status = self.db.fetch_data(
                "SELECT IF(freeze_until >= CURDATE(), 1, 0) as is_frozen, IF(group_blocked_until >= NOW(), 1, 0) as is_banned, group_blocked_until FROM Clients WHERE id_client = %s",
                (c_id,))
            if check_status:
                if check_status[0]['is_frozen']:
                    return messagebox.showerror("Заморозка", "Цей клієнт заморозив свій абонемент! Вхід заборонено.",
                                                parent=dialog)
                if check_status[0]['is_banned']:
                    return messagebox.showerror("Блокування",
                                                f"🚨 Клієнт заблокований до {check_status[0]['group_blocked_until']} за пізню відписку або неявку!\n\nДопуск на тренування заборонено.",
                                                parent=dialog)

            # 2. ПЕРЕВІРКА НА ВІЛЬНІ МІСЦЯ
            count_data = self.db.fetch_data("SELECT COUNT(*) as total_clients FROM Attendance WHERE id_schedule = %s",
                                            (s_id,))
            if count_data and count_data[0]['total_clients'] >= capacity:
                return messagebox.showerror("Немає місць",
                                            f"Ліміт залу вичерпано ({capacity} з {capacity})!\nБільше клієнтів додати неможливо.",
                                            parent=dialog)

            # 3. ПЕРЕВІРКА ВІКУ
            client_data = self.db.fetch_data("SELECT birth_date FROM Clients WHERE id_client = %s", (c_id,))
            if client_data:
                birth_dt = datetime.strptime(client_data[0]['birth_date'], '%Y-%m-%d').date() if isinstance(
                    client_data[0]['birth_date'], str) else client_data[0]['birth_date']
                today = date.today()
                age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
                if age < age_limit: return messagebox.showerror("Вік",
                                                                f"Клієнту лише {age} років (дозволено з {age_limit}).",
                                                                parent=dialog)
            # =========================================================
            # --- 3.5 ПЕРЕВІРКА НА НАКЛАДАННЯ ЧАСУ ---
            overlap_query = """
                        SELECT a.id_attendance 
                        FROM Attendance a
                        JOIN Schedule s ON a.id_schedule = s.id_schedule
                        WHERE a.id_client = %s 
                          AND a.presence_status IN ('Записаний', 'Присутній', 'Присутній (вручну)')
                          AND s.class_date = %s
                          AND s.start_time = %s
                          AND s.id_schedule != %s
                    """
            # Тут class_date і start_time ми вже витягнули на початку вікна журналу
            if self.db.fetch_data(overlap_query, (c_id, class_date, start_time, s_id)):
                return messagebox.showerror("Накладання часу",
                                            "Клієнт вже відмічений або записаний на інше тренування у цей самий час!",
                                            parent=dialog)
            # =========================================================

            # 4. СПИСАННЯ З АБОНЕМЕНТА ТА ЗАПИС
            mem_query = "SELECT sl.id_sale, m.package_name, sl.classes_left, sl.id_trainer FROM Sales sl JOIN Memberships m ON sl.id_membership = m.id_membership WHERE sl.id_client = %s AND sl.classes_left > 0 AND sl.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY) ORDER BY sl.sale_date ASC"
            valid_mems = self.db.fetch_data(mem_query, (c_id,))
            if not valid_mems: return messagebox.showerror("Блок",
                                                           "У клієнта немає дійсних абонементів із залишками занять!",
                                                           parent=dialog)

            valid_sale_id = None

            t_query = "SELECT id_trainer FROM Schedule WHERE id_schedule = %s"
            t_data = self.db.fetch_data(t_query, (s_id,))
            target_trainer_id = t_data[0]['id_trainer'] if t_data else None

            for mem in valid_mems:
                p_name = mem['package_name']
                is_valid = False
                if sec_type == 'Групова' and p_name in ['Групові + Тренажерний зал', 'Тільки групові',
                                                        'Разове (Групове)']:
                    is_valid = True
                elif sec_type == 'Індивідуальна' and p_name in ['Разове (З тренером)']:
                    if mem['id_trainer'] == target_trainer_id:
                        is_valid = True
                elif sec_type == 'ТЗ' and p_name in ['Групові + Тренажерний зал', 'Тренажерний зал']:
                    is_valid = True
                if is_valid:
                    valid_sale_id = mem['id_sale']
                    break

            if not valid_sale_id: return messagebox.showerror("Доступ",
                                                              f"Немає абонемента для секції '{sec_type}' або абонемент оформлений на іншого тренера!",
                                                              parent=dialog)

            check_query = "SELECT * FROM Attendance WHERE id_schedule = %s AND id_client = %s"
            if self.db.fetch_data(check_query, (s_id, c_id)): return messagebox.showerror("Помилка",
                                                                                          "Клієнт вже у списку!",
                                                                                          parent=dialog)

            if self.db.execute_query(
                    "INSERT INTO Attendance (id_schedule, id_client, id_sale, presence_status) VALUES (%s, %s, %s, 'Присутній (вручну)')",
                    (s_id, c_id, valid_sale_id)):  # <-- Рівно 3 аргументи для 3-х %s

                self.db.execute_query("UPDATE Sales SET classes_left = classes_left - 1 WHERE id_sale = %s",
                                      (valid_sale_id,))
                load_att()

        tk.Button(dialog, text="Відмітити присутність", bg="#2196F3", fg="white", command=mark_manual).pack(pady=5)

    # ==========================================
    # 6. КЛІЄНТ: АБОНЕМЕНТИ, РОЗКЛАД, ВІДПИСКА ТА ЗАМОРОЗКА
    # ==========================================
    def load_client_data(self):
        # Очищуємо вкладку, якщо вона викликається повторно
        for widget in self.tab_client.winfo_children():
            widget.destroy()

        # --- ВЕРХНІЙ БЛОК: АБОНЕМЕНТИ ---
        tk.Label(self.tab_client, text="Мої активні абонементи:", font=("Arial", 14, "bold")).pack(pady=5)

        filter_frame = tk.Frame(self.tab_client)
        filter_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(filter_frame, text="Фільтр за датою купівлі:").pack(side='left')
        self.entry_client_date = tk.Entry(filter_frame, width=15)
        self.entry_client_date.pack(side='left', padx=5)
        tk.Button(filter_frame, text="🔍 Знайти", bg="#2196F3", fg="white", command=self.refresh_client_table).pack(
            side='left', padx=5)
        tk.Button(filter_frame, text="Всі", command=self.reset_client_filter).pack(side='left', padx=5)

        # Кнопка Заморозки
        tk.Button(filter_frame, text="❄️ Заморозити (на 7 днів)", bg="#00BCD4", fg="white", font=("Arial", 10, "bold"),
                  command=self.freeze_membership).pack(side='right', padx=10)

        columns = ('package', 'date', 'left', 'exp_date')
        self.tree_client = ttk.Treeview(self.tab_client, columns=columns, show='headings', height=4)
        self.tree_client.heading('package', text='Абонемент',
                                 command=lambda: self.sort_treeview(self.tree_client, 'package', False))
        self.tree_client.heading('date', text='Дата купівлі',
                                 command=lambda: self.sort_treeview(self.tree_client, 'date', False))
        self.tree_client.heading('left', text='Залишилось занять',
                                 command=lambda: self.sort_treeview(self.tree_client, 'left', True))
        self.tree_client.heading('exp_date', text='Діє до...')

        self.tree_client.column('package', width=250, anchor='w')
        self.tree_client.column('date', width=100, anchor='center')
        self.tree_client.column('left', width=120, anchor='center')
        self.tree_client.column('exp_date', width=100, anchor='center')
        self.tree_client.pack(fill='x', padx=10, pady=5)

        # --- НИЖНІЙ БЛОК: МАЙБУТНІ ТРЕНУВАННЯ ТА ВІДПИСКА ---
        sched_frame = tk.LabelFrame(self.tab_client, text="Мої майбутні тренування", font=("Arial", 12, "bold"))
        sched_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols_sched = ('id', 'date', 'time', 'section', 'trainer')
        self.tree_client_sched = ttk.Treeview(sched_frame, columns=cols_sched, show='headings')
        self.tree_client_sched.heading('id', text='ID')
        self.tree_client_sched.heading('date', text='Дата')
        self.tree_client_sched.heading('time', text='Час')
        self.tree_client_sched.heading('section', text='Секція')
        self.tree_client_sched.heading('trainer', text='Тренер')

        self.tree_client_sched.column('id', width=40, anchor='center')
        self.tree_client_sched.column('date', width=100, anchor='center')
        self.tree_client_sched.column('time', width=80, anchor='center')
        self.tree_client_sched.column('section', width=200, anchor='w')
        self.tree_client_sched.column('trainer', width=200, anchor='w')

        # ВИПРАВЛЕННЯ: Спочатку фіксуємо кнопку в самому низу (side='bottom')
        tk.Button(sched_frame, text="❌ Відписатися від тренування", bg="#f44336", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.cancel_class).pack(side='bottom', pady=10)

        # А вже потім пакуємо таблицю (side='top'), щоб вона зайняла простір МІЖ кнопкою і заголовком
        self.tree_client_sched.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        self.refresh_client_table()
        self.refresh_client_schedule()

    def reset_client_filter(self):
        self.entry_client_date.delete(0, tk.END)
        self.refresh_client_table()

    def get_current_client_id(self):
        """Допоміжна функція для швидкого отримання ID поточного клієнта"""
        c_query = "SELECT id_client FROM Clients c JOIN Users u ON c.id_user = u.id_user WHERE u.username = %s"
        c_data = self.db.fetch_data(c_query, (self.username,))
        return c_data[0]['id_client'] if c_data else None

    def refresh_client_table(self):
        for row in self.tree_client.get_children(): self.tree_client.delete(row)
        c_id = self.get_current_client_id()
        if not c_id: return

        date_filter = self.entry_client_date.get().strip()

        # --- ІДЕАЛЬНИЙ ЗАПИТ: Групуємо за назвою ТА датою купівлі ---
        mem_query = """
                    SELECT m.package_name, 
                           sl.sale_date, 
                           SUM(sl.classes_left) AS visits_left,
                           DATE_ADD(sl.sale_date, INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY) AS exp_date
                    FROM Sales sl 
                    JOIN Memberships m ON sl.id_membership = m.id_membership 
                    WHERE sl.id_client = %s 
                      AND sl.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY)
                      AND sl.classes_left > 0 
                """
        params = [c_id]

        if date_filter:
            mem_query += " AND sl.sale_date = %s "
            params.append(date_filter)

        # Групуємо за назвою, датою продажу та новою датою закінчення
        mem_query += " GROUP BY m.package_name, sl.sale_date, exp_date ORDER BY exp_date ASC"

        memberships = self.db.fetch_data(mem_query, tuple(params))

        if memberships:
            for row in memberships:
                self.tree_client.insert('', 'end', values=(
                    row['package_name'],
                    row['sale_date'],
                    int(row['visits_left']),
                    row['exp_date']
                ))

    def refresh_client_schedule(self):
        """Оновлює таблицю з майбутніми тренуваннями клієнта"""
        for row in self.tree_client_sched.get_children(): self.tree_client_sched.delete(row)
        c_id = self.get_current_client_id()
        if not c_id: return

        query = """
            SELECT s.id_schedule, s.class_date, s.start_time, sec.section_name, t.full_name 
            FROM Attendance a
            JOIN Schedule s ON a.id_schedule = s.id_schedule
            JOIN Sections sec ON s.id_section = sec.id_section
            JOIN Trainers t ON s.id_trainer = t.id_trainer
            WHERE a.id_client = %s 
              AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) >= NOW()
            ORDER BY s.class_date, s.start_time
        """
        sched_data = self.db.fetch_data(query, (c_id,))
        if sched_data:
            for row in sched_data:
                self.tree_client_sched.insert('', 'end',
                                              values=(row['id_schedule'], row['class_date'], row['start_time'],
                                                      row['section_name'], row['full_name']))

    def freeze_membership(self):
        """Логіка заморозки абонемента (з лімітом 1 раз на 30 днів) та каскадним скасуванням"""
        from tkinter import messagebox
        from datetime import date, datetime, timedelta

        c_id = self.get_current_client_id()
        if not c_id: return

        # --- 1. ПЕРЕВІРКА СТАТУСУ ТА ЛІМІТІВ ЗАМОРОЗКИ ---
        status_check = self.db.fetch_data("SELECT freeze_until, last_freeze_date FROM Clients WHERE id_client = %s",
                                          (c_id,))

        if status_check:
            if status_check[0]['freeze_until'] and status_check[0]['freeze_until'] >= date.today():
                return messagebox.showinfo("Увага",
                                           f"Ваш абонемент вже заморожено до {status_check[0]['freeze_until']}!")

            last_freeze = status_check[0]['last_freeze_date']
            if last_freeze:
                if isinstance(last_freeze, str):
                    last_freeze = datetime.strptime(last_freeze, '%Y-%m-%d').date()
                elif isinstance(last_freeze, datetime):
                    last_freeze = last_freeze.date()

                days_since_freeze = (date.today() - last_freeze).days
                if days_since_freeze < 30:
                    next_available = last_freeze + timedelta(days=30)
                    return messagebox.showerror(
                        "Ліміт вичерпано",
                        f"Ви вже використовували заморозку нещодавно!\n\nЗа правилами клубу, ставити абонемент на паузу можна лише 1 раз на 30 днів.\n\nНаступна заморозка буде доступна: {next_available.strftime('%d.%m.%Y')}"
                    )

        if messagebox.askyesno("Підтвердження",
                               "Заморозити абонемент на 7 днів?\n\nВсі ваші майбутні записи на цей період будуть скасовані, а заняття повернуться на баланс.\n\nУВАГА: Наступна заморозка буде доступна лише через 30 днів!"):

            # --- 2. ВСТАНОВЛЮЄМО ЗАМОРОЗКУ ТА ФІКСУЄМО ДАТУ ---
            self.db.execute_query(
                "UPDATE Clients SET freeze_until = DATE_ADD(CURDATE(), INTERVAL 7 DAY), last_freeze_date = CURDATE() WHERE id_client = %s",
                (c_id,)
            )

            # =========================================================
            # --- БЛОК 3: СПОЧАТКУ СКАСУВАННЯ ТА ПОВЕРНЕННЯ ЗАНЯТЬ ---
            # =========================================================
            future_query = """
                SELECT a.id_attendance, a.id_schedule, a.id_sale, sec.section_type, s.id_trainer 
                FROM Attendance a
                JOIN Schedule s ON a.id_schedule = s.id_schedule
                JOIN Sections sec ON s.id_section = sec.id_section
                WHERE a.id_client = %s 
                  AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) > NOW()
                  AND s.class_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            """
            futures = self.db.fetch_data(future_query, (c_id,))

            cancelled_count = 0
            if futures:
                for f in futures:
                    self.db.execute_query("DELETE FROM Attendance WHERE id_attendance = %s", (f['id_attendance'],))
                    if f['id_sale']:
                        self.db.execute_query("UPDATE Sales SET classes_left = classes_left + 1 WHERE id_sale = %s",
                                              (f['id_sale'],))

                    cancelled_count += 1

            # =========================================================
            # --- БЛОК 4: ПОТІМ ФІЗИЧНЕ ПРОДОВЖЕННЯ АБОНЕМЕНТІВ ---
            # =========================================================
            extend_query = """
                            UPDATE Sales sl
                            JOIN Memberships m ON sl.id_membership = m.id_membership
                            SET sl.frozen_days = COALESCE(sl.frozen_days, 0) + 7
                            WHERE sl.id_client = %s 
                              AND sl.classes_left > 0 
                              AND sl.sale_date >= DATE_SUB(CURDATE(), INTERVAL (m.duration_days + COALESCE(sl.frozen_days, 0)) DAY)
                        """
            self.db.execute_query(extend_query, (c_id,))
            # =========================================================

            # --- 5. ФІНАЛЬНЕ ПОВІДОМЛЕННЯ ---
            if cancelled_count > 0:
                messagebox.showinfo("Успіх",
                                    f"Абонемент успішно заморожено!\n\nСкасовано тренувань: {cancelled_count} шт. Заняття повернуті на ваш баланс і продовжені на 7 днів.")
            else:
                messagebox.showinfo("Успіх", "Ваш абонемент успішно заморожено на 7 днів!")

            if hasattr(self, 'load_client_schedule'):
                self.load_client_schedule()
            if hasattr(self, 'refresh_client_history'):
                self.refresh_client_history()

    def cancel_class(self):
        """Логіка відписки від тренування із жорсткими санкціями та КАСКАДНИМ СКАСУВАННЯМ"""
        selected = self.tree_client_sched.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть тренування зі списку!")

        item = self.tree_client_sched.item(selected[0])['values']
        s_id = item[0]
        c_id = self.get_current_client_id()

        sched_info = self.db.fetch_data("""
            SELECT s.class_date, s.start_time, sec.section_type, a.id_sale
            FROM Attendance a
            JOIN Schedule s ON a.id_schedule = s.id_schedule
            JOIN Sections sec ON s.id_section = sec.id_section 
            WHERE s.id_schedule = %s AND a.id_client = %s
        """, (s_id, c_id))

        if not sched_info: return

        class_date = sched_info[0]['class_date']
        start_time = sched_info[0]['start_time']
        sec_type = sched_info[0]['section_type']
        current_sale_id = sched_info[0]['id_sale']

        from datetime import datetime

        if isinstance(class_date, str):
            class_dt_str = f"{class_date} {start_time}"
            class_datetime = datetime.strptime(class_dt_str,
                                               "%Y-%m-%d %H:%M:%S" if len(str(start_time)) > 5 else "%Y-%m-%d %H:%M")
        else:
            class_dt_str = f"{class_date} {start_time}"
            class_datetime = datetime.strptime(class_dt_str, "%Y-%m-%d %H:%M:%S")

        time_diff = (class_datetime - datetime.now()).total_seconds() / 3600.0

        is_late_cancel = False
        warning_msg = "Ви дійсно хочете відписатися від цього тренування?\n\nМісце буде звільнено, а заняття повернеться на ваш абонемент."

        # --- ЗМІНЕНО: Прибрали обмеження "Тільки Групова". Тепер будь-яка пізня відписка карається! ---
        if time_diff < 2.0:
            is_late_cancel = True
            warning_msg = "🚨 УВАГА! ДО ТРЕНУВАННЯ МЕНШЕ 2 ГОДИН!\n\nЯкщо ви відпишетесь зараз:\n1. Заняття ЗГОРИТЬ.\n2. Ви отримаєте БЛОКУВАННЯ на 7 днів!\n3. Усі ваші записи на наступні 7 днів будуть скасовані (заняття за них повернуться).\n\nВи впевнені?"

        # --- Допоміжна функція для повернення заняття ---
        def return_class(sale_id):
            if sale_id:
                self.db.execute_query("UPDATE Sales SET classes_left = classes_left + 1 WHERE id_sale = %s",
                                      (sale_id,))

        if messagebox.askyesno("Відписка", warning_msg):
            # Видаляємо поточний запис
            self.db.execute_query("DELETE FROM Attendance WHERE id_schedule = %s AND id_client = %s", (s_id, c_id))

            if not is_late_cancel:
                # Звичайна завчасна відписка - просто повертаємо 1 заняття
                return_class(current_sale_id)
                messagebox.showinfo("Успіх", "Ви успішно відписалися. Заняття повернуто на ваш абонемент.")
            else:
                # 1. Блокуємо клієнта
                self.db.execute_query(
                    "UPDATE Clients SET group_blocked_until = DATE_ADD(NOW(), INTERVAL 7 DAY) WHERE id_client = %s",
                    (c_id,))

                # 2. КАСКАДНЕ СКАСУВАННЯ МАЙБУТНІХ ТРЕНУВАНЬ (протягом 7 днів бану)
                future_query = """
                    SELECT a.id_schedule, a.id_sale, sec.section_type 
                    FROM Attendance a
                    JOIN Schedule s ON a.id_schedule = s.id_schedule
                    JOIN Sections sec ON s.id_section = sec.id_section
                    WHERE a.id_client = %s 
                      AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) > NOW()
                      AND CAST(CONCAT(s.class_date, ' ', s.start_time) AS DATETIME) <= DATE_ADD(NOW(), INTERVAL 7 DAY)
                """
                futures = self.db.fetch_data(future_query, (c_id,))

                cancelled_count = 0
                if futures:
                    for f in futures:
                        # Видаляємо майбутній запис
                        self.db.execute_query("DELETE FROM Attendance WHERE id_schedule = %s AND id_client = %s",
                                              (f['id_schedule'], c_id))
                        # Повертаємо заняття за скасоване майбутнє тренування
                        return_class(f['id_sale'])
                        cancelled_count += 1

                msg = "Ви відписалися в останній момент. Заняття згоріло, профіль заблоковано на 7 днів."
                if cancelled_count > 0:
                    msg += f"\n\nАвтоматично скасовано {cancelled_count} ваших майбутніх тренувань (заняття повернуто на баланс)."

                messagebox.showwarning("Санкції застосовано", msg)

            self.refresh_client_table()
            self.refresh_client_schedule()

    # ==========================================
    # УНІВЕРСАЛЬНА ФУНКЦІЯ СОРТУВАННЯ ТАБЛИЦЬ
    # ==========================================
    def sort_treeview(self, tree, col, reverse):
        # Збираємо всі значення з колонки
        l = [(tree.set(k, col), k) for k in tree.get_children('')]

        try:
            # Намагаємося відсортувати як числа (для сум і ID)
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Якщо це текст, застосовуємо спеціальне українське сортування
            def ukr_sort_key(item):
                text = item[0].lower().strip()  # Переводимо все в маленькі літери
                # Штучно "садимо" українські літери на їхні правильні місця в Unicode
                text = text.replace('ґ', 'г~').replace('є', 'е~').replace('і', 'и~').replace('ї', 'и~~')
                return text

            l.sort(key=ukr_sort_key, reverse=reverse)

        # Переміщуємо рядки на нові місця
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)

        # Змінюємо напрямок для наступного кліку (від А до Я -> від Я до А)
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))


class LoginWindow(ResponsiveWindowMixin):
    def __init__(self, root):
        self.db = DatabaseManager()
        self.root = root
        self.root.title("Авторизація")
        self.root.geometry("350x330")  # Трохи збільшили висоту вікна
        self.root.resizable(True, True)

        tk.Label(self.root, text="Вхід у систему", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.root, text="Логін:", font=("Arial", 12)).pack(pady=5)
        self.entry_login = tk.Entry(self.root, font=("Arial", 12))
        self.entry_login.pack()

        tk.Label(self.root, text="Пароль:", font=("Arial", 12)).pack(pady=5)
        self.entry_password = tk.Entry(self.root, show="*", font=("Arial", 12))
        self.entry_password.pack()

        # --- НОВИЙ БЛОК: Чекбокс для пароля ---
        self.show_pwd_var = tk.BooleanVar()
        self.chk_show_pwd = tk.Checkbutton(self.root, text="Показати пароль", variable=self.show_pwd_var,
                                           command=self.toggle_password)
        self.chk_show_pwd.pack(pady=5)

        self.btn_login = tk.Button(self.root, text="Увійти", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                                   command=self.check_login)
        self.btn_login.pack(pady=15)
        self.init_responsive_ui(350, 330)

    def toggle_password(self):
        if self.show_pwd_var.get():
            self.entry_password.config(show="")  # Показуємо текст
        else:
            self.entry_password.config(show="*")  # Ховаємо текст

    def check_login(self):
        from tkinter import messagebox

        username = self.entry_login.get()
        password = self.entry_password.get()
        if not username or not password:
            messagebox.showwarning("Увага", "Будь ласка, заповніть всі поля!")
            return

        # Додали витягування id_user з бази
        query = "SELECT id_user, role FROM Users WHERE username = %s AND password_hash = %s"
        result = self.db.fetch_data(query, (username, password))

        if result:
            user_role = result[0]['role']
            id_user = result[0]['id_user']

            # За замовчуванням залишаємо логін, якщо ПІБ раптом не знайдено
            full_name = username

            # --- РОЗУМНИЙ ПОШУК ПІБ ---
            if user_role == 'Client':
                # Шукаємо в Clients
                client_data = self.db.fetch_data("SELECT full_name FROM Clients WHERE id_user = %s", (id_user,))
                if client_data and client_data[0]['full_name']:
                    full_name = client_data[0]['full_name']

            elif user_role == 'Trainer':
                # Шукаємо в Trainers
                trainer_data = self.db.fetch_data("SELECT full_name FROM Trainers WHERE id_user = %s", (id_user,))
                if trainer_data and trainer_data[0]['full_name']:
                    full_name = trainer_data[0]['full_name']

            elif user_role in ['Manager', 'Admin']:
                # Шукаємо в новій таблиці Employees
                emp_data = self.db.fetch_data("SELECT full_name FROM Employees WHERE id_user = %s", (id_user,))
                if emp_data and emp_data[0]['full_name']:
                    full_name = emp_data[0]['full_name']

            # Передаємо full_name як ТРЕТІЙ параметр у головне вікно!
            self.open_main_window(user_role, username, full_name)
        else:
            messagebox.showerror("Помилка", "Невірний логін або пароль!")

    def open_main_window(self, role, username, full_name):
        for widget in self.root.winfo_children():
            widget.destroy()

        # ПЕРЕДАЄМО full_name у MainWindow!
        MainWindow(self.root, self.db, role, username, full_name)


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
