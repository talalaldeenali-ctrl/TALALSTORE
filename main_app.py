# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error as mysql_error
from sqlalchemy import create_engine
import io
import sys  # تمت إضافته لضمان عمل دوال فتح الملفات
from datetime import datetime
import os
import shutil
import warnings
import subprocess
import bcrypt
from PIL import Image
import base64
import ctypes
import time
import atexit
# مكتبات الـ PDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
import zipfile
import streamlit as st
import ctypes
import platform
import fitz
from sqlalchemy import text


# ==========================
# دالة لتفعيل منع السكون
# ==========================
def prevent_sleep():
    if platform.system() == "Windows":
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

# ==========================
# دالة لإعادة النظام لوضعه الطبيعي
# ==========================
def allow_sleep():
    if platform.system() == "Windows":
        ES_CONTINUOUS = 0x80000000
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

# ==========================
# تفعيل منع السكون تلقائيًا للمسؤول
# ==========================
if st.session_state.get('user_role') == 'admin':
    if "sleep_prevented" not in st.session_state or not st.session_state.sleep_prevented:
        prevent_sleep()
        st.session_state.sleep_prevented = True

    st.info("💡 تم تفعيل منع السكون تلقائيًا. الكمبيوتر لن يدخل في وضع السكون أثناء تشغيل التطبيق.")

# إخفاء تحذيرات Pandas 
warnings.filterwarnings("ignore", category=UserWarning)

# ================== الإعدادات وقاعدة البيانات ==================
# ================== الإعدادات وقاعدة البيانات السحابية الجديدة ==================
# ================== الإعدادات وقاعدة البيانات السحابية الجديدة ==================
MYSQL_HOST = "mysql-108ceb4c-talalaideenali-b880.k.aivencloud.com" 
MYSQL_USER = "avnadmin"
MYSQL_PASS = "AVNS_Kvb4qC_6i-JnNKt4Wn0"
MYSQL_DB   = "defaultdb"
MYSQL_PORT = 19554
ADMIN_PIN  = "Ana1984"

# إنشاء المجلدات الضرورية
for folder in ["assets", "invoice", "report", "backups", "uploads"]:
    os.makedirs(folder, exist_ok=True)

connection_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=MYSQL_USER,
    password=MYSQL_PASS,
    host=MYSQL_HOST,
    port=int(MYSQL_PORT),
    database=MYSQL_DB
)

engine = create_engine(
    connection_url,
    pool_size=5, max_overflow=10, pool_recycle=1800, pool_pre_ping=True
)
# ================== تهيئة الخطوط والستايلات ==================
style_normal = ParagraphStyle("NormalFont", fontName="Helvetica", fontSize=10, alignment=1)
style_h1 = ParagraphStyle("H1", fontName="Helvetica", fontSize=18, alignment=1, spaceAfter=20, textColor=colors.blue)
style_sign = ParagraphStyle("Sign", fontName="Helvetica", fontSize=11, alignment=2)

try:
    font_path = "arial.ttf"
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\arial.ttf"
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
        style_normal.fontName = "ArabicFont"
        style_h1.fontName = "ArabicFont"
        style_sign.fontName = "ArabicFont"
    else:
        st.error(f"❌ ملف الخط arial.ttf غير موجود.")
except Exception as e:
    st.error(f"❌ خطأ في تحميل الخطوط: {e}")
UPLOAD_FOLDER = "supplier_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================== الدوال المساعدة (Helper Functions) ==================
def ar(text):
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except: return str(text)

def t(en_text, ar_text):
    return ar_text if st.session_state.get("lang") == "ar" else en_text

def resource_path(relative_path):
    if not relative_path: return ""
    return os.path.join("assets", relative_path)
def get_all_users_list():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username FROM users ORDER BY username")
    users = [row[0] for row in c.fetchall()] 
    conn.close()
    return users

def get_system_projects():
    conn = get_db_connection()
    c = conn.cursor()
    # جلب المشاريع من جدول الصلاحيات الحالي
    c.execute("SELECT DISTINCT project_name FROM project_permissions")
    projs = [row[0] for row in c.fetchall()]
    conn.close()
    return projs
# ➕ إضافة مشروع جديد
# =====================================================
def add_project(project_name):

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # إضافة المشروع لجدول الصلاحيات
        c.execute(
            "INSERT INTO project_permissions (username, project_name) VALUES (%s, %s)",
            ("admin", project_name)
        )

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"Add Project Error: {e}")
        return False
