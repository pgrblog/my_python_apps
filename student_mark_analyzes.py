import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

COLUMNS = [
    "Class",
    "Total Students",
    "100%",
    "Above 90%",
    "Above 80%",
    "Above 70%",
    "Above 60%",
    "Above 50%",
    "Above 40%",
    "Below 40%",
    "Class Average",
    "Absentees"
]

BAND_COLS = ["100%", "Above 90%", "Above 80%", "Above 70%", "Above 60%", "Above 50%", "Above 40%", "Below 40%"]

class MarksEntryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Academic Marks Distribution & Review")
        self.root.geometry("1280x720")

        # Top Control Bar (All primary action buttons)
        top_frame = ttk.Frame(root, padding=(10, 10, 10, 5))
        top_frame.pack(fill=tk.X)

        # Left action buttons: Data Entry, Import & Management
        ttk.Button(top_frame, text="Add Row Manually", command=self.add_row).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="📂 Import Excel (.xlsx)", command=self.import_excel).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="Clear Table", command=self.clear_table).pack(side=tk.LEFT, padx=3)

        # Center action buttons: Review, Chart, and Learning Outcome Reports
        ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=6, fill=tk.Y)
        ttk.Button(top_frame, text="📊 Review Report", command=self.show_review_report).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="📈 View Chart", command=self.show_distribution_chart).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="🎯 Learning Outcomes & Actions", command=self.show_learning_outcome_report).pack(side=tk.LEFT, padx=3)

        # Right action buttons: Exporting
        ttk.Button(top_frame, text="Export to CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=3)
        ttk.Button(top_frame, text="Export to Excel (.xlsx)", command=self.export_excel).pack(side=tk.RIGHT, padx=3)

        # Subject Entry Section
        subject_frame = ttk.Frame(root, padding=(15, 6, 10, 10))
        subject_frame.pack(fill=tk.X)

        ttk.Label(subject_frame, text="Subject:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.subject_entry = ttk.Entry(subject_frame, width=28, font=("Segoe UI", 10))
        self.subject_entry.pack(side=tk.LEFT)
        self.subject_entry.focus_set()

        # Scrollable Area Container
        container = ttk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.table_frame = ttk.Frame(self.canvas)
        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.rows = []
        self.render_headers()
        self.add_row()

    def render_headers(self):
        for col_idx, col_name in enumerate(COLUMNS):
            lbl = tk.Label(
                self.table_frame,
                text=col_name,
                font=("Segoe UI", 9, "bold"),
                bg="#e2e8f0",
                fg="#1e293b",
                relief=tk.RIDGE,
                padx=6,
                pady=6
            )
            lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

    def add_row(self, values=None):
        row_idx = len(self.rows) + 1
        current_row_entries = []

        for col_idx in range(len(COLUMNS)):
            entry_width = 12 if col_idx == 0 else 10
            entry = ttk.Entry(self.table_frame, width=entry_width, justify="center" if col_idx > 0 else "left")
            entry.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")

            if values and col_idx < len(values):
                val = values[col_idx]
                entry.insert(0, "" if pd.isna(val) else str(val))

            entry.bind("<KeyRelease>", lambda event, r=len(self.rows), c=col_idx: self.on_cell_edit(r, c))
            entry.bind("<Return>", lambda event, r=len(self.rows), c=col_idx: self.navigate_next(r, c))

            current_row_entries.append(entry)

        self.rows.append(current_row_entries)

    def on_cell_edit(self, row_idx, col_idx):
        if row_idx == len(self.rows) - 1:
            val = self.rows[row_idx][col_idx].get().strip()
            if val:
                self.add_row()

    def navigate_next(self, r, c):
        if c + 1 < len(COLUMNS):
            self.rows[r][c + 1].focus_set()
        elif r + 1 < len(self.rows):
            self.rows[r + 1][0].focus_set()

    def get_dataframe(self):
        data = []
        subject_name = self.subject_entry.get().strip()
        for row in self.rows:
            row_vals = [entry.get().strip() for entry in row]
            if any(row_vals):
                data.append(row_vals)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=COLUMNS)
        df.insert(0, "Subject", subject_name if subject_name else "General")

        numeric_cols = [c for c in COLUMNS if c != "Class"]
        for c in numeric_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        return df

    # --- Feature 1: Import Excel File ---

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)

            # 1. Normalize column names (strip whitespace)
            df.columns = [str(c).strip() for c in df.columns]

            # 2. Case-insensitive search for a 'Subject' column
            subject_col = next((c for c in df.columns if c.lower() == "subject"), None)

            extracted_subject = ""
            if subject_col:
                valid_subjects = df[subject_col].dropna().astype(str).str.strip()
                if not valid_subjects.empty:
                    extracted_subject = valid_subjects.iloc[0]

            # 3. If no dedicated column, check if the file name contains the subject
            if not extracted_subject:
                import os
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                # If named like "Marks_Science.xlsx" or "Mathematics.xlsx"
                extracted_subject = base_name.replace("Marks_", "").replace("_", " ").title()

            # 4. Update the UI Subject Entry box
            self.subject_entry.delete(0, tk.END)
            self.subject_entry.insert(0, extracted_subject)

            # 5. Validate standard score columns (case-insensitive check)
            col_map = {col.lower(): col for col in COLUMNS}
            df_rename = {}
            for c in df.columns:
                if c.lower() in col_map:
                    df_rename[c] = col_map[c.lower()]
            df.rename(columns=df_rename, inplace=True)

            missing_cols = [col for col in COLUMNS if col not in df.columns]
            if missing_cols:
                messagebox.showerror(
                    "Format Error",
                    f"Selected Excel file is missing required columns:\n{', '.join(missing_cols)}"
                )
                return

            # 6. Clear current UI entries and populate rows
            for row in self.rows:
                for entry in row:
                    entry.destroy()
            self.rows.clear()

            for _, row_data in df.iterrows():
                vals = [row_data[c] for c in COLUMNS]
                self.add_row(values=vals)

            self.add_row()
            messagebox.showinfo(
                "Success", 
                f"Subject: '{extracted_subject if extracted_subject else 'Not Specified'}'\nLoaded {len(df)} row(s) successfully!"
            )

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read Excel file:\n{e}")

    # --- Feature 2: View & Save Learning Outcome & Action Plan Report ---

    def generate_learning_outcome_text(self, df):
        subject = df["Subject"].iloc[0].upper()
        lines = [
            "=" * 76,
            f"       STUDENT LEARNING OUTCOMES (SLO) & FUTURE ACTION PLAN: {subject}",
            "=" * 76,
            ""
        ]

        for _, row in df.iterrows():
            total = int(row["Total Students"])
            absentees = int(row["Absentees"])
            appeared = max(0, total - absentees)
            avg = row["Class Average"]
            c_name = row["Class"]

            mastery = int(row["100%"] + row["Above 90%"])
            proficient = int(row["Above 80%"] + row["Above 70%"])
            basic = int(row["Above 60%"] + row["Above 50%"] + row["Above 40%"])
            below_basic = int(row["Below 40%"])

            mastery_pct = (mastery / appeared * 100) if appeared > 0 else 0
            proficient_pct = (proficient / appeared * 100) if appeared > 0 else 0
            below_basic_pct = (below_basic / appeared * 100) if appeared > 0 else 0

            lines.append(f"CLASS / SECTION: {c_name}")
            lines.append(f"Enrollment: {total} | Present: {appeared} | Absent: {absentees} | Cohort Mean: {avg:.2f}%")
            lines.append("-" * 76)

            # 1. Learning Outcome Analysis
            lines.append("1. LEARNING OUTCOME PROFICIENCY:")
            lines.append(f"   • Advanced Mastery (>=90%) : {mastery} students ({mastery_pct:.1f}%) -> Target competencies fully attained.")
            lines.append(f"   • Competent / Sound (70-89%) : {proficient} students ({proficient_pct:.1f}%) -> Core curricular benchmarks achieved.")
            lines.append(f"   • Developing Range  (40-69%) : {basic} students -> Partial concept grasp, needs targeted revision.")
            lines.append(f"   • Critical Concern  (<40%)   : {below_basic} students ({below_basic_pct:.1f}%) -> Essential fundamentals unmastered.")
            lines.append("")

            # 2. Evidence-Based Diagnostic
            lines.append("2. OUTCOME EVALUATION:")
            if avg >= 75:
                lines.append("   • Evaluation: High outcome attainment across key concepts. Learning progression is on track.")
            elif avg >= 55:
                lines.append("   • Evaluation: Moderate mastery. Mid-tier concept gaps persist in application and problem-solving.")
            else:
                lines.append("   • Evaluation: Significant deficit in foundational learning objectives; high remedial burden.")

            if mastery > 5 and below_basic > 5:
                lines.append("   • Disparity Alert: Polarized cohort. High learning divergence between top and bottom quartiles.")
            lines.append("")

            # 3. Action Plan for Future Learning
            lines.append("3. STRATEGIC ACTION PLAN FOR FUTURE LEARNING:")
            if below_basic > 0:
                lines.append(f"   [Remedial Action] Form structured support clinics for the {below_basic} below-40% students.")
                lines.append("   [Diagnostic Check] Administer topic-wise micro-assessments to isolate root conceptual misunderstandings.")
            if mastery_pct >= 20:
                lines.append("   [Enrichment] Introduce higher-order thinking tasks (HOTS) and project-based challenges for top scorers.")
            if absentees > (total * 0.1):
                lines.append("   [Attendance Impact] High absence rate detected. Coordinate with academic counselors to reduce attendance-driven learning gaps.")
            lines.append("   [Pedagogy Update] Implement weekly spaced retrieval quizzes and interactive peer-tutoring circles.")
            lines.append("=" * 76)
            lines.append("")

        return "\n".join(lines)

    def show_learning_outcome_report(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "Please enter or import records first.")
            return

        report_text = self.generate_learning_outcome_text(df)

        report_win = tk.Toplevel(self.root)
        report_win.title("Learning Outcomes & Action Plan Report")
        report_win.geometry("820x600")

        # Top Button Bar in Report Window
        btn_bar = ttk.Frame(report_win, padding=(10, 8))
        btn_bar.pack(fill=tk.X)

        def save_report():
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")],
                initialfile=f"Learning_Outcome_Report_{df['Subject'].iloc[0]}.txt"
            )
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(report_text)
                    messagebox.showinfo("Report Saved", f"Report saved successfully to:\n{path}")
                except Exception as ex:
                    messagebox.showerror("Error", f"Failed to save report file:\n{ex}")

        ttk.Button(btn_bar, text="💾 Save Report (.txt)", command=save_report).pack(side=tk.LEFT)
        ttk.Button(btn_bar, text="Close", command=report_win.destroy).pack(side=tk.RIGHT)

        text_widget = tk.Text(report_win, wrap=tk.WORD, font=("Consolas", 10), padx=12, pady=12)
        v_bar = ttk.Scrollbar(report_win, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=v_bar.set)

        v_bar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)

        text_widget.insert(tk.END, report_text)
        text_widget.config(state=tk.DISABLED)

    # --- Analytics & Chart Views ---

    def show_review_report(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "Please enter some records first.")
            return

        report_win = tk.Toplevel(self.root)
        report_win.title("Performance Review Report")
        report_win.geometry("750x450")

        text = tk.Text(report_win, wrap=tk.WORD, font=("Courier New", 10), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)

        subject = df["Subject"].iloc[0]
        report_lines = [
            f"============================================================",
            f"          ACADEMIC PERFORMANCE SUMMARY: {subject.upper()}",
            f"============================================================\n"
        ]

        for _, row in df.iterrows():
            total = row["Total Students"]
            appeared = max(0, total - row["Absentees"])
            high_scorers = row["100%"] + row["Above 90%"] + row["Above 80%"]
            low_scorers = row["Below 40%"]

            distinction_pct = (high_scorers / appeared * 100) if appeared > 0 else 0
            critical_pct = (low_scorers / appeared * 100) if appeared > 0 else 0

            report_lines.append(f"Class: {row['Class']}")
            report_lines.append(f"  • Total Enrolled: {int(total)} | Absentees: {int(row['Absentees'])} | Appeared: {int(appeared)}")
            report_lines.append(f"  • Class Average : {row['Class Average']:.2f}%")
            report_lines.append(f"  • Distinction Tier (>=80%): {int(high_scorers)} ({distinction_pct:.1f}%)")
            report_lines.append(f"  • Remedial Tier    (<40%) : {int(low_scorers)} ({critical_pct:.1f}%)")
            report_lines.append("-" * 60)

        text.insert(tk.END, "\n".join(report_lines))
        text.config(state=tk.DISABLED)

    def show_distribution_chart(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showwarning("No Data", "Please enter some records first.")
            return

        chart_win = tk.Toplevel(self.root)
        chart_win.title("Score Distribution Chart")
        chart_win.geometry("900x550")

        fig, ax = plt.subplots(figsize=(10, 5))
        for _, row in df.iterrows():
            counts = [row[col] for col in BAND_COLS]
            ax.plot(BAND_COLS, counts, marker="o", label=f"Class {row['Class']}")

        ax.set_title(f"Score Distribution - Subject: {df['Subject'].iloc[0]}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Marks Range Percentage")
        ax.set_ylabel("Number of Students")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        plt.xticks(rotation=25)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # --- File Operations ---

    def export_excel(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showwarning("Empty", "No data entered to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Saved successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save Excel file:\n{e}")

    def export_csv(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showwarning("Empty", "No data entered to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Saved successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save CSV file:\n{e}")

    def clear_table(self):
        if not messagebox.askyesno("Confirm", "Clear all entered data?"):
            return
        self.subject_entry.delete(0, tk.END)
        for row in self.rows:
            for entry in row:
                entry.destroy()
        self.rows.clear()
        self.add_row()

if __name__ == "__main__":
    root = tk.Tk()
    app = MarksEntryApp(root)
    root.mainloop()
