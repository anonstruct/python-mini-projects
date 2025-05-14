import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import os
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from fpdf import FPDF

class ExpenseTracker:
    def __init__(self, root):
        """
        Initialize the Expense Tracker application
        """
        self.root = root
        self.root.title("Expense Tracker Pro")
        self.root.geometry("1200x800")

        # Setup database connection
        self.setup_database()

        # Initialize variables
        self.setup_variables()

        # Create UI components
        self.create_ui()

        # Load initial data
        self.refresh_data()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def setup_database(self):
        """Initialize database connection and create tables"""
        try:
            self.conn = sqlite3.connect('expenses.db')
            self.cursor = self.conn.cursor()

            # Create expenses table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT
                )
            ''')
            self.conn.commit()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{str(e)}")
            self.root.destroy()

    def setup_variables(self):
        """Initialize all Tkinter variables"""
        # Input form variables
        self.type_var = tk.StringVar(value="Expense")
        self.category_var = tk.StringVar()
        self.amount_var = tk.DoubleVar()
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.desc_var = tk.StringVar()

        # Filter variables
        self.filter_type_var = tk.StringVar(value="All")
        self.filter_from_var = tk.StringVar()
        self.filter_to_var = tk.StringVar()
        self.min_amount_var = tk.DoubleVar()
        self.max_amount_var = tk.DoubleVar()

        # Chart variables
        self.chart_type_var = tk.StringVar(value="Pie")
        self.chart_timeframe_var = tk.StringVar(value="Monthly")

    def create_ui(self):
        """Create all UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Transactions tab
        self.transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_tab, text="Transactions")

        # Reports tab
        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="Reports")

        # Build each tab's content
        self.create_transactions_tab()
        self.create_reports_tab()

    def create_transactions_tab(self):
        """Create content for transactions tab"""
        # Input form frame
        input_frame = ttk.LabelFrame(self.transactions_tab, text="Transaction Entry", padding=15)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Type selection
        ttk.Label(input_frame, text="Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.type_combo = ttk.Combobox(input_frame, textvariable=self.type_var,
                                     values=["Expense", "Income"], state="readonly")
        self.type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Category entry
        ttk.Label(input_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.category_entry = ttk.Entry(input_frame, textvariable=self.category_var)
        self.category_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Amount entry
        ttk.Label(input_frame, text="Amount:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var)
        self.amount_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Date entry
        ttk.Label(input_frame, text="Date:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, textvariable=self.date_var)
        self.date_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Description entry
        ttk.Label(input_frame, text="Description:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.desc_entry = ttk.Entry(input_frame, textvariable=self.desc_var)
        self.desc_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        # Action buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.add_btn = ttk.Button(btn_frame, text="Add", command=self.add_transaction)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        self.update_btn = ttk.Button(btn_frame, text="Update", command=self.update_transaction, state=tk.DISABLED)
        self.update_btn.pack(side=tk.LEFT, padx=5)

        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_transaction, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear", command=self.clear_form).pack(side=tk.LEFT, padx=5)

        # Filters frame
        filter_frame = ttk.LabelFrame(self.transactions_tab, text="Filters", padding=15)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        # Type filter
        ttk.Label(filter_frame, text="Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.filter_type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var,
                                            values=["All", "Expense", "Income"], state="readonly")
        self.filter_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Date range filters
        ttk.Label(filter_frame, text="From Date:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.filter_from_entry = ttk.Entry(filter_frame, textvariable=self.filter_from_var)
        self.filter_from_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        ttk.Label(filter_frame, text="To Date:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.filter_to_entry = ttk.Entry(filter_frame, textvariable=self.filter_to_var)
        self.filter_to_entry.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        # Amount range filters
        ttk.Label(filter_frame, text="Min Amount:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.min_amount_entry = ttk.Entry(filter_frame, textvariable=self.min_amount_var)
        self.min_amount_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(filter_frame, text="Max Amount:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.max_amount_entry = ttk.Entry(filter_frame, textvariable=self.max_amount_var)
        self.max_amount_entry.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Filter action buttons
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=1, column=4, columnspan=2, sticky="e", pady=5)

        ttk.Button(btn_frame, text="Apply", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_filters).pack(side=tk.LEFT)

        # Transactions treeview
        tree_frame = ttk.Frame(self.transactions_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Type", "Category", "Amount", "Date", "Description"), show="headings")

        # Configure columns
        self.tree.heading("ID", text="ID")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Description", text="Description")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Type", width=100, anchor=tk.CENTER)
        self.tree.column("Category", width=150, anchor=tk.CENTER)
        self.tree.column("Amount", width=100, anchor=tk.E)
        self.tree.column("Date", width=100, anchor=tk.CENTER)
        self.tree.column("Description", width=250, anchor=tk.W)

        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_reports_tab(self):
        """Create content for reports tab"""
        # Chart type selection
        chart_frame = ttk.LabelFrame(self.reports_tab, text="Chart Options", padding=15)
        chart_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(chart_frame, text="Chart Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.chart_type_combo = ttk.Combobox(chart_frame, textvariable=self.chart_type_var,
                                           values=["Pie", "Bar", "Line"], state="readonly")
        self.chart_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(chart_frame, text="Time Frame:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.chart_timeframe_combo = ttk.Combobox(chart_frame, textvariable=self.chart_timeframe_var,
                                                values=["Daily", "Weekly", "Monthly", "Yearly"], state="readonly")
        self.chart_timeframe_combo.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        ttk.Button(chart_frame, text="Generate Chart", command=self.generate_chart).grid(row=0, column=4, padx=5)

        # Chart display area
        self.chart_frame = ttk.Frame(self.reports_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Report generation buttons
        report_frame = ttk.Frame(self.reports_tab)
        report_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(report_frame, text="Generate PDF Report", command=self.generate_pdf_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_frame, text="Backup Database", command=self.create_backup).pack(side=tk.LEFT, padx=5)

    def validate_input(self):
        """Validate the input form data"""
        errors = []

        if not self.type_var.get():
            errors.append("Transaction type is required")

        if not self.category_var.get():
            errors.append("Category is required")

        if not self.amount_var.get():
            errors.append("Amount is required")
        else:
            try:
                amount = float(self.amount_var.get())
                if amount <= 0:
                    errors.append("Amount must be positive")
            except ValueError:
                errors.append("Amount must be a valid number")

        if not self.date_var.get():
            errors.append("Date is required")

        if errors:
            messagebox.showwarning("Input Error", "\n".join(errors))
            return False
        return True

    def add_transaction(self):
        """Add a new transaction to the database"""
        if not self.validate_input():
            return

        try:
            self.cursor.execute("""
                INSERT INTO expenses (type, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.type_var.get(),
                self.category_var.get(),
                float(self.amount_var.get()),
                self.date_var.get(),
                self.desc_var.get()
            ))
            self.conn.commit()
            self.refresh_data()
            self.clear_form()
            messagebox.showinfo("Success", "Transaction added successfully")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add transaction:\n{str(e)}")

    def update_transaction(self):
        """Update an existing transaction"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to update")
            return

        if not self.validate_input():
            return

        transaction_id = self.tree.item(selected[0])['values'][0]

        try:
            self.cursor.execute("""
                UPDATE expenses
                SET type=?, category=?, amount=?, date=?, description=?
                WHERE id=?
            """, (
                self.type_var.get(),
                self.category_var.get(),
                float(self.amount_var.get()),
                self.date_var.get(),
                self.desc_var.get(),
                transaction_id
            ))
            self.conn.commit()
            self.refresh_data()
            self.clear_form()
            messagebox.showinfo("Success", "Transaction updated successfully")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update transaction:\n{str(e)}")

    def delete_transaction(self):
        """Delete a transaction"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to delete")
            return

        transaction_id = self.tree.item(selected[0])['values'][0]

        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this transaction?")
        if not confirm:
            return

        try:
            self.cursor.execute("DELETE FROM expenses WHERE id=?", (transaction_id,))
            self.conn.commit()
            self.refresh_data()
            self.clear_form()
            messagebox.showinfo("Success", "Transaction deleted successfully")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete transaction:\n{str(e)}")

    def on_tree_select(self, event):
        """Handle selection of a transaction in the treeview"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.type_var.set(values[1])
            self.category_var.set(values[2])
            self.amount_var.set(values[3])
            self.date_var.set(values[4])
            self.desc_var.set(values[5] if len(values) > 5 else "")

            self.add_btn.config(state=tk.DISABLED)
            self.update_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)

    def clear_form(self):
        """Clear the input form"""
        self.type_combo.current(0)
        self.category_var.set("")
        self.amount_var.set(0.0)
        self.date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self.desc_var.set("")

        self.tree.selection_remove(self.tree.selection())
        self.add_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

    def refresh_data(self):
        """Refresh the transactions list"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
            for row in self.cursor.fetchall():
                self.tree.insert("", tk.END, values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load transactions:\n{str(e)}")

    def apply_filters(self):
        """Apply filters to the transactions list"""
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        # Type filter
        if self.filter_type_var.get() != "All":
            query += " AND type=?"
            params.append(self.filter_type_var.get())

        # Date range filters
        if self.filter_from_var.get():
            query += " AND date>=?"
            params.append(self.filter_from_var.get())

        if self.filter_to_var.get():
            query += " AND date<=?"
            params.append(self.filter_to_var.get())

        # Amount range filters
        if self.min_amount_var.get():
            query += " AND amount>=?"
            params.append(float(self.min_amount_var.get()))

        if self.max_amount_var.get():
            query += " AND amount<=?"
            params.append(float(self.max_amount_var.get()))

        query += " ORDER BY date DESC"

        try:
            self.cursor.execute(query, params)
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in self.cursor.fetchall():
                self.tree.insert("", tk.END, values=row)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to apply filters:\n{str(e)}")

    def clear_filters(self):
        """Clear all filters"""
        self.filter_type_var.set("All")
        self.filter_from_var.set("")
        self.filter_to_var.set("")
        self.min_amount_var.set(0.0)
        self.max_amount_var.set(0.0)
        self.refresh_data()

    def generate_chart(self):
        """Generate a chart based on selected options"""
        try:
            # Clear previous chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # Get data based on timeframe
            timeframe = self.chart_timeframe_var.get()
            chart_type = self.chart_type_var.get()

            if timeframe == "Daily":
                query = """
                    SELECT date, SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
                    FROM expenses
                    GROUP BY date
                    ORDER BY date
                """
            elif timeframe == "Weekly":
                query = """
                    SELECT strftime('%Y-%W', date) as week,
                           SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
                    FROM expenses
                    GROUP BY week
                    ORDER BY week
                """
            elif timeframe == "Monthly":
                query = """
                    SELECT strftime('%Y-%m', date) as month,
                           SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
                    FROM expenses
                    GROUP BY month
                    ORDER BY month
                """
            else:  # Yearly
                query = """
                    SELECT strftime('%Y', date) as year,
                           SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
                    FROM expenses
                    GROUP BY year
                    ORDER BY year
                """

            self.cursor.execute(query)
            data = self.cursor.fetchall()

            if not data:
                messagebox.showinfo("Info", "No data available for chart")
                return

            # Prepare data for plotting
            labels = [row[0] for row in data]
            income = [row[1] for row in data]
            expense = [row[2] for row in data]

            # Create figure
            fig, ax = plt.subplots(figsize=(8, 5))

            if chart_type == "Pie":
                total_income = sum(income)
                total_expense = sum(expense)

                if total_income + total_expense == 0:
                    messagebox.showinfo("Info", "No financial data available")
                    return

                ax.pie([total_income, total_expense],
                      labels=["Income", "Expense"],
                      autopct='%1.1f%%',
                      startangle=90)
                ax.set_title("Income vs Expense")

            elif chart_type == "Bar":
                width = 0.35
                x = range(len(labels))

                ax.bar(x, income, width, label="Income")
                ax.bar([p + width for p in x], expense, width, label="Expense")

                ax.set_xticks([p + width/2 for p in x])
                ax.set_xticklabels(labels, rotation=45)
                ax.set_title(f"{timeframe} Income and Expenses")
                ax.legend()

            else:  # Line chart
                ax.plot(labels, income, marker='o', label="Income")
                ax.plot(labels, expense, marker='o', label="Expense")
                ax.set_title(f"{timeframe} Income and Expenses Trend")
                ax.legend()
                plt.xticks(rotation=45)

            # Embed chart in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to generate chart:\n{str(e)}")

    def generate_pdf_report(self):
        """Generate a PDF report of all transactions"""
        try:
            self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
            transactions = self.cursor.fetchall()

            if not transactions:
                messagebox.showinfo("Info", "No transactions to generate report")
                return

            # Create PDF
            pdf = FPDF()
            pdf.add_page()

            # Set font
            pdf.set_font("Arial", 'B', 16)

            # Title
            pdf.cell(0, 10, "Expense Tracker Report", 0, 1, 'C')
            pdf.ln(10)

            # Summary
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Financial Summary", 0, 1)
            pdf.set_font("Arial", '', 10)

            # Calculate totals
            self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE type='Income'")
            total_income = self.cursor.fetchone()[0] or 0

            self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE type='Expense'")
            total_expense = self.cursor.fetchone()[0] or 0

            balance = total_income - total_expense

            pdf.cell(0, 10, f"Total Income: ${total_income:,.2f}", 0, 1)
            pdf.cell(0, 10, f"Total Expenses: ${total_expense:,.2f}", 0, 1)
            pdf.cell(0, 10, f"Balance: ${balance:,.2f}", 0, 1)
            pdf.ln(10)

            # Transactions table
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Transaction Details", 0, 1)
            pdf.set_font("Arial", 'B', 10)

            # Table header
            pdf.cell(15, 10, "ID", 1)
            pdf.cell(30, 10, "Type", 1)
            pdf.cell(40, 10, "Category", 1)
            pdf.cell(30, 10, "Amount", 1)
            pdf.cell(40, 10, "Date", 1)
            pdf.cell(0, 10, "Description", 1, 1)

            # Table rows
            pdf.set_font("Arial", '', 10)
            for row in transactions:
                pdf.cell(15, 10, str(row[0]), 1)
                pdf.cell(30, 10, row[1], 1)
                pdf.cell(40, 10, row[2], 1)
                pdf.cell(30, 10, f"${row[3]:,.2f}", 1)
                pdf.cell(40, 10, row[4], 1)
                pdf.cell(0, 10, row[5] if row[5] else "", 1, 1)

            # Save file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save PDF Report"
            )

            if file_path:
                pdf.output(file_path)
                messagebox.showinfo("Success", "PDF report generated successfully")

        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to generate PDF report:\n{str(e)}")

    def export_to_csv(self):
        """Export transactions to CSV file"""
        try:
            self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
            transactions = self.cursor.fetchall()

            if not transactions:
                messagebox.showinfo("Info", "No transactions to export")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                title="Export to CSV"
            )

            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Type', 'Category', 'Amount', 'Date', 'Description'])
                    writer.writerows(transactions)

                messagebox.showinfo("Success", "Data exported to CSV successfully")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export to CSV:\n{str(e)}")

    def create_backup(self):
        """Create a backup of the database"""
        try:
            os.makedirs('backups', exist_ok=True)
            backup_file = f"backups/expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            with open(backup_file, 'wb') as f:
                for line in self.conn.iterdump():
                    f.write(f"{line}\n".encode('utf-8'))

            messagebox.showinfo("Success", f"Database backup created:\n{backup_file}")

        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup:\n{str(e)}")

    def on_exit(self):
        """Handle application exit"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.conn.close()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
