import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from PIL import Image, ImageTk
import shutil
import hashlib

# Initialize database and directories
DB_NAME = "tenant_ledger.db"
PHOTO_DIR = "tenant_photos"
DOCS_DIR = "tenant_documents"
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# ======================
# Database Setup
# ======================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        move_in_date DATE NOT NULL,
        move_out_date DATE,
        rent_amount REAL NOT NULL,
        security_deposit REAL NOT NULL,
        deposit_refunded BOOLEAN DEFAULT 0,
        notes TEXT,
        is_active BOOLEAN DEFAULT 1,
        photo_path TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        property_id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        unit_number TEXT,
        owner_notes TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rent_payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date DATE NOT NULL,
        month_year TEXT NOT NULL,
        payment_method TEXT,
        late_fee REAL DEFAULT 0,
        notes TEXT,
        receipt_path TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
        FOREIGN KEY (property_id) REFERENCES properties(property_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        doc_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        expiry_date DATE,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ======================
# Material Design Styling
# ======================
class MaterialStyle:
    COLORS = {
        "primary": "#6200ee",
        "primary_dark": "#3700b3",
        "secondary": "#03dac6",
        "background": "#f5f5f5",
        "error": "#b00020",
        "text": "#333333"
    }
    
    @staticmethod
    def configure_styles(root):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TButton", 
                       padding=6, 
                       relief="flat",
                       background=MaterialStyle.COLORS["primary"],
                       foreground="white",
                       font=("Helvetica", 10))
        
        style.map("TButton",
                 background=[("active", MaterialStyle.COLORS["primary_dark"])])
        
        style.configure("TEntry", 
                       fieldbackground="white", 
                       padding=5,
                       relief="flat")
        
        style.configure("Card.TFrame", 
                       background="white", 
                       relief="raised", 
                       borderwidth=1)
        
        style.configure("Treeview.Heading", 
                       background=MaterialStyle.COLORS["primary"],
                       foreground="white",
                       font=("Helvetica", 10, "bold"))
        
        style.configure("Treeview",
                       rowheight=25,
                       font=("Helvetica", 10))

# ======================
# Utility Functions
# ======================
def save_file_to_storage(filepath, target_dir):
    """Securely save uploaded files with hashed names"""
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    ext = os.path.splitext(filepath)[1]
    new_filename = f"{file_hash}{ext}"
    target_path = os.path.join(target_dir, new_filename)
    
    shutil.copy(filepath, target_path)
    return target_path

def validate_phone(phone):
    return len(phone) >= 10 and phone.isdigit()

def format_currency(amount):
    return f"₹{amount:,.2f}"

