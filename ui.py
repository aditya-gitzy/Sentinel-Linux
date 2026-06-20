import json
import os
import subprocess
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Monkey patch CustomTkinter scrollable frame mouse scroll bug in Python 3.13/3.14
try:
    from customtkinter.windows.widgets.ctk_scrollable_frame import CTkScrollableFrame
    original_check = CTkScrollableFrame.check_if_master_is_canvas
    
    def patched_check(self, widget):
        if isinstance(widget, str):
            try:
                widget = self.nametowidget(widget)
            except Exception:
                return False
        return original_check(self, widget)
        
    CTkScrollableFrame.check_if_master_is_canvas = patched_check
except Exception:
    pass

# Resolve correct application directory for configurations, logs, and executable packaging
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(__file__)

CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# Premium Dynamic Color Palette (Supports Light & Dark Modes)
# Light Mode: Soft gray/white
# Dark Mode: Neutral dark charcoal & slate gray (Gemini Chat theme)
COLOR_BG = ("#F9F9F9", "#131314")           # Light Gray / Gemini Dark Background
COLOR_CARD = ("#FFFFFF", "#1E1E1F")         # Pure White / Gemini Card Background
COLOR_CARD_BORDER = ("#E3E3E3", "#2D2F31")  # Slate 200 / Slate 800
COLOR_SIDEBAR = ("#F0F4F9", "#1E1E1F")      # Slate 200 / Dark Sidebar
COLOR_TEXT_PRIMARY = ("#1F1F1F", "#E3E3E3") # Slate 900 / Slate 50
COLOR_TEXT_MUTED = ("#5F6368", "#C4C7C5")   # Slate 500 / Slate 400

# Nav active selection pills
COLOR_NAV_ACTIVE = ("#D3E3FD", "#2D2F31")
COLOR_NAV_ACTIVE_TEXT = ("#041E49", "#E3E3E3")

# Saturated rich accent colors for button backgrounds (gives high contrast white text)
COLOR_ACCENT = ("#0B57D0", "#1A73E8")       # Rich Google Blue
COLOR_ACCENT_HOVER = ("#0842A0", "#1557B0") # Darker Blue

# Soft accents for text labels only (for high contrast on dark backgrounds)
COLOR_TEXT_ACCENT = ("#0B57D0", "#A8C7FA")  # Soft Gemini Blue

COLOR_SUCCESS = ("#137333", "#1E8E3E")      # Rich Green
COLOR_SUCCESS_HOVER = ("#0F5B26", "#187232")

COLOR_DANGER = ("#C5221F", "#D93025")       # Rich Red
COLOR_DANGER_HOVER = ("#961C1A", "#B3261E")

COLOR_CONSOLE_BG = ("#1F1F1F", "#0E0E10")   # Deep Slate / Rich Obsidian
COLOR_CONSOLE_TEXT = ("#0B57D0", "#38BDF8") # Cyan / Mint Green

class SentinelUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Properties ---
        self.title("🛡️ Sentinel - Rules & Daemon Dashboard")
        self.geometry("1100x820")
        self.minsize(1000, 700)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- State Variables ---
        self.config_data = self.load_config()
        self.current_rule = None
        self.sentinel_process = None
        self.log_file_pos = 0

        # --- Themes ---
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLOR_BG)

        # --- Fonts ---
        self.font_title = ctk.CTkFont(family="Inter", size=20, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Inter", size=14, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=13, weight="normal")
        self.font_body_bold = ctk.CTkFont(family="Inter", size=13, weight="bold")
        self.font_checklist = ctk.CTkFont(family="Inter", size=14, weight="normal")
        self.font_console = ctk.CTkFont(family="Consolas", size=11, weight="normal")

        # --- Grid Layout Configuration ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # =====================================================================
        # 📂 SIDEBAR FRAME
        # =====================================================================
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLOR_SIDEBAR, border_color=COLOR_CARD_BORDER, border_width=1)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        # Logo and Title Area
        self.logo_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.logo_container.grid(row=0, column=0, padx=25, pady=(25, 15), sticky="w")
        
        self.logo_label = ctk.CTkLabel(self.logo_container, text="🛡️ SENTINEL", font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=COLOR_TEXT_ACCENT)
        self.logo_label.pack(anchor="w")
        
        self.version_label = ctk.CTkLabel(self.logo_container, text="Real-Time File Router v1.2", font=ctk.CTkFont(family="Inter", size=11, weight="normal"), text_color=COLOR_TEXT_MUTED)
        self.version_label.pack(anchor="w", pady=(2, 0))

        # Action Buttons Area
        self.sidebar_actions = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_actions.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        self.add_rule_btn = ctk.CTkButton(
            self.sidebar_actions, 
            text="➕ Add New Rule", 
            font=self.font_body_bold,
            fg_color=COLOR_ACCENT, 
            hover_color=COLOR_ACCENT_HOVER,
            height=38,
            corner_radius=8,
            command=self.add_new_rule
        )
        self.add_rule_btn.pack(fill="x", pady=5)

        # Scrollable Rule Registry List
        self.rule_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.rule_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Bottom Utilities Frame (Theme & Controls)
        self.sidebar_bottom = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_bottom.grid(row=3, column=0, padx=15, pady=25, sticky="ew")
        
        self.appearance_label = ctk.CTkLabel(self.sidebar_bottom, text="🌓 Theme Mode:", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.appearance_label.pack(anchor="w", pady=(0, 5))
        
        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar_bottom, 
            values=["Dark", "Light", "System"], 
            font=self.font_body,
            fg_color=COLOR_CARD,
            button_color=COLOR_CARD,
            button_hover_color=COLOR_CARD_BORDER,
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.change_appearance_mode_event
        )
        self.appearance_menu.pack(fill="x")

        # =====================================================================
        # 🖥️ MAIN WORKSPACE CONTAINER
        # =====================================================================
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------------------
        # 👑 TOP BAR / HEADER
        # ---------------------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self.main_container, height=65, fg_color=COLOR_CARD, corner_radius=0, border_color=COLOR_CARD_BORDER, border_width=1)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Header Title
        self.header_title = ctk.CTkLabel(self.header_frame, text="System Dashboard", font=self.font_title, text_color=COLOR_TEXT_PRIMARY)
        self.header_title.grid(row=0, column=0, padx=25, pady=22, sticky="w")

        # Daemon Controller (Start/Stop controls in header)
        self.daemon_status_card = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.daemon_status_card.grid(row=0, column=2, padx=25, pady=18, sticky="e")

        self.header_status_dot = ctk.CTkLabel(self.daemon_status_card, text="●", font=ctk.CTkFont(size=20), text_color=COLOR_TEXT_MUTED)
        self.header_status_dot.pack(side="left", padx=(0, 8))

        self.header_status_txt = ctk.CTkLabel(self.daemon_status_card, text="Daemon: Inactive", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.header_status_txt.pack(side="left", padx=(0, 15))

        self.daemon_toggle_btn = ctk.CTkButton(
            self.daemon_status_card, 
            text="▶️ Start Daemon", 
            font=self.font_body_bold,
            fg_color=COLOR_ACCENT, 
            hover_color=COLOR_ACCENT_HOVER,
            width=140,
            height=34,
            corner_radius=8,
            command=self.toggle_sentinel
        )
        self.daemon_toggle_btn.pack(side="left")

        # ---------------------------------------------------------------------
        # 📂 WORK AREA (Dashboard Card / Editor Card)
        # ---------------------------------------------------------------------
        self.work_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.work_area.grid(row=1, column=0, sticky="nsew", padx=25, pady=20)
        self.work_area.grid_rowconfigure(0, weight=1)
        self.work_area.grid_columnconfigure(0, weight=1)

        # --- A. Welcome Dashboard Frame ---
        self.dashboard_frame = ctk.CTkFrame(self.work_area, fg_color="transparent")
        
        # Dashboard Hero Section (Frameless, clean layout to maximize vertical space)
        self.hero_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.hero_frame.pack(fill="x", pady=(0, 15))
        
        self.hero_title = ctk.CTkLabel(self.hero_frame, text="Welcome to Sentinel", font=self.font_title, text_color=COLOR_TEXT_PRIMARY)
        self.hero_title.pack(anchor="w", padx=10, pady=(10, 2))
        self.hero_desc = ctk.CTkLabel(
            self.hero_frame, 
            text="Real-time background file sorting and folder clean-up automation daemon.",
            font=self.font_body, 
            text_color=COLOR_TEXT_MUTED,
            justify="left"
        )
        self.hero_desc.pack(anchor="w", padx=10, pady=(2, 5))

        # Statistics / Status Cards Row
        self.stats_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 15))
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Stat Card 1: Total Rules
        self.stats_rules = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.stats_rules.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(self.stats_rules, text="Active Rules", font=self.font_body, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 2))
        self.stats_rules_val = ctk.CTkLabel(self.stats_rules, text="0", font=ctk.CTkFont(family="Inter", size=28, weight="bold"), text_color=COLOR_TEXT_ACCENT)
        self.stats_rules_val.pack(anchor="w", padx=20, pady=(0, 10))

        # Stat Card 2: Monitored Directory
        self.stats_watch = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.stats_watch.grid(row=0, column=1, padx=10, sticky="ew")
        ctk.CTkLabel(self.stats_watch, text="Watch Directory", font=self.font_body, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 2))
        self.stats_watch_val = ctk.CTkLabel(self.stats_watch, text="Not Configured", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        self.stats_watch_val.pack(anchor="w", padx=20, pady=(4, 10))

        # Stat Card 3: Daemon PID / Status
        self.stats_status = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.stats_status.grid(row=0, column=2, padx=(10, 0), sticky="ew")
        ctk.CTkLabel(self.stats_status, text="System Daemon", font=self.font_body, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 2))
        self.stats_status_val = ctk.CTkLabel(self.stats_status, text="Inactive", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=COLOR_TEXT_MUTED)
        self.stats_status_val.pack(anchor="w", padx=20, pady=(4, 10))

        # Quick Start Guide Panel (Responsive list that expands to fill vertical space beautifully)
        self.guide_card = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.guide_card.pack(fill="both", expand=True)
        
        self.guide_title = ctk.CTkLabel(self.guide_card, text="⚙️ Getting Started Checklist", font=self.font_subtitle, text_color=COLOR_TEXT_PRIMARY)
        self.guide_title.pack(anchor="w", padx=25, pady=(15, 10))
        
        self.steps_container = ctk.CTkFrame(self.guide_card, fg_color="transparent")
        self.steps_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        guides = [
            ("1", "Click the '➕ Add New Rule' button on the sidebar to create a file routing instruction."),
            ("2", "Define the source folder you want Sentinel to watch (e.g. your Downloads folder)."),
            ("3", "Add file extensions (e.g. .pdf, .zip) or matching file keywords to target specific files."),
            ("4", "Specify the destination folder where matched files should be automatically relocated."),
            ("5", "Click 'Save Configuration' and toggle '▶️ Start Daemon' to run the automation in background.")
        ]
        
        for num, text in guides:
            # Horizontal bar row
            item_frame = ctk.CTkFrame(self.steps_container, fg_color=COLOR_BG, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
            item_frame.pack(fill="x", expand=True, pady=5)
            
            # Step Badge
            badge = ctk.CTkLabel(
                item_frame, 
                text=num, 
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color="#FFFFFF",
                fg_color=COLOR_ACCENT, 
                width=24, 
                height=24, 
                corner_radius=12
            )
            badge.pack(side="left", padx=15, pady=8)
            
            # Step Text
            lbl = ctk.CTkLabel(
                item_frame, 
                text=text, 
                font=self.font_checklist, 
                text_color=COLOR_TEXT_PRIMARY, 
                justify="left"
            )
            lbl.pack(side="left", padx=(5, 15), pady=8, fill="x")

        # --- B. Form Editor Frame ---
        self.editor_frame = ctk.CTkFrame(self.work_area, fg_color="transparent")
        
        self.editor_card = ctk.CTkScrollableFrame(self.editor_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.editor_card.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Form Header
        self.editor_form_title = ctk.CTkLabel(self.editor_card, text="Edit Routing Rule", font=self.font_subtitle, text_color=COLOR_TEXT_PRIMARY)
        self.editor_form_title.pack(anchor="w", padx=25, pady=(15, 10))

        # Rule Name Input
        self.rule_name_label = ctk.CTkLabel(self.editor_card, text="Rule Name (e.g., CollegeDocs):", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.rule_name_label.pack(anchor="w", padx=25, pady=(6, 2))
        self.rule_name_entry = ctk.CTkEntry(self.editor_card, height=36, corner_radius=6, border_color=COLOR_CARD_BORDER, fg_color=COLOR_BG, text_color=COLOR_TEXT_PRIMARY)
        self.rule_name_entry.pack(fill="x", padx=25, pady=(0, 8))

        # Source Input
        self.source_label = ctk.CTkLabel(self.editor_card, text="Source Watch Folder Path:", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.source_label.pack(anchor="w", padx=25, pady=(6, 2))
        self.source_frame = ctk.CTkFrame(self.editor_card, fg_color="transparent")
        self.source_frame.pack(fill="x", padx=25, pady=(0, 8))
        
        self.source_entry = ctk.CTkEntry(self.source_frame, height=36, corner_radius=6, border_color=COLOR_CARD_BORDER, fg_color=COLOR_BG, text_color=COLOR_TEXT_PRIMARY)
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.source_browse_btn = ctk.CTkButton(
            self.source_frame,
            text="📁 Browse",
            font=self.font_body_bold,
            width=100,
            height=36,
            fg_color=COLOR_CARD_BORDER,
            hover_color=COLOR_BG,
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda: self.browse_directory(self.source_entry),
        )
        self.source_browse_btn.pack(side="right")

        # Destination Input
        self.dest_label = ctk.CTkLabel(self.editor_card, text="Destination Folder Path:", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.dest_label.pack(anchor="w", padx=25, pady=(6, 2))
        self.dest_frame = ctk.CTkFrame(self.editor_card, fg_color="transparent")
        self.dest_frame.pack(fill="x", padx=25, pady=(0, 8))
        
        self.dest_entry = ctk.CTkEntry(self.dest_frame, height=36, corner_radius=6, border_color=COLOR_CARD_BORDER, fg_color=COLOR_BG, text_color=COLOR_TEXT_PRIMARY)
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.dest_browse_btn = ctk.CTkButton(
            self.dest_frame,
            text="📁 Browse",
            font=self.font_body_bold,
            width=100,
            height=36,
            fg_color=COLOR_CARD_BORDER,
            hover_color=COLOR_BG,
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda: self.browse_directory(self.dest_entry),
        )
        self.dest_browse_btn.pack(side="right")

        # Extensions Input
        self.ext_label = ctk.CTkLabel(self.editor_card, text="Target File Extensions (comma separated, e.g. .pdf, .docx):", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.ext_label.pack(anchor="w", padx=25, pady=(6, 2))
        self.ext_entry = ctk.CTkEntry(self.editor_card, height=36, corner_radius=6, border_color=COLOR_CARD_BORDER, fg_color=COLOR_BG, text_color=COLOR_TEXT_PRIMARY)
        self.ext_entry.pack(fill="x", padx=25, pady=(0, 8))

        # Keywords Input
        self.keyword_label = ctk.CTkLabel(self.editor_card, text="Target Filename Keywords (comma separated, e.g. assign, report):", font=self.font_body_bold, text_color=COLOR_TEXT_PRIMARY)
        self.keyword_label.pack(anchor="w", padx=25, pady=(6, 2))
        self.keyword_entry = ctk.CTkEntry(self.editor_card, height=36, corner_radius=6, border_color=COLOR_CARD_BORDER, fg_color=COLOR_BG, text_color=COLOR_TEXT_PRIMARY)
        self.keyword_entry.pack(fill="x", padx=25, pady=(0, 15))

        # Editor Form Button Bar
        self.btn_frame = ctk.CTkFrame(self.editor_card, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=25, pady=(0, 15))
        
        self.save_btn = ctk.CTkButton(
            self.btn_frame, 
            text="💾 Save Configuration", 
            font=self.font_body_bold,
            fg_color=COLOR_SUCCESS, 
            hover_color=COLOR_SUCCESS_HOVER, 
            height=38,
            command=self.save_config
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        self.del_btn = ctk.CTkButton(
            self.btn_frame, 
            text="🗑️ Delete Rule", 
            font=self.font_body_bold,
            fg_color=COLOR_DANGER, 
            hover_color=COLOR_DANGER_HOVER, 
            height=38,
            command=self.delete_rule
        )
        self.del_btn.pack(side="left")

        # Initialize Default State (Show Dashboard)
        self.show_dashboard()

        # ---------------------------------------------------------------------
        # 📝 REAL-TIME LOG Activity CONSOLE (Bottom Pane)
        # ---------------------------------------------------------------------
        self.console_frame = ctk.CTkFrame(self.main_container, height=140, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.console_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=(5, 20))
        self.console_frame.grid_propagate(False)
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(1, weight=1)

        # Console Header
        self.console_header = ctk.CTkFrame(self.console_frame, fg_color="transparent", height=32)
        self.console_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        self.console_header.grid_propagate(False)
        
        self.console_title = ctk.CTkLabel(self.console_header, text="📝 Live Activity Logs", font=self.font_subtitle, text_color=COLOR_TEXT_PRIMARY)
        self.console_title.pack(side="left")

        self.console_clear_btn = ctk.CTkButton(
            self.console_header, 
            text="Clear Log View", 
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            width=90,
            height=22,
            fg_color=COLOR_CARD_BORDER,
            hover_color=COLOR_BG,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.clear_console
        )
        self.console_clear_btn.pack(side="right")

        # Monospace Text Box Styled like a Terminal Console
        self.console_text = ctk.CTkTextbox(
            self.console_frame, 
            font=self.font_console,
            fg_color=COLOR_CONSOLE_BG, 
            text_color=COLOR_CONSOLE_TEXT,
            corner_radius=8,
            border_color=COLOR_CARD_BORDER,
            border_width=1
        )
        self.console_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Start the background log observer loop
        self.after(500, self.poll_logs)

    # =====================================================================
    # ⚙️ LOGIC & DATA METHODS
    # =====================================================================
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"watch_directory": "", "settle_seconds": 3, "rules": {}, "destinations": {}}

    def refresh_sidebar(self):
        # Clear existing button children
        for widget in self.rule_list_frame.winfo_children():
            widget.destroy()

        # Overview Navigation Item (Dynamic highlight based on state)
        is_dash_active = (self.current_rule is None)
        dash_bg = COLOR_NAV_ACTIVE if is_dash_active else "transparent"
        dash_txt = COLOR_NAV_ACTIVE_TEXT if is_dash_active else COLOR_TEXT_PRIMARY
        
        self.dash_nav_btn = ctk.CTkButton(
            self.rule_list_frame,
            text="📊  System Overview",
            font=self.font_body_bold,
            fg_color=dash_bg,
            text_color=dash_txt,
            hover_color=COLOR_ACCENT_HOVER,
            anchor="w",
            height=36,
            corner_radius=8,
            command=self.show_dashboard
        )
        self.dash_nav_btn.pack(pady=(0, 15), padx=5, fill="x")

        # Label Separator
        if self.config_data.get("rules", {}):
            lbl = ctk.CTkLabel(self.rule_list_frame, text="⚡ FILE RULES", font=ctk.CTkFont(family="Inter", size=10, weight="bold"), text_color=COLOR_TEXT_MUTED)
            lbl.pack(anchor="w", padx=10, pady=(0, 5))

        # Dynamic Rule Items
        for rule_name in self.config_data.get("rules", {}):
            is_active = (rule_name == self.current_rule)
            btn_bg = COLOR_NAV_ACTIVE if is_active else "transparent"
            btn_txt = COLOR_NAV_ACTIVE_TEXT if is_active else COLOR_TEXT_PRIMARY
            
            btn = ctk.CTkButton(
                self.rule_list_frame, 
                text=f"⚙️  {rule_name}", 
                font=self.font_body,
                fg_color=btn_bg, 
                text_color=btn_txt, 
                hover_color=COLOR_ACCENT_HOVER,
                anchor="w", 
                height=34,
                corner_radius=6,
                command=lambda r=rule_name: self.load_rule_into_editor(r)
            )
            btn.pack(pady=2, padx=5, fill="x")

    def show_dashboard(self):
        self.current_rule = None
        self.header_title.configure(text="System Dashboard")
        self.editor_frame.grid_forget()
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.refresh_sidebar()
        self.refresh_stats()

    def refresh_stats(self):
        # Dynamic update of dashboard indicators
        if not hasattr(self, "stats_rules_val"):
            return
            
        # 1. Total active rules counter
        total_rules = len(self.config_data.get("rules", {}))
        self.stats_rules_val.configure(text=str(total_rules))

        # 2. Watch directory label formatting
        watch_path = self.config_data.get("watch_directory", "")
        if watch_path:
            # Shorten if extremely long to fit inside stats card gracefully
            formatted_path = watch_path
            if len(formatted_path) > 30:
                formatted_path = "..." + formatted_path[-27:]
            self.stats_watch_val.configure(text=formatted_path, text_color=COLOR_TEXT_PRIMARY)
        else:
            self.stats_watch_val.configure(text="Not Configured", text_color=COLOR_DANGER)

        # 3. Daemon Process info
        if self.sentinel_is_running():
            pid_val = self.sentinel_process.pid if self.sentinel_process else "?"
            self.stats_status_val.configure(text=f"Active (PID {pid_val})", text_color=COLOR_SUCCESS)
        else:
            self.stats_status_val.configure(text="Stopped / Idle", text_color=COLOR_TEXT_MUTED)

    def load_rule_into_editor(self, rule_name):
        self.current_rule = rule_name
        self.header_title.configure(text=f"Rule Configuration: {rule_name}")
        self.dashboard_frame.grid_forget()
        self.editor_frame.grid(row=0, column=0, sticky="nsew")

        # Reset form fields
        self.rule_name_entry.delete(0, 'end')
        self.source_entry.delete(0, 'end')
        self.dest_entry.delete(0, 'end')
        self.ext_entry.delete(0, 'end')
        self.keyword_entry.delete(0, 'end')

        # Populate with data
        self.rule_name_entry.insert(0, rule_name)
        self.source_entry.insert(0, self.config_data.get("watch_directory", ""))
        self.dest_entry.insert(0, self.config_data.get("destinations", {}).get(rule_name, ""))
        
        ext_list = self.config_data.get("rules", {}).get(rule_name, {}).get("extensions", [])
        self.ext_entry.insert(0, ", ".join(ext_list))
        
        keyword_list = self.config_data.get("rules", {}).get(rule_name, {}).get("keywords", [])
        self.keyword_entry.insert(0, ", ".join(keyword_list))

        self.refresh_sidebar()

    def add_new_rule(self):
        self.current_rule = "NewRule"
        self.header_title.configure(text="Creating New Rule")
        self.dashboard_frame.grid_forget()
        self.editor_frame.grid(row=0, column=0, sticky="nsew")
        
        self.rule_name_entry.delete(0, 'end')
        self.source_entry.delete(0, 'end')
        self.dest_entry.delete(0, 'end')
        self.ext_entry.delete(0, 'end')
        self.keyword_entry.delete(0, 'end')
        
        self.rule_name_entry.insert(0, "NewRule")
        self.source_entry.insert(0, self.config_data.get("watch_directory", ""))
        self.refresh_sidebar()

    def browse_directory(self, entry_widget):
        current_path = entry_widget.get().strip()
        initial_dir = os.path.expanduser(current_path) if current_path else os.path.expanduser("~")
        selected_dir = filedialog.askdirectory(initialdir=initial_dir)

        if selected_dir:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, selected_dir)

    def save_config(self):
        if self.persist_config(show_feedback=True):
            messagebox.showinfo("Saved", f"Configuration for '{self.current_rule}' saved successfully!")

    def persist_config(self, show_feedback=False):
        if not self.current_rule:
            if show_feedback:
                messagebox.showerror("Error", "Select or create a rule before saving.")
            return False

        new_name = self.rule_name_entry.get().strip()
        source_dir = self.source_entry.get().strip()
        dest = self.dest_entry.get().strip()
        exts = [x.strip() for x in self.ext_entry.get().split(',') if x.strip()]
        keywords = [x.strip() for x in self.keyword_entry.get().split(',') if x.strip()]

        if not new_name:
            messagebox.showerror("Error", "Rule Name cannot be empty.")
            return False

        if not source_dir:
            messagebox.showerror("Error", "Source Folder Path cannot be empty.")
            return False

        # Clean old key if rule name was modified
        if self.current_rule != new_name and self.current_rule in self.config_data.get("rules", {}):
            if self.current_rule in self.config_data.get("rules", {}):
                del self.config_data["rules"][self.current_rule]
            if self.current_rule in self.config_data.get("destinations", {}):
                del self.config_data["destinations"][self.current_rule]

        # Register inside JSON structure
        self.config_data["watch_directory"] = source_dir
        
        if "rules" not in self.config_data:
            self.config_data["rules"] = {}
        if "destinations" not in self.config_data:
            self.config_data["destinations"] = {}
            
        self.config_data["rules"][new_name] = {"extensions": exts, "keywords": keywords}
        self.config_data["destinations"][new_name] = dest

        # Write updates out
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            messagebox.showerror("IO Error", f"Could not write configuration to disk:\n{e}")
            return False

        self.current_rule = new_name
        self.load_rule_into_editor(new_name)
        return True

    def delete_rule(self):
        if self.current_rule and self.current_rule in self.config_data.get("rules", {}):
            del self.config_data["rules"][self.current_rule]
            if self.current_rule in self.config_data.get("destinations", {}):
                del self.config_data["destinations"][self.current_rule]
            
            try:
                with open(CONFIG_PATH, 'w') as f:
                    json.dump(self.config_data, f, indent=2)
            except Exception as e:
                messagebox.showerror("IO Error", f"Could not write configuration update:\n{e}")
                return

            self.show_dashboard()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def clear_console(self):
        self.console_text.delete("1.0", "end")

    # =====================================================================
    # 🕵️ DAEMON OBSERVER LOG POLLING
    # =====================================================================
    def poll_logs(self):
        # Seek log file and dump delta differences into GUI text box
        log_path = os.path.join(APP_DIR, "logs", "sentinel.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    if self.log_file_pos == 0:
                        # Initial seek. Read last 2000 bytes so we show fresh relevant logs on startup
                        f.seek(0, 2)
                        size = f.tell()
                        f.seek(max(0, size - 2000), 0)
                        lines = f.readlines()
                        if lines:
                            content = "".join(lines[1:] if len(lines) > 1 else lines)
                            self.console_text.insert("end", content)
                            self.console_text.see("end")
                        self.log_file_pos = size
                    else:
                        f.seek(self.log_file_pos)
                        new_data = f.read()
                        if new_data:
                            self.console_text.insert("end", new_data)
                            self.console_text.see("end")
                        self.log_file_pos = f.tell()
            except Exception:
                pass
        self.after(1000, self.poll_logs)

    # =====================================================================
    # ⚙️ DAEMON PROCESS ORCHESTRATION
    # =====================================================================
    def toggle_sentinel(self):
        if self.sentinel_is_running():
            self.stop_sentinel()
        else:
            self.start_sentinel()

    def start_sentinel(self):
        # Validate rules are active
        if self.current_rule and not self.persist_config():
            return

        if not self.config_data.get("watch_directory") or not self.config_data.get("rules"):
            messagebox.showerror(
                "Configuration Required",
                "Add and save at least one rule with a source folder before running Sentinel.",
            )
            return

        if self.sentinel_is_running():
            self.update_run_status("Running", "Stop Sentinel", "red", "darkred")
            return

        startupinfo = None
        creationflags = 0

        # Silent shell execution configuration for Windows target compiles
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            if getattr(sys, 'frozen', False):
                daemon_exe = "SentinelDaemon.exe" if os.name == "nt" else "SentinelDaemon"
                daemon_path = os.path.join(APP_DIR, daemon_exe)
                cmd = [daemon_path]
            else:
                main_path = os.path.join(APP_DIR, "main.py")
                cmd = [sys.executable, main_path]

            self.sentinel_process = subprocess.Popen(
                cmd,
                cwd=APP_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except OSError as exc:
            self.sentinel_process = None
            self.update_run_status("Failed to start", "Run Sentinel", "green", "darkgreen")
            messagebox.showerror("Launch Failed", f"Could not start Sentinel.\n\n{exc}")
            return

        self.update_run_status("Running", "Stop Sentinel", "red", "darkred")
        self.after(1000, self.poll_sentinel_process)

    def stop_sentinel(self):
        if self.sentinel_process and self.sentinel_process.poll() is None:
            self.sentinel_process.terminate()
            try:
                self.sentinel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sentinel_process.kill()
                self.sentinel_process.wait(timeout=5)

        self.sentinel_process = None
        self.update_run_status("Stopped", "Run Sentinel", "green", "darkgreen")

    def sentinel_is_running(self):
        return self.sentinel_process is not None and self.sentinel_process.poll() is None

    def poll_sentinel_process(self):
        if self.sentinel_is_running():
            self.after(1000, self.poll_sentinel_process)
            return

        if self.sentinel_process is not None:
            exit_code = self.sentinel_process.poll()
            self.sentinel_process = None
            self.update_run_status("Stopped", "Run Sentinel", "green", "darkgreen")

            if exit_code not in (0, None):
                messagebox.showwarning(
                    "Sentinel Stopped",
                    f"Sentinel exited with code {exit_code}. Check logs/sentinel.log for details.",
                )

    def update_run_status(self, status_text, button_text, button_color, hover_color):
        if status_text == "Running":
            self.header_status_dot.configure(text="●", text_color=COLOR_SUCCESS)
            self.header_status_txt.configure(text="Daemon: Active")
            self.daemon_toggle_btn.configure(text="⏹️  Stop Sentinel", fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER)
        elif status_text == "Failed to start":
            self.header_status_dot.configure(text="●", text_color=COLOR_DANGER)
            self.header_status_txt.configure(text="Daemon: Failed")
            self.daemon_toggle_btn.configure(text="▶️  Start Sentinel", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER)
        else: # Stopped
            self.header_status_dot.configure(text="●", text_color=COLOR_TEXT_MUTED)
            self.header_status_txt.configure(text="Daemon: Inactive")
            self.daemon_toggle_btn.configure(text="▶️  Start Sentinel", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER)
        
        self.refresh_stats()

    def on_close(self):
        self.stop_sentinel()
        self.destroy()

if __name__ == "__main__":
    app = SentinelUI()
    app.mainloop()