import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import csv
from pathlib import Path
from datetime import date
import os
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# Set this to the Ubuntu host IP so all office PCs connect to the same DB
DB_HOST = "192.168.1.22"  # Replace with Ubuntu machine's IP (or '127.0.0.1' on host)
DB_USER = "root"
DB_PASS = "Pg63@#Imp"
DB_NAME = "ssvm_buses"

# ----------------- LOGIN WINDOW -----------------
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SSVM Buses - Login")
        self.geometry("380x240")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="SSVM Fleet Login", font=("Helvetica", 14, "bold")).pack(pady=10)

        ttk.Label(frame, text="Username:").pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=30)
        self.entry_user.pack(pady=3)

        ttk.Label(frame, text="Password:").pack(anchor="w")
        self.entry_pass = ttk.Entry(frame, width=30, show="*")
        self.entry_pass.pack(pady=3)

        ttk.Button(frame, text="Login", command=self.authenticate).pack(pady=15)

    def authenticate(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()

        try:
            conn = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
            )
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT username, full_name, role FROM app_users WHERE username = %s AND password_hash = %s",
                (user, pwd_hash)
            )
            account = cursor.fetchone()
            cursor.close()
            conn.close()

            if account:
                self.destroy()  # Close login window
                # Launch main app with active role
                app = SSVMApp(user_role=account["role"], user_name=account["full_name"])
                app.mainloop()
            else:
                messagebox.showerror("Access Denied", "Invalid username or password.")
        except mysql.connector.Error as err:
            messagebox.showerror("Connection Error", f"Cannot reach database server:\n{err}")

# ----------------- ROLE ENFORCEMENT IN MAIN APP -----------------
# In your existing SSVMApp class, accept user_role and user_name:

class SSVMApp(tk.Tk):
    def __init__(self, user_role="Manager", user_name="Admin"):
        super().__init__()
        self.user_role = user_role
        self.user_name = user_name
        self.title(f"SSVM Buses - Logged in as: {self.user_name} ({self.user_role})")
        self.geometry("1020x720")

        # ... (keep all your existing setup_tab calls) ...

        # Apply permissions based on role
        self.apply_role_permissions()

    def apply_role_permissions(self):
        """Disables input frames for executive/view-only roles."""
        if self.user_role in ["President", "Secretary"]:
            # Disable adding new records; allow viewing tables and exporting CSV
            for tab in [self.tab_vehicles, self.tab_students, self.tab_trips, self.tab_fuel, self.tab_maintenance]:
                for child in tab.winfo_children():
                    if isinstance(child, ttk.LabelFrame):
                        # Disable all input fields and buttons inside entry frames
                        for widget in child.winfo_children():
                            widget.configure(state="disabled")

        elif self.user_role == "Principal":
            # Principal can manage students, but trip/fuel/maintenance entry is managed by transport staff
            for tab in [self.tab_trips, self.tab_fuel, self.tab_maintenance]:
                for child in tab.winfo_children():
                    if isinstance(child, ttk.LabelFrame):
                        for widget in child.winfo_children():
                            widget.configure(state="disabled")

# ----------------- DATABASE CONFIGURATION -----------------
DB_HOST = "127.0.0.1"
DB_USER = "root"            # Or 'root'
DB_PASS = "Pg63@#Imp"       # Replace with your MySQL password
DB_NAME = "ssvm_buses"

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Connection failed:\n{err}")
        return None

