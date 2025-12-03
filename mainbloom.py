# minebloom.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from abc import ABC, abstractmethod
import random
import datetime
import json
import os
import re

# =========================
# BUSINESS LOGIC (OOP, Abstraction, Encapsulation, Inheritance, Polymorphism)
# =========================

class User:
    """Encapsulation: menyimpan data user (private attributes)."""
    def __init__(self, username: str, partner: str):
        self._username = username
        self._partner = partner
        self._journal_password = None
        self._journal_entries = []
        # file for persisting this user's journals
        safe_name = ''.join(c for c in username if c.isalnum() or c in (' ','.','_')).rstrip()
        self._journal_file = os.path.join(os.getcwd(), f"journals_{safe_name}.json")
        # try load existing
        self._load_journals()

    # Encapsulated accessors
    @property
    def username(self):
        return self._username

    @property
    def partner(self):
        return self._partner

    def set_journal_password(self, pwd: str):
        self._journal_password = pwd

    def check_journal_password(self, pwd: str) -> bool:
        return self._journal_password == pwd

    def add_journal_entry(self, entry: str, date: datetime.datetime = None):
        # store entries as (date, content)
        if date is None:
            date = datetime.datetime.now()
        # normalize date to datetime at midnight if a date object provided
        if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
            date = datetime.datetime(date.year, date.month, date.day)
        self._journal_entries.append((date, entry))
        # persist after adding
        try:
            self._save_journals()
        except Exception:
            pass

    def get_journal_entries(self):
        return list(self._journal_entries)

    def _save_journals(self):
        # write journal entries as list of dicts with ISO timestamps
        data = []
        for dt, content in self._journal_entries:
            data.append({"date": dt.isoformat(), "content": content})
        try:
            with open(self._journal_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_journals(self):
        if not os.path.exists(self._journal_file):
            return
        try:
            with open(self._journal_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._journal_entries = []
            for item in data:
                try:
                    dt = datetime.datetime.fromisoformat(item.get('date'))
                except Exception:
                    dt = datetime.datetime.now()
                self._journal_entries.append((dt, item.get('content', '')))
        except Exception:
            self._journal_entries = []


# Abstraction: base class untuk affirmation provider
class AffirmationProvider(ABC):
    @abstractmethod
    def get_affirmation(self):
        pass

# Inheritance + Polymorphism
class DailyAffirmationProvider(AffirmationProvider):
    def __init__(self, affirmations):
        self._affirmations = affirmations

    def get_affirmation(self):
        # Polymorphism: implementasi spesifik memilih afirmasi berdasarkan hari
        index = datetime.date.today().toordinal() % len(self._affirmations)
        return self._affirmations[index]

class RandomAffirmationProvider(AffirmationProvider):
    def __init__(self, affirmations):
        self._affirmations = affirmations

    def get_affirmation(self):
        return random.choice(self._affirmations)


# Stack manager (undo recent mood entries)
class StackManager:
    def __init__(self):
        self._stack = []  # LIFO

    def push(self, item):
        self._stack.append(item)

    def pop(self):
        if self._stack:
            return self._stack.pop()
        return None

    def peek(self):
        return self._stack[-1] if self._stack else None

    def list_all(self):
        return list(self._stack)


# =========================
# UI (Tkinter)
# =========================

class MineBloomApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # window setup
        self.title("MineBloom — Your Personal Healing Companion")
        self.geometry("900x600")
        self.configure(bg="#FFF4F7")

        # state
        self.current_user = None
        self.stack = StackManager()

        # Affirmations (sample set)
        self.affirmations = [
            "Kamu cantik, di dalam dan di luar.",
            "Kamu hebat dalam caramu sendiri.",
            "Kamu kuat lebih dari yang kamu kira.",
            "Kamu baik dan penuh kasih sayang.",
            "Kamu layak dicintai dan diperlakukan baik.",
            "Kamu pantas menerima ketenangan.",
            "Kamu cukup apa adanya.",
            "Kamu berharga.",
            "Kamu tidak sendiri.",
            "Kamu boleh istirahat hari ini.",
            "Kamu berhak atas batasan yang sehat.",
            "Kamu boleh memilih diri sendiri.",
            "Kamu tidak harus sempurna untuk dicintai.",
            "Kamu berani karena kamu terus mencoba.",
            "Kamu punya kekuatan dalam kelembutan.",
            "Kamu boleh menetapkan batas.",
            "Kamu layak mendapatkan rasa aman.",
            "Kamu berhak merasa tenang.",
            "Kamu mampu mengatasi ini perlahan-lahan.",
            "Kamu pantas mendapat dukungan."
        ]

        # providers
        self.daily_provider = DailyAffirmationProvider(self.affirmations)
        self.random_provider = RandomAffirmationProvider(self.affirmations)

        # Build login screen
        self._build_login_screen()

    # helper: create styled buttons with thin border and attractive color
    def _make_button(self, parent, text, cmd, bg=None, width=None, height=None, padx=10, pady=6):
        pastel_blue = "#D6EEFF"
        deep_blue = "#1E3A8A"
        btn_bg = pastel_blue
        kwargs = {"bg": btn_bg, "command": cmd, "bd": 1, "relief": "solid", "highlightthickness": 1, "highlightbackground": "#9ED0FF", "activebackground": btn_bg, "padx": padx, "pady": pady, "fg": deep_blue, "font": ("Poppins", 12, "bold")}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        return tk.Button(parent, text=text, **kwargs)

    # helper: add placeholder behavior to Entry widgets
    def _add_placeholder(self, entry: tk.Entry, placeholder: str, active_fg="#E05F7D"):
        placeholder_color = "#BEBEBE"
        try:
            entry.insert(0, placeholder)
            entry.config(fg=placeholder_color)
        except Exception:
            pass

        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
                entry.config(fg=active_fg)

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=placeholder_color)

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def _sub_partner(self, text: str) -> str:
        try:
            partner = self.current_user.partner
        except Exception:
            partner = None
        if partner and partner.strip() and partner != "Nama pasangan (opsional)...":
            return text.replace('pasanganmu', f"'{partner}'").replace('pasangan', f"'{partner}'")
        return text

    # ---------- UI BUILDERS ----------
    def _build_login_screen(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(expand=True)

        title = tk.Label(frame, text="Welcome to MineBloom", font=("Poppins", 44, "bold"), bg="#FFF4F7", fg="#E05F7D")
        title.pack(pady=10)

        subtitle = tk.Label(frame, text="Hi Mine... Kamu aman di sini 🤍", font=("Quicksand", 14), bg="#FFF4F7", fg="#8B6C8E")
        subtitle.pack(pady=6)

        form = tk.Frame(frame, bg="#FFF4F7")
        form.pack(pady=20)

        tk.Label(form, text="Nama Kamu:", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        username_entry = tk.Entry(form, width=30, bg="#FFFFFF", fg="#E05F7D", insertbackground="#E05F7D", relief="solid", bd=1)
        username_entry.grid(row=0, column=1, pady=6)
        self._add_placeholder(username_entry, "Masukkan nama kamu...")

        tk.Label(form, text="Nama Pasangan (opsional):", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        partner_entry = tk.Entry(form, width=30, bg="#FFFFFF", fg="#E05F7D", insertbackground="#E05F7D", relief="solid", bd=1)
        partner_entry.grid(row=1, column=1, pady=6)
        self._add_placeholder(partner_entry, "Nama pasangan (opsional)...")

        def do_login():
            uname = username_entry.get().strip()
            partner = partner_entry.get().strip()
            if not uname or uname == "Masukkan nama kamu...":
                messagebox.showwarning("Input Dibutuhkan", "Masukkan nama kamu dulu ya sayang.")
                return
            self.current_user = User(uname, partner)
            if partner and partner != "Nama pasangan (opsional)...":
                self.current_user.set_journal_password(partner)
            else:
                self.current_user.set_journal_password("mine123")
            self._build_home_screen()

        login_btn = self._make_button(frame, text="Masuk", cmd=do_login, bg="#FF8FB3", padx=20, pady=8)
        login_btn.pack(pady=12)

    # Remaining UI methods are defined further down in the file (kept as before)

    # helper: create styled buttons with thin border and attractive color
    def _make_button(self, parent, text, cmd, bg=None, width=None, height=None, padx=10, pady=6):
        # unify button look: pastel blue background, deep-sky blue text, aesthetic font
        pastel_blue = "#D6EEFF"
        deep_blue = "#1E3A8A"
        # enforce pastel-blue buttons and deep-blue text for a unified look
        btn_bg = pastel_blue if bg is None else bg
        kwargs = {"bg": btn_bg, "command": cmd, "bd": 1, "relief": "solid", "highlightthickness": 1, "highlightbackground": "#9ED0FF", "activebackground": btn_bg, "padx": padx, "pady": pady, "fg": deep_blue, "font": ("Poppins", 12, "bold")}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        return tk.Button(parent, text=text, **kwargs)

    # helper: add placeholder behavior to Entry widgets
    def _add_placeholder(self, entry: tk.Entry, placeholder: str, active_fg="#E05F7D"):
        placeholder_color = "#BEBEBE"
        try:
            entry.insert(0, placeholder)
            entry.config(fg=placeholder_color)
        except Exception:
            pass

        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
                entry.config(fg=active_fg)

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=placeholder_color)

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def _sub_partner(self, text: str) -> str:
        # replace occurrences of the word 'pasangan' with the partner's name in quotes, if provided
        try:
            partner = self.current_user.partner
        except Exception:
            partner = None
        if partner and partner.strip() and partner != "Nama pasangan (opsional)...":
            return text.replace('pasanganmu', f"'{partner}'").replace('pasangan', f"'{partner}'")
        return text

    # ---------- UI BUILDERS ----------
    def _build_login_screen(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(expand=True)

        title = tk.Label(frame, text="Welcome to MineBloom", font=("Poppins", 44, "bold"),
                 bg="#FFF4F7", fg="#E05F7D")
        title.pack(pady=10)

        subtitle = tk.Label(frame, text="Hi Mine... Kamu aman di sini 🤍", font=("Quicksand", 14),
                    bg="#FFF4F7", fg="#8B6C8E")
        subtitle.pack(pady=6)

        form = tk.Frame(frame, bg="#FFF4F7")
        form.pack(pady=20)

        tk.Label(form, text="Nama Kamu:", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        username_entry = tk.Entry(form, width=30, bg="#FFFFFF", fg="#E05F7D", insertbackground="#E05F7D", relief="solid", bd=1)
        username_entry.grid(row=0, column=1, pady=6)
        self._add_placeholder(username_entry, "Masukkan nama kamu...")

        tk.Label(form, text="Nama Pasangan (opsional):", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        partner_entry = tk.Entry(form, width=30, bg="#FFFFFF", fg="#E05F7D", insertbackground="#E05F7D", relief="solid", bd=1)
        partner_entry.grid(row=1, column=1, pady=6)
        self._add_placeholder(partner_entry, "Nama pasangan (opsional)...")

        def do_login():
            uname = username_entry.get().strip()
            partner = partner_entry.get().strip()
            if not uname or uname == "Masukkan nama kamu...":
                messagebox.showwarning("Input Dibutuhkan", "Masukkan nama kamu dulu ya sayang.")
                return
            self.current_user = User(uname, partner)
            # set journal password to partner's name if provided, else keep a fallback
            if partner and partner != "Nama pasangan (opsional)...":
                self.current_user.set_journal_password(partner)
            else:
                self.current_user.set_journal_password("mine123")
            self._build_home_screen()

        login_btn = self._make_button(frame, text="Masuk", cmd=do_login, bg="#FF8FB3", padx=20, pady=8)
        login_btn.pack(pady=12)

    def _build_home_screen(self):
        self.clear_window()
        # Top greeting & automatic affirmation
        header = tk.Frame(self, bg="#FFF4F7")
        header.pack(fill="x", pady=8, padx=10)

        greeting = tk.Label(header, text=f"Hi {self.current_user.username}… Kamu aman di sini 🤍",
                            font=("Poppins", 18, "bold"), bg="#FFF4F7", fg="#E05F7D")
        greeting.pack(side="left")

        # ornament: small flower on the header (girly vibe)
        ornament = tk.Label(header, text="🌸", font=("Segoe UI Emoji", 20), bg="#FFF4F7")
        ornament.pack(side="right", padx=8)

        small_info = tk.Label(header, text=f"This Mine space is yours — {self.current_user.username}.",
                              font=("Quicksand", 10), bg="#FFF4F7", fg="#8B6C8E")
        small_info.pack(side="left", padx=14)

        # automatic affirmation on login (deep + slightly playful tone)
        def _friendly_affirmation():
            base = self.daily_provider.get_affirmation()
            # add a playful friendly suffix
            playful = [
                "Keep going — you've got this (and maybe a cookie).",
                "You're doing better than you think — tiny victory dance.",
                "Slow breaths. Tiny wins. Big hugs (figurative).",
                "Tiny progress is still progress — and very cool. 😌",
                "You matter — and yes, even on weird days."
            ]
            return f"{base} — {random.choice(playful)}"

        auto_aff = _friendly_affirmation()
        aff_label = tk.Label(self, text=auto_aff, wraplength=760, justify="center",
                             bg="#FFF4F7", fg="#6B3A50", font=("Quicksand", 12, "italic"))
        aff_label.pack(pady=6)

        # Main cards
        cards = tk.Frame(self, bg="#FFF4F7")
        cards.pack(pady=10)

        # left column menu (petal-like)
        menu_frame = tk.Frame(cards, bg="#FFF4F7")
        menu_frame.grid(row=0, column=0, padx=12)

        btn_specs = [
            ("My Mood Blossom", self._open_mood_tracker),
            ("My Relationship Scan", self._open_relationship_scan),
            ("My Red-Flag Checker", self._open_red_flag_detector),
            ("My Healing Journal", self._open_healing_journal),
            ("My Passed Journey", self._open_passed_journey)
        ]

        for i, (label, cmd) in enumerate(btn_specs):
            b = self._make_button(menu_frame, text=label, cmd=cmd, bg="#FFB6D0", width=25, height=2)
            b.grid(row=i, column=0, pady=6)

        # right side: quick stats / queue preview / daily affirmation
        right = tk.Frame(cards, bg="#FFF4F7")
        right.grid(row=0, column=1, padx=6, sticky="n")

        # Daily Reminder (religious reminders replacing the previous boundaries queue)
        reminder_text = (
            "1. You are never alone; Allah is always with you.\n"
            "﴿ فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ۝ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾\n"
            "Surah Al-Inshirah (94): 5–6\n\n"
            "2. You are strong. Allah never burdens a soul beyond what it can bear.\n"
            "﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾\n"
            "Surah Al-Baqarah (2): 286\n\n"
            "3. Trust Allah. What is written for you will always find its way.\n"
            "﴿ وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ ﴾\n"
            "Surah At-Talaq (65): 3\n\n"
            "4. Let your heart rest—peace comes from remembering Allah.\n"
            "﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾\n"
            "Surah Ar-Ra‘d (13): 28\n\n"
            "5. Every step you take to improve yourself, Allah guides you further.\n"
            "﴿ وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا ﴾\n"
            "Surah Al-‘Ankabut (29): 69"
        )
        reminder_card = tk.LabelFrame(right, text="Daily Reminder", bg="#FFF4F7", fg="#E05F7D", padx=10, pady=10)
        reminder_card.pack(pady=8)
        reminder_label = tk.Label(reminder_card, text=reminder_text, bg="#FFF4F7", fg="#6B3A50", justify="left", wraplength=360, font=("Quicksand", 11))
        reminder_label.pack()

        # daily affirmation card (from daily provider)
        daily_aff_text = self.daily_provider.get_affirmation()
        daily_card = tk.LabelFrame(right, text="Daily Affirmation", bg="#FFF4F7", fg="#E05F7D",
                       padx=10, pady=10)
        daily_card.pack(pady=8)
        self.daily_aff_label = tk.Label(daily_card, text=daily_aff_text, wraplength=300, bg="#FFF4F7", fg="#E05F7D", font=("Poppins", 14, "bold"))
        self.daily_aff_label.pack()

        # Random quick affirmation button
        rand_btn = self._make_button(right, text="Get Random Affirmation", cmd=self._show_random_affirmation, bg="#FFD6E8")
        rand_btn.pack(pady=6)

    # ---------- Feature screens ----------
    def _open_mood_tracker(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(frame, text="My Mood Blossom Tracker", font=("Poppins", 16, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)
        # mood scale (1-5)
        mood_frame = tk.Frame(frame, bg="#FFF4F7")
        mood_frame.pack(pady=8)
        tk.Label(mood_frame, text="Pilih mood hari ini:", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).grid(row=0, column=0, columnspan=6, sticky="w")
        mood_var = tk.IntVar(value=3)
        # emoji labels for mood (extended) arranged in two rows to avoid stacking
        emojis = ["😢","😕","😐","🙂","😄","😂","🥰","😇","✨","🫶🏻","💸"]
        cols = 6
        for idx, em in enumerate(emojis):
            r = (idx // cols) + 1
            c = idx % cols
            rb = tk.Radiobutton(mood_frame, text=em, variable=mood_var, value=idx+1, bg="#FFF4F7", font=("Segoe UI Emoji", 60))
            rb.grid(row=r, column=c, padx=8, pady=6)

        tk.Label(frame, text="Catatan singkat (opsional):", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 12, "bold")).pack(anchor="w", pady=(12,0))
        note_entry = tk.Entry(frame, width=70, bg="#FFF7D6", fg="#E05F7D", insertbackground="#E05F7D", relief="solid", bd=1)
        note_entry.pack(pady=6)
        self._add_placeholder(note_entry, "Tulis catatan singkat...")

        # Time recorder for mood entry (hour:minute)
        time_frame = tk.Frame(frame, bg="#FFF4F7")
        time_frame.pack(pady=(6,0), anchor='w')
        now = datetime.datetime.now()
        tk.Label(time_frame, text="Jam:", bg="#FFF4F7", fg="#E05F7D").pack(side='left')
        hour_sb = tk.Spinbox(time_frame, from_=0, to=23, width=3)
        hour_sb.delete(0, 'end')
        hour_sb.insert(0, f"{now.hour:02d}")
        hour_sb.pack(side='left', padx=(4,6))
        tk.Label(time_frame, text=":", bg="#FFF4F7", fg="#E05F7D").pack(side='left')
        min_sb = tk.Spinbox(time_frame, from_=0, to=59, width=3)
        min_sb.delete(0, 'end')
        min_sb.insert(0, f"{now.minute:02d}")
        min_sb.pack(side='left', padx=(2,4))

        # button actions
        def save_mood():
            mood = mood_var.get()
            note = note_entry.get().strip()
            # build datetime from time spinboxes (use today's date)
            try:
                h = int(hour_sb.get())
                mi = int(min_sb.get())
                now = datetime.datetime.now()
                entry_dt = datetime.datetime(now.year, now.month, now.day, h, mi)
            except Exception:
                entry_dt = datetime.datetime.now()
            entry = {"date": entry_dt, "mood": mood, "note": note}
            self.stack.push(entry)
            # If/else untuk pesan afirmasi berdasarkan mood
            if mood >= 4:
                msg = "Kamu sudah melakukan hari ini dengan sangat baik. Istirahatlah untuk hadapi hari esok yang ceria 💖"
            elif mood == 3:
                msg = "Kamu melakukan yang terbaik hari ini — beri dirimu istirahat ya."
            else:
                msg = "Terima kasih karena sudah bertahan hari ini. Istirahat dulu, besok coba lagi."
            # plus additional affirmation from daily provider
            extra = self.daily_provider.get_affirmation()
            messagebox.showinfo("Mood Tersimpan", f"{msg}\n\nAffirmation: {extra}")
            # also save mood as a journal entry into user's passed journey
            try:
                emoji = emojis[mood-1]
            except Exception:
                emoji = str(mood)
            mood_content = f"Mood: {emoji} ({mood})\n{note}"
            self.current_user.add_journal_entry(mood_content, date=entry_dt)
            note_entry.delete(0, 'end')
            self._build_home_screen()

        btn_save = self._make_button(frame, text="Simpan", cmd=save_mood)
        btn_save.pack(pady=8)

        back_btn = self._make_button(frame, text="Kembali ke Home", cmd=self._build_home_screen)
        back_btn.pack(pady=12)

    def _open_relationship_scan(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(frame, text="My Relationship Scan", font=("Poppins", 16, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)

        # generate 50 relationship questions and show them one-by-one
        base_questions = [
            "Apakah pasanganmu mendukung impianmu?",
            "Apakah pasangan menghargai perasaanmu?",
            "Apakah komunikasi berjalan terbuka?",
            "Apakah ada pengendalian berlebih dari pasangan?",
            "Apakah pasangan mau minta maaf saat salah?",
            "Apakah kalian bisa berbagi tanggung jawab?",
            "Apakah pasangan mendengarkan ketika kamu butuh bicara?",
            "Apakah kamu merasa dihargai?",
            "Apakah ada rasa aman bersama pasangan?",
            "Apakah pasangan mendukung waktu pribadimu?",
            "Apakah pasangan menghormati batasanmu?",
            "Apakah konflik bisa diselesaikan dengan sehat?",
            "Apakah pasangan menunjukkan empati?",
            "Apakah pasangan memberimu ruang untuk tumbuh?",
            "Apakah pasangan terbuka soal perasaannya?",
            "Apakah pasangan mengapresiasi usahamu?",
            "Apakah hubungan kalian memberi rasa tenang?",
            "Apakah keputusan penting dibicarakan bersama?",
            "Apakah pasangan memberi dukungan emosional?",
            "Apakah ada kejujuran dalam hubungan?",
            "Apakah pasangan menghargai keluargamu?",
            "Apakah ada toleransi terhadap perbedaan?",
            "Apakah pasangan menjaga komitmen?",
            "Apakah pasangan mendorong kemandirianmu?",
            "Apakah pasangan hadir saat kamu butuh?",
            "Apakah komunikasi non-verbal terasa nyaman?",
            "Apakah pasangan menerima kekuranganmu?",
            "Apakah pasangan menyemangati mimpimu?",
            "Apakah pasangan mendukung kesehatan mentalmu?",
            "Apakah ada saling berbagi kegembiraan?",
            "Apakah pasangan menghindari perilaku merendahkan?",
            "Apakah pasangan memberi ruang untuk hobi?",
            "Apakah ada rasa saling percaya?",
            "Apakah pasangan bertanggung jawab secara finansial bersama?",
            "Apakah pasangan menghormati privasimu?",
            "Apakah pasangan membantu saat kamu lelah?",
            "Apakah pasangan menunjukkan rasa terima kasih?",
            "Apakah pasangan menghindari manipulasi emosional?",
            "Apakah ada upaya memperbaiki saat salah?",
            "Apakah hubungan memberikan energi positif?",
            "Apakah pasangan memberi umpan balik yang membangun?",
            "Apakah pasangan menghormati pendapatmu?",
            "Apakah ada rasa aman dalam berbagi rahasia?",
            "Apakah pasangan menepati janji?",
            "Apakah kalian menikmati waktu berkualitas bersama?",
            "Apakah pasangan peka terhadap kebutuhanmu?",
            "Apakah ada kemauan berkembang bersama?",
            "Apakah pasangan mendukung keputusan kariermu?",
            "Apakah komunikasi tetap hangat meski sibuk?"
        ]
        # ensure at least 50 questions
        questions = []
        i = 0
        while len(questions) < 50:
            q = base_questions[i % len(base_questions)]
            questions.append(self._sub_partner(q))
            i += 1

        current_idx = 0
        set_count = 0
        set_answers = []

        q_frame = tk.Frame(frame, bg="#FFF4F7")
        q_frame.pack(fill="both", expand=True)

        q_label = tk.Label(q_frame, text=questions[current_idx], bg="#FFF7D6", fg="#E05F7D", wraplength=700, font=("Quicksand", 14, "bold"))
        q_label.pack(pady=20, padx=12)

        # answer buttons
        def submit_answer(ans):
            nonlocal current_idx, set_count, set_answers
            set_answers.append(1 if ans else 0)
            set_count += 1
            current_idx += 1
            # if we've answered 10 in this set, show score
            if set_count >= 10 or current_idx >= len(questions):
                score = sum(set_answers)
                # build a short summary of the 10-question set and save to journal
                try:
                    start_idx = current_idx - len(set_answers)
                    qs = questions[start_idx:current_idx]
                    summary_lines = []
                    for i, (qtext, ans_val) in enumerate(zip(qs, set_answers), start=1):
                        summary_lines.append(f"{i}. {qtext} — {('Ya' if ans_val==1 else 'Tidak')}")
                    content = f"Relationship Scan — Score {score}/{len(set_answers)}\n" + "\n".join(summary_lines)
                    self.current_user.add_journal_entry(content, date=datetime.datetime.now())
                except Exception:
                    # best-effort: still show score even if save fails
                    pass
                messagebox.showinfo("Skor Relationship", f"Skor Anda untuk 10 pertanyaan ini: {score} dari {len(set_answers)}\n\nHasil telah disimpan di My Passed Journey.")
                # offer to continue to next 10 or finish
                if current_idx < len(questions):
                    if messagebox.askyesno("Lanjut", "Lanjut ke 10 pertanyaan berikutnya?"):
                        # reset set counters and show next question
                        set_count = 0
                        set_answers = []
                        q_label.config(text=questions[current_idx])
                        return
                # otherwise finish and go back
                self._build_home_screen()
                return
            # otherwise, show next question
            q_label.config(text=questions[current_idx])

        btns = tk.Frame(q_frame, bg="#FFF4F7")
        btns.pack(pady=8)
        yes_btn = self._make_button(btns, text="✔️ Ya", cmd=lambda: submit_answer(True), bg="#FFB6D0", width=12)
        yes_btn.pack(side="left", padx=12)
        no_btn = self._make_button(btns, text="❌ Tidak", cmd=lambda: submit_answer(False), bg="#FFD6E8", width=12)
        no_btn.pack(side="left", padx=12)

        back_btn = self._make_button(frame, text="Kembali", cmd=self._build_home_screen)
        back_btn.pack(pady=12)

    def _open_red_flag_detector(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(frame, text="My Red-Flag Checker", font=("Poppins", 16, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)
        items = [
            self._sub_partner("Sering mengontrol apa yg kamu lakukan?"),
            self._sub_partner("Sering menyalahkanmu atas segala hal?"),
            self._sub_partner("Meminta isolasi dari teman/keluarga?"),
            self._sub_partner("Tidak pernah bertanggung jawab atas perilaku buruk?"),
            self._sub_partner("Ada ancaman atau intimidasi?")
        ]
        answers = []
        idx = tk.IntVar(value=0)

        q_frame = tk.Frame(frame, bg="#FFF4F7")
        q_frame.pack(pady=8)
        canvas_w, canvas_h = 760, 120
        q_canvas = tk.Canvas(q_frame, width=canvas_w, height=canvas_h, bg="#FFF4F7", highlightthickness=0)
        q_canvas.pack()

        def draw_question(text):
            q_canvas.delete("all")
            x1, y1, x2, y2 = 10, 10, canvas_w - 10, canvas_h - 10
            r = 20
            q_canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill="#FFF7D6", outline="#FFF7D6")
            q_canvas.create_text(canvas_w // 2, canvas_h // 2, text=text, width=canvas_w - 60, fill="#E05F7D", font=("Quicksand", 14, "bold"))

        draw_question(items[0])

        def ans_yes():
            answers.append(1)
            next_q()

        def ans_no():
            answers.append(0)
            next_q()

        def next_q():
            i = idx.get()
            i += 1
            if i < len(items):
                idx.set(i)
                draw_question(items[i])
            else:
                count = sum(answers)
                if count == 0:
                    level = "Hijau (Aman)"
                    suggestion = "Terus pertahankan batas sehat."
                elif count <= 2:
                    level = "Kuning (Waspada)"
                    suggestion = "Waspadai, bicarakan dengan orang terpercaya."
                else:
                    level = "Merah (Berisiko)"
                    suggestion = "Pertimbangkan dukungan profesional dan rencana keselamatan."
                messagebox.showinfo("Hasil Red-Flag", f"Jumlah tanda: {count}\nLevel: {level}\n\n{suggestion}")
                self._build_home_screen()

        btn_yes = self._make_button(frame, text="✔️ Ya", cmd=ans_yes, bg="#FFB6D0", width=10)
        btn_yes.pack(side="left", padx=20, pady=12)
        btn_no = self._make_button(frame, text="❌ Tidak", cmd=ans_no, bg="#FFD6E8", width=10)
        btn_no.pack(side="left", padx=20, pady=12)

        back_btn = self._make_button(frame, text="Kembali", cmd=self._build_home_screen, bg="#D6F0FF")
        back_btn.pack(pady=18)

    def _open_healing_journal(self):
        # ask for password (encapsulation)
        pwd = simpledialog.askstring("Journal Password", "Masukkan password jurnal (nama pasangan yang diinput saat login):", show="*")
        if pwd is None:
            return  # cancel
        partner_name = self.current_user.partner
        if not partner_name or partner_name.strip() == "" or partner_name == "Nama pasangan (opsional)...":
            messagebox.showerror("Error", "Tidak ada nama pasangan yang diinput saat login. Jurnal hanya dapat dibuka menggunakan nama pasangan sebagai password.")
            return
        if pwd != partner_name:
            messagebox.showerror("Error", "Password salah.")
            return
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(frame, text="My Healing Journal — Mine only", font=("Poppins", 16, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)
        # Date picker (day, month, year) before writing the journal
        date_frame = tk.Frame(frame, bg="#FFF4F7")
        date_frame.pack(pady=6)
        today = datetime.date.today()
        tk.Label(date_frame, text="Tanggal entri:", bg="#FFF4F7", fg="#E05F7D", font=("Quicksand", 11, "bold")).pack(side="left", padx=(0,6))
        day_sb = tk.Spinbox(date_frame, from_=1, to=31, width=4)
        day_sb.delete(0, 'end')
        day_sb.insert(0, today.day)
        day_sb.pack(side="left")
        month_sb = tk.Spinbox(date_frame, from_=1, to=12, width=4)
        month_sb.delete(0, 'end')
        month_sb.insert(0, today.month)
        month_sb.pack(side="left", padx=6)
        year_sb = tk.Spinbox(date_frame, from_=2000, to=2100, width=6)
        year_sb.delete(0, 'end')
        year_sb.insert(0, today.year)
        year_sb.pack(side="left")

        # Time picker for journal entry
        time_frame_j = tk.Frame(date_frame, bg="#FFF4F7")
        time_frame_j.pack(side="left", padx=8)
        now_dt = datetime.datetime.now()
        tk.Label(time_frame_j, text="Jam entri:", bg="#FFF4F7", fg="#E05F7D").pack(side="left")
        hour_sb_j = tk.Spinbox(time_frame_j, from_=0, to=23, width=3)
        hour_sb_j.delete(0, 'end')
        hour_sb_j.insert(0, f"{now_dt.hour:02d}")
        hour_sb_j.pack(side="left", padx=(4,2))
        tk.Label(time_frame_j, text=":", bg="#FFF4F7", fg="#E05F7D").pack(side="left")
        min_sb_j = tk.Spinbox(time_frame_j, from_=0, to=59, width=3)
        min_sb_j.delete(0, 'end')
        min_sb_j.insert(0, f"{now_dt.minute:02d}")
        min_sb_j.pack(side="left", padx=(2,4))

        # Journal text area: larger font and pink text color
        text = tk.Text(frame, width=90, height=18, bg="#FFF4F7", fg="#E05F7D", insertbackground="#E05F7D", font=("Quicksand", 14))
        text.pack(pady=8)
        def save_entry():
            # build date from spinboxes
            try:
                d = int(day_sb.get())
                m = int(month_sb.get())
                y = int(year_sb.get())
                h = int(hour_sb_j.get())
                mi = int(min_sb_j.get())
                entry_date = datetime.datetime(y, m, d, h, mi)
            except Exception:
                entry_date = datetime.datetime.now()
            content = text.get("1.0", "end").strip()
            if content:
                self.current_user.add_journal_entry(content, date=entry_date)
                messagebox.showinfo("Tersimpan", "Entri jurnal tersimpan.")
                text.delete("1.0", "end")
            else:
                messagebox.showwarning("Kosong", "Isi dulu jurnalnya ya.")
        save_btn = self._make_button(frame, text="Simpan Entri", cmd=save_entry, bg="#FFB6D0")
        save_btn.pack(pady=6)
        back_btn = self._make_button(frame, text="Kembali", cmd=self._build_home_screen, bg="#D6F0FF")
        back_btn.pack(pady=8)

    def _open_affirmation_generator(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#FFF4F7")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(frame, text="My Affirmations", font=("Poppins", 16, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)

        result_label = tk.Label(frame, text=self.random_provider.get_affirmation(), wraplength=700, bg="#FFF4F7", font=("Quicksand", 12))
        result_label.pack(pady=12)

        def gen_rand():
            result_label.config(text=self.random_provider.get_affirmation())
        gen_btn = self._make_button(frame, text="Generate Affirmation", cmd=gen_rand)
        gen_btn.pack(pady=6)

        # save affirmation to user's "gallery" (we'll just push to stack as saved affs)
        def save_aff():
            aff = result_label.cget("text")
            # demonstrate encapsulation / stack usage: save to stack
            self.stack.push({"saved_aff": aff, "date": datetime.datetime.now()})
            messagebox.showinfo("Saved", "Afirmasi tersimpan ke gallery (undoable).")
        save_btn = self._make_button(frame, text="Save Affirmation", cmd=save_aff)
        save_btn.pack(pady=6)

        back_btn = self._make_button(frame, text="Kembali", cmd=self._build_home_screen)
        back_btn.pack(pady=10)

    def _open_passed_journey(self):
        # show saved journal entries grouped by date in a table-like, scrollable view
        self.clear_window()
        root = tk.Frame(self, bg="#FFF4F7")
        root.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(root, text="My Passed Journey", font=("Poppins", 20, "bold"), bg="#FFF4F7", fg="#E05F7D").pack(pady=6)

        # controls
        ctrl = tk.Frame(root, bg="#FFF4F7")
        ctrl.pack(fill="x", pady=6)
        sort_var = tk.StringVar(value="newest")
        newest_btn = self._make_button(ctrl, text="Newest first", cmd=lambda: (sort_var.set("newest"), draw_entries()), bg=None)
        newest_btn.pack(side="left", padx=6)
        oldest_btn = self._make_button(ctrl, text="Oldest first", cmd=lambda: (sort_var.set("oldest"), draw_entries()), bg=None)
        oldest_btn.pack(side="left", padx=6)

        # scrollable canvas
        canvas_frame = tk.Frame(root, bg="#FFF4F7")
        canvas_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg="#FFF4F7", highlightthickness=0)
        vsb = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg="#FFF4F7")
        canvas.create_window((0,0), window=inner, anchor='nw')

        def on_config(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))

        inner.bind('<Configure>', on_config)

        # group entries by date
        def group_by_date():
            entries = list(self.current_user.get_journal_entries())
            # sort ascending first
            entries.sort(key=lambda it: it[0])
            groups = {}
            for dt, content in entries:
                key = dt.date().isoformat()
                groups.setdefault(key, []).append((dt, content))
            # order groups by date according to sort_var
            ordered = sorted(groups.items(), key=lambda kv: kv[0], reverse=(sort_var.get()=="newest"))
            return ordered

        # draw entries as table-like rows: left column date, right column entries in pastel boxes
        def draw_entries():
            for w in inner.winfo_children():
                w.destroy()
            ordered = group_by_date()
            row = 0
            girly_font = ("Segoe Script", 14, "italic")
            pink = "#E05F7D"
            for date_str, items in ordered:
                # date label cell
                date_lbl = tk.Label(inner, text=f"🌸 {date_str}", font=("Poppins", 14, "bold"), bg="#FFF4F7", fg=pink)
                date_lbl.grid(row=row, column=0, sticky="nw", padx=8, pady=(12,4))

                # entries column: container frame
                cell = tk.Frame(inner, bg="#FFF4F7")
                cell.grid(row=row, column=1, sticky="nw", padx=6, pady=(8,4))
                # each day gets its own pastel box
                day_frame = tk.Frame(cell, bg="#FFF7D6", bd=0, relief='flat')
                day_frame.pack(fill="x", expand=True, pady=4)
                for dt, content in items:
                    # small card per entry
                    card = tk.Frame(day_frame, bg="#FFFDEB", bd=1, relief='solid')
                    card.pack(fill="x", padx=8, pady=6)
                    time_lbl = tk.Label(card, text=dt.strftime('%H:%M'), font=("Quicksand", 10), bg="#FFFDEB", fg="#8B6C8E")
                    time_lbl.pack(anchor='ne', padx=6, pady=2)
                    # remove emoji ordinal like ' (3)' after emoji when showing in passed journey
                    display_content = content
                    if display_content.startswith("Mood:"):
                        lines = display_content.split('\n')
                        # remove any trailing ' (number)' after emoji in first line
                        lines[0] = re.sub(r"\s*\(\d+\)", "", lines[0])
                        display_content = "\n".join(lines)
                    # content: two-line layout (date separate already); girly font & pink
                    content_lbl = tk.Label(card, text=display_content, font=girly_font, bg="#FFFDEB", fg=pink, justify='left', wraplength=600)
                    content_lbl.pack(anchor='w', padx=8, pady=6)
                row += 1

        draw_entries()

        back_btn = self._make_button(root, text="Kembali", cmd=self._build_home_screen, bg=None)
        back_btn.pack(pady=8)

    # ---------- Utilities ----------
    def _show_random_affirmation(self):
        txt = self.random_provider.get_affirmation()
        messagebox.showinfo("Affirmation", txt)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app = MineBloomApp()
    app.mainloop()
