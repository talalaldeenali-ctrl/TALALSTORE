import requests
import os, shutil, pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, END, LEFT, BOTH, X, Y, Toplevel # <<< تم إصلاح مكان Toplevel هنا
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageTk 
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
import base64
from tkinter import filedialog
import os
import tkinter.messagebox as messagebox
from tkinter import LEFT, X, BOTH, YES
# إذا كنت تستخدم Toplevel ضمن دالة edit_inventory_item محلياً
# تأكد من حذف الاستيراد المحلي الخاطئ التالي من داخل الدالة:
# from tkinter.ttk import Toplevel # هذا السطر يجب حذفه إذا وجد داخل الدالة


# ================== إعدادات الاتصال بالسيرفر (API) ==================
# استبدل localhost بـ IP السيرفر الحقيقي إذا كنت ستعمل من جهاز آخر
API_URL = "http://localhost:8000" 
ADMIN_PIN = "Ana1984"

INV_DIR = "invoice"
REP_DIR = "report"
ASSETS_DIR = "assets"

for d in [INV_DIR, REP_DIR, ASSETS_DIR]: 
    os.makedirs(d, exist_ok=True)

def copy_to_assets(source_path, asset_key):
    """ينسخ الملف المصدر إلى مجلد الأصول ويعيد المسار الجديد."""
    if not source_path: return ""
    file_name = os.path.basename(source_path)
    target_path = os.path.join(ASSETS_DIR, f"{asset_key}_{file_name}")
    try:
        shutil.copy(source_path, target_path)
        return target_path
    except IOError as e:
        messagebox.showerror("File Error", f"فشل في نسخ الملف: {e}")
        return ""

# ================== الخط العربي (إصلاح اللغة) ==================
font_path = "arial.ttf" 
try:
    pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
except:
    print("Warning: Arabic font not found.")

def ar(text):
    """تنسيق النص العربي لدعم العرض الصحيح في Tkinter"""
    return get_display(arabic_reshaper.reshape(text))
# ================== دوال الاتصال بالسيرفر بدلاً من MySQL (نسخة واحدة فقط) ==================
# ================== دوال الاتصال بالسيرفر بدلاً من MySQL (نسخة واحدة فقط) ==================

def get_setting(k):
    """
    جلب قيمة إعداد من السيرفر باستخدام الدالة العامة.
    تستخدمها الدوال العامة الأخرى مثل get_and_save_image.
    """
    try:
        response = requests.get(f"{API_URL}/get_setting/{k}", timeout=5)
        if response.status_code == 200:
            return response.json().get("value") or ""
        else:
            return ""
    except:
        return ""
        

def get_and_save_image(setting_key, filename):
    """
    تجلب الصورة المشفرة بنظام Base64 من السيرفر، 
    تحفظها كملف مؤقت محلياً، وتعيد مسار الملف الجديد.
    """
    # جلب النص الطويل (Base64) من السيرفر عبر الـ API
    img_data_base64 = get_setting(setting_key) 
    
    # التحقق من أن البيانات التي وصلت هي نص Base64 طويل وليست مسار ملف قديم فارغ
    if img_data_base64 and len(img_data_base64) > 100: 
        try:
            # فك تشفير النص إلى بيانات صورة
            img_data = base64.b64decode(img_data_base64)
            # تحديد مسار مؤقت لحفظ الملف بجانب البرنامج
            path = os.path.join(os.getcwd(), filename)
            
            with open(path, "wb") as f:
                f.write(img_data)
            return path # نُعيد المسار الجديد لاستخدامه في الـ PDF أو واجهة الدخول
            
        except Exception as e:
            # يمكن أن يحدث خطأ إذا كان النص تالفاً
            messagebox.showerror("Image Error", f"فشل فك تشفير الصورة: {e}")
            return None
    return None


def set_setting(k, v):
    """حفظ الإعدادات عبر الـ API"""
    try:
        requests.post(f"{API_URL}/set_setting", json={"key": k, "value": str(v)}, timeout=5)
    except:
        pass


def add_placeholder(entry, text):
    """إدارة النصوص المؤقتة (تبقى كما هي لأنها وظيفة واجهة رسومية فقط)"""
    entry.insert(0, text)
    entry.config(foreground='grey')
    def fin(e):
        if entry.get() == text: 
            entry.delete(0, END)
            entry.config(foreground='black')
    def fout(e):
        if not entry.get(): 
            entry.insert(0, text)
            entry.config(foreground='grey')
    entry.bind("<FocusIn>", fin)
    entry.bind("<FocusOut>", fout)

def update_or_insert_inventory(code, item, qty, unit, price, project, supplier, main_qty):
    """إرسال بيانات التحديث للسيرفر ليقوم هو بعملية الدمج والحفظ (لأمان البيانات)"""
    payload = {
        "code": str(code).strip(),
        "item": str(item).strip(),
        "qty": float(qty),
        "unit": str(unit).strip(),
        "price": float(price),
        "project": str(project).strip(),
        "supplier": str(supplier).strip(),
        "main_qty": float(main_qty)
    }
    try:
        response = requests.post(f"{API_URL}/update_inventory", json=payload, timeout=7)
        if response.status_code != 200:
            messagebox.showerror("Error", "فشل تحديث المخزون في السيرفر")
    except Exception as e:
        messagebox.showerror("Connection Error", f"لا يمكن الوصول للسيرفر: {e}")


