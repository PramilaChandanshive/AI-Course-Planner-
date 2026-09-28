"""
AI POWERED COURSE PLANNER - MODIFIED WITH PROPER SLEEP HANDLING
Courses are scheduled ONLY after sleep hours (after 7:00 AM)
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, Menu
from datetime import datetime, timedelta
import threading
import time
import re
from plyer import notification

# ==================== DATA STORAGE ====================
class Database:
    def __init__(self):
        self.users_file = "course_planner_data.json"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = []
        else:
            self.users = []
    
    def save_data(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def find_user_by_email(self, email):
        for user in self.users:
            if user.get('email', '').lower() == email.lower():
                return user
        return None
    
    def find_user_by_username(self, username):
        for user in self.users:
            if user.get('username', '').lower() == username.lower():
                return user
        return None
    
    def add_user(self, user_data):
        self.users.append(user_data)
        self.save_data()
    
    def update_user(self, email, updated_data):
        for i, user in enumerate(self.users):
            if user.get('email', '').lower() == email.lower():
                self.users[i] = updated_data
                self.save_data()
                return True
        return False

# ==================== MAIN APPLICATION ====================
class CoursePlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AI Course Planner - Smart Schedule After Sleep")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f2f5')
        self.root.minsize(1200, 700)
        
        self.db = Database()
        self.current_user = None
        self.daily_schedule = []
        self.notification_running = False
        self.notification_thread = None
        
        # Modern Color Palette
        self.colors = {
            'primary': '#4361EE',
            'secondary': '#06FFA5',
            'danger': '#EF476F',
            'warning': '#FFD166',
            'info': '#118AB2',
            'dark': '#073B4C',
            'light': '#F8F9FA',
            'white': '#FFFFFF',
            'success': '#06FFA5',
            'purple': '#7209B7',
            'orange': '#F8961E',
            'pink': '#F72585',
            'gradient_start': '#4361EE',
            'gradient_end': '#7209B7',
            'sleep': '#2E86AB',
            'study': '#A23B72'
        }
        
        self.show_welcome()
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    # ==================== WELCOME & AUTHENTICATION ====================
    def show_welcome(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Gradient background
        canvas = tk.Canvas(self.root, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        for i in range(100):
            color = self.interpolate_color(self.colors['gradient_start'], self.colors['gradient_end'], i/100)
            canvas.create_rectangle(0, i*9, self.root.winfo_screenwidth(), (i+1)*9, fill=color, outline='')
        
        # Center card
        card = tk.Frame(self.root, bg=self.colors['white'], relief='flat', bd=0)
        card.place(relx=0.5, rely=0.5, anchor='center', width=550, height=500)
        
        tk.Label(card, text="🎯", font=('Segoe UI', 60),
                bg=self.colors['white'], fg=self.colors['primary']).pack(pady=20)
        tk.Label(card, text="AI Course Planner", font=('Segoe UI', 28, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack()
        tk.Label(card, text="Smart Schedule After Sleep Hours", font=('Segoe UI', 12),
                bg=self.colors['white'], fg='gray').pack()
        
        btn_frame = tk.Frame(card, bg=self.colors['white'])
        btn_frame.pack(pady=40)
        
        for text, color, command in [("🔐 Login", self.colors['primary'], self.show_login),
                                      ("📝 Register", self.colors['success'], self.show_register)]:
            btn = tk.Button(btn_frame, text=text, font=('Segoe UI', 13, 'bold'),
                           bg=color, fg='white', padx=40, pady=12,
                           command=command, cursor='hand2', relief='flat')
            btn.pack(pady=10)
    
    def interpolate_color(self, color1, color2, factor):
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        result = tuple(int(c1[i] + (c2[i] - c1[i]) * factor) for i in range(3))
        return f'#{result[0]:02x}{result[1]:02x}{result[2]:02x}'
    
    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg=self.colors['primary'])
        main_frame.pack(fill='both', expand=True)
        
        card = tk.Frame(main_frame, bg=self.colors['white'], relief='flat')
        card.place(relx=0.5, rely=0.5, anchor='center', width=500, height=450)
        
        tk.Label(card, text="🔐 Welcome Back", font=('Segoe UI', 24, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(pady=30)
        
        form = tk.Frame(card, bg=self.colors['white'])
        form.pack(pady=20, padx=40, fill='both')
        
        for label, show in [("Email or Username", False), ("Password", True)]:
            tk.Label(form, text=label, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['white'], anchor='w').pack(fill='x')
            entry = tk.Entry(form, font=('Segoe UI', 12), relief='solid', bd=1)
            if show:
                entry.config(show="•")
            entry.pack(fill='x', pady=(5, 15))
            if label == "Email or Username":
                self.login_entry = entry
            else:
                self.login_password = entry
        
        self.login_message = tk.Label(form, text="", font=('Segoe UI', 10),
                                      bg=self.colors['white'], fg=self.colors['danger'])
        self.login_message.pack()
        
        tk.Button(form, text="Login", font=('Segoe UI', 12, 'bold'),
                 bg=self.colors['primary'], fg='white', padx=30, pady=10,
                 command=self.do_login).pack(pady=10)
        
        tk.Button(form, text="← Back", font=('Segoe UI', 10),
                 bg=self.colors['light'], fg=self.colors['dark'],
                 command=self.show_welcome).pack()
    
    def show_register(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg=self.colors['purple'])
        main_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(main_frame, bg=self.colors['purple'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['purple'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        card = tk.Frame(scrollable, bg=self.colors['white'], relief='flat')
        card.pack(pady=50, padx=50, ipadx=30, ipady=20)
        
        tk.Label(card, text="📝 Create Account", font=('Segoe UI', 24, 'bold'),
                bg=self.colors['white'], fg=self.colors['purple']).pack(pady=20)
        
        form = tk.Frame(card, bg=self.colors['white'])
        form.pack(pady=10, padx=40)
        
        fields = [("Full Name", "reg_name"), ("Email Address", "reg_email"),
                  ("Username", "reg_user"), ("Password", "reg_pass"), ("Confirm Password", "reg_confirm")]
        
        self.reg_entries = {}
        
        for label, key in fields:
            tk.Label(form, text=label, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['white'], anchor='w').pack(fill='x', pady=(10, 0))
            entry = tk.Entry(form, font=('Segoe UI', 12), relief='solid', bd=1, width=30)
            if 'Password' in label:
                entry.config(show="•")
            entry.pack(fill='x', pady=(5, 0))
            self.reg_entries[key] = entry
        
        self.reg_message = tk.Label(form, text="", font=('Segoe UI', 10),
                                    bg=self.colors['white'], fg=self.colors['danger'])
        self.reg_message.pack(pady=10)
        
        tk.Button(form, text="Register", font=('Segoe UI', 12, 'bold'),
                 bg=self.colors['success'], fg='white', padx=30, pady=10,
                 command=self.do_register).pack(pady=10)
        
        tk.Button(form, text="← Back", font=('Segoe UI', 10),
                 bg=self.colors['light'], fg=self.colors['dark'],
                 command=self.show_welcome).pack()
    
    def do_login(self):
        email_or_user = self.login_entry.get().strip()
        password = self.login_password.get()
        
        user = None
        if '@' in email_or_user:
            user = self.db.find_user_by_email(email_or_user)
        else:
            user = self.db.find_user_by_username(email_or_user)
        
        if user and user.get('password') == password:
            self.current_user = user
            self.daily_schedule = user.get('daily_schedule', [])
            
            # Initialize default schedule if empty
            if not self.daily_schedule:
                self.init_default_schedule()
            
            self.create_menu_bar()
            self.start_notifications()
            self.show_main_dashboard()
        else:
            self.login_message.config(text="❌ Invalid credentials!")
    
    def do_register(self):
        name = self.reg_entries['reg_name'].get().strip()
        email = self.reg_entries['reg_email'].get().strip()
        username = self.reg_entries['reg_user'].get().strip()
        password = self.reg_entries['reg_pass'].get()
        confirm = self.reg_entries['reg_confirm'].get()
        
        if not all([name, email, username, password]):
            self.reg_message.config(text="❌ All fields required!")
            return
        if not self.validate_email(email):
            self.reg_message.config(text="❌ Invalid email!")
            return
        if len(username) < 3:
            self.reg_message.config(text="❌ Username too short!")
            return
        if len(password) < 6:
            self.reg_message.config(text="❌ Password too short!")
            return
        if password != confirm:
            self.reg_message.config(text="❌ Passwords don't match!")
            return
        if self.db.find_user_by_email(email):
            self.reg_message.config(text="❌ Email exists!")
            return
        if self.db.find_user_by_username(username):
            self.reg_message.config(text="❌ Username taken!")
            return
        
        new_user = {
            'email': email, 'username': username, 'password': password,
            'name': name, 'enrolled_courses': [], 'completed_courses': [],
            'daily_schedule': [], 'streak': 0, 'last_study_date': None,
            'achievements': [], 'total_minutes': 0, 'created_at': datetime.now().isoformat()
        }
        
        self.db.add_user(new_user)
        self.current_user = new_user
        messagebox.showinfo("Success", f"✅ Welcome {name}!")
        self.show_schedule_setup()
    
    def init_default_schedule(self):
        """Initialize default schedule with proper sleep hours"""
        self.daily_schedule = [
            {'activity': '😴 Sleep', 'start': 23, 'end': 7},
            {'activity': '🏫 College/Work', 'start': 9, 'end': 17},
            {'activity': '🍽️ Lunch Break', 'start': 13, 'end': 14},
            {'activity': '🚌 Travel', 'start': 17, 'end': 18},
            {'activity': '🍲 Dinner', 'start': 19, 'end': 20}
        ]
        self.current_user['daily_schedule'] = self.daily_schedule
        self.db.update_user(self.current_user['email'], self.current_user)
    
    # ==================== NOTIFICATION SYSTEM ====================
    def start_notifications(self):
        self.notification_running = True
        
        def notification_worker():
            while self.notification_running and self.current_user:
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                
                # Check for study reminders (only after sleep hours, 7 AM to 11 PM)
                if current_minute == 0 and 7 <= current_hour <= 22:
                    for enrollment in self.current_user.get('enrolled_courses', []):
                        scheduled_hour = enrollment.get('scheduled_hour', 19)
                        if scheduled_hour == current_hour:
                            if enrollment['completed_lessons'] < enrollment['total_lessons']:
                                self.show_desktop_notification("📚 Study Time!", f"Time for {enrollment['course_name']}!")
                                break
                
                # Morning motivation after waking up (7:00 AM)
                if current_hour == 7 and current_minute == 0:
                    streak = self.current_user.get('streak', 0)
                    if streak > 0:
                        self.show_desktop_notification("🌅 Good Morning!", f"You're on a {streak}-day streak! Ready to learn?")
                
                time.sleep(60)
        
        self.notification_thread = threading.Thread(target=notification_worker, daemon=True)
        self.notification_thread.start()
    
    def show_desktop_notification(self, title, message):
        try:
            notification.notify(title=title, message=message, timeout=8)
        except:
            pass
    
    # ==================== MENU BAR ====================
    def create_menu_bar(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="🏠 Dashboard", command=self.show_main_dashboard)
        file_menu.add_command(label="📅 Dynamic Timetable", command=self.show_dynamic_timetable)
        file_menu.add_command(label="➕ Add Course", command=self.show_add_course_options)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Logout", command=self.logout)
        
        schedule_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📅 Schedule", menu=schedule_menu)
        schedule_menu.add_command(label="🕐 View Timetable", command=self.show_dynamic_timetable)
        schedule_menu.add_command(label="✏️ Edit Routine", command=self.show_schedule_setup)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="📖 Guide", command=self.show_guide)
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
    
    # ==================== ADD COURSE OPTIONS ====================
    def show_add_course_options(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Course")
        dialog.geometry("500x400")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="➕ Add New Course", font=('Segoe UI', 20, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(pady=20)
        
        quick_frame = tk.LabelFrame(dialog, text="📚 Quick Add from Library", 
                                   font=('Segoe UI', 12, 'bold'), bg=self.colors['white'],
                                   padx=15, pady=10)
        quick_frame.pack(fill='x', padx=30, pady=10)
        
        courses_list = ["🐍 Python Programming", "🌐 Web Development", "📊 Data Science",
                        "🤖 Artificial Intelligence", "☁️ Cloud Computing", "🔒 Cybersecurity"]
        
        self.quick_course_var = tk.StringVar()
        quick_dropdown = ttk.Combobox(quick_frame, textvariable=self.quick_course_var,
                                      values=courses_list, width=35, state='readonly')
        quick_dropdown.pack(pady=10)
        
        tk.Button(quick_frame, text="Add to My Courses", bg=self.colors['success'], fg='white',
                 font=('Segoe UI', 10, 'bold'), command=lambda: self.add_quick_course(dialog)).pack(pady=5)
        
        custom_frame = tk.LabelFrame(dialog, text="✏️ Create Custom Course", 
                                    font=('Segoe UI', 12, 'bold'), bg=self.colors['white'],
                                    padx=15, pady=10)
        custom_frame.pack(fill='x', padx=30, pady=10)
        
        tk.Button(custom_frame, text="Create Custom Course", bg=self.colors['info'], fg='white',
                 font=('Segoe UI', 10, 'bold'), command=lambda: [dialog.destroy(), self.show_custom_course_dialog()]).pack(pady=10)
    
    def add_quick_course(self, dialog):
        course_name = self.quick_course_var.get()
        if not course_name:
            messagebox.showerror("Error", "Select a course!")
            return
        
        course_map = {
            "🐍 Python Programming": {"hours": 15, "lessons": 30},
            "🌐 Web Development": {"hours": 20, "lessons": 40},
            "📊 Data Science": {"hours": 18, "lessons": 36},
            "🤖 Artificial Intelligence": {"hours": 25, "lessons": 50},
            "☁️ Cloud Computing": {"hours": 12, "lessons": 24},
            "🔒 Cybersecurity": {"hours": 16, "lessons": 32}
        }
        
        course_info = course_map.get(course_name, {"hours": 15, "lessons": 30})
        
        # Find best study time AFTER sleep (7 AM to 11 PM)
        scheduled_hour = self.find_best_study_time()
        
        new_id = 1000 + len(self.current_user.get('custom_courses', []))
        
        enrollment = {
            'course_id': new_id,
            'course_name': course_name,
            'completed_lessons': 0,
            'total_lessons': course_info['lessons'],
            'total_hours': course_info['hours'],
            'study_logs': [],
            'enrolled_date': datetime.now().isoformat(),
            'scheduled_hour': scheduled_hour
        }
        
        self.current_user['enrolled_courses'].append(enrollment)
        self.db.update_user(self.current_user['email'], self.current_user)
        
        messagebox.showinfo("Success", f"✅ Added {course_name} to your courses!\nScheduled at {scheduled_hour}:00 (after sleep)")
        dialog.destroy()
        self.show_dynamic_timetable()
    
    def show_custom_course_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Custom Course")
        dialog.geometry("500x550")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="✏️ Create Custom Course", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(pady=20)
        
        form = tk.Frame(dialog, bg=self.colors['white'])
        form.pack(padx=30, pady=20, fill='both', expand=True)
        
        fields = [
            ("Course Name:", "name", False),
            ("Total Hours:", "hours", False),
            ("Number of Lessons:", "lessons", False),
            ("Description:", "desc", True)
        ]
        
        entries = {}
        
        for label, key, is_text in fields:
            tk.Label(form, text=label, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['white'], anchor='w').pack(fill='x', pady=(10, 0))
            if is_text:
                entry = tk.Text(form, height=4, font=('Segoe UI', 10), relief='solid', bd=1)
                entry.pack(fill='x', pady=5)
            else:
                entry = tk.Entry(form, font=('Segoe UI', 11), relief='solid', bd=1)
                entry.pack(fill='x', pady=5)
            entries[key] = entry
        
        def save_custom():
            name = entries['name'].get().strip()
            try:
                hours = float(entries['hours'].get().strip())
                lessons = int(entries['lessons'].get().strip())
            except:
                messagebox.showerror("Error", "Invalid hours/lessons!")
                return
            
            desc = entries['desc'].get('1.0', tk.END).strip()
            
            if not name:
                messagebox.showerror("Error", "Course name required!")
                return
            
            scheduled_hour = self.find_best_study_time()
            new_id = 2000 + len(self.current_user.get('custom_courses', []))
            
            enrollment = {
                'course_id': new_id,
                'course_name': f"📘 {name}",
                'completed_lessons': 0,
                'total_lessons': lessons,
                'total_hours': hours,
                'study_logs': [],
                'enrolled_date': datetime.now().isoformat(),
                'description': desc,
                'is_custom': True,
                'scheduled_hour': scheduled_hour
            }
            
            self.current_user['enrolled_courses'].append(enrollment)
            self.db.update_user(self.current_user['email'], self.current_user)
            
            messagebox.showinfo("Success", f"✅ Custom course '{name}' added!\nScheduled at {scheduled_hour}:00")
            dialog.destroy()
            self.show_dynamic_timetable()
        
        tk.Button(form, text="Create & Add to My Courses", bg=self.colors['success'], fg='white',
                 font=('Segoe UI', 12, 'bold'), command=save_custom).pack(pady=20)
    
    def find_best_study_time(self):
        """Find the best study time after sleep hours (7 AM to 11 PM)"""
        free_slots = self.find_free_slots(self.daily_schedule)
        
        # Filter slots that are after sleep (after 7 AM)
        valid_slots = [slot for slot in free_slots if slot['start'] >= 7]
        
        if valid_slots:
            return int(valid_slots[0]['start'])
        return 19  # Default 7 PM
    
    # ==================== SCHEDULE SETUP ====================
    def show_schedule_setup(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_menu_bar()
        
        main_frame = tk.Frame(self.root, bg=self.colors['light'])
        main_frame.pack(fill='both', expand=True)
        
        header = tk.Frame(main_frame, bg=self.colors['primary'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="📅 Set Your Daily Schedule", font=('Segoe UI', 24, 'bold'),
                fg='white', bg=self.colors['primary']).pack(pady=30)
        
        content = tk.Frame(main_frame, bg=self.colors['light'])
        content.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Important info about sleep hours
        info = tk.Frame(content, bg=self.colors['info'], padx=15, pady=10)
        info.pack(fill='x', pady=10)
        tk.Label(info, text="💡 Courses will be scheduled ONLY after your sleep hours (after you wake up)", 
                font=('Segoe UI', 11), fg='white', bg=self.colors['info']).pack()
        
        self.schedule_entries = []
        schedule_frame = tk.LabelFrame(content, text="Daily Activities",
                                      font=('Segoe UI', 14, 'bold'), bg=self.colors['white'],
                                      padx=20, pady=15)
        schedule_frame.pack(fill='both', expand=True, pady=15)
        
        canvas = tk.Canvas(schedule_frame, bg=self.colors['white'], highlightthickness=0)
        scrollbar = tk.Scrollbar(schedule_frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.add_schedule_row(scrollable, "😴 Sleep", 23, 7)
        self.add_schedule_row(scrollable, "🏫 College/Work", 9, 17)
        self.add_schedule_row(scrollable, "🍽️ Lunch Break", 13, 14)
        self.add_schedule_row(scrollable, "🚌 Travel", 17, 18)
        self.add_schedule_row(scrollable, "🍲 Dinner", 19, 20)
        
        btn_frame = tk.Frame(schedule_frame, bg=self.colors['white'])
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="+ Add Activity", bg=self.colors['secondary'], fg='white',
                 command=lambda: self.add_schedule_row(scrollable)).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Continue →", bg=self.colors['primary'], fg='white',
                 font=('Segoe UI', 12, 'bold'), padx=30, command=self.save_schedule).pack(side='left', padx=20)
    
    def add_schedule_row(self, parent, activity="", start=9, end=17):
        row = tk.Frame(parent, bg=self.colors['white'])
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text="Activity:", bg=self.colors['white']).pack(side='left', padx=5)
        entry = tk.Entry(row, width=20)
        entry.insert(0, activity)
        entry.pack(side='left', padx=5)
        
        tk.Label(row, text="From:", bg=self.colors['white']).pack(side='left', padx=5)
        start_spin = tk.Spinbox(row, from_=0, to=23, width=5)
        start_spin.delete(0, tk.END)
        start_spin.insert(0, str(start))
        start_spin.pack(side='left', padx=5)
        
        tk.Label(row, text="To:", bg=self.colors['white']).pack(side='left', padx=5)
        end_spin = tk.Spinbox(row, from_=0, to=23, width=5)
        end_spin.delete(0, tk.END)
        end_spin.insert(0, str(end))
        end_spin.pack(side='left', padx=5)
        
        tk.Button(row, text="✖", bg=self.colors['danger'], fg='white',
                 command=lambda: row.destroy()).pack(side='right', padx=10)
        
        self.schedule_entries.append({'activity': entry, 'start': start_spin, 'end': end_spin})
    
    def save_schedule(self):
        self.daily_schedule = []
        
        for entry in self.schedule_entries:
            activity = entry['activity'].get().strip()
            if activity:
                start = int(entry['start'].get())
                end = int(entry['end'].get())
                if start < end:
                    self.daily_schedule.append({'activity': activity, 'start': start, 'end': end})
                elif start > end:
                    # Handle overnight activities (like Sleep 23-7)
                    self.daily_schedule.append({'activity': activity, 'start': start, 'end': 24})
                    self.daily_schedule.append({'activity': activity, 'start': 0, 'end': end})
                else:
                    messagebox.showwarning("Warning", f"Invalid time for '{activity}'!")
                    return
        
        if not self.daily_schedule:
            messagebox.showwarning("Warning", "Please add at least one activity!")
            return
        
        self.current_user['daily_schedule'] = self.daily_schedule
        self.db.update_user(self.current_user['email'], self.current_user)
        self.show_add_course_options()
    
    # ==================== DYNAMIC TIMETABLE ====================
    def find_free_slots(self, schedule):
        """Find free time slots, considering overnight sleep"""
        busy_slots = []
        for act in schedule:
            if act['end'] > act['start']:
                busy_slots.append((act['start'], act['end']))
            else:
                busy_slots.append((act['start'], 24))
                busy_slots.append((0, act['end']))
        
        busy_slots.sort()
        
        # Merge overlapping intervals
        merged = []
        for start, end in busy_slots:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        
        free_slots = []
        current = 0
        
        for start, end in merged:
            if current < start:
                duration = start - current
                if duration >= 0.5:
                    free_slots.append({'start': current, 'end': start, 'duration': duration})
            current = max(current, end)
        
        if current < 24:
            duration = 24 - current
            if duration >= 0.5:
                free_slots.append({'start': current, 'end': 24, 'duration': duration})
        
        return free_slots
    
    def show_dynamic_timetable(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_menu_bar()
        
        # Modern Header
        header = tk.Frame(self.root, bg=self.colors['primary'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="📅 Dynamic Study Timetable", font=('Segoe UI', 26, 'bold'),
                fg='white', bg=self.colors['primary']).pack(pady=25)
        
        # Progress Overview
        overview_frame = tk.Frame(self.root, bg=self.colors['light'], height=60)
        overview_frame.pack(fill='x')
        overview_frame.pack_propagate(False)
        
        enrolled = len(self.current_user.get('enrolled_courses', []))
        completed = len(self.current_user.get('completed_courses', []))
        total_progress = self.calculate_overall_progress()
        
        overview_inner = tk.Frame(overview_frame, bg=self.colors['white'], padx=20, pady=10)
        overview_inner.pack(fill='x', padx=30, pady=10)
        
        tk.Label(overview_inner, text=f"📚 Courses: {enrolled}", font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=20)
        tk.Label(overview_inner, text=f"✅ Completed: {completed}", font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white'], fg=self.colors['success']).pack(side='left', padx=20)
        tk.Label(overview_inner, text=f"📊 Overall Progress: {total_progress:.1f}%", 
                font=('Segoe UI', 11, 'bold'), bg=self.colors['white'], fg=self.colors['warning']).pack(side='left', padx=20)
        
        # Sleep info banner
        sleep_info = tk.Frame(self.root, bg=self.colors['sleep'], height=35)
        sleep_info.pack(fill='x')
        sleep_info.pack_propagate(False)
        tk.Label(sleep_info, text="😴 Courses are scheduled ONLY after you wake up (after 7:00 AM)", 
                font=('Segoe UI', 10, 'bold'), fg='white', bg=self.colors['sleep']).pack(pady=8)
        
        # Main Scrollable Timetable
        canvas = tk.Canvas(self.root, bg=self.colors['light'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['light'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        self.create_modern_timetable(scrollable)
        
        # Action Buttons
        btn_frame = tk.Frame(scrollable, bg=self.colors['light'])
        btn_frame.pack(pady=20)
        
        for text, color, command in [("📖 Log Study Session", self.colors['success'], self.log_study_session_dialog),
                                      ("➕ Add New Course", self.colors['info'], self.show_add_course_options),
                                      ("🏠 Dashboard", self.colors['primary'], self.show_main_dashboard)]:
            tk.Button(btn_frame, text=text, bg=color, fg='white', font=('Segoe UI', 11, 'bold'),
                     padx=20, pady=10, command=command).pack(side='left', padx=10)
    
    def calculate_overall_progress(self):
        enrolled = self.current_user.get('enrolled_courses', [])
        if not enrolled:
            return 0
        total = sum((c['completed_lessons'] / c['total_lessons']) * 100 for c in enrolled if c['total_lessons'] > 0)
        return total / len(enrolled) if enrolled else 0
    
    def create_modern_timetable(self, parent):
        enrolled_courses = self.current_user.get('enrolled_courses', [])
        days = ["Time", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        table_frame = tk.Frame(parent, bg=self.colors['white'], relief='solid', bd=1)
        table_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Headers
        for col, day in enumerate(days):
            header = tk.Label(table_frame, text=day, font=('Segoe UI', 12, 'bold'),
                             bg=self.colors['primary'], fg='white', padx=20, pady=12)
            header.grid(row=0, column=col, sticky='nsew')
            table_frame.grid_columnconfigure(col, weight=1)
        
        row = 1
        for hour in range(0, 24, 2):
            time_label = f"{hour}:00 - {hour+2}:00"
            time_cell = tk.Label(table_frame, text=time_label, font=('Segoe UI', 10, 'bold'),
                                 bg=self.colors['dark'], fg='white', padx=10, pady=15)
            time_cell.grid(row=row, column=0, sticky='nsew')
            
            # Check if busy during this time (considering overnight sleep)
            is_busy = False
            busy_activity = ""
            for activity in self.daily_schedule:
                if activity['end'] > activity['start']:
                    if activity['start'] <= hour < activity['end'] or activity['start'] <= hour+1 < activity['end']:
                        is_busy = True
                        busy_activity = activity['activity']
                        break
                else:
                    # Overnight activity (sleep)
                    if hour >= activity['start'] or hour+1 < activity['end']:
                        is_busy = True
                        busy_activity = activity['activity']
                        break
            
            for col in range(1, 8):
                if is_busy:
                    # Check if this is sleep time
                    if "Sleep" in busy_activity or "sleep" in busy_activity:
                        cell_text = f"😴\nSleep Time\nRest Well!"
                        bg_color = '#2E86AB'
                        fg_color = 'white'
                    else:
                        cell_text = f"🔴\n{busy_activity[:10]}"
                        bg_color = '#FFE0E0'
                        fg_color = '#D63031'
                elif enrolled_courses:
                    # Only schedule courses AFTER sleep hours (after 7 AM)
                    if hour >= 7:  # After waking up
                        course_idx = (hour + col) % len(enrolled_courses)
                        course = enrolled_courses[course_idx]
                        progress = (course['completed_lessons'] / course['total_lessons']) * 100 if course['total_lessons'] > 0 else 0
                        
                        if progress < 30:
                            status = "🔴"
                            status_text = "Beginner"
                            bg_color = '#FFE0E0'
                        elif progress < 70:
                            status = "🟡"
                            status_text = "In Progress"
                            bg_color = '#FFF3E0'
                        else:
                            status = "🟢"
                            status_text = "Advanced"
                            bg_color = '#E8F5E9'
                        
                        cell_text = f"{status}\n{course['course_name'][:10]}\n{status_text}\n{progress:.0f}%"
                        fg_color = self.colors['dark']
                    else:
                        # Early morning before waking up - rest time
                        cell_text = f"😴\nRest Time\nWaking up soon"
                        bg_color = '#2E86AB'
                        fg_color = 'white'
                else:
                    cell_text = "✨\nFree Time"
                    bg_color = '#F5F5F5'
                    fg_color = '#888'
                
                cell = tk.Label(table_frame, text=cell_text, font=('Segoe UI', 8),
                               bg=bg_color, fg=fg_color, padx=8, pady=12, relief='ridge', bd=0.5)
                cell.grid(row=row, column=col, sticky='nsew', padx=1, pady=1)
            
            row += 1
        
        # Legend
        legend_frame = tk.Frame(parent, bg=self.colors['white'], padx=20, pady=10)
        legend_frame.pack(fill='x', pady=10)
        
        tk.Label(legend_frame, text="📖 Legend:", font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white']).pack(anchor='w')
        
        legends = [("😴 Sleep/Rest Time", '#2E86AB'), ("🔴 Busy/Unavailable", '#FFE0E0'),
                   ("🟡 Course In Progress", '#FFF3E0'), ("🟢 Course Advanced", '#E8F5E9'),
                   ("✨ Free Time", '#F5F5F5')]
        
        for text, color in legends:
            leg_frame = tk.Frame(legend_frame, bg=self.colors['white'])
            leg_frame.pack(anchor='w', pady=2)
            tk.Label(leg_frame, text="    ", bg=color, width=5, relief='solid').pack(side='left')
            tk.Label(leg_frame, text=text, bg=self.colors['white']).pack(side='left', padx=5)
    
    def show_main_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_menu_bar()
        
        header = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="📊 Dashboard", font=('Segoe UI', 24, 'bold'),
                fg='white', bg=self.colors['primary']).pack(side='left', padx=30, pady=20)
        
        user_frame = tk.Frame(header, bg=self.colors['primary'])
        user_frame.pack(side='right', padx=30)
        
        tk.Label(user_frame, text=f"👤 {self.current_user.get('name', self.current_user.get('username', 'User'))}",
                font=('Segoe UI', 11), fg='white', bg=self.colors['primary']).pack(side='left', padx=10)
        tk.Label(user_frame, text=f"🔥 {self.current_user.get('streak', 0)} Day Streak",
                font=('Segoe UI', 11, 'bold'), fg=self.colors['warning'], bg=self.colors['primary']).pack(side='left', padx=10)
        
        tk.Button(user_frame, text="View Timetable", bg='white', fg=self.colors['primary'],
                 command=self.show_dynamic_timetable).pack(side='left', padx=10)
        tk.Button(user_frame, text="Logout", bg='white', fg=self.colors['danger'],
                 command=self.logout).pack(side='left', padx=10)
        
        # Stats
        stats_frame = tk.Frame(self.root, bg=self.colors['light'])
        stats_frame.pack(fill='x', padx=30, pady=15)
        
        enrolled = len(self.current_user.get('enrolled_courses', []))
        completed = len(self.current_user.get('completed_courses', []))
        total_mins = self.current_user.get('total_minutes', 0)
        
        stats = [
            ("📚 Enrolled", enrolled, self.colors['primary']),
            ("✅ Completed", completed, self.colors['success']),
            ("🔄 Ongoing", enrolled - completed, self.colors['warning']),
            ("⏱️ Hours", f"{total_mins//60}h", self.colors['info'])
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=self.colors['white'], relief='raised')
            card.grid(row=0, column=i, padx=10, pady=10, sticky='nsew')
            stats_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(card, text=label, font=('Segoe UI', 12), bg=self.colors['white']).pack(pady=(15, 5))
            tk.Label(card, text=str(value), font=('Segoe UI', 28, 'bold'),
                    fg=color, bg=self.colors['white']).pack(pady=(0, 15))
        
        self.create_courses_list()
    
    def create_courses_list(self):
        courses_frame = tk.LabelFrame(self.root, text="Your Courses", font=('Segoe UI', 14, 'bold'),
                                     bg=self.colors['white'], padx=15, pady=15)
        courses_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        canvas = tk.Canvas(courses_frame, bg=self.colors['white'], highlightthickness=0)
        scrollbar = tk.Scrollbar(courses_frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        for enrollment in self.current_user.get('enrolled_courses', []):
            progress = (enrollment['completed_lessons'] / enrollment['total_lessons']) * 100 if enrollment['total_lessons'] > 0 else 0
            
            card = tk.Frame(scrollable, bg=self.colors['white'], relief='groove', bd=1)
            card.pack(fill='x', pady=8, padx=10)
            
            header_frame = tk.Frame(card, bg=self.colors['white'])
            header_frame.pack(fill='x', padx=15, pady=10)
            
            tk.Label(header_frame, text=enrollment['course_name'], font=('Segoe UI', 12, 'bold'),
                    fg=self.colors['primary'], bg=self.colors['white']).pack(anchor='w')
            
            scheduled_time = enrollment.get('scheduled_hour', 19)
            tk.Label(header_frame, text=f"⏰ Scheduled: {scheduled_time}:00 (After Sleep)", 
                    font=('Segoe UI', 9), fg=self.colors['info'], bg=self.colors['white']).pack(anchor='w')
            
            tk.Label(card, text=f"Progress: {progress:.1f}%", font=('Segoe UI', 10),
                    bg=self.colors['white']).pack(anchor='w', padx=15)
            
            pb = ttk.Progressbar(card, length=400, mode='determinate', value=progress)
            pb.pack(padx=15, pady=5, fill='x')
            
            if progress < 100:
                tk.Button(card, text="📖 Log Study", bg=self.colors['primary'], fg='white',
                         command=lambda cid=enrollment['course_id']: self.log_study(cid)).pack(pady=10)
    
    def log_study_session_dialog(self):
        courses = self.current_user.get('enrolled_courses', [])
        if not courses:
            messagebox.showwarning("Warning", "No courses enrolled!\nUse 'Add New Course' to get started.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Log Study Session")
        dialog.geometry("400x350")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="📖 Log Study Session", font=('Segoe UI', 16, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(pady=20)
        
        tk.Label(dialog, text="Select Course:", font=('Segoe UI', 11),
                bg=self.colors['white']).pack()
        
        course_names = [f"{c['course_name']} ({c['completed_lessons']:.0f}/{c['total_lessons']} lessons)" for c in courses]
        course_var = tk.StringVar()
        course_dropdown = ttk.Combobox(dialog, textvariable=course_var, values=course_names,
                                       width=40, state='readonly')
        course_dropdown.pack(pady=10)
        
        tk.Label(dialog, text="Minutes Studied:", font=('Segoe UI', 11),
                bg=self.colors['white']).pack()
        
        minutes_var = tk.IntVar(value=45)
        tk.Spinbox(dialog, from_=15, to=180, textvariable=minutes_var,
                  width=10, font=('Segoe UI', 12)).pack(pady=10)
        
        def submit():
            if not course_var.get():
                messagebox.showerror("Error", "Select a course!")
                return
            selected_index = course_names.index(course_var.get())
            course = courses[selected_index]
            self.log_study_with_minutes(course['course_id'], minutes_var.get())
            dialog.destroy()
        
        tk.Button(dialog, text="Submit", bg=self.colors['success'], fg='white',
                 font=('Segoe UI', 12, 'bold'), command=submit).pack(pady=20)
    
    def log_study(self, course_id):
        self.log_study_with_minutes(course_id, 45)
    
    def log_study_with_minutes(self, course_id, minutes):
        for enrollment in self.current_user['enrolled_courses']:
            if enrollment['course_id'] == course_id:
                lessons_per_hour = enrollment['total_lessons'] / enrollment['total_hours']
                lessons_learned = (minutes / 60) * lessons_per_hour
                
                enrollment['completed_lessons'] = min(
                    enrollment['completed_lessons'] + lessons_learned,
                    enrollment['total_lessons']
                )
                
                self.current_user['total_minutes'] += minutes
                
                today = datetime.now().date().isoformat()
                if self.current_user.get('last_study_date'):
                    last_date = datetime.fromisoformat(self.current_user['last_study_date']).date()
                    today_date = datetime.now().date()
                    if (today_date - last_date).days == 1:
                        self.current_user['streak'] += 1
                    elif (today_date - last_date).days > 1:
                        self.current_user['streak'] = 1
                else:
                    self.current_user['streak'] = 1
                
                self.current_user['last_study_date'] = today
                
                if enrollment['completed_lessons'] >= enrollment['total_lessons']:
                    if course_id not in self.current_user.get('completed_courses', []):
                        self.current_user['completed_courses'].append(course_id)
                        self.show_desktop_notification("🎉 Course Completed!", f"You completed {enrollment['course_name']}!")
                
                self.db.update_user(self.current_user['email'], self.current_user)
                messagebox.showinfo("Success", f"✅ Logged {minutes} minutes!\nProgress: {enrollment['completed_lessons']:.0f}/{enrollment['total_lessons']} lessons")
                self.show_dynamic_timetable()
                break
    
    def show_guide(self):
        guide = """📖 AI Course Planner User Guide

