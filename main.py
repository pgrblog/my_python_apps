import os
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_USE_DEFAULT_INPUT"] = "0"
os.environ["KIVY_INPUT_MOUSE"] = "mouse"

import csv
import sqlite3
import hashlib
from datetime import date

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.spinner import Spinner

DB_FILE = "/home/krishna/my_python_apps/ssvm_buses.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    default_hash = hashlib.sha256("Pg63@#Imp".encode()).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO app_users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
    """, ("admin", default_hash, "Admin User", "Manager"))

    # 2. Vehicles Table (entry_date first)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            registration_no TEXT,
            seating_capacity TEXT,
            name_of_driver TEXT,
            mob_no_of_driver TEXT,
            name_of_AYA TEXT,
            mob_of_AYA TEXT,
            route_chart TEXT
        )
    """)

    # 3. Students Table (entry_date first)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            admission_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            class_grade TEXT,
            section TEXT,
            pickup_point TEXT,
            drop_point TEXT,
            parent_name TEXT,
            parent_contact TEXT,
            vehicle_id INTEGER,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # 4. Daily Trips Table (entry_date first)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_trips (
            trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            vehicle_id INTEGER NOT NULL,
            trip_type TEXT NOT NULL,
            start_point TEXT,
            halt_point TEXT,
            start_km REAL,
            end_km REAL,
            total_km REAL GENERATED ALWAYS AS (end_km - start_km) VIRTUAL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # 5. Fuel Logs Table (entry_date first)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuel_logs (
            fuel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            vehicle_id INTEGER NOT NULL,
            odometer_reading REAL,
            liters_filled REAL,
            cost_per_liter REAL,
            total_cost REAL GENERATED ALWAYS AS (liters_filled * cost_per_liter) VIRTUAL,
            fuel_station TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)

    # 6. Maintenance Logs Table (entry_date first)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            vehicle_id INTEGER NOT NULL,
            odometer_reading REAL,
            service_type TEXT,
            cost REAL,
            service_center TEXT,
            description TEXT,
            next_due_date TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
        )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def show_popup(title, message):
    box = BoxLayout(orientation='vertical', padding=10, spacing=10)
    lbl = Label(text=message, halign='center', valign='middle')
    lbl.bind(size=lbl.setter('text_size'))
    btn = Button(text="OK", size_hint=(1, 0.35), background_color=(0.2, 0.6, 0.9, 1))
    box.add_widget(lbl)
    box.add_widget(btn)
    popup = Popup(title=title, content=box, size_hint=(0.85, 0.35), auto_dismiss=False)
    btn.bind(on_press=popup.dismiss)
    popup.open()

def create_field_row(label_text, widget, label_width=140):
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=5)
    lbl = Label(
        text=label_text,
        size_hint_x=None,
        width=label_width,
        halign='left',
        valign='middle',
        bold=True,
        color=(0.9, 0.9, 0.9, 1)
    )
    lbl.bind(size=lbl.setter('text_size'))
    row.add_widget(lbl)
    row.add_widget(widget)
    return row


# ----------------- LOGIN SCREEN -----------------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        title = Label(
            text="SSVM Fleet Login",
            font_size="22sp",
            bold=True,
            size_hint_y=None,
            height=50,
            color=(0.1, 0.5, 0.9, 1)
        )
        layout.add_widget(title)

        self.entry_user = TextInput(multiline=False, text="admin")
        layout.add_widget(create_field_row("Username:", self.entry_user, label_width=100))

        self.entry_pass = TextInput(multiline=False, password=True, text="Pg63@#Imp")
        layout.add_widget(create_field_row("Password:", self.entry_pass, label_width=100))

        btn_login = Button(
            text="Login",
            size_hint_y=None,
            height=45,
            background_color=(0.1, 0.6, 0.3, 1),
            bold=True
        )
        btn_login.bind(on_press=self.authenticate)
        layout.add_widget(btn_login)

        layout.add_widget(Label())
        self.add_widget(layout)

    def authenticate(self, instance):
        user = self.entry_user.text.strip()
        pwd = self.entry_pass.text.strip()
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name, role FROM app_users WHERE username = ? AND password_hash = ?",
            (user, pwd_hash)
        )
        account = cursor.fetchone()
        conn.close()

        if account:
            app = App.get_running_app()
            app.user_name = account[0]
            app.user_role = account[1]
            self.manager.current = "main"
            self.manager.get_screen("main").initialize_dashboard()
        else:
            show_popup("Access Denied", "Invalid username or password.")