# ----------------- MAIN APP CLASS -----------------
class SSVMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SSVM Buses - Fleet & Student Management System (PGR)")
        self.geometry("1020x720")

        # Tab Controller
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab Frames
        self.tab_vehicles = ttk.Frame(self.notebook)
        self.tab_students = ttk.Frame(self.notebook)
        self.tab_trips = ttk.Frame(self.notebook)
        self.tab_fuel = ttk.Frame(self.notebook)
        self.tab_maintenance = ttk.Frame(self.notebook)

        # Register Tabs
        self.notebook.add(self.tab_vehicles, text=" Vehicles ")
        self.notebook.add(self.tab_students, text=" Students ")
        self.notebook.add(self.tab_trips, text=" Daily Trips ")
        self.notebook.add(self.tab_fuel, text=" Fuel Refill ")
        self.notebook.add(self.tab_maintenance, text=" Maintenance ")

        # Setup Views
        self.setup_vehicles_tab()
        self.setup_students_tab()
        self.setup_trips_tab()
        self.setup_fuel_tab()
        self.setup_maintenance_tab()

    # ================= CSV EXPORT UTILITY =================
    def export_table_to_csv(self, query, default_filename):
        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            headers = [desc[0] for desc in cursor.description]
            records = cursor.fetchall()

            # Path: /home/<user>/Documents/
            docs_dir = Path.home() / "Documents"
            docs_dir.mkdir(parents=True, exist_ok=True)
            file_path = docs_dir / default_filename

            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(records)

            messagebox.showinfo("Export Successful", f"Data exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")
        finally:
            cursor.close()
            conn.close()

    # ================= 1. VEHICLES TAB =================
    def setup_vehicles_tab(self):
        frame = ttk.LabelFrame(self.tab_vehicles, text="Add New Vehicle", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Bus No (e.g. BUS-01):").grid(row=0, column=0, sticky="w", pady=2)
        self.v_no = ttk.Entry(frame)
        self.v_no.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Registration No:").grid(row=0, column=2, sticky="w", pady=2)
        self.v_reg = ttk.Entry(frame)
        self.v_reg.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Capacity:").grid(row=1, column=0, sticky="w", pady=2)
        self.v_cap = ttk.Entry(frame)
        self.v_cap.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Driver Name:").grid(row=1, column=2, sticky="w", pady=2)
        self.v_driver = ttk.Entry(frame)
        self.v_driver.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Driver Mobile:").grid(row=2, column=0, sticky="w", pady=2)
        self.v_driver_mob = ttk.Entry(frame)
        self.v_driver_mob.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="AYA Name:").grid(row=2, column=2, sticky="w", pady=2)
        self.v_aya = ttk.Entry(frame)
        self.v_aya.grid(row=2, column=3, padx=5, pady=2)

        ttk.Label(frame, text="AYA Mobile:").grid(row=3, column=0, sticky="w", pady=2)
        self.v_aya_mob = ttk.Entry(frame)
        self.v_aya_mob.grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Route Chart:").grid(row=3, column=2, sticky="w", pady=2)
        self.v_route = ttk.Entry(frame)
        self.v_route.grid(row=3, column=3, padx=5, pady=2)

        btn_save = ttk.Button(frame, text="Save Vehicle", command=self.save_vehicle)
        btn_save.grid(row=4, column=0, columnspan=4, pady=8)

        self.v_tree = ttk.Treeview(self.tab_vehicles, columns=("id", "no", "reg", "driver", "route"), show="headings", height=8)
        self.v_tree.heading("id", text="ID")
        self.v_tree.heading("no", text="Bus No")
        self.v_tree.heading("reg", text="Reg No")
        self.v_tree.heading("driver", text="Driver")
        self.v_tree.heading("route", text="Route")
        self.v_tree.column("id", width=50)
        self.v_tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_exp = ttk.Button(
            self.tab_vehicles, 
            text="📁 Export Vehicles to Documents (CSV)", 
            command=lambda: self.export_table_to_csv("SELECT * FROM vehicles", "ssvm_vehicles.csv")
        )
        btn_exp.pack(pady=5)
        self.load_vehicles()

    def save_vehicle(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """INSERT INTO vehicles (vehicle_number, registration_no, seating_capacity, 
                 name_of_driver, mob_no_of_driver, name_of_AYA, mob_of_AYA, route_chart) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        vals = (self.v_no.get(), self.v_reg.get(), self.v_cap.get(), self.v_driver.get(),
                self.v_driver_mob.get(), self.v_aya.get(), self.v_aya_mob.get(), self.v_route.get())
        try:
            cursor.execute(sql, vals)
            conn.commit()
            messagebox.showinfo("Success", "Vehicle registered successfully!")
            self.load_vehicles()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    def load_vehicles(self):
        for row in self.v_tree.get_children():
            self.v_tree.delete(row)
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id, vehicle_number, registration_no, name_of_driver, route_chart FROM vehicles")
        for rec in cursor.fetchall():
            self.v_tree.insert("", "end", values=rec)
        cursor.close()
        conn.close()

    # ================= 2. STUDENTS TAB =================
    def setup_students_tab(self):
        frame = ttk.LabelFrame(self.tab_students, text="Register Student & Bus Assignment", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Admission No:").grid(row=0, column=0, sticky="w", pady=2)
        self.s_adm = ttk.Entry(frame)
        self.s_adm.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Student Name:").grid(row=0, column=2, sticky="w", pady=2)
        self.s_name = ttk.Entry(frame)
        self.s_name.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Class / Grade:").grid(row=1, column=0, sticky="w", pady=2)
        self.s_class = ttk.Entry(frame)
        self.s_class.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Section:").grid(row=1, column=2, sticky="w", pady=2)
        self.s_sec = ttk.Entry(frame)
        self.s_sec.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Pickup Point:").grid(row=2, column=0, sticky="w", pady=2)
        self.s_pickup = ttk.Entry(frame)
        self.s_pickup.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Drop Point:").grid(row=2, column=2, sticky="w", pady=2)
        self.s_drop = ttk.Entry(frame)
        self.s_drop.grid(row=2, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Parent Name:").grid(row=3, column=0, sticky="w", pady=2)
        self.s_parent = ttk.Entry(frame)
        self.s_parent.grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Parent Contact:").grid(row=3, column=2, sticky="w", pady=2)
        self.s_contact = ttk.Entry(frame)
        self.s_contact.grid(row=3, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Assigned Vehicle ID:").grid(row=4, column=0, sticky="w", pady=2)
        self.s_vid = ttk.Entry(frame)
        self.s_vid.grid(row=4, column=1, padx=5, pady=2)

        btn_save = ttk.Button(frame, text="Save Student", command=self.save_student)
        btn_save.grid(row=5, column=0, columnspan=4, pady=8)

        self.s_tree = ttk.Treeview(self.tab_students, columns=("id", "adm", "name", "class", "pickup", "parent_ph", "bus_no"), show="headings", height=8)
        self.s_tree.heading("id", text="ID")
        self.s_tree.heading("adm", text="Adm No")
        self.s_tree.heading("name", text="Name")
        self.s_tree.heading("class", text="Class")
        self.s_tree.heading("pickup", text="Pickup Point")
        self.s_tree.heading("parent_ph", text="Parent Contact")
        self.s_tree.heading("bus_no", text="Assigned Bus")
        self.s_tree.column("id", width=40)
        self.s_tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_exp = ttk.Button(
            self.tab_students, 
            text="📁 Export Students to Documents (CSV)", 
            command=lambda: self.export_table_to_csv(
                """SELECT s.admission_no, s.student_name, s.class_grade, s.section, 
                          s.pickup_point, s.drop_point, s.parent_name, s.parent_contact, 
                          v.vehicle_number AS assigned_bus
                   FROM students s
                   LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id""", 
                "ssvm_students.csv"
            )
        )
        btn_exp.pack(pady=5)
        self.load_students()

    def save_student(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """INSERT INTO students (admission_no, student_name, class_grade, section, 
                 pickup_point, drop_point, parent_name, parent_contact, vehicle_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        vals = (self.s_adm.get(), self.s_name.get(), self.s_class.get(), self.s_sec.get(),
                self.s_pickup.get(), self.s_drop.get(), self.s_parent.get(), self.s_contact.get(),
                self.s_vid.get() if self.s_vid.get() else None)
        try:
            cursor.execute(sql, vals)
            conn.commit()
            messagebox.showinfo("Success", "Student registered successfully!")
            self.load_students()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    def load_students(self):
        for row in self.s_tree.get_children():
            self.s_tree.delete(row)
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """SELECT s.student_id, s.admission_no, s.student_name, CONCAT(s.class_grade, ' ', COALESCE(s.section, '')),
                        s.pickup_point, s.parent_contact, COALESCE(v.vehicle_number, 'Unassigned')
                 FROM students s
                 LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id"""
        cursor.execute(sql)
        for rec in cursor.fetchall():
            self.s_tree.insert("", "end", values=rec)
        cursor.close()
        conn.close()

    # ================= 3. TRIPS TAB =================
    def setup_trips_tab(self):
        frame = ttk.LabelFrame(self.tab_trips, text="Log Daily Trip", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Vehicle ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.t_vid = ttk.Entry(frame)
        self.t_vid.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Trip Type:").grid(row=0, column=2, sticky="w", pady=2)
        self.t_type = ttk.Combobox(frame, values=["morning_pickup", "evening_drop", "special_trip"])
        self.t_type.set("morning_pickup")
        self.t_type.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Start Point:").grid(row=1, column=0, sticky="w", pady=2)
        self.t_start_pt = ttk.Entry(frame)
        self.t_start_pt.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Halt Point:").grid(row=1, column=2, sticky="w", pady=2)
        self.t_halt_pt = ttk.Entry(frame)
        self.t_halt_pt.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Start KM:").grid(row=2, column=0, sticky="w", pady=2)
        self.t_start_km = ttk.Entry(frame)
        self.t_start_km.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="End KM:").grid(row=2, column=2, sticky="w", pady=2)
        self.t_end_km = ttk.Entry(frame)
        self.t_end_km.grid(row=2, column=3, padx=5, pady=2)

        btn_save = ttk.Button(frame, text="Save Trip", command=self.save_trip)
        btn_save.grid(row=3, column=0, columnspan=4, pady=8)

        btn_exp = ttk.Button(
            frame, 
            text="📁 Export Daily Trips to Documents (CSV)", 
            command=lambda: self.export_table_to_csv(
                """SELECT t.trip_id, v.vehicle_number, t.trip_date, t.trip_type, 
                          t.start_point, t.halt_point, t.start_km, t.end_km, t.total_km 
                   FROM daily_trips t
                   JOIN vehicles v ON t.vehicle_id = v.vehicle_id""", 
                "ssvm_daily_trips.csv"
            )
        )
        btn_exp.grid(row=4, column=0, columnspan=4, pady=5)

    def save_trip(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """INSERT INTO daily_trips (vehicle_id, trip_date, trip_type, start_point, halt_point, start_km, end_km)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        vals = (self.t_vid.get(), date.today(), self.t_type.get(), self.t_start_pt.get(),
                self.t_halt_pt.get(), self.t_start_km.get(), self.t_end_km.get())
        try:
            cursor.execute(sql, vals)
            conn.commit()
            messagebox.showinfo("Success", "Daily trip saved successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    # ================= 4. FUEL TAB =================
    def setup_fuel_tab(self):
        frame = ttk.LabelFrame(self.tab_fuel, text="Log Fuel Refill", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Vehicle ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.f_vid = ttk.Entry(frame)
        self.f_vid.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Odometer Reading:").grid(row=0, column=2, sticky="w", pady=2)
        self.f_odo = ttk.Entry(frame)
        self.f_odo.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Liters Filled:").grid(row=1, column=0, sticky="w", pady=2)
        self.f_liters = ttk.Entry(frame)
        self.f_liters.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Cost per Liter (₹):").grid(row=1, column=2, sticky="w", pady=2)
        self.f_rate = ttk.Entry(frame)
        self.f_rate.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Station Name:").grid(row=2, column=0, sticky="w", pady=2)
        self.f_station = ttk.Entry(frame)
        self.f_station.grid(row=2, column=1, padx=5, pady=2)

        btn_save = ttk.Button(frame, text="Save Fuel Log", command=self.save_fuel)
        btn_save.grid(row=3, column=0, columnspan=4, pady=8)

        btn_exp = ttk.Button(
            frame, 
            text="📁 Export Fuel Logs to Documents (CSV)", 
            command=lambda: self.export_table_to_csv(
                """SELECT f.fuel_id, v.vehicle_number, f.refill_date, f.odometer_reading, 
                          f.liters_filled, f.cost_per_liter, f.total_cost, f.fuel_station 
                   FROM fuel_logs f
                   JOIN vehicles v ON f.vehicle_id = v.vehicle_id""", 
                "ssvm_fuel_logs.csv"
            )
        )
        btn_exp.grid(row=4, column=0, columnspan=4, pady=5)

    def save_fuel(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """INSERT INTO fuel_logs (vehicle_id, refill_date, odometer_reading, liters_filled, cost_per_liter, fuel_station)
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        vals = (self.f_vid.get(), date.today(), self.f_odo.get(), self.f_liters.get(), self.f_rate.get(), self.f_station.get())
        try:
            cursor.execute(sql, vals)
            conn.commit()
            messagebox.showinfo("Success", "Fuel entry recorded successfully!")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    # ================= 5. MAINTENANCE TAB =================
    def setup_maintenance_tab(self):
        frame = ttk.LabelFrame(self.tab_maintenance, text="Record Vehicle Maintenance / Service", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Vehicle ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.m_vid = ttk.Entry(frame)
        self.m_vid.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Service Type:").grid(row=0, column=2, sticky="w", pady=2)
        self.m_type = ttk.Combobox(frame, values=[
            "routine_service", "oil_change", "tyre_replacement", 
            "brake_repair", "battery", "fitness_certificate", "other"
        ])
        self.m_type.set("routine_service")
        self.m_type.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Total Cost (₹):").grid(row=1, column=0, sticky="w", pady=2)
        self.m_cost = ttk.Entry(frame)
        self.m_cost.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Odometer KM:").grid(row=1, column=2, sticky="w", pady=2)
        self.m_odo = ttk.Entry(frame)
        self.m_odo.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Service Center:").grid(row=2, column=0, sticky="w", pady=2)
        self.m_center = ttk.Entry(frame)
        self.m_center.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Next Due Date (YYYY-MM-DD):").grid(row=2, column=2, sticky="w", pady=2)
        self.m_next_date = ttk.Entry(frame)
        self.m_next_date.grid(row=2, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Description:").grid(row=3, column=0, sticky="w", pady=2)
        self.m_desc = ttk.Entry(frame, width=50)
        self.m_desc.grid(row=3, column=1, columnspan=3, padx=5, pady=2, sticky="w")

        btn_save = ttk.Button(frame, text="Save Maintenance Entry", command=self.save_maintenance)
        btn_save.grid(row=4, column=0, columnspan=4, pady=8)

        self.m_tree = ttk.Treeview(self.tab_maintenance, columns=("id", "bus", "date", "type", "cost", "next_due"), show="headings", height=8)
        self.m_tree.heading("id", text="ID")
        self.m_tree.heading("bus", text="Bus No")
        self.m_tree.heading("date", text="Service Date")
        self.m_tree.heading("type", text="Type")
        self.m_tree.heading("cost", text="Cost (₹)")
        self.m_tree.heading("next_due", text="Next Due")
        self.m_tree.column("id", width=40)
        self.m_tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_exp = ttk.Button(
            self.tab_maintenance, 
            text="📁 Export Maintenance to Documents (CSV)", 
            command=lambda: self.export_table_to_csv(
                """SELECT m.maintenance_id, v.vehicle_number, m.service_date, 
                          m.service_type, m.cost, m.service_center, m.next_due_date, m.description 
                   FROM maintenance_logs m
                   JOIN vehicles v ON m.vehicle_id = v.vehicle_id""", 
                "ssvm_maintenance.csv"
            )
        )
        btn_exp.pack(pady=5)
        self.load_maintenance()

    def save_maintenance(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """INSERT INTO maintenance_logs (vehicle_id, service_date, odometer_reading, 
                 service_type, cost, service_center, description, next_due_date) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        next_due = self.m_next_date.get().strip() or None
        vals = (self.m_vid.get(), date.today(), self.m_odo.get() or None,
                self.m_type.get(), self.m_cost.get(), self.m_center.get(),
                self.m_desc.get(), next_due)
        try:
            cursor.execute(sql, vals)
            conn.commit()
            messagebox.showinfo("Success", "Maintenance entry recorded successfully!")
            self.load_maintenance()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    def load_maintenance(self):
        for row in self.m_tree.get_children():
            self.m_tree.delete(row)
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        sql = """SELECT m.maintenance_id, v.vehicle_number, m.service_date, m.service_type, m.cost, COALESCE(m.next_due_date, '-')
                 FROM maintenance_logs m
                 JOIN vehicles v ON m.vehicle_id = v.vehicle_id
                 ORDER BY m.service_date DESC"""
        cursor.execute(sql)
        for rec in cursor.fetchall():
            self.m_tree.insert("", "end", values=rec)
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app = SSVMApp()
    app.mainloop()