# ======================
# Main Application
# ======================
class TenantLedgerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tenant Ledger (Local)")
        self.root.geometry("1200x800")
        MaterialStyle.configure_styles(root)
        
        self.current_tenant_id = None
        self.setup_ui()
        
    def setup_ui(self):
        # Navigation Bar
        self.navbar = tk.Frame(self.root, bg=MaterialStyle.COLORS["primary"])
        self.navbar.pack(side="top", fill="x")
        
        tk.Label(self.navbar, 
                text="Tenant Ledger", 
                bg=MaterialStyle.COLORS["primary"],
                fg="white",
                font=("Helvetica", 16, "bold")).pack(side="left", padx=20)
        
        nav_buttons = [
            ("Tenants", self.show_tenants),
            ("Rent", self.show_rent),
            ("Documents", self.show_documents)
        ]
        
        for text, command in nav_buttons:
            btn = ttk.Button(self.navbar, text=text, command=command)
            btn.pack(side="left", padx=5)
        
        # Main Content Area
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Show tenants by default
        self.show_tenants()
    
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    # ======================
    # Tenant Management
    # ======================
    def show_tenants(self):
        self.clear_main_frame()
        
        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, 
                 text="Tenant Management", 
                 font=("Helvetica", 14)).pack(side="left")
        
        ttk.Button(header, 
                  text="+ Add Tenant", 
                  command=self.show_add_tenant_dialog).pack(side="right")
        
        # Tenant list
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        self.tenant_tree = ttk.Treeview(tree_frame, 
                                      columns=("name", "phone", "rent", "status"), 
                                      selectmode="browse")
        
        # Configure columns
        self.tenant_tree.heading("#0", text="ID", anchor="w")
        self.tenant_tree.heading("name", text="Name", anchor="w")
        self.tenant_tree.heading("phone", text="Phone", anchor="w")
        self.tenant_tree.heading("rent", text="Monthly Rent", anchor="w")
        self.tenant_tree.heading("status", text="Status", anchor="w")
        
        self.tenant_tree.column("#0", width=50, stretch=False)
        self.tenant_tree.column("name", width=200, stretch=True)
        self.tenant_tree.column("phone", width=150, stretch=False)
        self.tenant_tree.column("rent", width=120, stretch=False)
        self.tenant_tree.column("status", width=100, stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tenant_tree.yview)
        self.tenant_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tenant_tree.pack(fill="both", expand=True)
        
        # Bind selection event
        self.tenant_tree.bind("<<TreeviewSelect>>", self.on_tenant_select)
        
        # Action buttons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, 
                  text="View Details", 
                  command=self.show_tenant_details).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, 
                  text="Edit Tenant", 
                  command=self.show_edit_tenant_dialog).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, 
                  text="Deactivate", 
                  command=self.toggle_tenant_status).pack(side="left", padx=5)
        
        # Load data
        self.load_tenants()
    
    def load_tenants(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tenant_id, full_name, phone, rent_amount, is_active 
            FROM tenants
            ORDER BY is_active DESC, full_name
        """)
        
        # Clear existing data
        for row in self.tenant_tree.get_children():
            self.tenant_tree.delete(row)
            
        # Add tenants to treeview
        for tenant in cursor.fetchall():
            tenant_id, name, phone, rent, is_active = tenant
            status = "Active" if is_active else "Inactive"
            self.tenant_tree.insert("", "end", 
                                  text=str(tenant_id), 
                                  values=(name, phone, format_currency(rent), status))
        
        conn.close()
    
    def on_tenant_select(self, event):
        selected = self.tenant_tree.focus()
        if selected:
            self.current_tenant_id = int(self.tenant_tree.item(selected, "text"))
    
    def show_add_tenant_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Tenant")
        dialog.geometry("500x650")
        dialog.resizable(False, False)
        
        # Form variables
        name_var = tk.StringVar()
        phone_var = tk.StringVar()
        email_var = tk.StringVar()
        rent_var = tk.DoubleVar(value=0.0)
        move_in_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        notes_var = tk.StringVar()
        photo_path_var = tk.StringVar()
        
        # Form fields
        ttk.Label(dialog, text="Full Name*").pack(pady=(10, 0))
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Phone*").pack()
        phone_entry = ttk.Entry(dialog, textvariable=phone_var)
        phone_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Email").pack()
        email_entry = ttk.Entry(dialog, textvariable=email_var)
        email_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Monthly Rent*").pack()
        rent_entry = ttk.Entry(dialog, textvariable=rent_var)
        rent_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Move-In Date*").pack()
        move_in_entry = ttk.Entry(dialog, textvariable=move_in_var)
        move_in_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Notes").pack()
        notes_entry = tk.Text(dialog, height=4)
        notes_entry.pack(fill="x", padx=20, pady=5)
        
        # Photo upload
        def upload_photo():
            filetypes = [("Image files", "*.jpg *.jpeg *.png")]
            filepath = filedialog.askopenfilename(filetypes=filetypes)
            if filepath:
                photo_path_var.set(filepath)
                photo_btn.config(text=f"Photo: {os.path.basename(filepath)}")
        
        photo_btn = ttk.Button(dialog, text="Upload ID Photo", command=upload_photo)
        photo_btn.pack(pady=10)
        
        # Submit button
        def submit():
            # Validate required fields
            if not name_var.get() or not phone_var.get() or not rent_var.get() or not move_in_var.get():
                messagebox.showerror("Error", "Please fill all required fields (*)")
                return
                
            if not validate_phone(phone_var.get()):
                messagebox.showerror("Error", "Invalid phone number")
                return
                
            try:
                # Save photo if uploaded
                photo_path = None
                if photo_path_var.get():
                    photo_path = save_file_to_storage(photo_path_var.get(), PHOTO_DIR)
                
                # Save to database
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO tenants (
                        full_name, phone, email, rent_amount, 
                        security_deposit, move_in_date, notes, photo_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name_var.get(),
                    phone_var.get(),
                    email_var.get(),
                    rent_var.get(),
                    rent_var.get() * 2,  # 2 months rent as deposit
                    move_in_var.get(),
                    notes_entry.get("1.0", "end").strip(),
                    photo_path
                ))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Tenant added successfully")
                dialog.destroy()
                self.load_tenants()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add tenant: {str(e)}")
        
        ttk.Button(dialog, text="Save Tenant", command=submit).pack(pady=20)
    
    def show_tenant_details(self):
        if not self.current_tenant_id:
            messagebox.showwarning("Warning", "Please select a tenant first")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Tenant Details")
        dialog.geometry("600x500")
        
        # Get tenant data
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT full_name, phone, email, rent_amount, security_deposit, 
                   move_in_date, move_out_date, notes, photo_path, is_active
            FROM tenants
            WHERE tenant_id = ?
        """, (self.current_tenant_id,))
        
        tenant = cursor.fetchone()
        conn.close()
        
        if not tenant:
            messagebox.showerror("Error", "Tenant not found")
            dialog.destroy()
            return
        
        # Display tenant info
        name, phone, email, rent, deposit, move_in, move_out, notes, photo_path, is_active = tenant
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Photo column
        photo_frame = ttk.Frame(main_frame)
        photo_frame.pack(side="left", fill="y", padx=(0, 20))
        
        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                
                photo_label = tk.Label(photo_frame, image=photo)
                photo_label.image = photo  # Keep reference
                photo_label.pack()
            except:
                ttk.Label(photo_frame, text="[Photo not available]").pack()
        else:
            ttk.Label(photo_frame, text="[No photo uploaded]").pack()
        
        # Details column
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(side="left", fill="both", expand=True)
        
        # Tenant info
        ttk.Label(details_frame, 
                 text=name, 
                 font=("Helvetica", 16, "bold")).pack(anchor="w", pady=(0, 10))
        
        info_rows = [
            ("Phone:", phone),
            ("Email:", email if email else "-"),
            ("Status:", "Active" if is_active else "Inactive"),
            ("Rent:", format_currency(rent)),
            ("Deposit:", format_currency(deposit)),
            ("Move-In Date:", move_in),
            ("Move-Out Date:", move_out if move_out else "-")
        ]
        
        for label, value in info_rows:
            row_frame = ttk.Frame(details_frame)
            row_frame.pack(fill="x", pady=2)
            
            ttk.Label(row_frame, text=label, width=12, anchor="e").pack(side="left")
            ttk.Label(row_frame, text=value, anchor="w").pack(side="left", padx=5)
        
        # Notes
        ttk.Label(details_frame, text="Notes:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 0))
        
        notes_text = tk.Text(details_frame, height=6, wrap="word")
        notes_text.pack(fill="x", pady=5)
        notes_text.insert("1.0", notes if notes else "No notes available")
        notes_text.config(state="disabled")
    
    def show_edit_tenant_dialog(self):
        # Similar to add tenant but pre-fills existing data
        # Implementation omitted for brevity
        pass
    
    def toggle_tenant_status(self):
        if not self.current_tenant_id:
            messagebox.showwarning("Warning", "Please select a tenant first")
            return
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute("SELECT is_active FROM tenants WHERE tenant_id = ?", (self.current_tenant_id,))
        is_active = cursor.fetchone()[0]
        
        new_status = not is_active
        action = "deactivated" if not new_status else "reactivated"
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} this tenant?"):
            cursor.execute("""
                UPDATE tenants 
                SET is_active = ?
                WHERE tenant_id = ?
            """, (new_status, self.current_tenant_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Tenant {action} successfully")
            self.load_tenants()
        else:
            conn.close()
    
    # ======================
    # Rent Management
    # ======================
    def show_rent(self):
        self.clear_main_frame()
        
        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, 
                 text="Rent Management", 
                 font=("Helvetica", 14)).pack(side="left")
        
        ttk.Button(header, 
                  text="+ Record Payment", 
                  command=self.show_add_payment_dialog).pack(side="right")
        
        # Rent payments treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        self.rent_tree = ttk.Treeview(tree_frame, 
                                    columns=("date", "amount", "method", "month", "late_fee"), 
                                    selectmode="browse")
        
        # Configure columns
        self.rent_tree.heading("#0", text="ID", anchor="w")
        self.rent_tree.heading("date", text="Payment Date", anchor="w")
        self.rent_tree.heading("amount", text="Amount", anchor="w")
        self.rent_tree.heading("method", text="Method", anchor="w")
        self.rent_tree.heading("month", text="For Month", anchor="w")
        self.rent_tree.heading("late_fee", text="Late Fee", anchor="w")
        
        self.rent_tree.column("#0", width=50, stretch=False)
        self.rent_tree.column("date", width=120, stretch=False)
        self.rent_tree.column("amount", width=100, stretch=False)
        self.rent_tree.column("method", width=100, stretch=False)
        self.rent_tree.column("month", width=100, stretch=False)
        self.rent_tree.column("late_fee", width=80, stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.rent_tree.yview)
        self.rent_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.rent_tree.pack(fill="both", expand=True)
        
        # Load data
        self.load_rent_payments()
    
    def load_rent_payments(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.payment_id, p.payment_date, p.amount, p.payment_method, 
                   p.month_year, p.late_fee, t.full_name
            FROM rent_payments p
            JOIN tenants t ON p.tenant_id = t.tenant_id
            ORDER BY p.payment_date DESC
        """)
        
        # Clear existing data
        for row in self.rent_tree.get_children():
            self.rent_tree.delete(row)
            
        # Add payments to treeview
        for payment in cursor.fetchall():
            payment_id, date, amount, method, month, late_fee, name = payment
            self.rent_tree.insert("", "end", 
                                text=str(payment_id), 
                                values=(date, format_currency(amount), method, month, 
                                       format_currency(late_fee) if late_fee else "-"))
        
        conn.close()
    
    def show_add_payment_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Record Rent Payment")
        dialog.geometry("500x400")
        
        # Form variables
        tenant_var = tk.StringVar()
        amount_var = tk.DoubleVar()
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        month_var = tk.StringVar(value=datetime.now().strftime("%m-%Y"))
        method_var = tk.StringVar(value="Cash")
        late_fee_var = tk.DoubleVar(value=0.0)
        notes_var = tk.StringVar()
        
        # Form fields
        ttk.Label(dialog, text="Tenant*").pack(pady=(10, 0))
        
        # Tenant dropdown
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT tenant_id, full_name FROM tenants WHERE is_active = 1")
        tenants = cursor.fetchall()
        conn.close()
        
        tenant_names = [f"{name} (ID: {id})" for id, name in tenants]
        tenant_dropdown = ttk.Combobox(dialog, textvariable=tenant_var, values=tenant_names)
        tenant_dropdown.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Amount*").pack()
        amount_entry = ttk.Entry(dialog, textvariable=amount_var)
        amount_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Payment Date*").pack()
        date_entry = ttk.Entry(dialog, textvariable=date_var)
        date_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="For Month*").pack()
        month_entry = ttk.Entry(dialog, textvariable=month_var)
        month_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Payment Method*").pack()
        method_dropdown = ttk.Combobox(dialog, textvariable=method_var, 
                                      values=["Cash", "Bank Transfer", "UPI", "Cheque"])
        method_dropdown.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Late Fee").pack()
        late_fee_entry = ttk.Entry(dialog, textvariable=late_fee_var)
        late_fee_entry.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Notes").pack()
        notes_entry = ttk.Entry(dialog, textvariable=notes_var)
        notes_entry.pack(fill="x", padx=20, pady=5)
        
        # Submit button
        def submit():
            # Validate required fields
            if not tenant_var.get() or not amount_var.get() or not date_var.get() or not month_var.get() or not method_var.get():
                messagebox.showerror("Error", "Please fill all required fields (*)")
                return
                
            try:
                # Extract tenant ID from selection
                tenant_id = int(tenant_var.get().split("(ID: ")[1].rstrip(")"))
                
                # Save to database
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO rent_payments (
                        tenant_id, amount, payment_date, month_year, 
                        payment_method, late_fee, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant_id,
                    amount_var.get(),
                    date_var.get(),
                    month_var.get(),
                    method_var.get(),
                    late_fee_var.get(),
                    notes_var.get()
                ))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Payment recorded successfully")
                dialog.destroy()
                self.load_rent_payments()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to record payment: {str(e)}")
        
        ttk.Button(dialog, text="Record Payment", command=submit).pack(pady=20)
    
    # ======================
    # Document Management
    # ======================
    def show_documents(self):
        self.clear_main_frame()
        
        # Header
        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, 
                 text="Document Management", 
                 font=("Helvetica", 14)).pack(side="left")
        
        ttk.Button(header, 
                  text="+ Add Document", 
                  command=self.show_add_document_dialog).pack(side="right")
        
        # Documents treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        self.doc_tree = ttk.Treeview(tree_frame, 
                                   columns=("type", "tenant", "expiry"), 
                                   selectmode="browse")
        
        # Configure columns
        self.doc_tree.heading("#0", text="ID", anchor="w")
        self.doc_tree.heading("type", text="Document Type", anchor="w")
        self.doc_tree.heading("tenant", text="Tenant", anchor="w")
        self.doc_tree.heading("expiry", text="Expiry Date", anchor="w")
        
        self.doc_tree.column("#0", width=50, stretch=False)
        self.doc_tree.column("type", width=150, stretch=True)
        self.doc_tree.column("tenant", width=200, stretch=True)
        self.doc_tree.column("expiry", width=100, stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.doc_tree.yview)
        self.doc_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.doc_tree.pack(fill="both", expand=True)
        
        # Load data
        self.load_documents()
    
    def load_documents(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.doc_id, d.doc_type, t.full_name, d.expiry_date
            FROM documents d
            JOIN tenants t ON d.tenant_id = t.tenant_id
            ORDER BY d.expiry_date
        """)
        
        # Clear existing data
        for row in self.doc_tree.get_children():
            self.doc_tree.delete(row)
            
        # Add documents to treeview
        for doc in cursor.fetchall():
            doc_id, doc_type, tenant_name, expiry = doc
            expiry_display = expiry if expiry else "N/A"
            self.doc_tree.insert("", "end", 
                               text=str(doc_id), 
                               values=(doc_type, tenant_name, expiry_display))
        
        conn.close()
    
    def show_add_document_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Document")
        dialog.geometry("500x400")
        
        # Form variables
        tenant_var = tk.StringVar()
        type_var = tk.StringVar()
        expiry_var = tk.StringVar()
        file_path_var = tk.StringVar()
        
        # Form fields
        ttk.Label(dialog, text="Tenant*").pack(pady=(10, 0))
        
        # Tenant dropdown
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT tenant_id, full_name FROM tenants WHERE is_active = 1")
        tenants = cursor.fetchall()
        conn.close()
        
        tenant_names = [f"{name} (ID: {id})" for id, name in tenants]
        tenant_dropdown = ttk.Combobox(dialog, textvariable=tenant_var, values=tenant_names)
        tenant_dropdown.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Document Type*").pack()
        type_dropdown = ttk.Combobox(dialog, textvariable=type_var, 
                                    values=["Lease Agreement", "PAN Card", "Aadhaar", 
                                           "Passport", "Driving License", "Other"])
        type_dropdown.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(dialog, text="Expiry Date (if applicable)").pack()
        expiry_entry = ttk.Entry(dialog, textvariable=expiry_var)
        expiry_entry.pack(fill="x", padx=20, pady=5)
        
        # File upload
        def upload_file():
            filetypes = [("All files", "*.*"), ("PDF files", "*.pdf"), ("Image files", "*.jpg *.jpeg *.png")]
            filepath = filedialog.askopenfilename(filetypes=filetypes)
            if filepath:
                file_path_var.set(filepath)
                file_btn.config(text=f"File: {os.path.basename(filepath)}")
        
        file_btn = ttk.Button(dialog, text="Select Document File", command=upload_file)
        file_btn.pack(pady=10)
        
        # Submit button
        def submit():
            # Validate required fields
            if not tenant_var.get() or not type_var.get() or not file_path_var.get():
                messagebox.showerror("Error", "Please fill all required fields (*)")
                return
                
            try:
                # Extract tenant ID from selection
                tenant_id = int(tenant_var.get().split("(ID: ")[1].rstrip(")"))
                
                # Save file
                saved_path = save_file_to_storage(file_path_var.get(), DOCS_DIR)
                if not saved_path:
                    raise Exception("Failed to save document file")
                
                # Save to database
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO documents (
                        tenant_id, doc_type, file_path, expiry_date
                    ) VALUES (?, ?, ?, ?)
                """, (
                    tenant_id,
                    type_var.get(),
                    saved_path,
                    expiry_var.get() if expiry_var.get() else None
                ))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Document added successfully")
                dialog.destroy()
                self.load_documents()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add document: {str(e)}")
        
        ttk.Button(dialog, text="Add Document", command=submit).pack(pady=20)

# ======================
# Run the Application
# ======================
if __name__ == "__main__":
    root = tk.Tk()
    app = TenantLedgerApp(root)
    root.mainloop()