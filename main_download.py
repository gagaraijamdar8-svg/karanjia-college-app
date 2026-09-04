from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser
import os
import json
import shutil
import threading


COLLEGE_URL = "https://karanjiacollege.com/"
EXAMINATION_URL = "https://karanjiacollege.com/examination.aspx"
STUDENT_PORTAL_URL = "https://soft.karanjiacollege.com/profile.aspx"

MATERIALS_FILE = "materials.json"
PROFILE_FILE = "student_profile.json"
SESSION_FILE = "student_session.json"
MATERIALS_FOLDER = "study_materials"


PLUS2_SUBJECTS = {
    "Arts": [
        "English", "M.I.L", "Environmental Education",
        "Basic Computer Education", "Political Science",
        "History / Mathematics", "Economics", "Odia / Sanskrit", "Logic"
    ],
    "Science": [
        "English", "M.I.L", "Environmental Education",
        "Physics", "Chemistry", "Mathematics", "Biology",
        "Information Technology"
    ],
    "Commerce": [
        "English", "M.I.L", "Environmental Education", "Yoga",
        "Basic Computer Education", "Accountancy - Paper I",
        "Business Studies & Management - Paper I",
        "Business Mathematics & Statistics - Paper I",
        "Banking & Insurance - Paper I",
        "Fundamentals of Entrepreneurship - Paper I",
        "Salesmanship - Paper I", "Information Technology - Paper I"
    ]
}

PLUS3_SUBJECTS = [
    "Mathematical Physics-I",
    "Mechanics",
    "Atomic Structure, Periodicity of Elements & Chemical Bonding",
    "Parishuddha Bhasa O Likhana Kaushala",
    "Human Rights",
    "Environmental Science and Disaster Management"
]