# ----------------- MAIN DASHBOARD SCREEN -----------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.container = BoxLayout(orientation='vertical')
        self.add_widget(self.container)

    def initialize_dashboard(self):
        self.container.clear_widgets()
        app = App.get_running_app()

        top_bar = BoxLayout(size_hint_y=None, height=42, padding=5, spacing=8)
        user_info = Label(
            text=f"[b]{app.user_name}[/b] ({app.user_role})",
            markup=True,
            halign='left',
            valign='middle'
        )
        user_info.bind(size=user_info.setter('text_size'))
        top_bar.add_widget(user_info)

        btn_logout = Button(text="Logout", size_hint_x=None, width=80, background_color=(0.8, 0.2, 0.2, 1))
        btn_logout.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        top_bar.add_widget(btn_logout)
        self.container.add_widget(top_bar)

        self.tabs = TabbedPanel(do_default_tab=False, tab_width=95)
        self.setup_tabs(app.user_role)
        self.container.add_widget(self.tabs)

    def setup_tabs(self, role):
        tab_v = TabbedPanelItem(text="Vehicles")
        tab_v.content = self.create_vehicles_view(role)
        self.tabs.add_widget(tab_v)

        tab_s = TabbedPanelItem(text="Students")
        tab_s.content = self.create_students_view(role)
        self.tabs.add_widget(tab_s)

        tab_t = TabbedPanelItem(text="Trips")
        tab_t.content = self.create_trips_view(role)
        self.tabs.add_widget(tab_t)

        tab_f = TabbedPanelItem(text="Fuel")
        tab_f.content = self.create_fuel_view(role)
        self.tabs.add_widget(tab_f)

        tab_m = TabbedPanelItem(text="Service")
        tab_m.content = self.create_maintenance_view(role)
        self.tabs.add_widget(tab_m)

    def export_csv(self, query, filename):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            headers = [desc[0] for desc in cursor.description]
            records = cursor.fetchall()
            conn.close()

            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(records)

            show_popup("Export Successful", f"Saved as:\n{filename}")
        except Exception as e:
            show_popup("Export Error", str(e))

    # ================= 1. VEHICLES VIEW =================
    def create_vehicles_view(self, role):
        root = BoxLayout(orientation='vertical', padding=6, spacing=6)
        can_edit = role not in ["President", "Secretary"]

        if can_edit:
            form = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
            form.bind(minimum_height=form.setter('height'))

            today_str = str(date.today())
            self.v_entry_date = TextInput(multiline=False, text=today_str)
            self.v_no = TextInput(multiline=False)
            self.v_reg = TextInput(multiline=False)
            self.v_cap = TextInput(multiline=False)
            self.v_driver = TextInput(multiline=False)
            self.v_driver_mob = TextInput(multiline=False)
            self.v_aya = TextInput(multiline=False)
            self.v_aya_mob = TextInput(multiline=False)
            self.v_route = TextInput(multiline=False)

            # Entry Date as First Column/Row
            form.add_widget(create_field_row("Entry Date:", self.v_entry_date))
            form.add_widget(create_field_row("Bus Number:", self.v_no))
            form.add_widget(create_field_row("Reg Number:", self.v_reg))
            form.add_widget(create_field_row("Capacity:", self.v_cap))
            form.add_widget(create_field_row("Driver Name:", self.v_driver))
            form.add_widget(create_field_row("Driver Mobile:", self.v_driver_mob))
            form.add_widget(create_field_row("AYA Name:", self.v_aya))
            form.add_widget(create_field_row("AYA Mobile:", self.v_aya_mob))
            form.add_widget(create_field_row("Route Chart:", self.v_route))

            btn_save = Button(text="Save Vehicle", size_hint_y=None, height=38, background_color=(0.2, 0.7, 0.3, 1))
            btn_save.bind(on_press=self.save_vehicle)
            form.add_widget(btn_save)

            form_scroll = ScrollView(size_hint_y=0.55)
            form_scroll.add_widget(form)
            root.add_widget(form_scroll)

        btn_exp = Button(text="📁 Export Vehicles to CSV", size_hint_y=None, height=34, background_color=(0.3, 0.4, 0.8, 1))
        btn_exp.bind(on_press=lambda inst: self.export_csv("SELECT * FROM vehicles", "ssvm_vehicles.csv"))
        root.add_widget(btn_exp)

        header_bar = BoxLayout(size_hint_y=None, height=26)
        header_bar.add_widget(Label(text="[b]Saved Vehicle Records[/b]", markup=True, halign='left', color=(0.9, 0.7, 0.1, 1)))
        root.add_widget(header_bar)

        self.v_list = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.v_list.bind(minimum_height=self.v_list.setter('height'))
        list_scroll = ScrollView(size_hint=(1, 0.45))
        list_scroll.add_widget(self.v_list)
        root.add_widget(list_scroll)

        self.load_vehicles()
        return root

    def save_vehicle(self, instance):
        vals = (
            self.v_entry_date.text.strip() or str(date.today()),
            self.v_no.text.strip(), self.v_reg.text.strip(),
            self.v_cap.text.strip(), self.v_driver.text.strip(), self.v_driver_mob.text.strip(),
            self.v_aya.text.strip(), self.v_aya_mob.text.strip(), self.v_route.text.strip()
        )
        if not vals[1]:
            show_popup("Warning", "Bus number is required.")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO vehicles (entry_date, vehicle_number, registration_no, seating_capacity,
            name_of_driver, mob_no_of_driver, name_of_AYA, mob_of_AYA, route_chart)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vals)
        conn.commit()
        conn.close()

        for f in [self.v_no, self.v_reg, self.v_cap, self.v_driver, self.v_driver_mob, self.v_aya, self.v_aya_mob, self.v_route]:
            f.text = ""
        self.v_entry_date.text = str(date.today())

        show_popup("Success", "Vehicle registered successfully!")
        self.load_vehicles()

    def load_vehicles(self):
        self.v_list.clear_widgets()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT vehicle_id, entry_date, vehicle_number, registration_no, name_of_driver, route_chart FROM vehicles ORDER BY vehicle_id DESC")
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=50, padding=2)
            card.add_widget(Label(text=f"[b]{r[2]}[/b] ({r[3]}) | Entry Date: {r[1]}", markup=True, halign='left'))
            card.add_widget(Label(text=f"Driver: {r[4]} | Route: {r[5]} (ID: {r[0]})", halign='left', color=(0.8, 0.8, 0.8, 1)))
            self.v_list.add_widget(card)

    # ================= 2. STUDENTS VIEW =================
    def create_students_view(self, role):
        root = BoxLayout(orientation='vertical', padding=6, spacing=6)
        can_edit = role not in ["President", "Secretary"]

        if can_edit:
            form = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
            form.bind(minimum_height=form.setter('height'))

            today_str = str(date.today())
            self.s_entry_date = TextInput(multiline=False, text=today_str)
            self.s_adm = TextInput(multiline=False)
            self.s_name = TextInput(multiline=False)
            self.s_class = TextInput(multiline=False)
            self.s_sec = TextInput(multiline=False)
            self.s_pickup = TextInput(multiline=False)
            self.s_drop = TextInput(multiline=False)
            self.s_parent = TextInput(multiline=False)
            self.s_contact = TextInput(multiline=False)
            self.s_vid = TextInput(multiline=False)

            # Entry Date as First Column/Row
            form.add_widget(create_field_row("Entry Date:", self.s_entry_date))
            form.add_widget(create_field_row("Admission No:", self.s_adm))
            form.add_widget(create_field_row("Student Name:", self.s_name))
            form.add_widget(create_field_row("Class/Grade:", self.s_class))
            form.add_widget(create_field_row("Section:", self.s_sec))
            form.add_widget(create_field_row("Pickup Point:", self.s_pickup))
            form.add_widget(create_field_row("Drop Point:", self.s_drop))
            form.add_widget(create_field_row("Parent Name:", self.s_parent))
            form.add_widget(create_field_row("Parent Contact:", self.s_contact))
            form.add_widget(create_field_row("Assigned Bus ID:", self.s_vid))

            btn_save = Button(text="Save Student", size_hint_y=None, height=38, background_color=(0.2, 0.7, 0.3, 1))
            btn_save.bind(on_press=self.save_student)
            form.add_widget(btn_save)

            form_scroll = ScrollView(size_hint_y=0.55)
            form_scroll.add_widget(form)
            root.add_widget(form_scroll)

        btn_exp = Button(text="📁 Export Students to CSV", size_hint_y=None, height=34, background_color=(0.3, 0.4, 0.8, 1))
        btn_exp.bind(on_press=lambda inst: self.export_csv(
            """SELECT s.entry_date, s.admission_no, s.student_name, s.class_grade, s.section,
                      s.pickup_point, s.drop_point, s.parent_name, s.parent_contact,
                      v.vehicle_number AS assigned_bus
               FROM students s LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id""",
            "ssvm_students.csv"
        ))
        root.add_widget(btn_exp)

        header_bar = BoxLayout(size_hint_y=None, height=26)
        header_bar.add_widget(Label(text="[b]Saved Student Records[/b]", markup=True, halign='left', color=(0.9, 0.7, 0.1, 1)))
        root.add_widget(header_bar)

        self.s_list = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.s_list.bind(minimum_height=self.s_list.setter('height'))
        list_scroll = ScrollView(size_hint=(1, 0.45))
        list_scroll.add_widget(self.s_list)
        root.add_widget(list_scroll)

        self.load_students()
        return root

    def save_student(self, instance):
        vals = (
            self.s_entry_date.text.strip() or str(date.today()),
            self.s_adm.text.strip(), self.s_name.text.strip(),
            self.s_class.text.strip(), self.s_sec.text.strip(), self.s_pickup.text.strip(),
            self.s_drop.text.strip(), self.s_parent.text.strip(), self.s_contact.text.strip(),
            self.s_vid.text.strip() if self.s_vid.text.strip() else None
        )
        if not vals[1] or not vals[2]:
            show_popup("Warning", "Admission No and Name are required.")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO students (entry_date, admission_no, student_name, class_grade, section,
            pickup_point, drop_point, parent_name, parent_contact, vehicle_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vals)
        conn.commit()
        conn.close()

        for f in [self.s_adm, self.s_name, self.s_class, self.s_sec, self.s_pickup, self.s_drop, self.s_parent, self.s_contact, self.s_vid]:
            f.text = ""
        self.s_entry_date.text = str(date.today())

        show_popup("Success", "Student registered successfully!")
        self.load_students()

    def load_students(self):
        self.s_list.clear_widgets()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.student_id, s.entry_date, s.admission_no, s.student_name,
                   (s.class_grade || ' ' || COALESCE(s.section, '')), s.pickup_point,
                   s.parent_contact, COALESCE(v.vehicle_number, 'Unassigned')
            FROM students s LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id
            ORDER BY s.student_id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=50, padding=2)
            card.add_widget(Label(text=f"[b]{r[2]} - {r[3]}[/b] ({r[4]}) | Entry: {r[1]}", markup=True, halign='left'))
            card.add_widget(Label(text=f"Pickup: {r[5]} | Bus: {r[7]} | Ph: {r[6]}", halign='left', color=(0.8, 0.8, 0.8, 1)))
            self.s_list.add_widget(card)

    # ================= 3. TRIPS VIEW =================
    def create_trips_view(self, role):
        root = BoxLayout(orientation='vertical', padding=6, spacing=6)
        can_edit = role not in ["President", "Secretary", "Principal"]

        if can_edit:
            form = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
            form.bind(minimum_height=form.setter('height'))

            today_str = str(date.today())
            self.t_entry_date = TextInput(multiline=False, text=today_str)
            self.t_vid = TextInput(multiline=False)
            self.t_type = Spinner(
                text="morning_pickup",
                values=("morning_pickup", "evening_drop", "special_trip")
            )
            self.t_start_pt = TextInput(multiline=False)
            self.t_halt_pt = TextInput(multiline=False)
            self.t_start_km = TextInput(multiline=False)
            self.t_end_km = TextInput(multiline=False)

            # Entry Date as First Column/Row
            form.add_widget(create_field_row("Entry Date:", self.t_entry_date))
            form.add_widget(create_field_row("Vehicle ID:", self.t_vid))
            form.add_widget(create_field_row("Trip Type:", self.t_type))
            form.add_widget(create_field_row("Start Point:", self.t_start_pt))
            form.add_widget(create_field_row("Halt Point:", self.t_halt_pt))
            form.add_widget(create_field_row("Start KM:", self.t_start_km))
            form.add_widget(create_field_row("End KM:", self.t_end_km))

            btn_save = Button(text="Save Trip Log", size_hint_y=None, height=38, background_color=(0.2, 0.7, 0.3, 1))
            btn_save.bind(on_press=self.save_trip)
            form.add_widget(btn_save)

            form_scroll = ScrollView(size_hint_y=0.55)
            form_scroll.add_widget(form)
            root.add_widget(form_scroll)

        btn_exp = Button(text="📁 Export Daily Trips to CSV", size_hint_y=None, height=34, background_color=(0.3, 0.4, 0.8, 1))
        btn_exp.bind(on_press=lambda inst: self.export_csv(
            """SELECT t.entry_date, t.trip_id, v.vehicle_number, t.trip_type,
                      t.start_point, t.halt_point, t.start_km, t.end_km, t.total_km
               FROM daily_trips t JOIN vehicles v ON t.vehicle_id = v.vehicle_id""",
            "ssvm_daily_trips.csv"
        ))
        root.add_widget(btn_exp)

        header_bar = BoxLayout(size_hint_y=None, height=26)
        header_bar.add_widget(Label(text="[b]Recent Trips[/b]", markup=True, halign='left', color=(0.9, 0.7, 0.1, 1)))
        root.add_widget(header_bar)

        self.t_list = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.t_list.bind(minimum_height=self.t_list.setter('height'))
        list_scroll = ScrollView(size_hint=(1, 0.45))
        list_scroll.add_widget(self.t_list)
        root.add_widget(list_scroll)

        self.load_trips()
        return root

    def save_trip(self, instance):
        try:
            vid = int(self.t_vid.text.strip())
            s_km = float(self.t_start_km.text.strip() or 0)
            e_km = float(self.t_end_km.text.strip() or 0)
            e_date = self.t_entry_date.text.strip() or str(date.today())
        except ValueError:
            show_popup("Error", "Vehicle ID and KMs must be numbers.")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO daily_trips (entry_date, vehicle_id, trip_type, start_point, halt_point, start_km, end_km)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (e_date, vid, self.t_type.text, self.t_start_pt.text.strip(),
              self.t_halt_pt.text.strip(), s_km, e_km))
        conn.commit()
        conn.close()

        for f in [self.t_vid, self.t_start_pt, self.t_halt_pt, self.t_start_km, self.t_end_km]:
            f.text = ""
        self.t_entry_date.text = str(date.today())

        show_popup("Success", "Daily trip saved successfully!")
        self.load_trips()

    def load_trips(self):
        self.t_list.clear_widgets()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.trip_id, t.entry_date, v.vehicle_number, t.trip_type, t.start_km, t.end_km, (t.end_km - t.start_km)
            FROM daily_trips t JOIN vehicles v ON t.vehicle_id = v.vehicle_id
            ORDER BY t.trip_id DESC LIMIT 30
        """)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=48, padding=2)
            card.add_widget(Label(text=f"[b]{r[2]} - {r[3]}[/b] | Entry Date: {r[1]}", markup=True, halign='left'))
            card.add_widget(Label(text=f"KM: {r[4]} to {r[5]} (Total: {r[6]} KM)", halign='left', color=(0.8, 0.8, 0.8, 1)))
            self.t_list.add_widget(card)

    # ================= 4. FUEL VIEW =================
    def create_fuel_view(self, role):
        root = BoxLayout(orientation='vertical', padding=6, spacing=6)
        can_edit = role not in ["President", "Secretary", "Principal"]

        if can_edit:
            form = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
            form.bind(minimum_height=form.setter('height'))

            today_str = str(date.today())
            self.f_entry_date = TextInput(multiline=False, text=today_str)
            self.f_vid = TextInput(multiline=False)
            self.f_odo = TextInput(multiline=False)
            self.f_liters = TextInput(multiline=False)
            self.f_rate = TextInput(multiline=False)
            self.f_station = TextInput(multiline=False)

            # Entry Date as First Column/Row
            form.add_widget(create_field_row("Entry Date:", self.f_entry_date))
            form.add_widget(create_field_row("Vehicle ID:", self.f_vid))
            form.add_widget(create_field_row("Odometer KM:", self.f_odo))
            form.add_widget(create_field_row("Liters Filled:", self.f_liters))
            form.add_widget(create_field_row("Rate/Liter (₹):", self.f_rate))
            form.add_widget(create_field_row("Station Name:", self.f_station))

            btn_save = Button(text="Save Fuel Log", size_hint_y=None, height=38, background_color=(0.2, 0.7, 0.3, 1))
            btn_save.bind(on_press=self.save_fuel)
            form.add_widget(btn_save)

            form_scroll = ScrollView(size_hint_y=0.55)
            form_scroll.add_widget(form)
            root.add_widget(form_scroll)

        btn_exp = Button(text="📁 Export Fuel Logs to CSV", size_hint_y=None, height=34, background_color=(0.3, 0.4, 0.8, 1))
        btn_exp.bind(on_press=lambda inst: self.export_csv(
            """SELECT f.entry_date, f.fuel_id, v.vehicle_number, f.odometer_reading,
                      f.liters_filled, f.cost_per_liter, (f.liters_filled * f.cost_per_liter) AS total_cost, f.fuel_station
               FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.vehicle_id""",
            "ssvm_fuel_logs.csv"
        ))
        root.add_widget(btn_exp)

        header_bar = BoxLayout(size_hint_y=None, height=26)
        header_bar.add_widget(Label(text="[b]Recent Fuel Refills[/b]", markup=True, halign='left', color=(0.9, 0.7, 0.1, 1)))
        root.add_widget(header_bar)

        self.f_list = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.f_list.bind(minimum_height=self.f_list.setter('height'))
        list_scroll = ScrollView(size_hint=(1, 0.45))
        list_scroll.add_widget(self.f_list)
        root.add_widget(list_scroll)

        self.load_fuel()
        return root

    def save_fuel(self, instance):
        try:
            vid = int(self.f_vid.text.strip())
            odo = float(self.f_odo.text.strip() or 0)
            liters = float(self.f_liters.text.strip() or 0)
            rate = float(self.f_rate.text.strip() or 0)
            e_date = self.f_entry_date.text.strip() or str(date.today())
        except ValueError:
            show_popup("Error", "Vehicle ID, Odo, Liters, and Rate must be valid numbers.")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fuel_logs (entry_date, vehicle_id, odometer_reading, liters_filled, cost_per_liter, fuel_station)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (e_date, vid, odo, liters, rate, self.f_station.text.strip()))
        conn.commit()
        conn.close()

        for f in [self.f_vid, self.f_odo, self.f_liters, self.f_rate, self.f_station]:
            f.text = ""
        self.f_entry_date.text = str(date.today())

        show_popup("Success", "Fuel entry recorded successfully!")
        self.load_fuel()

    def load_fuel(self):
        self.f_list.clear_widgets()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT f.fuel_id, f.entry_date, v.vehicle_number, f.liters_filled, (f.liters_filled * f.cost_per_liter), f.fuel_station
            FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            ORDER BY f.fuel_id DESC LIMIT 30
        """)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=48, padding=2)
            card.add_widget(Label(text=f"[b]{r[2]} - {r[3]} L[/b] (₹{r[4]:.2f}) | Date: {r[1]}", markup=True, halign='left'))
            card.add_widget(Label(text=f"Station: {r[5]} (Log ID: {r[0]})", halign='left', color=(0.8, 0.8, 0.8, 1)))
            self.f_list.add_widget(card)

    # ================= 5. MAINTENANCE VIEW =================
    def create_maintenance_view(self, role):
        root = BoxLayout(orientation='vertical', padding=6, spacing=6)
        can_edit = role not in ["President", "Secretary", "Principal"]

        if can_edit:
            form = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
            form.bind(minimum_height=form.setter('height'))

            today_str = str(date.today())
            self.m_entry_date = TextInput(multiline=False, text=today_str)
            self.m_vid = TextInput(multiline=False)
            self.m_type = Spinner(
                text="routine_service",
                values=("routine_service", "oil_change", "tyre_replacement", "brake_repair", "battery", "fitness_certificate", "other")
            )
            self.m_cost = TextInput(multiline=False)
            self.m_odo = TextInput(multiline=False)
            self.m_center = TextInput(multiline=False)
            self.m_next_date = TextInput(multiline=False, hint_text="YYYY-MM-DD")
            self.m_desc = TextInput(multiline=False)

            # Entry Date as First Column/Row
            form.add_widget(create_field_row("Entry Date:", self.m_entry_date))
            form.add_widget(create_field_row("Vehicle ID:", self.m_vid))
            form.add_widget(create_field_row("Service Type:", self.m_type))
            form.add_widget(create_field_row("Total Cost (₹):", self.m_cost))
            form.add_widget(create_field_row("Odometer KM:", self.m_odo))
            form.add_widget(create_field_row("Service Center:", self.m_center))
            form.add_widget(create_field_row("Next Due Date:", self.m_next_date))
            form.add_widget(create_field_row("Description:", self.m_desc))

            btn_save = Button(text="Save Maintenance Entry", size_hint_y=None, height=38, background_color=(0.2, 0.7, 0.3, 1))
            btn_save.bind(on_press=self.save_maintenance)
            form.add_widget(btn_save)

            form_scroll = ScrollView(size_hint_y=0.55)
            form_scroll.add_widget(form)
            root.add_widget(form_scroll)

        btn_exp = Button(text="📁 Export Maintenance to CSV", size_hint_y=None, height=34, background_color=(0.3, 0.4, 0.8, 1))
        btn_exp.bind(on_press=lambda inst: self.export_csv(
            """SELECT m.entry_date, m.maintenance_id, v.vehicle_number,
                      m.service_type, m.cost, m.service_center, m.next_due_date, m.description
               FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id = v.vehicle_id""",
            "ssvm_maintenance.csv"
        ))
        root.add_widget(btn_exp)

        header_bar = BoxLayout(size_hint_y=None, height=26)
        header_bar.add_widget(Label(text="[b]Recent Maintenance Entries[/b]", markup=True, halign='left', color=(0.9, 0.7, 0.1, 1)))
        root.add_widget(header_bar)

        self.m_list = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.m_list.bind(minimum_height=self.m_list.setter('height'))
        list_scroll = ScrollView(size_hint=(1, 0.45))
        list_scroll.add_widget(self.m_list)
        root.add_widget(list_scroll)

        self.load_maintenance()
        return root

    def save_maintenance(self, instance):
        try:
            vid = int(self.m_vid.text.strip())
            cost = float(self.m_cost.text.strip() or 0)
            odo = float(self.m_odo.text.strip() or 0)
            e_date = self.m_entry_date.text.strip() or str(date.today())
        except ValueError:
            show_popup("Error", "Vehicle ID, Cost, and Odometer must be numeric.")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO maintenance_logs (entry_date, vehicle_id, odometer_reading, service_type, cost, service_center, description, next_due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (e_date, vid, odo, self.m_type.text, cost,
              self.m_center.text.strip(), self.m_desc.text.strip(), self.m_next_date.text.strip() or None))
        conn.commit()
        conn.close()

        for f in [self.m_vid, self.m_cost, self.m_odo, self.m_center, self.m_next_date, self.m_desc]:
            f.text = ""
        self.m_entry_date.text = str(date.today())

        show_popup("Success", "Maintenance entry recorded successfully!")
        self.load_maintenance()

    def load_maintenance(self):
        self.m_list.clear_widgets()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.maintenance_id, m.entry_date, v.vehicle_number, m.service_type, m.cost, COALESCE(m.next_due_date, '-')
            FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id = v.vehicle_id
            ORDER BY m.maintenance_id DESC LIMIT 30
        """)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=48, padding=2)
            card.add_widget(Label(text=f"[b]{r[2]} - {r[3]}[/b] (₹{r[4]}) | Entry: {r[1]}", markup=True, halign='left'))
            card.add_widget(Label(text=f"Next Due: {r[5]} (Log ID: {r[0]})", halign='left', color=(0.8, 0.8, 0.8, 1)))
            self.m_list.add_widget(card)


# ----------------- APP ENTRY POINT -----------------
class SSVMFleetApp(App):
    user_name = "Admin"
    user_role = "Manager"

    def build(self):
        self.title = "SSVM Buses - Fleet Management"
        init_db()

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        return sm


if __name__ == "__main__":
    SSVMFleetApp().run()