🎯 Getting Started:
1. Login/Register
2. Set your daily schedule (SLEEP hours are CRITICAL - 23:00 to 7:00)
3. Courses are scheduled ONLY after you wake up

😴 Sleep Schedule:
• Default sleep: 23:00 - 7:00
• All courses are scheduled AFTER 7:00 AM
• You can customize sleep hours in schedule

📚 Adding Courses:
• Quick Add - Choose from library
• Custom Course - Create your own

📅 Dynamic Timetable:
• Shows sleep time (😴), busy time (🔴), study time (🟡/🟢)
• Courses only appear after 7:00 AM
• Mouse wheel scrolling support

📖 Logging Study:
• Track daily study minutes
• Auto-calculates progress
• Earn streaks for consistency

💡 Tips:
• Set accurate sleep hours for best scheduling
• Study during recommended free slots (after 7 AM)
• Log sessions immediately after studying"""
        messagebox.showinfo("User Guide", guide)
    
    def show_about(self):
        about = """🤖 AI Course Planner v7.0

✨ NEW FEATURE:
• Courses scheduled ONLY AFTER SLEEP HOURS
• Proper overnight sleep handling (23:00-7:00)
• No study scheduling during sleep time

🎯 Features:
• Dynamic Color-Coded Timetable
• Multiple Course Addition Options
• Real-Time Progress Tracking
• Desktop Notifications
• Streak System

Made with ❤️ for Smart Learning!"""
        messagebox.showinfo("About", about)
    
    def logout(self):
        self.notification_running = False
        self.current_user = None
        self.show_welcome()

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    try:
        from plyer import notification
    except ImportError:
        import os
        os.system("pip install plyer")
    
    root = tk.Tk()
    app = CoursePlannerApp(root)
    root.mainloop()