class CollegeApp(App):

    def build(self):
        self.current_course = ""
        self.current_term = ""
        self.current_stream = ""
        self.selected_pdf = None

        self.create_material_folder()

        # Root must exist before showing the first screen.
        self.root = BoxLayout(orientation="vertical")

        if self.check_session():
            self.show_dashboard()
        else:
            self.show_login()

        return self.root

    # ---------------- FILE HELPERS ----------------

    def app_file(self, filename):
        return os.path.join(self.user_data_dir, filename)

    def materials_folder(self):
        folder = os.path.join(self.user_data_dir, MATERIALS_FOLDER)
        os.makedirs(folder, exist_ok=True)
        return folder

    def create_material_folder(self):
        os.makedirs(self.materials_folder(), exist_ok=True)

    # ---------------- SESSION ----------------

    def save_session(self):
        try:
            with open(self.app_file(SESSION_FILE), "w", encoding="utf-8") as f:
                json.dump({"logged_in": True}, f)
        except Exception:
            pass

    def check_session(self):
        try:
            path = self.app_file(SESSION_FILE)
            if not os.path.exists(path):
                return False

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data.get("logged_in", False)
        except Exception:
            return False

    def clear_session(self):
        try:
            path = self.app_file(SESSION_FILE)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # ---------------- PROFILE ----------------

    def save_profile(self, profile):
        try:
            with open(self.app_file(PROFILE_FILE), "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load_profile(self):
        try:
            path = self.app_file(PROFILE_FILE)
            if not os.path.exists(path):
                return {}

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ---------------- MATERIALS ----------------

    def load_materials(self):
        try:
            path = self.app_file(MATERIALS_FILE)
            if not os.path.exists(path):
                return {}

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_materials(self, data):
        try:
            with open(self.app_file(MATERIALS_FILE), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    # ---------------- COMMON UI ----------------

    def make_button(self, text, callback, height=50):
        button = Button(
            text=text,
            size_hint_y=None,
            height=height,
            font_size=16
        )
        button.bind(on_release=callback)
        return button

    def title_label(self, text, size=24):
        return Label(
            text=text,
            font_size=size,
            size_hint_y=None,
            height=60
        )

    def screen_layout(self):
        return BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

    # ---------------- LOGIN ----------------

    def show_login(self, *args):
        layout = self.screen_layout()

        layout.add_widget(
            self.title_label("Karanjia Autonomous College", 23)
        )

        layout.add_widget(
            Label(
                text="Student Login",
                font_size=22,
                size_hint_y=None,
                height=50
            )
        )

        layout.add_widget(
            Label(
                text="Official Student Portal se login karein.",
                font_size=15,
                size_hint_y=None,
                height=60
            )
        )

        layout.add_widget(
            self.make_button(
                "Open Student Portal",
                self.open_student_portal,
                55
            )
        )

        layout.add_widget(
            self.make_button(
                "Continue to App",
                self.login_continue,
                55
            )
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def open_student_portal(self, instance=None):
        webbrowser.open(STUDENT_PORTAL_URL)

    def login_continue(self, instance=None):
        self.save_session()
        self.show_dashboard()

    # ---------------- DASHBOARD ----------------

    def show_dashboard(self, *args):
        root = BoxLayout(orientation="vertical")
        scroll = ScrollView()

        layout = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10,
            size_hint_y=None
        )
        layout.bind(minimum_height=layout.setter("height"))

        layout.add_widget(
            self.title_label("Karanjia Autonomous College", 22)
        )

        layout.add_widget(
            Label(
                text="Student Dashboard",
                font_size=21,
                size_hint_y=None,
                height=50
            )
        )

        buttons = [
            ("Student Profile", self.student_profile),
            ("College Notices", self.show_notices),
            ("Attendance", self.attendance),
            ("Results", self.results),
            ("Study Materials", self.study_materials),
            ("Admin Panel", self.admin_panel),
            ("Timetable", self.timetable),
            ("Logout", self.logout)
        ]

        for text, callback in buttons:
            layout.add_widget(self.make_button(text, callback, 55))

        scroll.add_widget(layout)
        root.add_widget(scroll)

        self.root.clear_widgets()
        self.root.add_widget(root)

    # ---------------- PROFILE ----------------

    def student_profile(self, instance=None):
        profile = self.load_profile()
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Student Profile", 23))

        name = TextInput(
            hint_text="Student Name",
            text=profile.get("name", ""),
            multiline=False,
            size_hint_y=None,
            height=48
        )

        roll = TextInput(
            hint_text="Roll No",
            text=profile.get("roll", ""),
            multiline=False,
            size_hint_y=None,
            height=48
        )

        registration = TextInput(
            hint_text="Registration No",
            text=profile.get("registration", ""),
            multiline=False,
            size_hint_y=None,
            height=48
        )

        course = Spinner(
            text=profile.get("course", "Select Course"),
            values=["+2", "+3"],
            size_hint_y=None,
            height=48
        )

        stream = Spinner(
            text=profile.get("stream", "Select Stream"),
            values=["Arts", "Science", "Commerce"],
            size_hint_y=None,
            height=48
        )

        term = Spinner(
            text=profile.get("term", "Select Semester / Year"),
            values=[
                "1st Semester", "2nd Semester", "3rd Semester",
                "4th Semester", "5th Semester", "6th Semester",
                "1st Year", "2nd Year", "3rd Year"
            ],
            size_hint_y=None,
            height=48
        )

        layout.add_widget(name)
        layout.add_widget(roll)
        layout.add_widget(registration)
        layout.add_widget(course)
        layout.add_widget(stream)
        layout.add_widget(term)

        def save(instance):
            data = {
                "name": name.text.strip(),
                "roll": roll.text.strip(),
                "registration": registration.text.strip(),
                "course": course.text,
                "stream": stream.text,
                "term": term.text
            }

            if self.save_profile(data):
                self.popup_message("Success", "Student profile saved.")
            else:
                self.popup_message("Error", "Profile save nahi ho paya.")

        layout.add_widget(self.make_button("Save Profile", save, 55))
        layout.add_widget(self.make_button("Back", self.back_dashboard, 55))

        self.root.clear_widgets()
        self.root.add_widget(layout)

    # ---------------- NOTICES ----------------

    def show_notices(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("College Notices", 23))

        self.notice_status = Label(
            text="Loading notices...",
            font_size=16,
            size_hint_y=None,
            height=45
        )
        layout.add_widget(self.notice_status)

        scroll = ScrollView()

        self.notice_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=5,
            size_hint_y=None
        )
        self.notice_box.bind(
            minimum_height=self.notice_box.setter("height")
        )

        scroll.add_widget(self.notice_box)
        layout.add_widget(scroll)

        layout.add_widget(
            self.make_button(
                "Retry",
                lambda x: self.start_notice_loading(),
                50
            )
        )

        layout.add_widget(
            self.make_button(
                "Open College Website",
                self.open_college_website,
                50
            )
        )

        layout.add_widget(
            self.make_button(
                "Back",
                self.back_dashboard,
                50
            )
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

        self.start_notice_loading()

    def start_notice_loading(self):
        if not hasattr(self, "notice_status"):
            return

        self.notice_status.text = (
            "Connecting to official college website..."
        )
        self.notice_box.clear_widgets()

        threading.Thread(
            target=self.notice_worker,
            daemon=True
        ).start()

    def notice_worker(self):
        try:
            notices = self.get_live_notices()
            Clock.schedule_once(
                lambda dt: self.display_notices(notices)
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt, msg=str(e): self.notice_error(msg)
            )

    def get_live_notices(self):
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Linux; Android 10) "
                "AppleWebKit/537.36 "
                "Chrome/120.0 Mobile Safari/537.36"
        }

        response = requests.get(
            COLLEGE_URL,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        heading = None

        for tag in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        ):
            text = tag.get_text(" ", strip=True).lower()

            if "notice board" in text:
                heading = tag
                break

        if heading is None:
            raise Exception("Notice Board section nahi mila.")

        notices = []

        for element in heading.find_all_next():
            if element.name in [
                "h1", "h2", "h3", "h4", "h5", "h6"
            ]:
                section = element.get_text(
                    " ", strip=True
                ).lower()

                if element != heading and (
                    "upcoming events" in section
                    or section == "events"
                    or "event" in section
                ):
                    break

            if element.name != "a":
                continue

            title = element.get_text(" ", strip=True)
            href = element.get("href")

            if not title or not href or len(title) < 5:
                continue

            link = urljoin(COLLEGE_URL, href)
            item = (title, link)

            if item not in notices:
                notices.append(item)

            if len(notices) >= 30:
                break

        if not notices:
            raise Exception("Notice Board me koi notice nahi mila.")

        return notices

    def display_notices(self, notices):
        self.notice_status.text = "Live notices loaded."
        self.notice_box.clear_widgets()

        for index, (title, link) in enumerate(notices, start=1):
            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=110,
                spacing=5
            )

            label = Label(
                text=f"{index}. {title}",
                font_size=18,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=55
            )

            label.bind(
                size=lambda obj, value: setattr(
                    obj, "text_size", value
                )
            )

            card.add_widget(label)

            button = Button(
                text="Open Official Notice",
                size_hint_y=None,
                height=45
            )
            button.bind(
                on_release=lambda btn, url=link:
                webbrowser.open(url)
            )

            card.add_widget(button)
            self.notice_box.add_widget(card)

    def notice_error(self, error):
        self.notice_status.text = "Notice load nahi ho paya."
        self.notice_box.clear_widgets()

        self.notice_box.add_widget(
            Label(
                text=(
                    "Internet connection check karein.\n\n"
                    f"Error: {error}"
                ),
                font_size=14,
                size_hint_y=None,
                height=120
            )
        )

    # ---------------- ATTENDANCE ----------------

    def attendance(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("My Attendance", 23))

        layout.add_widget(
            Label(
                text="Attendance official student portal se check karein.",
                font_size=16,
                size_hint_y=None,
                height=80
            )
        )

        layout.add_widget(
            self.make_button(
                "Open Student Portal",
                self.open_student_portal,
                55
            )
        )

        layout.add_widget(
            self.make_button(
                "Open College Website",
                self.open_college_website,
                55
            )
        )

        layout.add_widget(
            self.make_button("Back", self.back_dashboard, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    # ---------------- RESULTS ----------------

    def results(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Results", 23))

        layout.add_widget(
            Label(
                text="Result official student portal se check karein.",
                font_size=16,
                size_hint_y=None,
                height=80
            )
        )

        layout.add_widget(
            self.make_button(
                "Open Student Portal",
                self.open_student_portal,
                55
            )
        )

        layout.add_widget(
            self.make_button(
                "Open Examination Page",
                self.open_examination,
                55
            )
        )

        layout.add_widget(
            self.make_button("Back", self.back_dashboard, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    # ---------------- TIMETABLE ----------------

    def timetable(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Timetable", 23))

        layout.add_widget(
            Label(
                text=(
                    "Official examination page se "
                    "timetable check karein."
                ),
                font_size=16,
                size_hint_y=None,
                height=80
            )
        )

        layout.add_widget(
            self.make_button(
                "Open Examination Page",
                self.open_examination,
                55
            )
        )

        layout.add_widget(
            self.make_button("Back", self.back_dashboard, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    # ---------------- STUDY MATERIALS ----------------

    def study_materials(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Study Materials", 23))

        layout.add_widget(
            Label(
                text="Select Course",
                font_size=17,
                size_hint_y=None,
                height=40
            )
        )

        layout.add_widget(
            self.make_button(
                "+2",
                lambda x: self.material_stream_selection(),
                55
            )
        )

        layout.add_widget(
            self.make_button(
                "+3",
                lambda x: self.material_term_selection(),
                55
            )
        )

        layout.add_widget(
            self.make_button("Back", self.back_dashboard, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def material_stream_selection(self, *args):
        layout = self.screen_layout()

        layout.add_widget(
            self.title_label("+2 - Select Stream", 22)
        )

        for stream in ["Arts", "Science", "Commerce"]:
            layout.add_widget(
                self.make_button(
                    stream,
                    lambda x, s=stream:
                    self.material_plus2_term(s),
                    55
                )
            )

        layout.add_widget(
            self.make_button("Back", self.study_materials, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def material_plus2_term(self, stream, *args):
        layout = self.screen_layout()

        layout.add_widget(
            self.title_label(f"+2 {stream}", 22)
        )

        for term in ["1st Year", "2nd Year"]:
            layout.add_widget(
                self.make_button(
                    term,
                    lambda x, t=term, s=stream:
                    self.material_subjects("+2", t, s),
                    55
                )
            )

        layout.add_widget(
            self.make_button(
                "Back",
                lambda x: self.material_stream_selection(),
                55
            )
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def material_term_selection(self, *args):
        layout = self.screen_layout()

        layout.add_widget(
            self.title_label("+3 - Select Semester", 22)
        )

        semesters = [
            "1st Semester", "2nd Semester", "3rd Semester",
            "4th Semester", "5th Semester", "6th Semester"
        ]

        for term in semesters:
            layout.add_widget(
                self.make_button(
                    term,
                    lambda x, t=term:
                    self.material_subjects("+3", t, ""),
                    55
                )
            )

        layout.add_widget(
            self.make_button("Back", self.study_materials, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def material_subjects(self, course, term, stream="", *args):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Subjects", 23))

        if course == "+2":
            subjects = PLUS2_SUBJECTS.get(stream, [])
        else:
            subjects = PLUS3_SUBJECTS

        scroll = ScrollView()

        box = BoxLayout(
            orientation="vertical",
            spacing=8,
            padding=5,
            size_hint_y=None
        )
        box.bind(minimum_height=box.setter("height"))

        for subject in subjects:
            box.add_widget(
                self.make_button(
                    subject,
                    lambda x,
                    c=course, t=term, s=stream, sub=subject:
                    self.open_notes(c, t, s, sub),
                    60
                )
            )

        scroll.add_widget(box)
        layout.add_widget(scroll)

        if course == "+2":
            back_function = lambda x: self.material_plus2_term(stream)
        else:
            back_function = self.material_term_selection

        layout.add_widget(
            self.make_button("Back", back_function, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def open_notes(self, course, term, stream, subject, *args):
        data = self.load_materials()

        materials = (
            data.get(course, {})
            .get(term, {})
            .get(subject, [])
        )

        layout = self.screen_layout()
        layout.add_widget(self.title_label(subject, 19))

        if not materials:
            layout.add_widget(
                Label(
                    text=(
                        "Is subject ke liye abhi "
                        "koi PDF available nahi hai."
                    ),
                    font_size=15
                )
            )
        else:
            scroll = ScrollView()

            box = BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=5,
                size_hint_y=None
            )
            box.bind(minimum_height=box.setter("height"))

            for material in materials:
                name = material.get("name", "PDF")
                path = material.get("path", "")

                button = Button(
                    text=name,
                    size_hint_y=None,
                    height=55,
                    font_size=15
                )
                button.bind(
                    on_release=lambda x, p=path:
                    self.open_pdf(p)
                )
                box.add_widget(button)

            scroll.add_widget(box)
            layout.add_widget(scroll)

        layout.add_widget(
            self.make_button(
                "Back",
                lambda x: self.material_subjects(
                    course, term, stream
                ),
                55
            )
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def open_pdf(self, path):
        if not path:
            return

        if not os.path.exists(path):
            self.popup_message("Error", "PDF file nahi mili.")
            return

        try:
            webbrowser.open("file://" + path)
        except Exception:
            self.popup_message("PDF Location", path)

    # ---------------- ADMIN PANEL ----------------

    def admin_panel(self, instance=None):
        layout = self.screen_layout()

        layout.add_widget(self.title_label("Admin Panel", 23))

        course = Spinner(
            text="+3",
            values=["+2", "+3"],
            size_hint_y=None,
            height=48
        )

        stream = Spinner(
            text="Arts",
            values=["Arts", "Science", "Commerce"],
            size_hint_y=None,
            height=48
        )

        term = Spinner(
            text="1st Semester",
            values=[
                "1st Semester", "2nd Semester", "3rd Semester",
                "4th Semester", "5th Semester", "6th Semester",
                "1st Year", "2nd Year", "3rd Year"
            ],
            size_hint_y=None,
            height=48
        )

        subject = Spinner(
            text="Select Subject",
            values=[],
            size_hint_y=None,
            height=48
        )

        selected_label = Label(
            text="No PDF selected.",
            font_size=14,
            size_hint_y=None,
            height=55
        )

        def update_subjects(*args):
            if course.text == "+2":
                subject.values = PLUS2_SUBJECTS.get(
                    stream.text, []
                )
            else:
                subject.values = PLUS3_SUBJECTS

            if subject.values:
                subject.text = subject.values[0]
            else:
                subject.text = "Select Subject"

        course.bind(text=update_subjects)
        stream.bind(text=update_subjects)
        update_subjects()

        for label_text, widget in [
            ("Course", course),
            ("Stream", stream),
            ("Semester / Year", term),
            ("Subject", subject)
        ]:
            layout.add_widget(
                Label(
                    text=label_text,
                    size_hint_y=None,
                    height=30
                )
            )
            layout.add_widget(widget)

        layout.add_widget(
            self.make_button(
                "Select PDF / Notes",
                lambda x:
                self.select_pdf_popup(selected_label),
                55
            )
        )

        layout.add_widget(selected_label)

        def add_material(instance):
            if not self.selected_pdf:
                self.popup_message(
                    "Error",
                    "Pehle PDF select karein."
                )
                return

            if subject.text == "Select Subject":
                self.popup_message(
                    "Error",
                    "Subject select karein."
                )
                return

            try:
                folder = self.materials_folder()
                filename = os.path.basename(self.selected_pdf)
                destination = os.path.join(folder, filename)

                # Avoid accidental overwrite by using a unique name.
                if os.path.exists(destination):
                    base, ext = os.path.splitext(filename)
                    counter = 2
                    while os.path.exists(destination):
                        filename = f"{base}_{counter}{ext}"
                        destination = os.path.join(folder, filename)
                        counter += 1

                shutil.copy2(self.selected_pdf, destination)

                data = self.load_materials()
                data.setdefault(course.text, {})
                data[course.text].setdefault(term.text, {})
                data[course.text][term.text].setdefault(
                    subject.text, []
                )

                data[course.text][term.text][subject.text].append({
                    "name": filename,
                    "path": destination
                })

                if self.save_materials(data):
                    self.popup_message(
                        "Success",
                        "Material successfully added."
                    )
                    self.selected_pdf = None
                    selected_label.text = "No PDF selected."
                else:
                    self.popup_message(
                        "Error",
                        "Material data save nahi ho paya."
                    )

            except Exception as e:
                self.popup_message("Error", str(e))

        layout.add_widget(
            self.make_button(
                "Add Material",
                add_material,
                55
            )
        )

        layout.add_widget(
            self.make_button("Back", self.back_dashboard, 55)
        )

        self.root.clear_widgets()
        self.root.add_widget(layout)

    def select_pdf_popup(self, selected_label):
        download_paths = [
            "/storage/emulated/0/Download",
            "/sdcard/Download",
            os.path.join(os.path.expanduser("~"), "Downloads")
        ]

        download_path = None

        for path in download_paths:
            if os.path.exists(path):
                download_path = path
                break

        if download_path is None:
            download_path = os.getcwd()

        content = BoxLayout(
            orientation="vertical",
            spacing=10
        )

        chooser = FileChooserListView(
            path=download_path,
            filters=["*.pdf", "*.PDF"],
            multiselect=False
        )
        content.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=5
        )

        select_button = Button(text="Select")
        cancel_button = Button(text="Cancel")

        buttons.add_widget(select_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)

        popup = Popup(
            title="Select PDF",
            content=content,
            size_hint=(0.95, 0.95)
        )

        def select_file(instance):
            if not chooser.selection:
                self.popup_message(
                    "Error",
                    "PDF select karein."
                )
                return

            path = chooser.selection[0]

            if not path.lower().endswith(".pdf"):
                self.popup_message(
                    "Error",
                    "Sirf PDF file select karein."
                )
                return

            self.selected_pdf = path
            selected_label.text = (
                "Selected:\n" + os.path.basename(path)
            )
            popup.dismiss()

        select_button.bind(on_release=select_file)
        cancel_button.bind(on_release=popup.dismiss)

        popup.open()

    # ---------------- NAVIGATION ----------------

    def logout(self, instance=None):
        self.clear_session()
        self.show_login()

    def back_dashboard(self, instance=None):
        self.show_dashboard()

    def open_college_website(self, instance=None):
        webbrowser.open(COLLEGE_URL)

    def open_examination(self, instance=None):
        webbrowser.open(EXAMINATION_URL)

    def popup_message(self, title, message):
        content = BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=10
        )

        content.add_widget(
            Label(
                text=str(message),
                font_size=15
            )
        )

        close_button = Button(
            text="OK",
            size_hint_y=None,
            height=50
        )
        content.add_widget(close_button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.4)
        )

        close_button.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    CollegeApp().run()