def generate_custody_pdf_web(recipient, national_id, project, doc_no, title, items_list):
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY

    buffer = io.BytesIO()
    try:
        cpdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        elements = []
        style_normal = getSampleStyleSheet()['Normal']

        # --- 1. إعدادات الهيدر (الشعار والشركة) ---
        company = get_setting("company") or ""
        addr1 = get_setting("addr1") or ""
        logo_path = resource_path(get_setting("logo"))
        watermark_path_db = get_setting("watermark")
        logo = RLImage(logo_path, 2.8*cm, 2.8*cm) if os.path.exists(logo_path) else ""

        header_style = ParagraphStyle('HeaderStyle', parent=style_normal, fontName='ArabicFont', fontSize=18, alignment=TA_CENTER)
        header_data = [[logo, Paragraph(ar(company), header_style), ""]]
        header_table = Table(header_data, colWidths=[3*cm, 12*cm, 3*cm])
        elements.append(header_table)
        elements.append(Paragraph(ar(addr1), ParagraphStyle('Addr', fontName='ArabicFont', fontSize=11, alignment=TA_CENTER, textColor=colors.grey)))
        elements.append(Spacer(1, 15))

        # --- 2. عنوان السند وبيانات المستلم ---
        elements.append(Paragraph(ar(title), ParagraphStyle('Title', fontName='ArabicFont', fontSize=20, alignment=TA_CENTER, textColor=colors.HexColor("#0A4D68"))))
        elements.append(Spacer(1, 10))

        info_style = ParagraphStyle('Info', fontName='ArabicFont', fontSize=11, alignment=TA_RIGHT)
        info_data = [
            [Paragraph(f"{doc_no}", info_style), Paragraph(ar("رقم السند / Doc No"), info_style)],
            [Paragraph(ar(recipient), info_style), Paragraph(ar("اسم المستلم / Name"), info_style)],
            [Paragraph(f"{national_id}", info_style), Paragraph(ar("رقم الهوية / ID No"), info_style)],
            [Paragraph(ar(project), info_style), Paragraph(ar("المشروع / Project"), info_style)]
        ]
        info_table = Table(info_data, colWidths=[13*cm, 4*cm])
        info_table.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.3, colors.lightgrey), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # --- 3. جدول المعدات (10 صفوف) ---
        table_data = [[ar("الملاحظات / Note"), ar("الكمية / Qty"), ar("المعدة / Item"), ar("م")]]
        for i, itm in enumerate(items_list, 1):
            table_data.append([ar(itm.get('note', '')), str(itm['qty']), ar(itm['item']), str(i)])

        for _ in range(max(0, 11 - len(table_data))):
            table_data.append(["", "", "", ""])

        items_table = Table(table_data, colWidths=[6*cm, 2.5*cm, 7.5*cm, 1*cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A4D68")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), 'ArabicFont'),
            ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ROWHEIGHT', (0,0), (-1,-1), 22),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 15))

        # --- 4. ⚖️ التعهد القانوني (Legal Declaration) ---
        style_legal = ParagraphStyle('Legal', parent=style_normal, fontName='ArabicFont', fontSize=9, leading=11, alignment=TA_JUSTIFY)
        legal_text = (
            "أقر أنا الموقع أدناه باستلامي العهدة المذكورة أعلاه بحالة جيدة، وأتعهد بالحفاظ عليها وإعادتها فور طلبها. "
            "وفي حالة عدم إرجاعها أو تلفها، أفوض الشركة باتخاذ اللازم نحو خصم القيمة التي تقدرها مقابل العهدة من مستحقاتي لديها دون أي اعتراض مني. <br/><br/>"
            "I, the undersigned, acknowledge receiving the items in good condition. I pledge to maintain and return them upon request. "
            "In case of loss or damage, I authorize the company to deduct the estimated value from my dues without any objection."
        )
        elements.append(Paragraph(ar(legal_text), style_legal))
        elements.append(Spacer(1, 20))

        # --- 5. التوقيع ---
        elements.append(Paragraph(ar("توقيع المستلم / Signature: ________________________________"), info_style))

        # --- 6. دالة العلامة المائية (إصلاح خطأ الحساب) ---
        def add_watermark(canvas, doc):
            canvas.saveState()
            page_w, page_h = A4
            if watermark_path_db:
                w_path = resource_path(watermark_path_db)
                if os.path.exists(w_path):
                    canvas.setFillAlpha(0.12)
                    canvas.drawImage(w_path, (page_w/2)-(7*cm), (page_h/2)-(7*cm), width=14*cm, height=14*cm, mask='auto', preserveAspectRatio=True)
            canvas.restoreState()

        cpdf.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error PDF: {e}")
        return None




def get_user_menu_perms(user):
    conn = get_db_connection()
    c = conn.cursor()
    # إنشاء الجدول إذا لم يكن موجوداً لتجنب خطأ البرمجة
    c.execute("CREATE TABLE IF NOT EXISTS user_menu_permissions (username VARCHAR(255), menu_name VARCHAR(255))")
    c.execute("SELECT menu_name FROM user_menu_permissions WHERE username=%s", (user,))
    res = [row[0] for row in c.fetchall()]
    conn.close()
    return res


def get_db_connection(include_db=True):
    try:
        config = {'host': MYSQL_HOST, 'user': MYSQL_USER, 'password': MYSQL_PASS, 'charset': 'utf8mb4'}
        if include_db: config['database'] = MYSQL_DB
        return mysql.connector.connect(**config)
    except mysql_error as e:
        st.error(f"Database Connection Error: {e}")
        return None
def get_user_projects(username):
    try:
        conn = get_db_connection()
        # نستخدم dictionary=False لضمان الحصول على tuples بسيطة
        cursor = conn.cursor(dictionary=False) 
        
        query = """
            SELECT DISTINCT TRIM(project_name) AS p_name
            FROM project_permissions
            WHERE username=%s
            ORDER BY p_name
        """
        cursor.execute(query, (username,))
        rows = cursor.fetchall()
        conn.close()
        
        # استخراج الاسم الأول من كل صف (row[0])
        projects = [row[0] for row in rows if row and row[0]]
        return projects
        
    except Exception as e:
        st.error(f"خطأ في جلب المشاريع: {e}")
        return []

def get_setting(k):
    try:
        df = pd.read_sql(f"SELECT value FROM settings WHERE key_col='{k}'", engine)
        return df['value'].iloc[0] if not df.empty else ""
    except: return ""

def set_setting(k, v):
    conn = get_db_connection()
    if not conn: return
    c = conn.cursor()
    try:
        c.execute("INSERT INTO settings (key_col, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = VALUES(value)", (k, str(v)))
        conn.commit()
    finally: c.close(); conn.close()
def generate_audit_number():
    from datetime import datetime

    year = datetime.now().year

    result = pd.read_sql(
        "SELECT COUNT(*) as total FROM stock_audit_log WHERE YEAR(audit_date)=%s",
        engine,
        params=(year,)
    )

    count = int(result.iloc[0]["total"]) + 1

    return f"AUD-{year}-{str(count).zfill(4)}"
def get_projects_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TRIM(name) FROM projects")
        rows = cursor.fetchall()
        conn.close()
        
        # استخراج الأسماء وتنظيفها
        projects = sorted([row[0] for row in rows if row[0]])
        
        # إضافة المخزن الرئيسي كخيار أساسي
        if "Main Warehouse" not in projects:
            projects.insert(0, "Main Warehouse")
            
        return projects
    except:
        return ["Main Warehouse"]


# تحميل اللغة عند بداية التشغيل
if "lang" not in st.session_state:
    st.session_state["lang"] = get_setting("lang") or "en"

def update_or_insert_inventory(code, item, qty, unit, price, project, supplier, main_qty):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    try:
        code = str(code).strip()
        c.execute("SELECT id, qty, main_qty FROM inventory WHERE code=%s", (code,))
        row = c.fetchone()
        if row:
            inv_id, old_qty_db, old_main_db = row
            new_qty = (float(old_qty_db) if old_qty_db else 0.0) + float(qty)
            new_main = (float(old_main_db) if old_main_db else 0.0) + float(main_qty)
            c.execute("""UPDATE inventory SET item=%s, qty=%s, unit=%s, price=%s, project=%s, supplier=%s, main_qty=%s
                         WHERE id=%s""", (item, new_qty, unit, price, project, supplier, new_main, inv_id))
        else:
            c.execute("""INSERT INTO inventory (code, item, qty, unit, price, project, supplier, main_qty)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (code, item, qty, unit, price, project, supplier, main_qty))
        
        # تسجيل الحركة في جدول السجلات
        c.execute("""INSERT INTO inventory_logs (code, item, qty, project, supplier, date)
                     VALUES (%s, %s, %s, %s, %s, NOW())""", (code, item, qty, project, supplier))
        conn.commit()
    except mysql_error as e: 
        conn.rollback()
        st.error(t(f"Database Error: {e}", f"خطأ في قاعدة البيانات: {e}"))
    finally:
        c.close(); conn.close()
# ================== الجزء 2 من 4: إدارة البيانات والمستخدمين ==================
def perform_stock_audit(code, real_qty):

    conn = get_db_connection()
    if not conn:
        return

    c = conn.cursor()

    try:
        c.execute("SELECT item, qty FROM inventory WHERE code=%s", (code,))
        row = c.fetchone()

        if not row:
            st.error("Code not found")
            return

        item, system_qty = row
        system_qty = float(system_qty)
        real_qty = float(real_qty)

        difference = real_qty - system_qty

        # تحديث المخزون للكمية الفعلية
        c.execute("UPDATE inventory SET qty=%s WHERE code=%s",
                  (real_qty, code))

        # تسجيل حركة تعديل
        adj_type = "IN-ADJ" if difference > 0 else "OUT-ADJ"

        if difference != 0:
            c.execute("""
                INSERT INTO transactions
                (date, code, item, qty, type, person, project, unit, price, supplier)
                SELECT %s, code, item, %s, %s, %s, project, unit, price, supplier
                FROM inventory WHERE code=%s
            """,
            (datetime.now().strftime("%Y-%m-%d %H:%M"),
             abs(difference),
             adj_type,
             "STOCK-AUDIT",
             code))

        # تسجيل في جدول الجرد
        c.execute("""
            INSERT INTO stock_audit
            (code, item, system_qty, real_qty, difference, audit_date, user)
            VALUES (%s,%s,%s,%s,%s,NOW(),%s)
        """,
        (code, item, system_qty, real_qty, difference,
         st.session_state['user_role']))

        conn.commit()
        st.success("✅ Stock audit completed successfully")

    except Exception as e:
        conn.rollback()
        st.error(f"Audit failed: {e}")

    finally:
        c.close()
        conn.close()

def import_excel_web(uploaded_file):
    # تم تصحيح المسافة البادئة لهذه الدالة
    if uploaded_file is None: return
    try:
        df = pd.read_excel(uploaded_file)
        required = ['code', 'item', 'qty', 'unit', 'price', 'project', 'supplier', 'main_qty']
        if not all(col in df.columns for col in required):
            st.error(t(f"❌ Import error: File must contain columns: {str(required)}", f"❌ خطأ استيراد: يجب أن يحتوي الملف على الأعمدة: {str(required)}"))
            return
        success_count = 0
        for _, row in df.iterrows():

            try:

                update_or_insert_inventory(
                    code=str(row['code']),
                    item=str(row['item']),
                    qty=row['qty'],
                    unit=str(row['unit']),
                    price=row['price'],
                    project=selected_project,
                    supplier=str(row['supplier']),
                    main_qty=row['main_qty']
                )

                success_count += 1

            except:
                continue

        st.success(
            t(
                f"✅ {success_count} items imported successfully.",
                f"✅ تم استيراد {success_count} صنف بنجاح."
            )
        )

    except Exception as e:

        st.error(
            t(
                f"❌ Failed to read Excel file: {e}",
                f"❌ فشل قراءة ملف الإكسل: {e}"
            )
        )
def delete_inventory_item_web(code):
    conn = get_db_connection()
    if not conn: return
    c = conn.cursor()
    try:
        c.execute("DELETE FROM inventory WHERE code=%s", (code,))
        conn.commit()
        st.success(t(f"✅ Item {code} deleted successfully.", f"✅ تم حذف الصنف {code} بنجاح."))
    except Exception as e:
        st.error(t(f"❌ Deletion failed: {e}", f"❌ فشل الحذف: {e}"))
    finally:
        c.close(); conn.close()

def add_user_web_ui():
    st.subheader(t("Add New User", "إضافة مستخدم جديد"))
    with st.form("new_user_form"):
        col1, col2 = st.columns(2)
        with col1: u_ent = st.text_input(t("Username", "اسم المستخدم"))
        with col2: p_ent = st.text_input(t("Password", "كلمة المرور"), type="password")
        r_cb = st.selectbox(t("Role", "الرتبة"), ["admin", "employee"], index=1)
        st.markdown(t("**Access Permissions:**", "**صلاحيات الوصول:**"))
        perms = {
            "inv": st.checkbox(t("Manage Inventory", "إدارة المخزن"), value=True),
            "bill": st.checkbox(t("Issue Invoices", "إصدار فواتير"), value=True),
            "rep": st.checkbox(t("View Reports", "عرض التقارير"), value=True),
            "set": st.checkbox(t("System Settings", "إعدادات النظام"), value=False),
            "bak": st.checkbox(t("Backup", "النسخ الاحتياطي"), value=False)
        }
        submitted = st.form_submit_button(t("Save New User", "حفظ المستخدم الجديد"))
        if submitted:
            if not u_ent or not p_ent:
                st.warning(t("Username and password must be filled", "يجب تعبئة الاسم وكلمة المرور"))
                return
            conn = get_db_connection(); c = conn.cursor()
            try:
                c.execute("SELECT username FROM users WHERE username=%s", (u_ent,))
                if c.fetchone():
                    st.error(t("Username already exists", "اسم المستخدم موجود بالفعل"))
                    return
                query = """INSERT INTO users (username, password, role, can_inventory, can_invoice, can_reports, can_settings, can_backup) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                hashed_pwd = bcrypt.hashpw(p_ent.encode(), bcrypt.gensalt()).decode()

                values = (
                    u_ent,
                    hashed_pwd,
                    r_cb,
                    perms["inv"],
                    perms["bill"],
                    perms["rep"],
                    perms["set"],
                    perms["bak"]
                )

                c.execute(query, values)
                conn.commit()
                st.success(t(f"Added {u_ent} successfully.", f"تمت إضافة {u_ent} بنجاح."))
            except Exception as e:
                st.error(t(f"Database Error: {e}", f"خطأ في قاعدة البيانات: {e}"))
            finally:
                c.close(); conn.close()

def upload_generic_web(key, uploaded_file):
    """رفع الملفات (الشعارات) وحفظ مسارها في الإعدادات"""
    if uploaded_file is not None:
        file_path = os.path.join(ASSETS_DIR, f"{key}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # حفظ اسم الملف فقط في قاعدة البيانات
        set_setting(key, f"{key}_{uploaded_file.name}")
        st.success(t(f"✅ {key} updated successfully.", f"✅ تم تحديث {key} بنجاح."))
# ================== الجزء 3 من 4: حفظ الفاتورة وتوليد الـ PDF الاحترافي ==================

def save_invoice_web(recipient, project_name, cart):
    """
    حفظ الفاتورة وخصم الكميات مع مراقبة المشروع لضمان دقة المخزون
    """
    if not cart: 
        st.warning(t("⚠️ Cart is empty.", "⚠️ العربة فارغة."))
        return False
        
    conn = get_db_connection()
    c = conn.cursor(dictionary=True, buffered=True)
    
    try:
        last_val = get_setting("last_inv")
        invoice_no = int(last_val if last_val and str(last_val).isdigit() else 1000) + 1
        
        for entry in cart:
            code = entry.get('code')
            item = entry.get('item')
            # المشروع الأصلي الذي سُحبت منه المادة (قد يكون Main Warehouse أو مشروع محدد)
            item_source_proj = entry.get('project') 
            qty = float(entry.get('qty', 0))

            # 1️⃣ التحقق من الكمية في المشروع المحدد (المصدر)
            c.execute("""
                SELECT qty FROM inventory 
                WHERE code=%s AND (project=%s OR project_name=%s)
            """, (code, item_source_proj, item_source_proj))
            
            res = c.fetchone()
            current_qty = float(res['qty']) if res else 0.0

            if qty > current_qty:
                st.error(t(
                    f"❌ Insufficient qty for {item} in {item_source_proj}.",
                    f"❌ كمية {item} غير كافية في {item_source_proj}."
                ))
                conn.rollback()
                return False

            # 2️⃣ التحديث: الخصم من المشروع المصدر حصراً
            c.execute("""
                UPDATE inventory SET qty = qty - %s 
                WHERE code=%s AND (project=%s OR project_name=%s)
            """, (qty, code, item_source_proj, item_source_proj))

            # 3️⃣ تسجيل الحركة
            c.execute("""
                INSERT INTO transactions
                (date, doc_no, code, item, qty, type, person, project, unit, price, supplier)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                datetime.now(), invoice_no, code, item, qty, "OUT",
                recipient, project_name, # المشروع المستلم للفاتورة
                entry.get('unit'), entry.get('price'), entry.get('supplier')
            ))
        
        conn.commit()
        set_setting("last_inv", str(invoice_no))
        return True

    except Exception as e:
        if conn: conn.rollback()
        st.error(f"❌ Database Error: {e}")
        return False
    finally:
        if c: c.close()
        if conn: conn.close()

def generate_issue_pdf_web(recipient, project, doc_no, title, cart_items_list, save_path=None):

    buffer = io.BytesIO()

    try:
        cpdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        elements = []

        # =========================
        # 🔷 Header Section
        # =========================

        company = get_setting("company") or ""
        addr1 = get_setting("addr1") or ""
        logo_path = resource_path(get_setting("logo"))
        watermark_path_db = get_setting("watermark")
        logo = RLImage(logo_path, 2.8*cm, 2.8*cm) if os.path.exists(logo_path) else ""

        style_company = ParagraphStyle(
            'CompanyStyle',
            parent=style_normal,
            fontName='ArabicFont',
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#003366"),
            spaceAfter=4
        )

        style_address = ParagraphStyle(
            'AddressStyle',
            parent=style_normal,
            fontName='ArabicFont',
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.grey
        )

        header_data = [
            [logo,
             Paragraph(ar(company), style_company),
             ""]
        ]

        header_table = Table(header_data, colWidths=[3*cm, 12*cm, 3*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))

        elements.append(header_table)
        elements.append(Paragraph(ar(addr1), style_address))
        elements.append(Spacer(1, 20))

        # =========================
        # 🔷 Invoice Title
        # =========================

        style_title = ParagraphStyle(
            'InvoiceTitle',
            parent=style_normal,
            fontName='ArabicFont',
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0A4D68"),
            spaceAfter=15
        )

        elements.append(Paragraph(ar(title), style_title))
        elements.append(Spacer(1, 10))

        # =========================
        # 🔷 Info Section (Professional Layout)
        # =========================

        style_info_right = ParagraphStyle(
            'InfoRight',
            parent=style_normal,
            alignment=TA_RIGHT,
            fontName='ArabicFont',
            fontSize=11,
        )

        style_info_left = ParagraphStyle(
            'InfoLeft',
            parent=style_normal,
            alignment=TA_LEFT,
            fontName='ArabicFont',
            fontSize=11,
        )

        info_data = [
            [
                Paragraph("Invoice No", style_info_left),
                Paragraph(f"{doc_no}", ParagraphStyle(
                    'CenterInfo',
                    parent=style_normal,
                    alignment=TA_CENTER,
                    fontName='ArabicFont',
                    fontSize=12,
                )),
                Paragraph(ar("رقم السند"), style_info_right),
            ],
            [
                Paragraph("Recipient", style_info_left),
                Paragraph(ar(recipient), ParagraphStyle(
                    'CenterInfo2',
                    parent=style_normal,
                    alignment=TA_CENTER,
                    fontName='ArabicFont',
                    fontSize=12,
                )),
                Paragraph(ar("المستلم"), style_info_right),
            ],
            [
                Paragraph("Project", style_info_left),
                Paragraph(ar(project), ParagraphStyle(
                    'CenterInfo3',
                    parent=style_normal,
                    alignment=TA_CENTER,
                    fontName='ArabicFont',
                    fontSize=12,
                )),
                Paragraph(ar("المشروع"), style_info_right),
            ],
            [
                Paragraph("Date", style_info_left),
                Paragraph(datetime.now().strftime('%Y-%m-%d'), ParagraphStyle(
                    'CenterInfo4',
                    parent=style_normal,
                    alignment=TA_CENTER,
                    fontName='ArabicFont',
                    fontSize=12,
                )),
                Paragraph(ar("التاريخ"), style_info_right),
            ],
        ]

        info_table = Table(info_data, colWidths=[5.5*cm, 6*cm, 5.5*cm])

        info_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))


        elements.append(info_table)
        elements.append(Spacer(1, 25))

        # =========================
        # =========================
        # 🔷 Items Table (تعديل القراءة لتناسب القاموس)
        # =========================
        table_data = [[
            "Code / " + ar("الكود"),
            "Item / " + ar("المادة"),
            "Unit / " + ar("الوحدة"),
            "Qty / " + ar("الكمية"),
            "Project / " + ar("المشروع")
        ]]

        for entry in cart_items_list:
            # استخراج البيانات من القاموس بأمان
            code     = entry.get('code', '')
            item     = entry.get('item', '')
            proj_row = entry.get('project', '')
            qty      = entry.get('qty', 0)
            unit     = entry.get('unit', '')

            table_data.append([
                Paragraph(ar(str(code)), ParagraphStyle('p', fontName='ArabicFont', fontSize=10, alignment=1)),
                Paragraph(ar(str(item)), ParagraphStyle('p', fontName='ArabicFont', fontSize=10, alignment=1)),
                Paragraph(ar(str(unit)), ParagraphStyle('p', fontName='ArabicFont', fontSize=10, alignment=1)),
                Paragraph(f"{float(qty):.2f}", ParagraphStyle('p', fontName='ArabicFont', fontSize=10, alignment=1)),
                Paragraph(ar(str(proj_row)), ParagraphStyle('p_project', fontName='ArabicFont', fontSize=10, alignment=1, wordWrap='CJK'))
            ])


        # إضافة صفوف فارغة إذا كانت أقل من 10
        for _ in range(max(0, 10 - len(cart_items_list))):
            table_data.append(["", "", "", "", ""])

        items_table = Table(
            table_data,
            colWidths=[3*cm, 6*cm, 2.5*cm, 2.5*cm, 3*cm]
        )

        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A4D68")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), 'ArabicFont'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('ROWHEIGHT', (0,0), (-1,-1), 18),
        ]))

        elements.append(items_table)
        elements.append(Spacer(1, 40))
        # =========================
        # 🔷 Signature Section
        # =========================

        style_signature = ParagraphStyle(
            'SignStyle',
            parent=style_normal,
            fontName='ArabicFont',
            fontSize=12,
            alignment=TA_RIGHT,
        )

        elements.append(Paragraph(ar("توقيع المستلم: ________________________________"), style_signature))


        # دالة العلامة المائية
        # =========================
        # 🔷 Watermark Function
        # =========================

        def add_watermark(canvas, doc):
            canvas.saveState()
            try:
                w, h = A4

                if watermark_path_db:
                    watermark_path = resource_path(watermark_path_db)

                    if os.path.exists(watermark_path):
                        canvas.setFillAlpha(0.15)
                        canvas.drawImage(
                            watermark_path,
                            w/2 - 7*cm,
                            h/2 - 7*cm,
                            width=14*cm,
                            height=14*cm,
                            preserveAspectRatio=True,
                            mask='auto'
                        )

                # ✅ الكتابة المائية أسفل الصفحة في المنتصف
                canvas.setFillAlpha(0.25)
                canvas.setFillColorRGB(0.6, 0.6, 0.6)
                canvas.setFont("Helvetica-Bold", 18)

                canvas.drawCentredString(
                    w / 2,        # منتصف الصفحة أفقياً
                    1.5 * cm,     # ارتفاع 1.5 سم من الأسفل
                    "TALAL STORE"
                )

            except Exception as e:
                print("Watermark error:", e)

            canvas.restoreState()


        # =========================
        # 🔷 Build PDF
        # =========================

        cpdf.build(
            elements,
            onFirstPage=add_watermark,
            onLaterPages=add_watermark
        )
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(buffer.getbuffer())
            
            # **منطق الفتح التلقائي الجديد:**
            if sys.platform.startswith('darwin'): # macOS
                subprocess.Popen(['open', save_path])
            elif sys.platform.startswith('win'): # Windows
                os.startfile(save_path)
            elif sys.platform.startswith('linux'): # Linux
                subprocess.Popen(['xdg-open', save_path])
        
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error generating PDF or opening file: {e}")
        return None
def backup_database_web():
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    file_name = f"Backup_{datetime.now().strftime('%Y%m%d_%H%M')}.sql"
    file_path = os.path.join(backup_dir, file_name)

    try:
        mysqldump_path = shutil.which("mysqldump")

        if not mysqldump_path:
            st.error("mysqldump not found. Please check PATH.")
            return

        # تمرير كلمة المرور عبر متغير بيئة (بدون تحذير)
        env = os.environ.copy()
        env["MYSQL_PWD"] = MYSQL_PASS

        subprocess.run([
            mysqldump_path,
            "-h", MYSQL_HOST,
            "-u", MYSQL_USER,
            MYSQL_DB
        ],
        stdout=open(file_path, 'w'),
        check=True,
        env=env)

        with open(file_path, "rb") as f:
            st.download_button(
                "📥 Download Backup File",
                f.read(),
                file_name=file_name,
                mime="application/sql"
            )

        st.success("✅ Backup created successfully")

    except Exception as e:
        st.error(str(e))

# تعيين اللغة الافتراضية عند التشغيل لأول مرة
if get_setting("lang") == "":
    set_setting("lang", "ar")

st.set_page_config(page_title=t("Al-Rajhi 2026 System - Web", "نظام الراجحي 2026 - ويب"), layout="wide")

# تهيئة متغيرات الجلسة
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'cart_items' not in st.session_state: st.session_state['cart_items'] = []
# 💡 متغيّر لحفظ بيانات الـ PDF المؤقتة لزر التحميل 💡
if 'last_pdf' not in st.session_state: st.session_state['last_pdf'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = ""
 


# =========================
# 🔐 PREMIUM 2026 LOGIN
# ======# --- شاشة تسجيل الدخول المعدلة ---
if not st.session_state.get('logged_in', False):

    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0

    # CSS محسّن لربط المكونات
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0A4D68, #088395); }
    
    /* تنسيق حاوية الدخول الرئيسية */
    [data-testid="stVerticalBlock"] > div:has(div.login-header) {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        max-width: 450px;
        margin: auto;
        color: white;
    }
    .welcome-title { font-size: 22px; font-weight: bold; margin-top: 15px; text-align: center;}
    .welcome-subtitle { font-size: 15px; opacity: 0.85; margin-bottom: 25px; text-align: center;}
    
    /* تعديل مظهر المدخلات */
    input { border-radius: 12px !important; }
    div[data-testid="stButton"] button {
        background: #FFD369 !important;
        color: black !important;
        border-radius: 12px !important;
        height: 3em !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # استخدام حاوية (Container) لتوسيط المحتوى
    with st.container():
        st.markdown('<div class="login-header"></div>', unsafe_allow_html=True)
        
        # الشعار
        logo_path = os.path.join(os.getcwd(), "uploads", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=180)

        st.markdown("""
            <div class="welcome-title">مرحباً بكم في مستودع الراجحي للبناء والتعمير</div>
            <div class="welcome-subtitle">Welcome to Alrajhi Construction & Supply Warehouse</div>
        """, unsafe_allow_html=True)

        user = st.text_input("Username", key="login_user", placeholder="اسم المستخدم")
        pwd = st.text_input("Password", type="password", key="login_pass", placeholder="كلمة المرور")

        if st.button("Login", width='content'):
            if not user or not pwd:
                st.warning("Please enter username and password")
            else:
                conn = get_db_connection()
                if conn:
                    c = conn.cursor(dictionary=True)
                    try:
                        # 1. محاولة جلب المستخدم
                        c.execute("SELECT username, password, role FROM users WHERE username=%s", (user,))
                        result = c.fetchone()

                        if result:
                            stored_pwd = result['password']
                            is_correct = False
                            
                            # 2. التحقق من كلمة المرور (تشفير أو نص عادي)
                            try:
                                if bcrypt.checkpw(pwd.encode('utf-8'), stored_pwd.encode('utf-8')):
                                    is_correct = True
                            except ValueError:
                                if pwd == stored_pwd:
                                    is_correct = True

                            if is_correct:
                                st.session_state['logged_in'] = True
                                st.session_state['user_role'] = str(result['role']).lower()
                                st.session_state['username'] = result['username']
                                st.session_state["login_attempts"] = 0
                                st.rerun()
                            else:
                                st.session_state["login_attempts"] += 1
                                st.error("❌ بيانات الدخول غير صحيحة")
                        else:
                            st.error("❌ المستخدم غير موجود")

                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        # إغلاق الاتصال دائماً في النهاية
                        c.close()
                        conn.close()
    


# --- واجهة النظام الرئيسية (بعد الدخول) ---
if st.session_state.get('logged_in', False):
    # جلب البيانات الحقيقية من قاعدة البيانات
    try:
        # حساب القيمة المالية (الكمية * السعر)
        df_inv = pd.read_sql("SELECT SUM(qty * price) as total_val, SUM(qty) as total_qty FROM inventory", engine)
        stock_value = df_inv['total_val'].iloc[0] or 0
        stock_units = df_inv['total_qty'].iloc[0] or 0
        
        # جلب عدد المستخدمين
        df_u = pd.read_sql("SELECT COUNT(*) as count FROM users", engine)
        user_count = df_u['count'].iloc[0] or 0
    except:
        stock_value, stock_units, user_count = 0, 0, 0

    # شريط علوي (Top Bar)
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 10px 20px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <h4 style="margin:0;">🏢 {t('Management Dashboard', 'لوحة الإدارة')}</h4>
            <p style="margin:0;">👤 {st.session_state['username']} | <span style="color: green;">● Online</span></p>
        </div>
    """, unsafe_allow_html=True)
    
    # تقسيم الشاشة إلى لوحات معلومات (Dashboards)
    m1, m2, m3 = st.columns(3)
    
    # 1. إظهار الرصيد المالي (11 مليون+) للأدمن فقط، وللموظف يظهر عدد الوحدات
    if st.session_state.get('user_role') == 'admin':
        m1.metric(t("Stock Value", "قيمة المخزون"), f"{stock_value:,.2f} SAR")
    else:
        m1.metric(t("Inventory", "المخزون"), f"{stock_units:,.0f} Units")

    # 2. إظهار عدد الوحدات (426 ألف+) في الخانة الثانية
    m2.metric(t("Total Units", "إجمالي الوحدات"), f"{stock_units:,.0f}")
    
    # 3. عدد المستخدمين النشطين
    m3.metric(t("Active Users", "المستخدمين"), user_count, "Live")

    # إعدادات اللغة في الجانبي
    if "lang" not in st.session_state:
        st.session_state["lang"] = get_setting("lang") or "ar"

    current_lang = st.session_state.get("lang", "en")

    if st.sidebar.button(f"🌐 Change Language ({'AR' if current_lang == 'en' else 'EN'})"):
        new_lang = "ar" if current_lang == "en" else "en"
        set_setting("lang", new_lang)
        st.session_state["lang"] = new_lang
        st.rerun()
    # 1. القاموس المرجعي لكل القوائم (المفاتيح والأسماء)
    all_menu_map = {
        "inventory": t("📦 Inventory", "📦 المخزن"),
        "issue_invoice": t("🧾 Issue Invoice", "🧾 صرف فاتورة"),
        "invoice_mgmt": t("📄 Invoice Management", "📄 إدارة الفواتير"),
        "reports": t("📊 Reports", "📊 التقارير"),
        "import_export": t("📁 Import/Export Excel", "📁 استيراد/تصدير"),
        "stock_audit": t("📋 Stock Audit", "📋 جرد المخزون"),
        "supplier_receipts": t("📂 Supplier Receipts", "📂 سندات الموردين"),
        "equipment_custody": t("📂 equipment_custody", "📂العهد"),
        "settings": t("⚙️ Settings & Users", "⚙️ الإعدادات")
    }

    # 2. جلب المفاتيح المسموحة للمستخدم الحالي
    current_user = st.session_state.get('username')
    user_role = st.session_state.get('user_role')

    if user_role == 'admin':
        # المسؤول يرى كل القوائم تلقائياً
        user_allowed_keys = list(all_menu_map.keys())
    else:
        # المستخدم العادي يرى فقط ما حددته له في الإعدادات
        user_allowed_keys = get_user_menu_perms(current_user)

    # 3. بناء القائمة المصفاة بناءً على الصلاحيات
    menu_options = []
    for key in user_allowed_keys:
        if key in all_menu_map:
            menu_options.append({"key": key, "label": all_menu_map[key]})

    # 4. عرض القائمة الجانبية (Sidebar)
    if menu_options:
        menu_labels = [opt["label"] for opt in menu_options]
        menu_choice = st.sidebar.radio(t("Go to:", "انتقل إلى:"), menu_labels)
        
        # ربط الاختيار بالمفتاح التشغيلي (menu_key)
        menu_key = next(opt["key"] for opt in menu_options if opt["label"] == menu_choice)
    else:
        st.sidebar.warning(t("No Permissions Assigned", "لم يتم تعيين صلاحيات وصول لك"))
        menu_key = None



         # ======================================
    if menu_key == "inventory":
        # تصفير بيانات الفاتورة فور الدخول للمخزون
        st.session_state['last_pdf'] = None
        st.session_state['last_inv_no'] = None

        st.header(t("📦 Inventory Management", "📦 إدارة المخزون"))
        current_user = st.session_state.get("username")

        # 1️⃣ تحديد صلاحية المشاريع
        if current_user == "zizo":
            projects = ["مشروع الحرم haram"]
            selected_project = "مشروع الحرم haram"
            st.info(f"📍 {t('Authorized Project: ', 'المشروع المصرح لك: ')} **{selected_project}**")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM projects ORDER BY name")
            projects = [row[0] for row in cursor.fetchall()]
            conn.close()
            if "Main Warehouse" not in projects:
                projects.insert(0, "Main Warehouse")
            selected_project = st.selectbox(t("Select Project", "اختر المشروع"), projects, key="inv_main_sel")

        # 2️⃣ إنشاء التبويبات بشكل ديناميكي (لتجنب IndexError)
        if current_user == "zizo":
            tabs = st.tabs([t("View Inventory", "عرض المخزون"), t("Add Item", "إضافة صنف")])
        else:
            tabs = st.tabs([
                t("View Inventory", "عرض المخزون"), 
                t("Add / Edit Item", "إضافة / تعديل صنف"), 
                t("Transfer Items", "نقل مواد")
            ])

        # 🟢 التبويب الأول: عرض المخزون
        # ======================================
        with tabs[0]:
            if current_user == "zizo":
                view_option = t("By Project", "حسب المشروع")
            else:
                view_option = st.radio(t("View Mode", "طريقة العرض"), 
                                      [t("Full Inventory", "كامل المخزون"), t("By Project", "حسب المشروع")], 
                                      horizontal=True, key="v_mode_secure")

            if view_option == t("Full Inventory", "كامل المخزون") and current_user != "zizo":
                query = "SELECT * FROM inventory ORDER BY item ASC"
                df = pd.read_sql(query, engine)
            else:
                target_q = "مشروع الحرم haram" if current_user == "zizo" else selected_project
                # البحث في كلا العمودين لضمان ظهور بيانات الإكسل والمخزن اليدوي
                query = "SELECT * FROM inventory WHERE (project_name=%s OR project=%s) ORDER BY item ASC"
                df = pd.read_sql(query, engine, params=(target_q, target_q))

            if 'main_qty' in df.columns:
                df = df.drop(columns=['main_qty'])

            search_q = st.text_input(t("Quick Search", "بحث سريع"), key="search_inv_main")
            if search_q and not df.empty:
                df = df[df['item'].astype(str).str.contains(search_q, case=False, na=False) | 
                        df['code'].astype(str).str.contains(search_q, case=False, na=False)]

            if not df.empty:
                st.dataframe(df, width="stretch")
            else:
                st.info(t("No items found", "لا توجد أصناف لهذا المشروع حالياً"))

        # 🔵 التبويب الثاني: إضافة / تعديل صنف
        # ======================================
        with tabs[1]:
            st.subheader(t("Add or Edit Items", "إضافة أو تعديل الأصناف"))
            if "receipt_cart" not in st.session_state:
                st.session_state["receipt_cart"] = []

            if "receipt_pdf" not in st.session_state:
                st.session_state["receipt_pdf"] = None

            
            code = st.text_input(t("Item Code", "كود الصنف"), key="input_code")
            name = st.text_input(t("Item Name", "اسم الصنف"), key="input_name")
            supplier = st.text_input(t("Supplier", "المورد"), key="input_supp")

            col1, col2 = st.columns(2)
            with col1:
                qty = st.number_input(t("Quantity", "الكمية"), min_value=0.0, step=1.0, key="input_qty")
            with col2:
                price = st.number_input(t("Price", "السعر"), min_value=0.0, step=1.0, key="input_price")

            unit = st.text_input(t("Unit", "الوحدة"), key="input_unit")
            # =========================
            # إضافة للسلة
            # =========================
            if st.button(
                t("➕ Add To Receipt", "➕ إضافة لسند الاستلام"),
                width="stretch",
                key="btn_add_receipt"
            ):

                if not code or not name or qty <= 0:
                    st.error(
                        t(
                            "Code, Name and Quantity required",
                            "يجب إدخال الكود والاسم والكمية"
                        )
                    )
                else:

                    st.session_state["receipt_cart"].append({
                        "code": code,
                        "item": name,
                        "qty": qty,
                        "unit": unit,
                        "project": selected_project
                    })

                    st.success(
                        t(
                            "Added to receipt",
                            "تمت الإضافة إلى سند الاستلام"
                        )
                    )

                    st.rerun()

            # =========================
            # عرض السلة
            # =========================
            if st.session_state["receipt_cart"]:

                st.markdown("### 📋 سند الاستلام")

                receipt_df = pd.DataFrame(
                    st.session_state["receipt_cart"]
                )

                st.dataframe(
                    receipt_df,
                    width="stretch"
                )

                col_r1, col_r2 = st.columns(2)

                with col_r1:

                    if st.button(
                        t("🗑 Clear Receipt", "🗑 مسح السند"),
                        width="stretch"
                    ):

                        st.session_state["receipt_cart"] = []
                        st.rerun()

                with col_r2:

                    if st.button(
                        t("🖨 Save & Print Receipt", "🖨 حفظ وطباعة السند"),
                        width="stretch"
                    ):

                        try:

                            target_p = (
                                "مشروع الحرم haram"
                                if current_user == "zizo"
                                else selected_project
                            )

                            conn = get_db_connection()
                            cursor = conn.cursor()

                            for row in st.session_state["receipt_cart"]:

                                cursor.execute("""
                                    SELECT id
                                    FROM inventory
                                    WHERE code=%s
                                    AND (project_name=%s OR project=%s)
                                """, (
                                    row["code"],
                                    target_p,
                                    target_p
                                ))

                                exists = cursor.fetchone()

                                if exists:

                                    cursor.execute("""
                                        UPDATE inventory
                                        SET qty = qty + %s
                                        WHERE code=%s
                                        AND (project_name=%s OR project=%s)
                                    """, (
                                        row["qty"],
                                        row["code"],
                                        target_p,
                                        target_p
                                    ))

                                else:

                                    cursor.execute("""
                                        INSERT INTO inventory
                                        (
                                            code,
                                            item,
                                            qty,
                                            unit,
                                            project,
                                            project_name
                                        )
                                        VALUES
                                        (
                                            %s,%s,%s,%s,%s,%s
                                        )
                                    """, (
                                        row["code"],
                                        row["item"],
                                        row["qty"],
                                        row["unit"],
                                        target_p,
                                        target_p
                                    ))

                            conn.commit()
                            conn.close()

                            doc_no = (
                                f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            )

                            pdf_buffer = generate_issue_pdf_web(
                                recipient="المستودع",
                                project=target_p,
                                doc_no=doc_no,
                                title="سند استلام مواد",
                                cart_items_list=st.session_state["receipt_cart"]
                            )

                            st.session_state["receipt_pdf"] = pdf_buffer.getvalue()

                            st.session_state["receipt_cart"] = []

                            st.success(
                                t(
                                    "Receipt saved successfully",
                                    "تم حفظ المواد وإنشاء سند الاستلام"
                                )
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(f"Error: {e}")

            if st.session_state.get("receipt_pdf"):

                st.download_button(
                    "📥 تحميل سند الاستلام PDF",
                    data=st.session_state["receipt_pdf"],
                    file_name="Receipt_IN.pdf",
                    mime="application/pdf",
                    width="stretch"
                )

            col_add, col_delete = st.columns(2)
            with col_add:
                if st.button(t("💾 Save Item", "💾 حفظ الصنف"), width="stretch", key="btn_save_item"):
                    if not code or not name:
                        st.error(t("Code and Name required", "الكود والاسم مطلوبان"))

                    else:
                        target_p = "مشروع الحرم haram" if current_user == "zizo" else selected_project
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        # البحث في كلا العمودين
                        cursor.execute("SELECT id FROM inventory WHERE code=%s AND (project_name=%s OR project=%s)", (code, target_p, target_p))
                        exists = cursor.fetchone()

                        if exists:
                            cursor.execute("""
                                UPDATE inventory SET item=%s, supplier=%s, qty=%s, price=%s, unit=%s, project=%s, project_name=%s
                                WHERE code=%s AND (project_name=%s OR project=%s)
                            """, (name, supplier, qty, price, unit, target_p, target_p, code, target_p, target_p))
                            st.success(t("Item updated", "تم تحديث الصنف"))
                        else:
                            cursor.execute("""
                                INSERT INTO inventory (code, item, supplier, qty, price, unit, project, project_name)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (code, name, supplier, qty, price, unit, target_p, target_p))
                            st.success(t("Item added", "تمت إضافة الصنف"))
                        conn.commit()
                        conn.close()
                        st.rerun()

            with col_delete:
                if current_user != "zizo":
                    if st.button(t("🗑 Delete Item", "🗑 حذف الصنف"), width="stretch", key="btn_delete_main"):
                        if not code:
                            st.warning(t("Enter code first", "ادخل الكود أولاً"))
                        else:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM inventory WHERE code=%s AND (project_name=%s OR project=%s)", (code, selected_project, selected_project))
                            conn.commit()
                            conn.close()
                            st.success(t("Item deleted", "تم حذف الصنف"))
                            st.rerun()
        if current_user != "zizo" and len(tabs) > 2:
            with tabs[2]:
                st.subheader(t("🔄 Transfer Between Projects", "🔄 نقل مواد بين المشاريع"))

                col_from, col_to = st.columns(2)
                with col_from:
                    # إضافة خيار "كامل المخزون" يسمح لك بسحب مواد من أي مكان وتوجيهها لمشروع محدد
                    from_project = st.selectbox(t("From Project", "من مشروع"), [t("Full Inventory", "كامل المخزون")] + projects, key="t_from_sel")
                with col_to:
                    to_project = st.selectbox(t("To Project", "إلى مشروع"), projects, key="t_to_sel")

                if from_project == to_project:
                    st.warning(t("Cannot transfer to same project", "لا يمكن النقل لنفس المشروع"))
                else:
                    search_t = st.text_input(t("Search Item", "بحث عن صنف (اسم أو كود)"), key="s_trans_item")
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # جلب البيانات مع التأكد من جلب اسم المشروع الحالي للصنف
                    if from_project == t("Full Inventory", "كامل المخزون"):
                        cursor.execute("SELECT code, item, qty, price, unit, supplier, project, project_name FROM inventory WHERE qty > 0")
                    else:
                        cursor.execute("SELECT code, item, qty, price, unit, supplier, project, project_name FROM inventory WHERE (project=%s OR project_name=%s) AND qty > 0", (from_project, from_project))
                    
                    all_items = cursor.fetchall()
                    conn.close()

                    # تحسين الفلترة لتشمل الكود والاسم
                    filtered = [i for i in all_items if search_t.lower() in str(i[1]).lower() or search_t.lower() in str(i[0]).lower()] if search_t else all_items
                    
                    if filtered:
                        # عرض اسم المشروع الأصلي للصنف بجانب اسمه (مفيد جداً في حالة "كامل المخزون")
                        item_d = {f"{i[1]} ({i[0]}) | Source: {i[6] or i[7]}": i for i in filtered}
                        sel_label = st.selectbox(t("Select Item", "اختر الصنف"), list(item_d.keys()), key="t_sel")
                        i_data = item_d[sel_label]
                        
                        # تحديد المشروع المصدر الفعلي للصنف المختير
                        actual_source = i_data[6] if i_data[6] else i_data[7]

                        t_qty_input = st.number_input(t("Qty", "الكمية"), min_value=0.1, max_value=float(i_data[2]), value=min(1.0, float(i_data[2])))
                        
                        if st.button(t("🚚 Transfer", "🚚 تنفيذ النقل"), width="stretch", type="primary"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            try:
                                # 1. الخصم من المصدر الفعلي (باستخدام الكود والمشروع بدقة)
                                cursor.execute("UPDATE inventory SET qty = qty - %s WHERE code=%s AND (project=%s OR project_name=%s)", 
                                             (t_qty_input, i_data[0], actual_source, actual_source))
                                
                                # 2. الإضافة للمستهدف (تحديث الحقلين معاً لضمان الظهور في التقارير)
                                cursor.execute("SELECT id FROM inventory WHERE code=%s AND (project=%s OR project_name=%s)", 
                                             (i_data[0], to_project, to_project))
                                
                                target_record = cursor.fetchone()
                                if target_record:
                                    cursor.execute("UPDATE inventory SET qty = qty + %s WHERE id=%s", (t_qty_input, target_record[0]))
                                else:
                                    cursor.execute("""
                                        INSERT INTO inventory (code, item, qty, price, unit, supplier, project, project_name) 
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (i_data[0], i_data[1], t_qty_input, i_data[3], i_data[4], i_data[5], to_project, to_project))
                                
                                conn.commit()
                                st.success(t(f"Successfully transferred {t_qty_input} to {to_project}", f"تم نقل {t_qty_input} بنجاح إلى {to_project}"))
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error: {e}")
                            finally:
                                conn.close()
                    else:
                        st.info(t("No items matching your search", "لا توجد أصناف تطابق بحثك"))
        # أضف تبويب "جرد المشاريع" في قائمة التبويبات لديك
        # tabs = st.tabs([..., t("Project Summary", "جرد المشاريع")])

        with tabs[-1]: # التبويب الأخير (الجرد)
            st.subheader(t("📊 Inventory Summary by Project", "📊 ملخص المخزون حسب المشروع"))
            
            # استعلام لجلب إجمالي الكميات والقيم المالية لكل مشروع
            summary_query = """
                SELECT 
                    COALESCE(project_name, project) as project_label,
                    COUNT(id) as total_items,
                    SUM(qty) as total_qty,
                    SUM(qty * price) as total_value
                FROM inventory
                GROUP BY project_label
                ORDER BY total_value DESC
            """
            
            try:
                df_summary = pd.read_sql(summary_query, engine)
                
                if not df_summary.empty:
                    # تحسين مظهر الجدول للعرض
                    df_summary.columns = [
                        t("Project Name", "اسم المشروع"),
                        t("Items Count", "عدد الأصناف"),
                        t("Total Qty", "إجمالي الكمية"),
                        t("Inventory Value", "قيمة المخزون (ريال)")
                    ]
                    
                    # عرض بطاقات سريعة (Metrics) لأعلى القيم
                    total_all_value = df_summary[t("Inventory Value", "قيمة المخزون (ريال)")].sum()
                    st.metric(t("Total Global Inventory Value", "إجمالي قيمة مخزون الشركة"), f"{total_all_value:,.2f} SR")
                    
                    st.dataframe(df_summary, width="stretch", hide_index=True)
                    
                    # رسم بياني بسيط لتوزيع القيمة بين المشاريع
                    st.bar_chart(data=df_summary, x=t("Project Name", "اسم المشروع"), y=t("Inventory Value", "قيمة المخزون (ريال)"))
                    
                else:
                    st.info(t("No data available for summary.", "لا توجد بيانات متاحة للملخص."))
            except Exception as e:
                st.error(f"Error generating summary: {e}")


        # 🔴 التبويب الثالث: نقل مواد (للأدمن فقط)
        # ======================================
    elif menu_key == "issue_invoice":
        if 'cart_items' not in st.session_state:
            st.session_state['cart_items'] = []

        st.header(t("🧾 Create Material Issue Invoice", "🧾 إنشاء فاتورة صرف مواد"))

        col_inv1, col_inv2 = st.columns(2)
        with col_inv1:
            recipient = st.text_input(t("Recipient Name", "اسم المستلم"), key="inv_recipient")
        with col_inv2:
            projects_list = get_projects_list()
            project_name = st.selectbox(t("Project Name", "اسم المشروع"), projects_list, key="inv_project_select")
        
        search_q = st.text_input(t("Quick search...", "بحث سريع عن مادة بالكود أو الاسم..."), key="inv_quick_search")
        
        if search_q:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # استعلام للبحث يشمل المشروع المختار والمستودع الرئيسي
            query = """
                SELECT * FROM inventory 
                WHERE (item LIKE %s OR code LIKE %s) 
                AND qty > 0 
                AND (project_name = %s OR project_name = 'Main Warehouse')
                LIMIT 20
            """
            cursor.execute(query, (f'%{search_q}%', f'%{search_q}%', project_name))
            search_results = cursor.fetchall()
            conn.close()

            if search_results:
                for r in search_results:
                    c_btn, c_qty, c_info = st.columns([1, 1, 4])
                    item_proj = (r.get('project_name') or r.get('project') or "").strip()
                    
                    unique_key = f"{r['code']}_{r['id']}"
                    with c_qty:
                        max_available = float(r['qty'])
                        q_val = st.number_input(t("Qty", "الكمية"), min_value=0.0, max_value=max_available, value=min(1.0, max_available), key=f"q_{unique_key}")
                    
                    with c_btn:
                        st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
                        # تم تحديث width لتصبح 'stretch' لتفادي التحذير
                        if st.button(t("➕ Add", "➕ إضافة"), key=f"add_{unique_key}", width="stretch"):
                            st.session_state['cart_items'].append({
                                'code': r['code'], 'item': r['item'], 'project': item_proj,
                                'qty': q_val, 'unit': r['unit'], 'price': r['price'], 'supplier': r['supplier']
                            })
                            st.rerun()
                            
                    with c_info:
                        is_main = "main warehouse" in item_proj.lower()
                        color = "blue" if is_main else "green"
                        label = "المخزن الرئيسي" if is_main else item_proj
                        st.markdown(f"**{r['item']}** | `{r['code']}`")
                        st.markdown(f":[{color}][المصدر: {label}] ({t('Stock', 'المخزون')}: {r['qty']})")
                    
        # --- 🛒 عرض محتويات السلة ---
        if st.session_state['cart_items']:
            st.divider()
            st.subheader(t("🛒 Selected Items", "🛒 المواد المختارة في السلة"))
            
            for i, item in enumerate(st.session_state['cart_items']):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
                with c1:
                    st.write(f"**{item['item']}** ({item['code']})")
                with c2:
                    st.write(f"{t('Qty', 'الكمية')}: {item['qty']}")
                with c3:
                    st.write(f"{item['price']} {t('SAR', 'ريال')}")
                with c4:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state['cart_items'].pop(i)
                        st.rerun()
            
            st.divider()
            
            # --- 🔘 أزرار التحكم (تظهر فقط إذا كانت السلة بها مواد) ---
            col_clear, col_save = st.columns(2)

            with col_clear:
                if st.button(t("🗑 Clear Cart", "🗑 تفريغ السلة"), width="content", key="clear_cart_btn"):
                    st.session_state['cart_items'] = []
                    st.rerun()

            with col_save:
                if st.button(t("✅ Save & Print", "✅ حفظ وطباعة"), width="content", type="primary", key="save_invoice_btn"):
                    if not recipient:
                        st.error(t("Recipient required", "اسم المستلم مطلوب"))
                    elif not project_name:
                        st.error(t("Project required", "المشروع مطلوب"))
                    else:
                        # منطق الحفظ وتوليد PDF
                        last_val = get_setting("last_inv")
                        new_no = int(last_val if last_val and str(last_val).isdigit() else 0) + 1
                        formatted_inv_no = f"{new_no:04d}"

                        if save_invoice_web(recipient, project_name, st.session_state['cart_items']):
                            set_setting("last_inv", str(new_no))
                            pdf_buffer = generate_issue_pdf_web(recipient, project_name, formatted_inv_no, t("Issue Note", "سند صرف"), st.session_state['cart_items'])
                            
                            if pdf_buffer:
                                st.session_state['last_pdf'] = pdf_buffer.getvalue()
                                st.session_state['last_inv_no'] = formatted_inv_no
                                st.success(f"✅ تم الحفظ برقم: {formatted_inv_no}")
                                st.rerun() # تحديث لإظهار زر التحميل

        else:
            # رسالة تظهر فقط إذا كانت السلة فارغة تماماً
            st.info(t("Cart is empty. Search and add items above.", "السلة فارغة. ابحث وأضف مواد أعلاه."))

        # --- 📄 قسم تحميل الملف (يظهر بعد الحفظ بنجاح) ---
        if st.session_state.get("last_pdf"):
            st.write("---")
            st.download_button(
                label=t("📥 Download PDF Now", "📥 تحميل الفاتورة الآن"),
                data=st.session_state["last_pdf"],
                file_name=f"Invoice_{st.session_state.get('last_inv_no','0001')}.pdf",
                mime="application/pdf",
                key="download_pdf_btn"
            )

            if st.button(t("🆕 New Invoice", "🆕 فاتورة جديدة"), key="new_inv_btn"):
                st.session_state['cart_items'] = []
                st.session_state['last_pdf'] = None
                st.rerun()

    # ======================================
        # ==============================
    elif menu_key == "invoice_mgmt":

        st.header(t("📄 Invoice Management", "📄 إدارة الفواتير"))

        # ✅ تعريف المستخدم الحالي لتجنب NameError
        current_user = st.session_state.get("username", None)
        if not current_user:
            st.warning(t("Please log in to access invoices", "الرجاء تسجيل الدخول للوصول إلى الفواتير"))
            st.stop()

        # تهيئة المتغير
        if "last_invoice_search" not in st.session_state:
            st.session_state["last_invoice_search"] = []

        st.subheader(t("🔎 Search by Invoice No", "🔎 البحث برقم السند"))
        search_doc = st.text_input(t("Enter Invoice No", "ادخل رقم السند"))

        # زر البحث
        if st.button(t("بحث", "Search")):
            if not search_doc.strip().isdigit():
                st.error(t("رقم السند يجب أن يكون رقم", "Invoice must be numeric"))
            else:
                conn = get_db_connection()
                if conn:
                    c = conn.cursor(dictionary=True)
                    try:
                        c.execute("""
                            SELECT *
                            FROM transactions
                            WHERE doc_no = %s
                            ORDER BY date DESC
                        """, (int(search_doc),))
                        results = c.fetchall()
                        st.session_state["last_invoice_search"] = results
                    finally:
                        c.close()
                        conn.close()

        # مثال استخدام current_user لجلب مشاريع المستخدم إذا احتجت
        projects_list = get_user_projects(current_user)  # ✅ الآن current_user معرف
                        
        st.divider()
        st.subheader(t("⚙️ System Settings", "⚙️ إعدادات النظام"))
        
        # 1. التحقق من أن المستخدم الحالي هو "admin"
        if st.session_state.get('user_role') == 'admin':
            with st.expander(t("⚠️ Danger Zone: Reset Invoice Counter", "⚠️ منطقة العمليات الحساسة: إعادة ضبط عداد الفواتير")):
                if st.button(t("🔄 Reset Invoice Counter to 01", "🔄 إعادة ضبط الترقيم إلى 01"), type="secondary"):
                    set_setting("last_inv", "0")
                    st.warning(t("Counter reset to 0. Next invoice will be 01.", "تم تصفير العداد إلى 0. الفاتورة القادمة ستكون رقم 01."))
                    st.rerun()
        else:
            st.info(t("Settings options are for admins only.", "خيارات الإعدادات مخصصة للمسؤولين فقط."))
        st.divider()
    # 2. تأكد أن هذا السطر (elif menu...) يبدأ في بداية السطر تماماً (بدون مسافات قبله)
        # ======================================
    elif menu_key == "reports":
        st.header(t("📊 Reports & Analytics", "📊 التقارير والتحليلات"))

        # 1. جلب المشاريع
        user_projects = get_user_projects(st.session_state['username'])
        project_options = [t("All Projects", "كل المشاريع")] + user_projects
        selected_project = st.selectbox(t("Filter by Project", "تصفية حسب المشروع"), project_options)

        # 2. اختيار نوع التقرير
        report_type = st.selectbox(
            t("Select Report Type", "اختر نوع التقرير"),
            [
                t("Incoming Logistics (IN)", "تقرير الوارد (إضافات المخزن)"),
                t("Outgoing Transactions (OUT)", "تقرير الصادر (حركات الصرف)")
            ]
        )

        st.divider()

        # تجهيز الاستعلام: استخدام LIKE مع البحث عن جزء من النص لضمان المطابقة
        if selected_project == t("All Projects", "كل المشاريع"):
            project_filter = ""
            params = ()
        else:
            # نأخذ أول كلمة إنجليزية من اسم المشروع (مثل VILLAS) لضمان البحث
            # هذا يحل مشكلة المسافات أو اختلاف الشرطة (-)
            simple_name = selected_project.split(' ')[0].strip() 
            project_filter = "AND project LIKE %s"
            params = (f"%{simple_name}%",)

        # ======================================
        # 📥 تقرير الوارد (IN)
        # ======================================
        if report_type == t("Incoming Logistics (IN)", "تقرير الوارد (إضافات المخزن)"):
            st.subheader(f"📥 {report_type} - {selected_project}")
            
            # تم تصحيح الاستعلام هنا
            query = f"""
                SELECT date, doc_no, code, item, qty, price, project, (qty*price) as total 
                FROM transactions 
                WHERE type='IN' {project_filter} 
                ORDER BY date DESC
            """
            
            try:
                df_in = pd.read_sql(query, engine, params=params)
                
                if not df_in.empty:
                    st.dataframe(df_in, width="stretch")
                    st.metric(t("Total Incoming Value", "إجمالي قيمة الواردات"), f"{df_in['total'].sum():,.2f} SAR")
                else:
                    st.info(t("No incoming records found", "لا توجد سجلات وارد لهذا المشروع"))
            except Exception as e:
                st.error(f"خطأ في قاعدة البيانات: {e}")

        # ======================================
        # 📤 تقرير الصادر (OUT)
        # ======================================
        elif report_type == t("Outgoing Transactions (OUT)", "تقرير الصادر (حركات الصرف)"):
            st.subheader(f"📤 {report_type} - {selected_project}")
            
            query = f"""
                SELECT date, doc_no, code, item, qty, price, project, (qty*price) as total 
                FROM transactions 
                WHERE type='OUT' {project_filter} 
                ORDER BY date DESC
            """
            
            try:
                df_out = pd.read_sql(query, engine, params=params)
                
                if not df_out.empty:
                    st.dataframe(df_out, width="stretch")
                    st.metric(t("Total Outgoing Value", "إجمالي قيمة الصادر"), f"{df_out['total'].sum():,.2f} SAR")
                else:
                    st.info(t("No outgoing records found", "لا توجد سجلات صرف لهذا المشروع"))
            except Exception as e:
                st.error(f"خطأ في قاعدة البيانات: {e}")

    elif menu_key == "import_export":
        st.header(t("📥 Import & Export Data", "📥 استيراد وتصدير البيانات"))

        # جلب المشاريع الحالية للمستخدم
        user_projects = get_user_projects(st.session_state['username'])

        # إضافة المستودع الرئيسي يدوياً للقائمة لتظهر في الخيارات
        if "Main Warehouse" not in user_projects:
            user_projects.insert(0, "Main Warehouse")

        if not user_projects:
            st.warning(t("No assigned projects found.", "لا توجد مشاريع مرتبطة بحسابك."))
        else:
            # الآن سيظهر "Main Warehouse" كخيار أول في القائمة المنسدلة
            target_project = st.selectbox(t("Select Target Project", "اختر المشروع المستهدف"), user_projects)

            tab1, tab2 = st.tabs([t("Import (Excel)", "استيراد (إكسل)"), t("Export (Excel)", "تصدير (إكسل)")])

            # --- قسم الاستيراد ---
            with tab1:
                st.subheader(t("Import to Project", "استيراد بيانات للمشروع"))
                up_file = st.file_uploader(t("Upload Excel File", "رفع ملف إكسل للمخزن"), type=["xlsx"])
                
                if up_file:
                    df_upload = pd.read_excel(up_file)
                    
                    # تنظيف الأعمدة الرقمية
                    numeric_cols = ['qty', 'price', 'main_q', 'main_qty'] 
                    for col in numeric_cols:
                        if col in df_upload.columns:
                            df_upload[col] = df_upload[col].astype(str).str.extract(r'(\d+\.?\d*)')
                            df_upload[col] = pd.to_numeric(df_upload[col], errors='coerce').fillna(0)
                    
                    df_upload = df_upload.fillna("")
                    df_upload['project'] = target_project
                    
                    total_rows = len(df_upload)
                    st.info(f"📊 تم اكتشاف {total_rows} بند لمشروع: {target_project}")
                    st.dataframe(df_upload.head(5))
                    if st.session_state.get("import_pdf"):

                        st.download_button(
                            label="📥 تحميل سند الاستلام PDF",
                            data=st.session_state["import_pdf"],
                            file_name="Import_Receipt.pdf",
                            mime="application/pdf",
                            width="stretch"
                        ) 

                    if st.button(t(f"Confirm Import {total_rows} Items", f"تأكيد استيراد {total_rows} بند")):
                        try:
                            import random
                            import time

                            doc_no = random.randint(100000, 999999)

                            imported_items = []

                            conn = get_db_connection()
                            cursor = conn.cursor()

                            for index, row in df_upload.iterrows():

                                imported_items.append({
                                    "code": str(row['code']),
                                    "item": row['item'],
                                    "qty": row['qty'],
                                    "unit": row['unit'],
                                    "project": target_project
                                })

                                cursor.execute(
                                    "SELECT id FROM inventory WHERE code=%s AND project=%s",
                                    (str(row['code']), target_project)
                                )

                                exists = cursor.fetchone()

                                if exists:

                                    existing_id = exists[0]

                                    cursor.execute(
                                        "UPDATE inventory SET qty = qty + %s WHERE id=%s",
                                        (row['qty'], existing_id)
                                    )

                                else:

                                    cursor.execute("""
                                        INSERT INTO inventory
                                        (
                                            code,
                                            item,
                                            qty,
                                            unit,
                                            price,
                                            supplier,
                                            project,
                                            project_name
                                        )
                                        VALUES
                                        (
                                            %s,%s,%s,%s,%s,%s,%s,%s
                                        )
                                    """, (
                                        str(row['code']),
                                        row['item'],
                                        row['qty'],
                                        row['unit'],
                                        row['price'],
                                        row['supplier'],
                                        target_project,
                                        target_project
                                    ))

                                cursor.execute("""
                                    INSERT INTO transactions
                                    (
                                        date,
                                        doc_no,
                                        code,
                                        item,
                                        qty,
                                        price,
                                        project,
                                        type
                                    )
                                    VALUES
                                    (
                                        NOW(),
                                        %s,
                                        %s,
                                        %s,
                                        %s,
                                        %s,
                                        %s,
                                        'IN'
                                    )
                                """, (
                                    doc_no,
                                    str(row['code']),
                                    row['item'],
                                    row['qty'],
                                    row['price'],
                                    target_project
                                ))

                            conn.commit()
                            conn.close()

                            pdf_buffer = generate_issue_pdf_web(
                                recipient="المستودع",
                                project=target_project,
                                doc_no=doc_no,
                                title="سند استلام مواد",
                                cart_items_list=imported_items
                            )

                            if pdf_buffer:
                                st.session_state["import_pdf"] = pdf_buffer.getvalue()
                            # =====================================
                            # إنشاء سند استلام المواد PDF
                            # =====================================

                            receipt_items = []

                            for _, row in df_upload.iterrows():
                                receipt_items.append({
                                    "code": str(row.get("code", "")),
                                    "item": str(row.get("item", "")),
                                    "qty": float(row.get("qty", 0)),
                                    "unit": str(row.get("unit", "")),
                                    "project": target_project
                                })

                            pdf_buffer = generate_issue_pdf_web(
                                recipient="أمين المستودع",
                                project=target_project,
                                doc_no=f"IMP-{doc_no}",
                                title="سند استلام مواد",
                                cart_items_list=receipt_items
                            )

                            if pdf_buffer:
                                st.session_state["import_pdf"] = pdf_buffer.getvalue()
                                st.session_state["import_pdf_name"] = f"Receipt_{doc_no}.pdf"

                            st.balloons()

                            st.success(
                                t(
                                    f"✅ Success! {total_rows} items imported to {target_project}.",
                                    f"✅ تم الاستيراد بنجاح! تم إضافة {total_rows} صنف إلى {target_project}."
                                )
                            )

                        except Exception as e:
                            st.error(f"❌ Error during import: {e}")
                            # إظهار رسالة النجاح والبالونات
                            st.balloons()
                            st.success(t(f"✅ Success! {total_rows} items imported to {target_project}.", 
                                         f"✅ تم الاستيراد بنجاح! تم إضافة {total_rows} صنف إلى {target_project}."))
                            if st.session_state.get("import_pdf"):

                                st.download_button(
                                    label="📄 تحميل سند الاستلام PDF",
                                    data=st.session_state["import_pdf"],
                                    file_name=st.session_state["import_pdf_name"],
                                    mime="application/pdf",
                                    width="stretch",
                                    type="primary"
                                )
                            
                           
                         

                        except Exception as e:
                            st.error(f"❌ Error during import: {e}")

            # --- قسم التصدير ---
            with tab2:
                st.subheader(t("Export Project Data", "تصدير بيانات المشروع"))
                if st.button(t(f"Prepare Export for {target_project}", f"تجهيز ملف تصدير لـ {target_project}")):
                    query = "SELECT * FROM inventory WHERE project = %s"
                    df_ex = pd.read_sql(query, engine, params=(target_project,))
                    
                    if not df_ex.empty:
                        import io
                        out_ex = io.BytesIO()
                        with pd.ExcelWriter(out_ex, engine='xlsxwriter') as wr: 
                            df_ex.to_excel(wr, index=False)
                        st.download_button(
                            label=t("Download Excel File", "تحميل ملف الإكسل"),
                            data=out_ex.getvalue(),
                            file_name=f"Inventory_{target_project}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning(t("No data found for this project.", "لا توجد بيانات مسجلة لهذا المشروع."))
    elif menu_key == "settings":
        if st.session_state['user_role'] == 'admin':
            t1, t2, t3 = st.tabs([
                t("Settings", "الإعدادات"),
                t("Users", "المستخدمين"),
                t("Backup", "النسخ")
            ])

            # =========================
            # 🔹 Tab 1 - Settings
            # =========================
            with t1:
                with st.form("set_f"):
                    c_n = st.text_input(
                        t("Company", "الشركة"),
                        get_setting("company")
                    )

                    addr = st.text_input(
                        t("Address", "العنوان"),
                        get_setting("addr1")
                    )

                    logo = st.file_uploader(
                        t("Logo", "الشعار"),
                        type=["jpg", "png"]
                    )

                    watermark = st.file_uploader(
                        t("Watermark Logo", "الشعار المائي"),
                        type=["jpg", "png"]
                    )

                    if st.form_submit_button(t("Save", "حفظ")):
                        set_setting("company", c_n)
                        set_setting("addr1", addr)

                        if logo:
                            upload_generic_web("logo", logo)

                        if watermark:
                            upload_generic_web("watermark", watermark)

                        st.success("✅")
                        st.rerun()
                # ➕ إضافة مشروع جديد
                # =================================================
                st.divider()

                st.subheader("➕ إضافة مشروع جديد")

                new_project_name = st.text_input(
                    "اسم المشروع الجديد"
                )

                if st.button("➕ إنشاء المشروع"):

                    if new_project_name.strip():

                        if add_project(new_project_name.strip()):

                            st.success("✅ تم إنشاء المشروع بنجاح")

                            st.rerun()

                        else:
                            st.error("❌ فشل إنشاء المشروع")

                    else:
                        st.warning("أدخل اسم المشروع")

            # =========================
            # 🔹 Tab 2 - Users & Permissions
            # =========================
            with t2:
                st.subheader(t("Add New User", "إضافة مستخدم جديد"))
                add_user_web_ui()

                st.divider()
                st.subheader(t("Manage Users & Full Permissions", "إدارة المستخدمين والصلاحيات الشاملة"))

                all_menu_map = {
                    "inventory": t("📦 Inventory", "📦 المخزن"),
                    "issue_invoice": t("🧾 Issue Invoice", "🧾 صرف فاتورة"),
                    "invoice_mgmt": t("📄 Invoice Management", "📄 إدارة الفواتير"),
                    "reports": t("📊 Reports", "📊 التقارير"),
                    "import_export": t("📁 Import/Export Excel", "📁 استيراد/تصدير"),
                    "stock_audit": t("📋 Stock Audit", "📋 جرد المخزون"),
                    "supplier_receipts": t("📂 Supplier Receipts", "📂 سندات الموردين"),
                    "equipment_custody": t("📂 equipment_custody", "📂العهد"),
                    "settings": t("⚙️ Settings & Users", "⚙️ الإعدادات")
                }

                all_users = get_all_users_list()
                if all_users:
                    target_user = st.selectbox(t("Select User", "اختر المستخدم للتعديل"), all_users)
                    current_user_menus = get_user_menu_perms(target_user)
                    current_user_projs = get_user_projects(target_user)

                    with st.form("master_user_edit_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_name = st.text_input(t("Username", "اسم المستخدم"), value=target_user)
                        with col2:
                            new_pass = st.text_input(
                                t("New Password", "كلمة مرور جديدة"),
                                type="password",
                                help="أدخل كلمة مرور لتشفيرها بـ bcrypt وإصلاح خطأ Salt"
                            )

                        st.write("---")

                        valid_defaults = [m for m in current_user_menus if m in all_menu_map]

                        selected_menus = st.multiselect(
                            t("Allowed Menus", "القوائم المسموحة"),
                            options=list(all_menu_map.keys()),
                            default=valid_defaults,
                            format_func=lambda x: all_menu_map[x]
                        )

                        selected_projs = st.multiselect(
                            t("Allowed Projects", "المشاريع المسموحة"),
                            options=get_system_projects(),
                            default=current_user_projs
                        )

                        new_proj_manual = st.text_input(t("Add Project Manually", "إضافة اسم مشروع جديد يدوياً"))

                        if st.form_submit_button(t("Save All Permissions", "حفظ كافة التغييرات")):
                            try:
                                conn = get_db_connection()
                                c = conn.cursor()

                                # أ. تحديث وتشفير الباسورد بـ bcrypt
                                if new_pass:
                                    import bcrypt
                                    hashed_pw = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                    c.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_pw, target_user))

                                # ب. تحديث الاسم (مع فحص التكرار)
                                if new_name != target_user:
                                    c.execute("SELECT username FROM users WHERE username = %s", (new_name,))
                                    if c.fetchone():
                                        st.error("اسم المستخدم محجوز مسبقاً")
                                        st.stop()
                                    c.execute("UPDATE users SET username = %s WHERE username = %s", (new_name, target_user))
                                    c.execute("UPDATE project_permissions SET username = %s WHERE username = %s", (new_name, target_user))
                                    c.execute("UPDATE user_menu_permissions SET username = %s WHERE username = %s", (new_name, target_user))

                                # ج. تحديث صلاحيات القوائم
                                c.execute("DELETE FROM user_menu_permissions WHERE username = %s", (new_name,))
                                for m in selected_menus:
                                    c.execute("INSERT INTO user_menu_permissions (username, menu_name) VALUES (%s, %s)", (new_name, m))

                                # د. تحديث صلاحيات المشاريع
                                c.execute("DELETE FROM project_permissions WHERE username = %s", (new_name,))
                                final_projs = set(selected_projs)
                                if new_proj_manual.strip():
                                    final_projs.add(new_proj_manual.strip())
                                for p in final_projs:
                                    c.execute("INSERT INTO project_permissions (username, project_name) VALUES (%s, %s)", (new_name, p))

                                conn.commit()
                                st.success("✅ تم تحديث الصلاحيات وتصفية القيم القديمة بنجاح!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                            finally:
                                conn.close()
            # 🔹 Tab 3 - Backup
            # =========================
            with t3:
                backup_database_web()

            # =========================
            # 🔴 Admin Actions
            # =========================
            st.divider()
            st.subheader(t("⚠️ Admin Actions", "⚠️ إجراءات المسؤول"))

            # -------- Delete All Inventory --------
            if st.button(t("🗑 Delete All Inventory", "🗑 حذف كل المخزون")):
                st.session_state["confirm_delete_inventory"] = True

            if st.session_state.get("confirm_delete_inventory"):
                st.warning(t("⚠️ This will delete ALL inventory permanently!", "⚠️ سيتم حذف كل المخزون نهائيًا!"))

                if st.button(t("✅ Confirm Delete Inventory", "✅ تأكيد حذف المخزون")):
                    try:
                        conn = get_db_connection()
                        c = conn.cursor()

                        # تصفير جدول المخزون والعداد (ID)
                        try:
                            c.execute("TRUNCATE TABLE inventory")
                            c.execute("TRUNCATE TABLE inventory_logs")
                        except:
                            # في حال استخدام SQLite
                            c.execute("DELETE FROM inventory")
                            c.execute("DELETE FROM inventory_logs")
                            c.execute("DELETE FROM sqlite_sequence WHERE name IN ('inventory', 'inventory_logs')")
                        
                        conn.commit()
                        st.success(t("✅ All inventory & IDs reset", "✅ تم حذف المخزون وتصفير الـ ID"))
                        st.session_state["confirm_delete_inventory"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        c.close()
                        conn.close()

            # -------- Delete All Transactions --------
            if st.button(t("🗑 Delete All Transactions", "🗑 حذف كل الفواتير")):
                st.session_state["confirm_delete_transactions"] = True

            if st.session_state.get("confirm_delete_transactions"):
                st.warning(t("⚠️ This will delete ALL invoices permanently!", "⚠️ سيتم حذف كل الفواتير نهائيًا!"))

                if st.button(t("✅ Confirm Delete Transactions", "✅ تأكيد حذف الفواتير")):
                    try:
                        conn = get_db_connection()
                        c = conn.cursor()

                        # تصفير جدول العمليات والعداد (ID)
                        try:
                            c.execute("TRUNCATE TABLE transactions")
                        except:
                            # في حال استخدام SQLite
                            c.execute("DELETE FROM transactions")
                            c.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")

                        conn.commit()
                        st.success(t("✅ All invoices & IDs reset", "✅ تم حذف كل الفواتير وتصفير الـ ID"))
                        st.session_state["confirm_delete_transactions"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        c.close()
                        conn.close()

    elif menu_key == "stock_audit":
        st.header(t("🏢 ERP Stock Audit System", "🏢 نظام جرد احترافي"))

        search_audit = st.text_input(
            t("Search by Code or Name", "ابحث بالكود أو الاسم")
        )

        if search_audit:
            query = """
                SELECT id, code, item, qty, price
                FROM inventory
                WHERE code LIKE %s
                OR item LIKE %s
                ORDER BY item ASC
            """
            like_value = f"%{search_audit}%"

            df_items = pd.read_sql(
                query,
                engine,
                params=(like_value, like_value)
            )

            if not df_items.empty:
                # دمج الكود والاسم بـ 12 مسافة (العرض فقط)
                spacer = " " * 12
                df_items["display_text"] = df_items["code"].astype(str) + spacer + df_items["item"]

                selected_display = st.selectbox(
                    t("Select Item", "اختر الصنف"),
                    df_items["display_text"]
                )

                # استخراج السطر المختار
                selected_row = df_items[df_items["display_text"] == selected_display].iloc[0]

                selected_code = selected_row["code"]
                system_qty = float(selected_row["qty"])
                item_name = selected_row["item"]
                
          

                st.divider()

                col1, col2 = st.columns(2)

                with col1:
                    st.info(
                        t(
                            f"System Quantity: {system_qty}",
                            f"الكمية المسجلة: {system_qty}"
                        )
                    )

                with col2:
                    real_qty = st.number_input(
                        t("Real Quantity", "الكمية الفعلية"),
                        min_value=0.0,
                        value=system_qty
                    )

                difference = real_qty - system_qty

                if difference > 0:
                    st.success(f"Increase: +{difference}")
                elif difference < 0:
                    st.error(f"Decrease: {difference}")
                else:
                    st.warning(t("No difference", "لا يوجد فرق"))

                # -------- ERP FIELDS --------
                reason = st.selectbox(
                    t("Audit Reason", "سبب الجرد"),
                    ["Damage", "Loss", "Entry Error", "Adjustment", "Other"]
                )

                employee = st.text_input(
                    t("Employee Name", "اسم الموظف")
                )

                if st.button(t("Apply ERP Audit", "تنفيذ الجرد الاحترافي")):

                    if difference != 0 and employee:
                        audit_no = generate_audit_number()

                        try:
                            # استخدام engine.begin لضمان تنفيذ العمليات أو التراجع عنها في حال الخطأ
                            with engine.begin() as conn:
                                # 1. تحديث المخزون
                                conn.execute(
                                    text("UPDATE inventory SET qty=:qty WHERE code=:code"),
                                    {"qty": real_qty, "code": selected_code}
                                )

                                # 2. تسجيل في log
                                conn.execute(text("""
                                    INSERT INTO stock_audit_log 
                                    (audit_no, code, item, system_qty, real_qty, difference, reason, employee)
                                    VALUES (:audit_no, :code, :item, :system_qty, :real_qty, :difference, :reason, :employee)
                                """), {
                                    "audit_no": audit_no,
                                    "code": selected_code,
                                    "item": item_name,
                                    "system_qty": system_qty,
                                    "real_qty": real_qty,
                                    "difference": difference,
                                    "reason": reason,
                                    "employee": employee
                                })

                                # 3. تسجيل حركة
                                # 3. تسجيل حركة (بدون عمود total)
                                movement_type = "AUDIT-IN" if difference > 0 else "AUDIT-OUT"
                                conn.execute(text("""
                                    INSERT INTO transactions 
                                    (date, doc_no, type, code, item, qty, price)
                                    VALUES (NOW(), :doc_no, :type, :code, :item, :qty, :price)
                                """), {
                                    "doc_no": audit_no,
                                    "type": movement_type,
                                    "code": selected_code,
                                    "item": item_name,
                                    "qty": abs(difference),
                                    "price": float(selected_row["price"])
                                })

                            st.success(f"Audit Completed ✔️ ({audit_no})")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")

                    else:
                        st.warning(t("Please enter employee name and ensure quantity changed.", "يرجى إدخال اسم الموظف والتأكد من تغيير الكمية"))


# -------------------------------
    # -------------------------------
# 4️⃣ Supplier Receipts Module
# -------------------------------
    elif menu_key == "supplier_receipts":
        st.header(t("📂 Supplier Receipts", "📂 سندات الموردين"))

        # التحقق من تسجيل الدخول
        current_user = st.session_state.get('username', None)
        if not current_user:
            st.warning(t("Please log in to access supplier receipts", "الرجاء تسجيل الدخول للوصول إلى سندات الموردين"))
            st.stop()

        # 1️⃣ جلب بيانات المشاريع والموردين وتجهيز القواميس
        projects = []
        project_id_map = {}
        vendors = []

        try:
            conn = get_db_connection()
            with conn.cursor(dictionary=True) as cursor:
                # جلب المشاريع بدون تكرار
                cursor.execute("SELECT DISTINCT id, project_name FROM project_permissions ORDER BY project_name ASC")
                projects = cursor.fetchall()
            
                # جلب الموردين المتاحين
                cursor.execute("SELECT vendor_name FROM vendors ORDER BY vendor_name ASC")
                vendors = cursor.fetchall()
            
            project_id_map = {p["project_name"]: p["id"] for p in projects}
        except Exception as e:
            st.error(f"DB Error: {e}")
        finally:
            if conn:
                conn.close()

        project_names = sorted(list(set([p["project_name"] for p in projects])))
        vendor_names = [v["vendor_name"] for v in vendors]

        # 2️⃣ بناء النموذج الذكي (Smart Form)
        st.subheader(t("📝 Register New Receipt", "📝 تسجيل سند جديد"))

        selected_date = st.date_input(t("Date", "التاريخ"), format="YYYY-MM-DD")
        
        # صندوق المورد الذكي: يدعم كتابة اسم جديد غير مدرج بالقائمة
        vendor_input = st.selectbox(
            t("Select or Type Vendor Name", "اختر المورد أو اكتب اسماً جديداً"),
            options=[""] + vendor_names + ["➕ إضافة مورد جديد..."],
            index=0
        )

        selected_vendor = ""
        if vendor_input == "➕ إضافة مورد جديد...":
            selected_vendor = st.text_input(t("Type New Vendor Name", "اكتب اسم المورد الجديد هنا:")).strip()
        else:
            selected_vendor = vendor_input

        # صندوق اختيار المشروع بالبحث
        project_name_input = st.selectbox(
            t("Select Project Code", "اختر رمز المشروع"),
            options=[""] + project_names,
            index=0
        )

        # حقل رفع ملفات الـ PDF
        uploaded_files = st.file_uploader(
            t("Upload PDF Files", "رفع ملفات PDF"),
            type=["pdf"],
            accept_multiple_files=True
        )
        
        # زر الحفظ والمعالجة
        if st.button(t("Save and Process", "حفظ ومعالجة البيانات")):
            if not selected_vendor or not project_name_input or not uploaded_files:
                st.error(t("Please fill in all fields and upload files.", "الرجاء تعبئة جميع الحقول ورفع الملفات."))
            else:
                project_id = project_id_map.get(project_name_input)
                project_dir = os.path.join("project_uploads", project_name_input)
                os.makedirs(project_dir, exist_ok=True)

                conn = get_db_connection()
                cursor = conn.cursor()
            
                date_str = selected_date.strftime("%Y-%m-%d")

                # فحص وإضافة المورد تلقائياً لقاعدة البيانات إذا كان جديداً
                if selected_vendor not in vendor_names:
                    try:
                        cursor.execute("INSERT IGNORE INTO vendors (vendor_name) VALUES (%s)", (selected_vendor,))
                        conn.commit()
                    except Exception as ex:
                        print(f"Error saving new vendor: {ex}")

                # معالجة الملفات المرفوعة وتسميتها ذكياً
                for uploaded_file in uploaded_files:
                    fname_lower = uploaded_file.name.lower()

                    if fname_lower.endswith(".pdf"):
                        # صياغة الاسم الجديد تلقائياً: Vendor Name - Date - Project Name.pdf
                        new_filename = f"{selected_vendor} - {date_str} - {project_name_input}.pdf"
                        # تنظيف الاسم من الرموز غير المسموحة في نظام التشغيل
                        clean_name = "".join([c for c in new_filename if c.isalnum() or c in "._- "]).strip()
                        dst_path = os.path.join(project_dir, clean_name)

                        # حفظ الملف في المجلد الفعلي
                        with open(dst_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # تسجيل الملف في قاعدة البيانات
                        cursor.execute("""INSERT IGNORE INTO supplier_documents
                            (project_id, file_name, file_path, file_size, uploaded_by)
                            VALUES (%s, %s, %s, %s, %s)""",
                            (project_id, clean_name, dst_path, uploaded_file.size, current_user))
                        
                        st.success(f"✅ {clean_name}")

                conn.commit()
                cursor.close()
                conn.close()
                st.rerun()

        # 3️⃣ عرض وتصفح السندات مع تصفية حية ذكية أثناء الكتابة
        st.divider()
        st.subheader(t("📂 Browse & Download Receipts", "📂 تصفح وتحميل السندات"))
        
        search_project_select = st.selectbox(
            t("Select Project to View Files", "اختر المشروع لعرض ملفاته"),
            options=[""] + project_names,
            key="search_project_select"
        )

        if search_project_select:
            project_dir = os.path.join("project_uploads", search_project_select)
            files_list = [f for f in os.listdir(project_dir) if f.lower().endswith(".pdf")] if os.path.exists(project_dir) else []

            # صندوق البحث بمجرد الكتابة لتصفية المورد أو التاريخ أو الملف
            search_pdf = st.text_input(t("Search by Vendor, Date, or File Name", "بحث باسم المورد، التاريخ، أو اسم الملف"))
            # ... كود الفلترة وصندوق البحث ...
            filtered_files = [f for f in files_list if search_pdf.lower() in f.lower()] if search_pdf else files_list

            from streamlit_pdf_viewer import pdf_viewer

            for fname in filtered_files:
                fpath = os.path.join(project_dir, fname)
                
                # استخدام اسم الملف كمفتاح فريد وآمن للـ session_state والـ buttons
                safe_key = fname.replace(".", "_").replace(" ", "_").replace("-", "_")
                
                state_key = f"view_pdf_{safe_key}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False

                st.markdown("---")
                with st.expander(f"📄 {fname}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        # تعديل الـ key هنا
                        if st.button(t("👁️ Preview", "👁️ معاينة"), key=f"btn_pre_{safe_key}"):
                            st.session_state[state_key] = not st.session_state[state_key]

                    with col2:
                        with open(fpath, "rb") as f:
                            # تعديل الـ key هنا لزر التحميل
                            st.download_button(
                                t("📥 Download", "📥 تحميل"), 
                                f.read(), 
                                file_name=fname, 
                                key=f"btn_dl_{safe_key}",
                                mime="application/pdf"
                            )

                    # المعاينة باستخدام الـ safe_key ومفتاح مخصص للـ pdf_viewer
                    if st.session_state[state_key] and os.path.exists(fpath):
                        pdf_viewer(fpath, width=700, height=800, key=f"viewer_{safe_key}")


    elif menu_key == "equipment_custody":

        # 1. تهيئة متغيرات الجلسة
        if "custody_cart" not in st.session_state:
            st.session_state["custody_cart"] = []

        if "pdf_blob" not in st.session_state:
            st.session_state["pdf_blob"] = None

        # دالة جلب البيانات
        def get_known_recipients():
            try:
                conn = get_db_connection()

                if not conn:
                    return []

                cursor = conn.cursor(dictionary=True)

                cursor.execute("""
                    SELECT recipient, national_id, project 
                    FROM equipment_custody 
                    GROUP BY recipient, national_id, project
                """)

                data = cursor.fetchall()

                conn.close()

                return data

            except:
                return []

        st.header(t("📋 Equipment Custody Management", "📋 إدارة العهدة"))

        known_users = get_known_recipients()

        search_options = {
            f"{u['recipient']} | {u['national_id']}": u
            for u in known_users
        }

        tab_add, tab_search, tab_report, tab_alerts = st.tabs([
            t("➕ New Entry", "➕ حركة جديدة"),
            t("🔍 Manage", "🔍 إدارة المراجعة"),
            t("📊 Report", "📊 جرد صافي العهدة"),
            t("⚠️ Alerts", "⚠️ تنبيهات التأخير")
        ])

     
        # ------------------- التبويب الأول: إضافة عهدة (إزاحة 8 مسافات) -------------------
        with tab_add:
            # زر تصفير العمليات (12 مسافة مع خاصية width='stretch')
            if st.button(t("🆕 New Receipt", "🆕 سند جديد / تصفير"), width='stretch', key="reset_custody"):
                st.session_state["custody_cart"] = []
                st.session_state["pdf_blob"] = None
                st.rerun()

            # عرض زر تحميل الـ PDF (12 مسافة)
            if st.session_state.get("pdf_blob"):
                st.download_button(
                    label="📥 تحميل السند PDF", 
                    data=st.session_state["pdf_blob"], 
                    file_name="Receipt.pdf", 
                    mime="application/pdf", 
                    width='stretch', 
                    type="primary"
                )
                st.divider()

            col_m1, col_m2 = st.columns(2)
            with col_m1: 
                m_type = st.selectbox(t("Type", "نوع الحركة"), ["OUT", "IN"], format_func=lambda x: "إعطاء عهدة (OUT)" if x=="OUT" else "إرجاع عهدة (IN)")
            
            # تحسين البحث والاختيار (12 مسافة)
            selected_option = st.selectbox(t("Search Name/ID", "ابحث عن مستلم (اسم/هوية)"), options=[""] + list(search_options.keys()))
            new_name = st.text_input(t("Or New Name", "أو اسم مستلم جديد"))
            
            if new_name:
                final_recipient, default_id, default_pj = new_name, "", ""
            elif selected_option and selected_option != "":
                u_d = search_options[selected_option]
                final_recipient, default_id, default_pj = u_d['recipient'], u_d['national_id'], u_d['project']
            else:
                final_recipient, default_id, default_pj = "", "", ""

            # حقول الإدخال (12 مسافة)
            c_id, c_pj, c_it = st.columns(3)
            with c_id: cust_id = st.text_input(t("ID No", "رقم الهوية"), value=default_id, key="c_id_input")
            with c_pj: cust_project = st.text_input(t("Project", "المشروع"), value=default_pj, key="c_pj_input")
            with c_it: cust_item = st.text_input(t("Item", "المعدة / الجهاز"), key="c_item_input")

            c_qty, c_date = st.columns(2)
            with c_qty: 
                st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)
                cust_qty = st.number_input(t("Qty", "الكمية"), min_value=1.0, value=1.0)
            with c_date: 
                st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)
                cust_date = st.date_input(t("Date", "التاريخ"))

            # زر الإضافة (12 مسافة مع خاصية width='stretch')
            if st.button(t("➕ Add to List", "➕ إضافة للقائمة"), width='stretch'):
                if final_recipient and cust_item and cust_id:
                    st.session_state["custody_cart"].append({
                        "item": cust_item, "qty": cust_qty, "date": str(cust_date), 
                        "proj": cust_project, "recipient": final_recipient, "id": cust_id, "type": m_type
                    })
                    st.success(t("Added to list", "تمت الإضافة للقائمة"))
                    st.rerun()
                else:
                    st.error(t("Please fill Name, ID and Item", "يرجى إكمال الاسم والهوية والصنف"))
        if st.session_state["custody_cart"]:
            st.divider()
            st.subheader(t("Items in Receipt", "الأصناف في السند الحالي"))
            st.table(pd.DataFrame(st.session_state["custody_cart"]))
            
            if st.button(t("✅ Final Save & Generate", "✅ حفظ نهائي واستخراج السند"), type="primary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # ترقيم السندات
                    current_year = datetime.now().year
                    last_val = get_setting("last_cust_no") or "0"
                    new_no = int(last_val) + 1
                    
                    # تمييز نوع السند
                    is_return = any(row['type'] == 'IN' for row in st.session_state["custody_cart"])
                    doc_no = f"RET-{current_year}-{new_no:04d}" if is_return else f"{current_year}-{new_no:04d}"
                    doc_title = t("Return Note", "سند مرتجع عهدة") if is_return else t("Custody Note", "سند استلام عهدة")

                    for row in st.session_state["custody_cart"]:
                        cursor.execute("""
                            INSERT INTO equipment_custody (recipient, national_id, project, item, qty, move_type, custody_date, doc_no)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (row['recipient'], row['id'], row['proj'], row['item'], row['qty'], row['type'], row['date'], doc_no))
                    
                    conn.commit()
                    set_setting("last_cust_no", str(new_no))
                    
                    # توليد الملف
                    pdf_buf = generate_custody_pdf_web(
                        final_recipient, cust_id, cust_project, doc_no, doc_title, 
                        st.session_state["custody_cart"]
                    )
                    
                    if pdf_buf:
                        st.session_state["pdf_blob"] = pdf_buf.getvalue()
                        st.session_state["custody_cart"] = [] # تصفير السلة بعد الحفظ
                        conn.close()
                        st.rerun()
                            
                except Exception as e: 
                    st.error(f"Error during save: {e}")



        # ------------------- التبويب الثاني: البحث والمراجعة (4 مسافات) -------------------
        # ------------------- التبويب الثاني: البحث والمراجعة (إزاحة 8 مسافات) -------------------
        with tab_search:
            st.subheader(t("🔍 Manage & Review", "🔍 مراجعة الحركات"))
            search_query = st.text_input(t("Search...", "ابحث باسم المستلم، الهوية، أو المعدة"), key="search_cust_review")
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                # استعلام جلب البيانات مع الفلترة (12 مسافة)
                sql = """
                    SELECT *, 
                    CASE WHEN move_type = 'OUT' THEN '📥 إعطاء' ELSE '📤 إرجاع' END as status_display 
                    FROM equipment_custody 
                    WHERE recipient LIKE %s OR national_id LIKE %s OR item LIKE %s
                    ORDER BY custody_date DESC
                """
                params = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()

                if rows:
                    df_search = pd.DataFrame(rows)
                    
                    # --- زر تصدير إكسل (12 مسافة) ---
                    col_search, col_excel = st.columns([3, 1])
                    with col_excel:
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_search.to_excel(writer, index=False, sheet_name='Custody_Report')
                        
                        st.download_button(
                            label=t("📥 Export to Excel", "📥 تصدير إلى إكسل"),
                            data=output.getvalue(),
                            file_name=f"Custody_Search_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width='stretch'
                        )

                    # --- عرض النتائج بالتفصيل (12 مسافة) ---
                    for row in rows:
                        label = f"{row['status_display']} | {row['custody_date']} | {row['recipient']} -> {row['item']}"
                        
                        with st.expander(label):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.write(f"**{t('Doc No', 'رقم السند')}:** {row['doc_no']}")
                                st.write(f"**{t('National ID', 'رقم الهوية')}:** {row['national_id']}")
                            with c2:
                                st.write(f"**{t('Item', 'المعدة/الجهاز')}:** {row['item']}")
                                st.write(f"**{t('Qty', 'الكمية')}:** {row['qty']}")
                            with c3:
                                st.write(f"**{t('Project', 'المشروع')}:** {row['project']}")
                                st.write(f"**{t('Type', 'النوع')}:** {row['move_type']}")
                else:
                    st.info(t("No records found", "لا توجد سجلات تطابق بحثك"))
                    
            except Exception as e:
                st.error(f"Search Error: {e}")

        # ------------------- التبويب الثالث: جرد صافي العهدة (4 مسافات) -------------------
        # ------------------- التبويب الثالث: جرد صافي العهدة (إزاحة 8 مسافات) -------------------
        with tab_report:
            st.subheader(t("📊 Net Custody Report", "📊 تقرير صافي العهدة الحالية"))
            
            try:
                conn = get_db_connection()
                # استعلام ذكي يحسب الصافي (12 مسافة)
                query = """
                    SELECT 
                        recipient AS 'المستلم',
                        national_id AS 'رقم الهوية',
                        item AS 'المعدة/الجهاز',
                        project AS 'المشروع',
                        SUM(CASE WHEN move_type = 'OUT' THEN qty ELSE 0 END) - 
                        SUM(CASE WHEN move_type = 'IN' THEN qty ELSE 0 END) AS 'الرصيد الحالي'
                    FROM equipment_custody
                    GROUP BY recipient, national_id, item, project
                    HAVING `الرصيد الحالي` > 0
                """
                df_report = pd.read_sql(query, conn)
                conn.close()

                if not df_report.empty:
                    # زر تصدير التقرير الصافي إلى Excel (12 مسافة)
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_report.to_excel(writer, index=False, sheet_name='Net_Custody')
                    
                    st.download_button(
                        label=t("📥 Export Net Custody to Excel", "📥 تصدير جرد العهدة إلى إكسل"),
                        data=output.getvalue(),
                        file_name=f"Net_Custody_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )

                    # عرض الجدول بشكل أنيق (12 مسافة)
                    st.dataframe(df_report, width='stretch')
                    
                    st.info(t("Note: This table shows only items currently with the employees.", 
                              "ملاحظة: هذا الجدول يظهر فقط المواد الموجودة في ذمة الموظفين حالياً."))
                else:
                    st.warning(t("No active custody found.", "لا توجد عهد نشطة حالياً (تم إرجاع الكل أو لم يتم التسجيل بعد)."))
                    
            except Exception as e:
                st.error(f"Report Error: {e}")

        # ------------------- التبويب الرابع: التنبيهات (إزاحة 8 مسافات) -------------------
        with tab_alerts:
            st.subheader(t("⚠️ Late Returns", "⚠️ عهد متأخرة (>30 يوم)"))
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    # استعلام لجلب العهد التي خرجت ولم تعد وتجاوزت 30 يوماً (12 مسافة)
                    cursor.execute("""
                        SELECT 
                            recipient AS 'المستلم', 
                            item AS 'المعدة', 
                            custody_date AS 'تاريخ الاستلام', 
                            DATEDIFF(CURDATE(), custody_date) AS 'أيام التأخير'
                        FROM equipment_custody 
                        WHERE move_type = 'OUT' 
                        AND (recipient, item) NOT IN (
                            SELECT recipient, item FROM equipment_custody WHERE move_type = 'IN'
                        )
                        AND DATEDIFF(CURDATE(), custody_date) > 30
                    """)
                    late_rows = cursor.fetchall()
                    conn.close()
                    
                    if late_rows:
                        # عرض النتائج في جدول (12 مسافة)
                        st.table(pd.DataFrame(late_rows))
                    else:
                        st.success(t("No late items found.", "لا يوجد متأخرات حالياً."))
            except Exception as e:
                # معالجة الخطأ في حال وجود مشكلة في قاعدة البيانات
                st.error(f"Alerts Error: {e}")
# =========================================================
# 📄 دالة توليد سند العهدة PDF (التعهد القانوني + إصلاح العلامة المائية)
# =========================================================