# بداية كلاس التطبيق الرئيسي
class App(tb.Window):
    def __init__(self):
        super().__init__(themename="cosmo", size=(1200, 800))
       
        self.lang = get_setting("lang") or "ar"
        self.logo = get_setting("logo")
        self.user_role = None
        self.user_perms = {}
        self.cart = [] 
        # انقل تعريف المتغيرات هنا قبل تسجيل الدخول
        self.current_offset = 0 # متتبع الدفعة الحالية
        self.PAGE_SIZE = 50     # حجم الصفحة
        self.loading_complete = False
        self.show_login() # الآن يمكنك استدعاء تسجيل الدخول بأمان
    def t(self, en, ar_text):
        return ar_text if self.lang == "ar" else en

    def get_setting(self, key):
        """
        جلب قيمة إعداد من السيرفر.
        إذا لم توجد القيمة أو السيرفر لم يرد أو حصل خطأ، تعيد قيمة افتراضية فارغة.
        """
        try:
            response = requests.get(f"{self.API_URL}/get_setting/{key}", timeout=5)
            if response.status_code == 200:
                val = response.json().get("value")
                if val is None:  # إذا القيمة None
                    return ""
                return val
            else:
                return ""  # إذا 404 أو أي كود آخر
        except:
            return ""  # إذا فشل الاتصال نهائياً
    def show_login(self):
        """واجهة الدخول الأصلية مع عرض الشعار المحفوظ (باستخدام Base64)"""
        for w in self.winfo_children(): w.destroy()
        self.main_frame = tb.Frame(self)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # >>> استخدام دالة get_and_save_image لجلب الشعار المؤقت: <<<
        # نبحث عن المفتاح "logo_data" في السيرفر
        # تم تغيير الاستدعاء إلى الدالة الخارجية get_and_save_image
        logo_path = get_and_save_image("logo_data", "temp_logo_login.png")
        
        if logo_path:
            try:
                img_open = Image.open(logo_path).resize((150, 150))
                img = ImageTk.PhotoImage(img_open)
                self.logo_label = tb.Label(self.main_frame, image=img)
                self.logo_label.image = img
                self.logo_label.pack(pady=10)
            except Exception as e:
                # طباعة الخطأ في الكونسول للمطور إذا فشل تحميل الصورة
                print(f"Error loading login image: {e}")

        # تم تغيير الاستدعاءات هنا إلى self.get_setting
        tb.Label(self.main_frame, text=self.get_setting("company"), font=("Arial", 24, "bold"), bootstyle=PRIMARY).pack(pady=5)
        tb.Label(self.main_frame, text=self.get_setting("welcome"), font=("Arial", 12), bootstyle=SECONDARY).pack(pady=5)
        
        self.u = tb.Entry(self.main_frame, width=30)
        add_placeholder(self.u, "Username")
        self.u.pack(pady=5)

        self.p = tb.Entry(self.main_frame, show="*", width=30)
        add_placeholder(self.p, "Password")
        self.p.pack(pady=5)

        tb.Button(self.main_frame, text=self.t("LOGIN", "دخول"), width=20, bootstyle=SUCCESS, command=self.login).pack(pady=20)


    def login(self):
        """تسجيل الدخول عبر السيرفر"""
        user = self.u.get()
        pwd = self.p.get()
        if not user or not pwd:
            messagebox.showwarning("!", "أدخل اسم المستخدم وكلمة المرور")
            return
        try:
            payload = {"u": user, "p": pwd}
            response = requests.post(f"{API_URL}/login", json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.user_role = data.get("role", "User")
                # >>>>> أضف هذا السطر لحفظ الصلاحيات المستلمة <<<<<
                self.user_perms = data.get("perms", {}) 
                self.show_main()
            elif response.status_code == 422:
                messagebox.showerror("Error", "تأكد من تنسيق البيانات أو حقل مفقود")
            else:
                messagebox.showerror("Error", "اسم المستخدم أو كلمة المرور خاطئة")
        except Exception as e:
            messagebox.showerror("Connection Error", f"فشل الاتصال بالسيرفر: {e}")

    def upload_logo_to_server(self, setting_key):
        """فتح اختيار ملف، تحويله لـ Base64، ورفعه للسيرفر"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path: return

        try:
            with open(file_path, "rb") as image_file:
                # تحويل الصورة إلى نص Base64
                # إزاحة 12 مسافة هنا لأننا داخل try و داخل with
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
                # إرسال النص الطويل للسيرفر كقيمة للإعداد
                response = requests.post(
                    f"{API_URL}/set_setting", 
                    json={"key": setting_key, "value": encoded_string},
                    timeout=10
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "تم رفع الشعار بنجاح")
                else:
                    messagebox.showerror("Error", "فشل الرفع للسيرفر")
        except Exception as e:
            messagebox.showerror("Error", f"خطأ أثناء المعالجة: {e}")

    def show_main(self):
        """بناء القائمة الجانبية والحاوية الرئيسية (Container)"""
        for w in self.winfo_children(): w.destroy()
        
        # القائمة الجانبية (Sidebar)
        side = tb.Frame(self, bootstyle=DARK, width=200)
        side.pack(side=LEFT, fill=Y)
        
        menu_items = {
            "Inventory": ("inventory", self.view_inv),
            "Invoices": ("invoice", self.view_invoice),
            "Reports": ("reports", self.view_reports),
            "Settings": ("settings", self.open_settings),
            "Backup": ("backup", self.open_backup),
        }
        
        for t_en, (key, cmd) in menu_items.items():
            if self.user_perms.get(key, False):
                btn_text = self.t(t_en, t_en) 
                tb.Button(side, text=btn_text, bootstyle=LINK, command=cmd).pack(fill=X, padx=10, pady=5)

        # منطقة عرض المحتوى (Container)
        self.container = tb.Frame(self, padding=20)
        self.container.pack(fill=BOTH, expand=True)
        
        if self.user_perms.get("inventory", False):
            self.view_inv()
    def load_inv_data(self):
        """جلب بيانات المخزون من السيرفر وعرضها في Treeview"""
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            response = requests.get(f"{API_URL}/inventory", timeout=5)
            if response.status_code == 200:
                rows = response.json().get("data", [])
                for r in rows:
                    self.tree.insert("", END, values=[
                        r.get("id", ""), r.get("code", ""), r.get("item", ""), 
                        r.get("qty", 0), r.get("unit", ""), r.get("price", 0),
                        r.get("project", ""), r.get("supplier", ""), r.get("main_qty", 0)
                    ])
            else:
                messagebox.showerror("Error", "فشل جلب بيانات المخزون")
        except Exception as e:
            messagebox.showerror("Connection Error", f"فشل الاتصال بالسيرفر: {e}")

    def view_inv(self):
        """واجهة عرض المخزون الرئيسية Paged"""
        for w in self.container.winfo_children(): w.destroy()
        self.current_offset = 0 
        self.loading_complete = False

        # إطار أزرار التحكم العلوية
        btn_f = tb.Frame(self.container)
        btn_f.pack(fill=X, pady=5)

        # الأزرار الحالية
        tb.Button(btn_f, text=self.t("Manual Add", "إنشاء سند استلام"), command=self.view_rec_manager).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text=self.t("Import Excel", "استيراد Excel"), command=self.import_excel).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text=self.t("Export Excel", "تصدير Excel"), command=self.export_inv_excel).pack(side=LEFT, padx=5)
        
        # >>> أزرار الحذف والتعديل المضافة <<<
        tb.Button(btn_f, text=self.t("Edit Item", "تعديل صنف"), bootstyle=WARNING, command=self.edit_inventory_item).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text=self.t("Delete Item", "حذف صنف"), bootstyle=DANGER, command=self.delete_inventory_item).pack(side=LEFT, padx=5)
      
        cols = ("id", "code", "item", "qty", "unit", "price", "project", "supplier", "main_qty")
        
        # إنشاء الجدول
        self.tree = ttk.Treeview(self.container, columns=cols, show="headings", bootstyle=INFO)
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        for c in cols: 
            self.tree.heading(c, text=ar(self.t(c.upper(), c.upper())))
            self.tree.column(c, width=100, anchor=CENTER)

        # إطار أزرار التحميل بالأسفل
        btn_f2 = tb.Frame(self.container)
        btn_f2.pack(fill=X, pady=5)
        tb.Button(btn_f2, text=self.t("Load More (50 items)", "تحميل المزيد (50 صنف)"), command=self.load_inv_data).pack()

        self.load_inv_data()

    def edit_inventory_item(self):
        """تعديل صنف محدد عبر نافذة منبثقة (الـ Code للقراءة فقط)"""
        # لم تعد بحاجة لأي استيرادات محلية هنا لأنها في بداية الملف

        if not self.check_admin_access():
            return
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(self.t("Select", "اختر صنف لتعديله"), 
                                 self.t("Select Item", "الرجاء اختيار صنف من الجدول أولاً"))
            return
        
        vals = self.tree.item(selected, "values")
        item_code_val = vals[1] 

        # استخدام tb.Toplevel الآن لأنها مستوردة كـ Toplevel في بداية الملف
        win = Toplevel(self) 
        win.title(self.t("Edit Item", "تعديل الصنف")) 
        win.geometry("400x550")
        
        # >>> استخدام tb.Label الآن <<<
        tb.Label(win, text=f"{self.t('Code', 'الرمز')}: {item_code_val}", 
                 font=('Helvetica', 12, 'bold')).pack(pady=10)

        fields = ["Item", "Qty", "Unit", "Price", "Project", "Supplier", "Main Qty"]
        ents = {}
        for i, f in enumerate(fields):
            label_text = self.t(f, f) 
            tb.Label(win, text=label_text).pack(pady=2) # <<< استخدام tb.Label
            e = tb.Entry(win) # <<< استخدام tb.Entry
            e.insert(0, vals[i+2]) 
            e.pack(pady=5, fill=X, padx=30)
            ents[f] = e

        # استخدام tb.Button
        tb.Button(win, text=self.t("Save Edit", "حفظ التعديل"), bootstyle="success",
               command=lambda: self.save_edit(item_code_val, ents, win)).pack(pady=20)


    def save_edit(self, item_code, entries, edit_win):
        """إرسال التعديلات إلى السيرفر عبر update_inventory"""

        payload = {
            "code": item_code,
            "item": entries["Item"].get(),
            "qty": float(entries["Qty"].get()),
            "unit": entries["Unit"].get(),
            "price": float(entries["Price"].get()),
            "project": entries["Project"].get(),
            "supplier": entries["Supplier"].get(),
            "main_qty": float(entries["Main Qty"].get())
        }

        try:
            response = requests.post(
                f"{API_URL}/update_inventory",
                json=payload,
                timeout=7
            )

            if response.status_code == 200:
                messagebox.showinfo(
                    self.t("Success", "تم"),
                    self.t("Updated", "تم تحديث الصنف بنجاح")
                )
                edit_win.destroy()
                self.view_inv()
            else:
                messagebox.showerror(
                    self.t("Error", "خطأ"),
                    f"فشل السيرفر: {response.status_code}"
                )

        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"فشل الاتصال بالسيرفر: {e}"
            )
        # تم حذف السطر الزائد والمكرر الذي كان يسبب IndentationError/SyntaxError في هذا المكان



    def delete_inventory_item(self):
        """حذف صنف محدد عبر API"""
        if not self.check_admin_access():
            messagebox.showerror("Denied", "الوصول مقيد للمسؤولين فقط")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "اختر صنف للحذف")
            return
        
        vals = self.tree.item(selected[0], "values")
        code = vals[1] 

        if messagebox.askyesno("Confirm", f"هل تريد حذف الصنف {code}?"):
            try:
                # سنقوم بإضافة هذا المسار delete_item في ملف server.py لاحقاً
                response = requests.delete(f"{API_URL}/delete_item/{code}", timeout=5)
                if response.status_code == 200:
                    messagebox.showinfo("Deleted", f"تم حذف الصنف {code}")
                    self.load_inv_data() # تحديث الجدول فوراً
                else:
                    messagebox.showerror("Error", "فشل الحذف من السيرفر")
            except Exception as e:
                messagebox.showerror("Connection Error", f"خطأ اتصال: {e}")

    # ================== الكتلة المفقودة (نظام الفواتير المطور) ==================
    def check_admin_access(self):
        """التحقق مما إذا كان المستخدم يملك رتبة admin (بغض النظر عن حالة الأحرف)"""
        # استخدام .lower() لتحويل قيمة الرتبة إلى أحرف صغيرة للمقارنة
        if self.user_role and self.user_role.lower() == "admin":
            return True
        else:
            messagebox.showerror(
                self.t("Access Denied", "تم رفض الوصول"), 
                self.t("Admin Only", "هذه العملية مسموحة للمدراء فقط")
            )
            return False
    def view_invoice(self):
        """واجهة إنشاء الفاتورة الكاملة مع البحث التلقائي عبر API"""
        for w in self.container.winfo_children(): w.destroy()
        self.cart = [] # تفريغ العربة

        tb.Label(self.container, text=self.t("Create Invoice", "إنشاء فاتورة صرف مواد"), 
                 font=("Arial", 20, "bold")).pack(pady=10)

        # 1. بيانات المستلم والمشروع
        top = tb.Frame(self.container)
        top.pack(fill=X, pady=5)
        
        self.inv_recipient = tb.Entry(top)
        # تم تصحيح الاستدعاء لاستخدام الدالة العامة مباشرة
        add_placeholder(self.inv_recipient, self.t("Recipient Name", "اسم المستلم"))
        self.inv_recipient.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        self.inv_project = tb.Entry(top)
        # تم تصحيح الاستدعاء لاستخدام الدالة العامة مباشرة
        add_placeholder(self.inv_project, self.t("Project Name", "اسم المشروع"))
        self.inv_project.pack(side=LEFT, padx=5, expand=True, fill=X)

        # 2. محرك البحث الذكي (اسم المادة أو الكود)
        search_f = tb.Frame(self.container)
        search_f.pack(fill=X, pady=10)
        tb.Label(search_f, text=self.t("Search Item", "بحث عن منتج:")).pack(side=LEFT)
        
        self.search_ent = tb.Entry(search_f)
        self.search_ent.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.search_ent.bind("<KeyRelease>", self.search_items)

        # قائمة النتائج (Listbox)
        self.search_list = tk.Listbox(self.container, height=5, font=("Arial", 11))
        self.search_list.pack(fill=X)
        self.search_list.bind("<<ListboxSelect>>", self.add_item_to_cart)

        # 3. جدول معاينة العربة (Cart Tree)
        cols = ("code", "item", "project", "supplier", "qty", "unit", "price")
        self.cart_tree = ttk.Treeview(self.container, columns=cols, show="headings", bootstyle=SECONDARY)
        for c in cols:
            self.cart_tree.heading(c, text=ar(self.t(c.upper(), c.upper())))
            self.cart_tree.column(c, width=110, anchor=CENTER)
        self.cart_tree.pack(fill=BOTH, expand=True, pady=10)

        # 4. أزرار الحفظ والإلغاء
        btn_action = tb.Frame(self.container)
        btn_action.pack(fill=X, pady=10)
        
        tb.Button(btn_action, text=self.t("Save & Print PDF", "حفظ وطباعة الفاتورة"),
                  bootstyle=SUCCESS, command=self.save_invoice).pack(side=LEFT, padx=5)
        
        tb.Button(btn_action, text=self.t("Clear Cart", "تفريغ العربة"),
                  bootstyle=DANGER, command=self.view_invoice).pack(side=LEFT, padx=5)


    def search_items(self, event=None):
        """دالة البحث اللحظي عبر السيرفر"""
        val = self.search_ent.get()
        self.search_list.delete(0, END)
        if not val or val == self.t("Search Item", "بحث عن منتج"): return
        
        try:
            # إرسال طلب البحث للسيرفر
            response = requests.get(f"{API_URL}/search_items", params={"q": val}, timeout=3)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for r in results:
                    # r[0] هو الاسم، r[1] هو الكود
                    self.search_list.insert(END, f"{r[0]} ({r[1]})")
        except:
            pass # فشل صامت لتحسين تجربة المستخدم أثناء الكتابة السريعة
    def add_item_to_cart(self, event=None):
        """إضافة الصنف المختار من القائمة إلى العربة مع فحص الكمية عبر السيرفر"""

        if not self.search_list.curselection():
            return

        sel_text = self.search_list.get(self.search_list.curselection())

        match = re.search(r'\((.*?)\)', sel_text)
        if not match:
            return

        item_code = match.group(1)

        if any(row[0] == item_code for row in self.cart):
            messagebox.showwarning(
                "!",
                self.t("Already in cart", "المادة موجودة بالفعل")
            )
            return

        qty = simpledialog.askfloat(
            self.t("Qty", "الكمية"),
            self.t("Enter Quantity:", "أدخل الكمية المطلوبة:")
        )

        if not qty or qty <= 0:
            return

        try:
            # جلب تفاصيل المادة والكمية المتوفرة من السيرفر
            response = requests.get(
                f"{API_URL}/item_details/{item_code}",
                timeout=5
            )

            if response.status_code == 200:
                res = response.json()

                if qty > float(res['qty']):
                    messagebox.showerror(
                        "!",
                        self.t("Stock low", f"الكمية لا تكفي. المتاح: {res['qty']}")
                    )
                    return

                # (code, item, project, supplier, qty, unit, price)
                new_row = (
                    res['code'],
                    res['item'],
                    res['project'],
                    res['supplier'],
                    qty,
                    res['unit'],
                    res['price']
                )

                self.cart.append(new_row)

                self.cart_tree.insert(
                    "",
                    END,
                    values=(
                        res['code'],
                        ar(res['item']),
                        ar(res['project']),
                        ar(res['supplier']),
                        qty,
                        ar(res['unit']),
                        res['price']
                    )
                )
            else:
                messagebox.showerror("Error", "فشل جلب بيانات الصنف")

        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"خطأ اتصال: {e}"
            )

    def view_rec_manager(self):
        """واجهة بناء سند استلام (توريد) متعدد الأصناف عبر API"""
        for w in self.container.winfo_children(): w.destroy()
        self.cart = [] 
        
        tb.Label(self.container, text=self.t("New Receipt", "إنشاء سند استلام جديد - توريد مخزني"), font=("Arial", 18)).pack(pady=10)

        top = tb.Frame(self.container)
        top.pack(fill=X, pady=5)
        
        self.rec_supplier = tb.Entry(top)
        self.add_placeholder(self.rec_supplier, self.t("Supplier", "المورد"))
        self.rec_supplier.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        self.rec_project = tb.Entry(top)
        self.add_placeholder(self.rec_project, self.t("Project", "المشروع/الموقع"))
        self.rec_project.pack(side=LEFT, padx=5, expand=True, fill=X)

        btn_f = tb.Frame(self.container)
        btn_f.pack(fill=X, pady=10)
        
        tb.Button(btn_f, text=self.t("Add Item", "إضافة صنف للقائمة"), command=self.add_rec_item_ui, bootstyle=INFO).pack(side=LEFT, padx=5)
        tb.Button(btn_f, text=self.t("Save & Print PDF", "حفظ السند وطباعته"), command=self.save_receipt_bulk, bootstyle=SUCCESS).pack(side=LEFT, padx=5)

        cols = ("code", "item", "qty", "unit", "price", "project", "supplier")
        self.cart_tree = ttk.Treeview(self.container, columns=cols, show="headings", bootstyle=SECONDARY)
        for c in cols:
            self.cart_tree.heading(c, text=ar(self.t(c.upper(), c.upper())))
            self.cart_tree.column(c, width=100, anchor=CENTER)
        self.cart_tree.pack(fill=BOTH, expand=True)

    def add_rec_item_ui(self):
        """نافذة إضافة مادة مع جلب البيانات من السيرفر تلقائياً عند إدخال الكود"""
        win = tb.Toplevel(title=self.t("Add Item", "إضافة بند للسند"))
        win.geometry("450x600")

        fields = [("Code", "الكود"), ("Item Name", "اسم المادة"), ("Qty", "الكمية"), ("Unit", "الوحدة"), ("Price", "السعر"), ("Project", "المشروع"), ("Supplier", "المورد")]
        ents = {}
        for en, ar_t in fields:
            tb.Label(win, text=self.t(en, ar_t)).pack(pady=2)
            e = tb.Entry(win)
            e.pack(pady=2, padx=20, fill=X)
            ents[en] = e

        ents["Project"].insert(0, self.rec_project.get() if self.rec_project.get() != self.t("Project", "المشروع/الموقع") else "")
        ents["Supplier"].insert(0, self.rec_supplier.get() if self.rec_supplier.get() != self.t("Supplier", "المورد") else "")

        def on_code_change(event):
            """جلب بيانات الصنف من السيرفر عند الخروج من حقل الكود"""
            code_val = ents["Code"].get()
            if len(code_val) < 1: return
            try:
                # نستخدم مسار item_details الذي أعددناه سابقاً في السيرفر
                response = requests.get(f"{API_URL}/item_details/{code_val}", timeout=5)
                if response.status_code == 200:
                    r = response.json()
                    ents["Item Name"].delete(0, END); ents["Item Name"].insert(0, r['item'])
                    ents["Unit"].delete(0, END); ents["Unit"].insert(0, r['unit'])
                    ents["Price"].delete(0, END); ents["Price"].insert(0, r['price'])
            except: pass
        
        ents["Code"].bind("<FocusOut>", on_code_change)

        def save_to_list():
            """حفظ مادة جديدة في العربة مع معالجة None وتحويل الكميات والأسعار"""
            try:
                row = (
                    ents["Code"].get() or "",
                    ents["Item Name"].get() or "",
                    ents["Project"].get() or "",
                    ents["Supplier"].get() or "",
                    float(ents["Qty"].get() or 0),
                    ents["Unit"].get() or "",
                    float(ents["Price"].get() or 0)
                )
                self.cart.append(row)
                # عرض البيانات في الـ Treeview
                self.cart_tree.insert(
                    "",
                    END,
                    values=(row[0], ar(row[1]), row[4], ar(row[5]), row[6], ar(row[2]), ar(row[3]))
                )
                # غلق النافذة بعد الإضافة
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "الكمية والسعر يجب أن تكون أرقاماً")
    def save_receipt_bulk(self):
        """حفظ سند التوريد عبر API"""
        if not self.cart:
            messagebox.showwarning("!", "القائمة فارغة")
            return
        formatted_cart = []
        for item in self.cart:
            formatted_cart.append({
                "code": item[0],
                "item": item[1],
                "project": item[2],
                "supplier": item[3],
                "qty": item[4],
                "unit": item[5],
                "price": item[6]
            })
        try:
            response = requests.post(
                f"{API_URL}/process_transaction",
                params={"type": "IN", "recipient": "System", "project": self.rec_project.get()},
                json=formatted_cart,
                timeout=10
            )
            if response.status_code == 200:
                receipt_no = response.json().get("no")
                self.save_receipt_pdf(self.rec_supplier.get(), self.rec_project.get(), receipt_no)
                messagebox.showinfo("Done", f"تم حفظ السند رقم {receipt_no} بنجاح")
                self.view_inv()
            else:
                messagebox.showerror("Error", response.json().get("detail", "فشل الحفظ"))
        except Exception as e:
            messagebox.showerror("Connection Error", f"فشل الاتصال بالسيرفر: {e}")

    def save_invoice(self):
        """حفظ فاتورة الصرف عبر API"""
        if not self.cart:
            messagebox.showerror("Invoice", "العربة فارغة")
            return
        recipient = self.inv_recipient.get()
        project_name = self.inv_project.get()
        if not recipient:
            messagebox.showerror("Invoice", "الرجاء إدخال اسم المستلم")
            return
        formatted_cart = []
        for row in self.cart:
            formatted_cart.append({
                "code": row[0], "item": row[1], "project": row[2],
                "supplier": row[3], "qty": row[4], "unit": row[5], "price": row[6]
            })
        try:
            response = requests.post(
                f"{API_URL}/process_transaction",
                params={"type": "OUT", "recipient": recipient, "project": project_name},
                json=formatted_cart,
                timeout=10
            )
            if response.status_code == 200:
                invoice_no = response.json().get("no")
                self.generate_pdf(os.path.join(INV_DIR, f"INV_{invoice_no}.pdf"), recipient, project_name, invoice_no)
                messagebox.showinfo("Success", f"تم حفظ الفاتورة رقم {invoice_no} بنجاح")
                self.view_invoice()
            else:
                messagebox.showerror("Stock Error", response.json().get("detail", "فشل الصرف"))
        except Exception as e:
            messagebox.showerror("Connection Error", f"فشل الاتصال بالسيرفر: {e}")


    # دوال الـ PDF تبقى كما هي لأنها تعتمد على البيانات المحلية (self.cart) والملفات
    def save_receipt_pdf(self, recipient, project_name, receipt_no):
        pdf_path = os.path.join(INV_DIR, f"RECEIPT_{receipt_no}.pdf")
        self.generate_issue_pdf(pdf_path, recipient, project_name, receipt_no, "سند استلام مواد")

    def generate_receipt_pdf(self, pdf_path, recipient, project, receipt_no):
        try:
            self.generate_issue_pdf(pdf_path=pdf_path, recipient=recipient, project=project, invoice_no=receipt_no)
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))
    def generate_pdf(self, pdf_path, recipient, project, invoice_no):
        """غلاف توافق مع الاستدعاءات القديمة"""
        self.generate_issue_pdf(
          pdf_path,
          recipient,
          project,
          invoice_no,
          self.t("Issue Document", "سند صرف مواد")
        )

    def generate_issue_pdf(self, pdf_path, recipient, project, doc_no, title):
        """محرك موحد لطباعة السندات (يعتمد على البيانات المحلية والإعدادات عبر API و Base64)"""
        try:
            # تأكد من استيراد Spacer في بداية ملفك: from reportlab.platypus import ..., Spacer, ...
            cpdf = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                topMargin=1*cm,
                bottomMargin=1*cm,
                leftMargin=1.5*cm,
                rightMargin=1.5*cm
            )
            elements = []
            style_normal = ParagraphStyle("NormalFont", fontName="ArabicFont", fontSize=10, alignment=1)
            style_h1 = ParagraphStyle("H1", fontName="ArabicFont", fontSize=18, alignment=1, spaceAfter=20, textColor=colors.blue)
            style_sign = ParagraphStyle("Sign", fontName="ArabicFont", fontSize=11, alignment=2)

            # >>> استخدام نظام Base64 لجلب مسارات الصور المؤقتة: <<<
            # تأكد أن دالة get_and_save_image معرفة خارج الكلاس
            logo_path = get_and_save_image("logo_data", "temp_logo_pdf.png")
            watermark_path = get_and_save_image("wm_data", "temp_wm_pdf.png")

            # استخدام Spacer إذا لم يتم العثور على المسار المؤقت لتجنب خطأ wrapOn
            logo_left = RLImage(logo_path, 3*cm, 3*cm) if logo_path else Spacer(0, 0)
            logo_right = Spacer(0, 0) # يمكن استخدامها لشعار إضافي

            company_info = [
                Paragraph(f"<b>{ar(get_setting('company') or '')}</b>", style_h1),
                Paragraph(ar(get_setting('addr1') or ''), style_normal)
            ]

            header_table = Table([[logo_left, company_info, logo_right]], colWidths=[4*cm, 11*cm, 4*cm])
            header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'CENTER')]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(ar(title), style_h1))

            info_table = Table(
                [
                    [ar(f"رقم السند: {doc_no}"), "", ar(f"اسم المستلم: {recipient}")],
                    [ar(f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}"), "", ar(f"المشروع: {project}")]
                ],
                colWidths=[6*cm, 7*cm, 6*cm]
            )
            info_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'ArabicFont'), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            elements.append(info_table)
            elements.append(Spacer(1, 15))

            # بناء بيانات الجدول من العربة الحالية في الذاكرة (تم تصحيح الفهارس)
            data = [[ar("الوحدة"), ar("الكمية"), ar("وصف المادة"), ar("الكود")]]
            for row in self.cart:
                # الفهارس: 0=code, 1=item, 4=qty, 5=unit, 2=project, 3=supplier, 6=price
                data.append([
                    ar(row[5]),  # الوحدة
                    row[4],      # الكمية
                    ar(row[1]),  # وصف المادة
                    row[0]       # الكود
                ])
                
            for _ in range(max(0, 12 - len(self.cart))):
                data.append(["", "", "", ""])

            table = Table(data, colWidths=[3*cm, 3*cm, 10*cm, 3*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'ArabicFont'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))

            elements.append(table)
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(ar("توقيع المستلم: ______________________"), style_sign))

            # تحديث دالة العلامة المائية لاستخدام المسار الجديد
            def add_watermark(canvas, doc):
                canvas.saveState()
                if watermark_path: # نستخدم المسار المؤقت الجديد
                    try:
                        canvas.setFillAlpha(0.1)
                        canvas.drawImage(watermark_path, 5*cm, 8*cm, 11*cm, 11*cm, mask='auto')
                    except: pass
                canvas.setFont("Helvetica-Bold", 50)
                canvas.setFillColorRGB(0.72, 0.72, 0.72)
                canvas.translate(A4[0] / 2, A4[1] / 2)
                canvas.rotate(45)
                canvas.drawCentredString(0, -3*cm, "TALAL STORE")
                canvas.restoreState()

            cpdf.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
            os.startfile(pdf_path)

        except Exception as e:
            messagebox.showerror("PDF Error", f"فشل في إنشاء ملف PDF: {str(e)}")


    def open_settings(self):
        """نظام الحماية للدخول إلى الإعدادات (باستخدام PIN من السيرفر أو محلي)"""
        pin = simpledialog.askstring(
            self.t("Security", "حماية"),
            self.t("Enter PIN", "ادخل الرقم السري"),
            show="*",
            parent=self
        )
        # تم تصحيح الاستدعاء إلى self.get_setting
        current_pin = self.get_setting("admin_pin") or ADMIN_PIN
        if pin != current_pin:
            messagebox.showerror(self.t("Denied", "مرفوض"), self.t("Wrong PIN", "رقم سري غير صحيح"))
            return
        self.view_settings()

    def view_settings(self):
        """إدارة إعدادات النظام والشعارات عبر API"""
        for w in self.container.winfo_children(): w.destroy()
        self.set_entries = {}
        
        # التحقق من الصلاحيات
        if str(self.user_role).lower() != 'admin':
            tb.Label(self.container, text=ar("عذراً، الوصول للإعدادات للمسؤولين فقط"), font=("Arial", 16), foreground="red").pack(pady=50)
            return

        tb.Label(self.container, text=self.t("System Settings", "إعدادات النظام العامة"), font=("Arial", 18)).pack(pady=10)
        
        fields = [("company", "اسم الشركة"), ("addr1", "العنوان الرئيسي"), ("welcome", "رسالة الترحيب"), ("lang", "اللغة (ar/en)"), ("admin_pin", "رقم PIN الإعدادات")]
        for k, l in fields:
            tb.Label(self.container, text=ar(l)).pack(pady=2)
            e = tb.Entry(self.container, width=60)
            # تم تصحيح الاستدعاء إلى self.get_setting
            val = self.get_setting(k)
            e.insert(0, val)
            e.pack(pady=2)
            self.set_entries[k] = e

        btn_f = tb.Frame(self.container)
        btn_f.pack(pady=20)
        # تغيير دالة الاستدعاء من upload_generic إلى upload_logo_to_server
        tb.Button(btn_f, text=ar("رفع الشعار الرئيسي"), 
                  command=lambda: self.upload_logo_to_server("logo_data"), 
                  bootstyle=INFO).pack(side=LEFT, padx=5)
        
        # يمكنك إضافة زر للعلامة المائية (Watermark) أيضاً بنفس الطريقة
        tb.Button(btn_f, text=ar("رفع العلامة المائية"), 
                  command=lambda: self.upload_logo_to_server("wm_data"), 
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        tb.Button(btn_f, text=ar("حفظ الإعدادات"), command=self.save_settings, bootstyle=SUCCESS).pack(side=LEFT, padx=20)
        
        adv_f = tb.Labelframe(self.container, text=ar("إدارة متقدمة"), padding=10)
        adv_f.pack(fill=X, pady=20, padx=20)
        
        tb.Button(adv_f, text=ar("إضافة مستخدم"), command=self.add_user_ui, bootstyle=SUCCESS).pack(side=LEFT, padx=10)
        tb.Button(adv_f, text=ar("نسخ احتياطي"), command=self.backup_database, bootstyle=WARNING).pack(side=LEFT, padx=10)
        tb.Button(adv_f, text=ar("تصدير المخزون"), command=self.export_inv_excel, bootstyle=INFO).pack(side=LEFT)
    def setup_inventory_buttons(self):
        """إضافة أزرار التحكم (تعديل، حذف) أسفل جدول المخزون ودعم اللغة"""
        btn_frame = tb.Frame(self.container)
        btn_frame.pack(pady=10, fill=X)

        self.edit_btn = tb.Button(
            btn_frame, 
            text=self.t("Edit Item", "تعديل الصنف"), # استخدام دالة الترجمة
            command=self.edit_inventory_item, 
            bootstyle=INFO, 
            width=15
        )
        self.edit_btn.pack(side=RIGHT, padx=10)

        self.delete_btn = tb.Button(
            btn_frame, 
            text=self.t("Delete Item", "حذف الصنف"), # استخدام دالة الترجمة
            command=self.delete_inventory_item, 
            bootstyle=DANGER, 
            width=15
        )
        self.delete_btn.pack(side=RIGHT, padx=10)

        self.refresh_btn = tb.Button(
            btn_frame, 
            text=self.t("Refresh List", "تحديث القائمة"), # استخدام دالة الترجمة
            command=self.load_inv_data, 
            bootstyle=SECONDARY, 
            width=15
        )
        self.refresh_btn.pack(side=LEFT, padx=10)
       

    def save_settings(self):
        """حفظ إعدادات النظام في MySQL وتحديث الواجهة فوراً"""
        try:
            for k, e in self.set_entries.items():
                set_setting(k, e.get())
            
            # تحديث متغير اللغة في الكلاس لضمان استجابة البرنامج فوراً
            self.lang = get_setting("lang") or "ar" 
            
            messagebox.showinfo(self.t("Success", "نجاح"), self.t("Settings saved successfully", "تم حفظ الإعدادات بنجاح"))
            
            # إعادة بناء الواجهة الرئيسية لتطبيق اللغة الجديدة والشعار الجديد
            self.show_main()
        except Exception as e:
            messagebox.showerror("Error", f"فشل حفظ الإعدادات: {e}")
    def add_user_ui(self):
        """إضافة مستخدم جديد"""
        win = tb.Toplevel(title=ar("إضافة مستخدم جديد"))
        win.geometry("400x500")
        
        fields = ["Username", "Password", "Role (Admin/User)"]
        ents = {}
        for f in fields:
            tb.Label(win, text=ar(f)).pack(pady=5)
            e = tb.Entry(win)
            e.pack(pady=5, padx=30, fill=X)
            ents[f] = e

        def save_user():
            u, p, r = ents["Username"].get(), ents["Password"].get(), ents["Role (Admin/User)"].get()
            if not u or not p:
                messagebox.showwarning("!", "الرجاء إدخال الاسم وكلمة المرور")
                return
            
            conn = get_db_connection()
            if not conn: return
            c = conn.cursor()
            try:
                c.execute("SELECT username FROM users WHERE username=%s", (u,))
                if c.fetchone():
                    messagebox.showerror("Error", "اسم المستخدم موجود مسبقاً")
                    return
                
                c.execute("""INSERT INTO users (username, password, role, can_inventory, can_invoice, can_reports, can_settings, can_backup) 
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (u, p, r, 1, 1, 1, 1, 1))
                conn.commit()
                messagebox.showinfo("Success", f"تمت إضافة المستخدم {u} بنجاح")
                win.destroy()
            finally:
                c.close(); conn.close()

        tb.Button(win, text=ar("حفظ المستخدم"), command=save_user, bootstyle=SUCCESS).pack(pady=20)

    # دالة فرعية للتأكد من وجود المجلدات (أمان إضافي)
    def check_directories(self):
        for d in [INV_DIR, REP_DIR, ASSETS_DIR]:
            if not os.path.exists(d):
                os.makedirs(d)

    def import_excel(self):
        """استيراد بيانات المخزن مع فحص دقيق لمنع تكرار الأسطر"""
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if not path: return
        
        try:
            df = pd.read_excel(path)
            # قائمة الأعمدة المطلوبة للتحقق من سلامة الملف
            required = ['code', 'item', 'qty', 'unit', 'price', 'project', 'supplier', 'main_qty']
            if not all(col in df.columns for col in required):
                messagebox.showerror(self.t("Import Error", "خطأ استيراد"), 
                                   self.t("Excel must contain: ", "يجب أن يحتوي الملف على الأعمدة: ") + str(required))
                return
            
            success_count = 0
            for _, row in df.iterrows():
                try:
                    # استدعاء دالة التحديث الذكي التي تمنع التكرار
                    update_or_insert_inventory(
                        code=str(row['code']),
                        item=str(row['item']),
                        qty=row['qty'],
                        unit=str(row['unit']),
                        price=row['price'],
                        project=str(row['project']),
                        supplier=str(row['supplier']),
                        main_qty=row['main_qty']
                    )
                    success_count += 1
                except Exception as row_error:
                    print(f"Error in row: {row_error}")
                    continue
            
            self.load_inv_data()
            messagebox.showinfo(self.t("Import Done", "تم الاستيراد"), 
                               self.t(f"Successfully imported {success_count} items.", f"تم استيراد {success_count} صنف بنجاح."))
        except Exception as e:
            messagebox.showerror("Critical Error", f"فشل قراءة ملف الإكسل: {e}")

    def export_inv_excel(self):
        """تصدير كامل بيانات المخزن الحالية إلى ملف Excel مع الحفاظ على الترميز"""
        conn = get_db_connection()
        if not conn: return
        try:
            # جلب البيانات مباشرة من MySQL
            query = "SELECT code, item, qty, unit, price, project, supplier, main_qty FROM inventory"
            df = pd.read_sql(query, conn)
            
            # تحديد مسار الحفظ وتوليد اسم ملف تلقائي بالتاريخ
            file_name = f"Inventory_Backup_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=file_name)
            
            if path:
                df.to_excel(path, index=False)
                messagebox.showinfo(self.t("Export Success", "نجاح التصدير"), 
                                   self.t("Data exported to: ", "تم تصدير البيانات إلى: ") + path)
        except Exception as e:
            messagebox.showerror("Export Error", f"حدث خطأ أثناء التصدير: {e}")
        finally:
            conn.close()




    def view_reports(self):
        """واجهة التقارير الشاملة مع فلاتر البحث"""
        for w in self.container.winfo_children(): w.destroy()
        
        tb.Label(self.container, text=self.t("Inventory Movement Report", "تقرير حركات المخازن"), font=("Arial", 18)).pack(pady=10)

        filter_f = tb.Frame(self.container)
        filter_f.pack(fill=X, pady=10)

        tb.Button(filter_f, text=self.t("View All", "عرض الكل"), command=lambda: self.load_reports("ALL"), bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        tb.Button(filter_f, text=self.t("In (IN)", "الوارد (IN)"), command=lambda: self.load_reports("IN"), bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(filter_f, text=self.t("Out (OUT)", "الصادر (OUT)"), command=lambda: self.load_reports("OUT"), bootstyle=DANGER).pack(side=LEFT, padx=5)
        tb.Button(filter_f, text=self.t("Export Current Report", "تصدير للتقرير الحالي"), command=self.export_reports_excel, bootstyle=INFO).pack(side=RIGHT, padx=5)

        # جدول التقارير
        cols = ("date", "code", "item", "qty", "type", "person", "project", "supplier")
        self.rep_tree = ttk.Treeview(self.container, columns=cols, show="headings", bootstyle=INFO)
        for c in cols:
            # استخدام self.t لترجمة رؤوس الأعمدة
            self.rep_tree.heading(c, text=ar(self.t(c.upper(), c.upper())))
            self.rep_tree.column(c, width=110, anchor=CENTER)
        
        self.rep_tree.pack(fill=BOTH, expand=True, pady=10)
        self.current_filter = "ALL"
        self.load_reports("ALL")

    def load_reports(self, filter_type):
        """جلب الحركات من MySQL بناءً على نوع الحركة"""
        self.current_filter = filter_type
        for item in self.rep_tree.get_children(): self.rep_tree.delete(item)
        
        conn = get_db_connection()
        if not conn: return
        c = conn.cursor(buffered=True)
        try:
            if filter_type == "ALL":
                c.execute("SELECT date, code, item, qty, type, person, project, supplier FROM transactions ORDER BY id DESC")
            else:
                c.execute("SELECT date, code, item, qty, type, person, project, supplier FROM transactions WHERE type LIKE %s ORDER BY id DESC", (f"{filter_type}%",))
            
            rows = c.fetchall()
            for r in rows:
                processed = [ar(v) if isinstance(v, str) else v for v in r]
                self.rep_tree.insert("", END, values=processed)
        finally:
            c.close(); conn.close()

 
    def export_reports_excel(self):
        """تصدير التقرير المعروض حالياً إلى ملف Excel"""
        conn = get_db_connection()
        if not conn: return
        try:
            query = "SELECT date, code, item, qty, type, person, project, supplier FROM transactions"
            if self.current_filter != "ALL":
                query += f" WHERE type LIKE '{self.current_filter}%'"
            
            df = pd.read_sql(query, conn)
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Report_{self.current_filter}.xlsx")
            if path:
                df.to_excel(path, index=False)
                messagebox.showinfo("Success", "تم تصدير التقرير بنجاح")
        except Exception as e:
            messagebox.showerror("Error", f"فشل التصدير: {e}")
        finally:
            conn.close()


    def upload_generic(self, key):
        """رفع الصور وحفظ المسار عبر الـ API"""
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if path:
            new_path = copy_to_assets(path, key)
            if new_path:
                set_setting(key, new_path)
                messagebox.showinfo("Success", ar(f"تم تحديث {key} بنجاح"))
                if key == "logo": self.logo = new_path

    def open_backup(self):
        """واجهة النسخ الاحتياطي عبر السيرفر"""
        pin = simpledialog.askstring(self.t("Security", "حماية"), self.t("Enter PIN", "ادخل الرقم السري"), show="*", parent=self)
        if pin != ADMIN_PIN:
            messagebox.showerror(self.t("Denied", "مرفوض"), ar("الرقم السري غير صحيح"))
            return
            
        for w in self.container.winfo_children(): w.destroy()
        tb.Label(self.container, text=self.t("Backup & Restore", "النسخ الاحتياطي السحابي"), font=("Arial", 18)).pack(pady=20)
        
        f = tb.Frame(self.container)
        f.pack(pady=20)
        
        msg = "يتم تنفيذ النسخ الاحتياطي الآن مباشرة على السيرفر لضمان سلامة قاعدة البيانات السحابية."
        tb.Label(f, text=ar(msg), wraplength=600, justify=CENTER, font=("Arial", 11)).pack(pady=10)
        
        btn_f = tb.Frame(f)
        btn_f.pack(pady=20)
        tb.Button(btn_f, text=ar("بدء النسخ الاحتياطي الآن"), command=self.backup_database, bootstyle=SUCCESS).pack(side=LEFT, padx=10)
        tb.Button(btn_f, text=ar("فتح مجلد التقارير المحلي"), command=lambda: os.startfile(REP_DIR), bootstyle=INFO).pack(side=LEFT, padx=10)

    def backup_database(self):
        """إرسال أمر للسيرفر لعمل نسخة احتياطية"""
        try:
            response = requests.post(f"{API_URL}/create_backup", timeout=20)
            if response.status_code == 200:
                file_name = response.json().get("file")
                messagebox.showinfo(ar("النسخ الاحتياطي"), ar(f"تم إنشاء النسخة بنجاح على السيرفر: {file_name}"))
            else:
                messagebox.showerror("Error", ar("فشل السيرفر في إنشاء النسخة الاحتياطية"))
        except:
            messagebox.showerror("Error", ar("فشل الاتصال بالسيرفر"))

    def on_closing(self):
        """تنبيه قبل إغلاق البرنامج"""
        if messagebox.askokcancel(self.t("Exit", "خروج"), ar("هل تريد الخروج من نظام مخازن الراجحي 2026؟")):
            self.destroy()

# ================== تشغيل محرك البرنامج (Main Loop) ==================

if __name__ == "__main__":
    try:
        # التأكد من وجود مجلدات العمل المحلية
        for d in [INV_DIR, REP_DIR, ASSETS_DIR]:
            if not os.path.exists(d): os.makedirs(d)
            
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
        
    except Exception as e:
        error_msg = f"[{datetime.now()}] CRITICAL ERROR: {str(e)}\n"
        with open("critical_error_log.txt", "a", encoding="utf-8") as f:
            f.write(error_msg)
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("System Crash", f"حدث خطأ غير متوقع:\n{e}")

