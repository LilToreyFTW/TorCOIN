#!/usr/bin/env python3
"""
TorCOIN Wallet GUI Application
A full-featured desktop wallet for TorCOIN with modern GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import hashlib
import secrets
import time
from datetime import datetime
import threading
import webbrowser

class TorCOINWallet:
    def __init__(self, root):
        self.root = root

        # Wallet data (initialize early for color access)
        self.wallet_data = {
            "address": "",
            "private_key": "",
            "balance": 0.0,
            "transactions": [],
            "settings": {
                "theme": "dark",
                "auto_backup": True,
                "notifications": True
            }
        }

        # Load wallet if exists
        self.load_wallet()

        # Create GUI styles first
        self.create_styles()

        # Configure root window for dark chrome theme
        self.root.title("TorCOIN Wallet v1.1.0 - Dark Chrome 3D Edition")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        self.root.configure(bg=self.colors['bg_primary'])

        # Create GUI components
        self.create_menu()
        self.create_status_bar()
        self.create_main_interface()

        # Apply theme
        self.apply_theme()

        # Start balance update thread
        self.start_balance_updates()

    def create_styles(self):
        """Create custom styles for the application with 3D dark chrome theme."""
        style = ttk.Style()

        # Configure colors for clean black text theme with no weird backgrounds
        self.colors = {
            'bg_primary': '#f5f5f5',      # Light gray main background
            'bg_secondary': '#ffffff',    # Clean white background
            'bg_tertiary': '#f0f0f0',     # Light gray panels
            'bg_panel': '#ffffff',        # Clean white panels
            'accent_primary': '#FF0066', # Deep red accent
            'accent_secondary': '#00BFFF', # Deep blue accent
            'accent_gold': '#FFD700',    # Gold for highlights
            'text_primary': '#000000',   # Pure black text
            'text_secondary': '#333333', # Dark gray text
            'text_muted': '#666666',     # Medium gray text
            'border_primary': '#cccccc', # Light gray borders
            'border_accent': '#FF0066',  # Red accent borders
            'success': '#00AA66',        # Dark green for success
            'warning': '#FF8800',        # Dark orange warning
            'error': '#CC0000',          # Dark red error
            'glow_primary': '#FF0066',   # Red glow
            'glow_secondary': '#00BFFF', # Blue glow
        }

        # Custom button styles with 3D effects
        style.configure('Accent.TButton',
                       background=self.colors['accent_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'),
                       padding=12,
                       relief='raised',
                       borderwidth=2)

        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_secondary']),
                           ('pressed', self.colors['bg_tertiary'])],
                 relief=[('pressed', 'sunken')])

        style.configure('Primary.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 9, 'bold'),
                       padding=8,
                       relief='raised')

        style.map('Primary.TButton',
                 background=[('active', self.colors['accent_secondary']),
                           ('pressed', self.colors['bg_secondary'])])

        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['bg_primary'],
                       font=('Segoe UI', 9, 'bold'),
                       padding=10,
                       relief='raised')

        style.configure('Danger.TButton',
                       background=self.colors['error'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 9, 'bold'),
                       padding=10,
                       relief='raised')

        # Enhanced label styles
        style.configure('Title.TLabel',
                       font=('Segoe UI', 28, 'bold'),
                       foreground=self.colors['accent_primary'])

        style.configure('Header.TLabel',
                       font=('Segoe UI', 18, 'bold'),
                       foreground=self.colors['text_primary'])

        style.configure('Balance.TLabel',
                       font=('Segoe UI', 36, 'bold'),
                       foreground=self.colors['accent_gold'])

        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 14),
                       foreground=self.colors['text_secondary'])

        # Frame styles
        style.configure('Card.TFrame',
                       background=self.colors['bg_panel'],
                       relief='raised',
                       borderwidth=2)

        style.configure('Panel.TFrame',
                       background=self.colors['bg_secondary'],
                       relief='groove',
                       borderwidth=1)

    def create_menu(self):
        """Create the application menu bar with dark chrome styling."""
        menubar = tk.Menu(self.root, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                         activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'],
                         relief='flat', bd=0)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="💾 File", menu=file_menu)
        file_menu.add_command(label="🆕 New Wallet", command=self.create_new_wallet)
        file_menu.add_command(label="📂 Open Wallet", command=self.open_wallet)
        file_menu.add_command(label="💾 Save Wallet", command=self.save_wallet)
        file_menu.add_separator()
        file_menu.add_command(label="🔄 Backup Wallet", command=self.backup_wallet)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.on_closing)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", command=lambda: self.show_frame("dashboard"))
        view_menu.add_command(label="Send", command=lambda: self.show_frame("send"))
        view_menu.add_command(label="Receive", command=lambda: self.show_frame("receive"))
        view_menu.add_command(label="Transactions", command=lambda: self.show_frame("transactions"))
        view_menu.add_command(label="Settings", command=lambda: self.show_frame("settings"))

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                            activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Address Book", command=self.show_address_book)
        tools_menu.add_command(label="Price Calculator", command=self.show_price_calculator)
        tools_menu.add_separator()
        tools_menu.add_command(label="Network Status", command=self.show_network_status)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="Security Tips", command=self.show_security_tips)
        help_menu.add_separator()
        help_menu.add_command(label="About TorCOIN Wallet", command=self.show_about)

    def create_main_interface(self):
        """Create the main interface with different frames and 3D chrome styling."""
        # Main container with chrome effect
        self.main_container = tk.Frame(self.root, bg=self.colors['bg_primary'],
                                     relief='raised', bd=3)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create frames for different views
        self.frames = {}
        self.create_dashboard_frame()
        self.create_send_frame()
        self.create_receive_frame()
        self.create_transactions_frame()
        self.create_settings_frame()

        # Show dashboard by default
        self.show_frame("dashboard")

    def create_dashboard_frame(self):
        """Create the dashboard/main view with 3D chrome styling."""
        frame = tk.Frame(self.main_container, bg=self.colors['bg_primary'])
        self.frames["dashboard"] = frame

        # Header with 3D chrome effect
        header_frame = tk.Frame(frame, bg=self.colors['bg_secondary'],
                               relief='raised', bd=3, height=100)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        # Clean header background without gradients

        title_label = ttk.Label(header_frame, text="TorCOIN Wallet", style='Title.TLabel')
        title_label.pack(pady=(20, 5))

        # Live date/time display
        self.datetime_label = ttk.Label(header_frame, text="", style='Subtitle.TLabel')
        self.datetime_label.pack(pady=(0, 15))
        self.update_datetime()

        # Balance section with 3D chrome effect
        balance_frame = tk.Frame(frame, bg=self.colors['bg_panel'],
                                relief='ridge', bd=4)
        balance_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        # Clean balance section without glow effects

        balance_title = ttk.Label(balance_frame, text="💰 Available Balance",
                                 style='Header.TLabel', background=self.colors['bg_panel'])
        balance_title.pack(pady=(25, 15))

        self.balance_label = ttk.Label(balance_frame, text=".2f",
                                      style='Balance.TLabel', background=self.colors['bg_panel'])
        self.balance_label.pack(pady=(0, 25))

        # Quick actions with 3D effects
        actions_frame = tk.Frame(frame, bg=self.colors['bg_primary'])
        actions_frame.pack(fill=tk.X, padx=25, pady=(0, 20))

        actions_title = ttk.Label(actions_frame, text="⚡ Quick Actions", style='Header.TLabel')
        actions_title.pack(pady=(0, 20))

        buttons_frame = tk.Frame(actions_frame, bg=self.colors['bg_primary'])
        buttons_frame.pack()

        # Clean buttons with black text
        send_btn = tk.Button(buttons_frame, text="Send TorCOIN",
                           bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                           font=('Segoe UI', 11, 'bold'), relief='raised', bd=2,
                           activebackground=self.colors['bg_tertiary'],
                           activeforeground=self.colors['text_primary'],
                           padx=20, pady=10, cursor='hand2',
                           command=lambda: self.show_frame("send"))
        send_btn.pack(side=tk.LEFT, padx=15)

        receive_btn = tk.Button(buttons_frame, text="Receive TorCOIN",
                              bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                              font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                              activebackground=self.colors['bg_secondary'],
                              padx=20, pady=10, cursor='hand2',
                              command=lambda: self.show_frame("receive"))
        receive_btn.pack(side=tk.LEFT, padx=15)

        tx_btn = tk.Button(buttons_frame, text="Transactions",
                          bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                          font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                          activebackground=self.colors['bg_secondary'],
                          padx=20, pady=10, cursor='hand2',
                          command=lambda: self.show_frame("transactions"))
        tx_btn.pack(side=tk.LEFT, padx=15)

        # Recent transactions with chrome styling
        recent_frame = tk.Frame(frame, bg=self.colors['bg_secondary'],
                               relief='groove', bd=3)
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))

        recent_title = ttk.Label(recent_frame, text="📈 Recent Transactions",
                                style='Header.TLabel', background=self.colors['bg_secondary'])
        recent_title.pack(pady=20)

        # Transaction list preview with enhanced styling
        self.recent_transactions_frame = tk.Frame(recent_frame, bg=self.colors['bg_panel'],
                                                relief='sunken', bd=2)
        self.recent_transactions_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.update_recent_transactions()

    def create_send_frame(self):
        """Create the send TorCOIN interface with chrome styling."""
        frame = tk.Frame(self.main_container, bg=self.colors['bg_primary'])
        self.frames["send"] = frame

        # Header with 3D effect
        header_frame = tk.Frame(frame, bg=self.colors['bg_secondary'],
                               relief='raised', bd=4, height=90)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        # Clean header background without gradients

        title_label = ttk.Label(header_frame, text="🚀 Send TorCOIN", style='Title.TLabel')
        title_label.pack(pady=25)

        # Send form with chrome panel
        form_frame = tk.Frame(frame, bg=self.colors['bg_panel'],
                             relief='groove', bd=3)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        # Recipient address with chrome styling
        addr_frame = tk.Frame(form_frame, bg=self.colors['bg_panel'])
        addr_frame.pack(fill=tk.X, padx=25, pady=25)

        ttk.Label(addr_frame, text="📧 Recipient Address:", style='Header.TLabel',
                 background=self.colors['bg_panel']).pack(anchor=tk.W, pady=(0, 15))

        # Address input with 3D effect
        addr_container = tk.Frame(addr_frame, bg=self.colors['bg_tertiary'],
                                 relief='sunken', bd=3)
        addr_container.pack(fill=tk.X)

        self.send_address_entry = tk.Text(addr_container, height=3, font=('Consolas', 11),
                                        bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                        insertbackground=self.colors['accent_gold'],
                                        relief='flat', bd=2)
        self.send_address_entry.pack(fill=tk.BOTH, padx=10, pady=10)

        # Amount with chrome styling
        amount_frame = tk.Frame(form_frame, bg=self.colors['bg_panel'])
        amount_frame.pack(fill=tk.X, padx=25, pady=(0, 25))

        ttk.Label(amount_frame, text="💰 Amount (TOR):", style='Header.TLabel',
                 background=self.colors['bg_panel']).pack(anchor=tk.W, pady=(0, 15))

        amount_entry_frame = tk.Frame(amount_frame, bg=self.colors['bg_panel'])
        amount_entry_frame.pack(fill=tk.X)

        # Amount input with 3D styling
        amount_container = tk.Frame(amount_entry_frame, bg=self.colors['bg_tertiary'],
                                   relief='sunken', bd=3)
        amount_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.send_amount_entry = tk.Entry(amount_container, font=('Segoe UI', 16, 'bold'),
                                        bg=self.colors['bg_tertiary'], fg=self.colors['accent_gold'],
                                        insertbackground=self.colors['accent_gold'],
                                        relief='flat', bd=2)
        self.send_amount_entry.pack(fill=tk.X, padx=15, pady=10)

        # Clean MAX button
        max_btn = tk.Button(amount_entry_frame, text="MAX",
                           bg=self.colors['warning'], fg=self.colors['text_primary'],
                           font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                           activebackground=self.colors['bg_tertiary'],
                           padx=15, pady=8, cursor='hand2',
                           command=self.set_max_amount)
        max_btn.pack(side=tk.RIGHT, padx=(15, 0))

        # Fee selection
        fee_frame = tk.Frame(form_frame, bg=self.colors['bg_secondary'])
        fee_frame.pack(fill=tk.X, padx=20, pady=(0, 30))

        ttk.Label(fee_frame, text="Transaction Fee:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))

        self.fee_var = tk.StringVar(value="standard")
        fee_options_frame = tk.Frame(fee_frame, bg=self.colors['bg_secondary'])
        fee_options_frame.pack(fill=tk.X)

        ttk.Radiobutton(fee_options_frame, text="Slow (0.001 TOR)", variable=self.fee_var,
                       value="slow").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(fee_options_frame, text="Standard (0.01 TOR)", variable=self.fee_var,
                       value="standard").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(fee_options_frame, text="Fast (0.1 TOR)", variable=self.fee_var,
                       value="fast").pack(side=tk.LEFT)

        # Send button with enhanced 3D chrome effect
        send_container = tk.Frame(form_frame, bg=self.colors['bg_panel'])
        send_container.pack(pady=30)

        send_button = tk.Button(send_container, text="SEND TORCOIN",
                               bg=self.colors['success'], fg=self.colors['text_primary'],
                               font=('Segoe UI', 14, 'bold'), relief='raised', bd=2,
                               activebackground=self.colors['bg_tertiary'],
                               padx=40, pady=15, cursor='hand2',
                               command=self.send_transaction)
        send_button.pack()

        # Clean button without glow effects

        # Back button
        ttk.Button(frame, text="← Back to Dashboard", style='Primary.TButton',
                  command=lambda: self.show_frame("dashboard")).pack(pady=(0, 20))

    def create_receive_frame(self):
        """Create the receive TorCOIN interface."""
        frame = tk.Frame(self.main_container, bg=self.colors['bg_primary'])
        self.frames["receive"] = frame

        # Header
        header_frame = tk.Frame(frame, bg=self.colors['bg_secondary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(header_frame, text="Receive TorCOIN", style='Title.TLabel')
        title_label.pack(pady=20)

        # Address display
        address_frame = tk.Frame(frame, bg=self.colors['bg_secondary'])
        address_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        ttk.Label(address_frame, text="Your TorCOIN Address:", style='Header.TLabel').pack(pady=(20, 10))

        # Address display area
        address_display_frame = tk.Frame(address_frame, bg=self.colors['bg_tertiary'], relief='sunken', bd=2)
        address_display_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.address_label = tk.Text(address_display_frame, height=3, font=('Consolas', 12),
                                   bg=self.colors['bg_tertiary'], fg=self.colors['accent_primary'],
                                   state='disabled', wrap=tk.WORD)
        self.address_label.pack(fill=tk.X, padx=10, pady=10)
        self.update_address_display()

        # QR Code placeholder
        qr_frame = tk.Frame(address_frame, bg=self.colors['bg_secondary'])
        qr_frame.pack(pady=(0, 20))

        # QR Code placeholder (would need QR code library for actual implementation)
        qr_placeholder = tk.Canvas(qr_frame, width=200, height=200, bg='white')
        qr_placeholder.pack(pady=10)
        qr_placeholder.create_text(100, 100, text="QR Code\nPlaceholder", fill='black', font=('Arial', 14))

        # Action buttons
        buttons_frame = tk.Frame(address_frame, bg=self.colors['bg_secondary'])
        buttons_frame.pack(pady=(0, 20))

        ttk.Button(buttons_frame, text="📋 Copy Address", style='Primary.TButton',
                  command=self.copy_address).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🔄 Generate New Address", style='Accent.TButton',
                  command=self.generate_new_address).pack(side=tk.LEFT)

        # Request payment
        request_frame = tk.Frame(frame, bg=self.colors['bg_secondary'])
        request_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(request_frame, text="Request Payment:", style='Header.TLabel').pack(anchor=tk.W, pady=(20, 10))

        request_amount_frame = tk.Frame(request_frame, bg=self.colors['bg_secondary'])
        request_amount_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(request_amount_frame, text="Amount (TOR):").pack(side=tk.LEFT, padx=(0, 10))
        self.request_amount_entry = tk.Entry(request_amount_frame, width=15,
                                           font=('Segoe UI', 11))
        self.request_amount_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(request_amount_frame, text="Generate Payment Link", style='Success.TButton',
                  command=self.generate_payment_link).pack(side=tk.LEFT)

        # Back button
        ttk.Button(frame, text="← Back to Dashboard", style='Primary.TButton',
                  command=lambda: self.show_frame("dashboard")).pack(pady=(0, 20))

    def create_transactions_frame(self):
        """Create the transactions history interface."""
        frame = tk.Frame(self.main_container, bg=self.colors['bg_primary'])
        self.frames["transactions"] = frame

        # Header
        header_frame = tk.Frame(frame, bg=self.colors['bg_secondary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(header_frame, text="Transaction History", style='Title.TLabel')
        title_label.pack(pady=20)

        # Transactions list
        list_frame = tk.Frame(frame, bg=self.colors['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Filter buttons
        filter_frame = tk.Frame(list_frame, bg=self.colors['bg_secondary'])
        filter_frame.pack(fill=tk.X, pady=(20, 10))

        ttk.Button(filter_frame, text="All", style='Primary.TButton',
                  command=lambda: self.filter_transactions("all")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_frame, text="Sent", style='Primary.TButton',
                  command=lambda: self.filter_transactions("sent")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(filter_frame, text="Received", style='Primary.TButton',
                  command=lambda: self.filter_transactions("received")).pack(side=tk.LEFT)

        # Transactions display
        self.transactions_text = scrolledtext.ScrolledText(list_frame, wrap=tk.WORD,
                                                         font=('Consolas', 10),
                                                         bg=self.colors['bg_tertiary'],
                                                         fg=self.colors['text_primary'])
        self.transactions_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        self.update_transactions_display()

        # Back button
        ttk.Button(frame, text="← Back to Dashboard", style='Primary.TButton',
                  command=lambda: self.show_frame("dashboard")).pack(pady=(0, 20))

    def create_settings_frame(self):
        """Create the settings interface."""
        frame = tk.Frame(self.main_container, bg=self.colors['bg_primary'])
        self.frames["settings"] = frame

        # Header
        header_frame = tk.Frame(frame, bg=self.colors['bg_secondary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(header_frame, text="Settings", style='Title.TLabel')
        title_label.pack(pady=20)

        # Settings content
        settings_frame = tk.Frame(frame, bg=self.colors['bg_secondary'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Appearance settings
        appearance_frame = tk.Frame(settings_frame, bg=self.colors['bg_tertiary'])
        appearance_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(appearance_frame, text="Appearance", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 15))

        theme_frame = tk.Frame(appearance_frame, bg=self.colors['bg_tertiary'])
        theme_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT, padx=(0, 20))
        self.theme_var = tk.StringVar(value=self.wallet_data["settings"]["theme"])
        ttk.Combobox(theme_frame, textvariable=self.theme_var,
                    values=["dark", "light"], state="readonly", width=10).pack(side=tk.LEFT)

        # Privacy settings
        privacy_frame = tk.Frame(settings_frame, bg=self.colors['bg_tertiary'])
        privacy_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(privacy_frame, text="Privacy & Security", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 15))

        self.auto_backup_var = tk.BooleanVar(value=self.wallet_data["settings"]["auto_backup"])
        ttk.Checkbutton(privacy_frame, text="Enable automatic wallet backups",
                       variable=self.auto_backup_var).pack(anchor=tk.W, pady=(0, 10))

        self.notifications_var = tk.BooleanVar(value=self.wallet_data["settings"]["notifications"])
        ttk.Checkbutton(privacy_frame, text="Enable transaction notifications",
                       variable=self.notifications_var).pack(anchor=tk.W)

        # Network settings
        network_frame = tk.Frame(settings_frame, bg=self.colors['bg_tertiary'])
        network_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(network_frame, text="Network", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 15))

        ttk.Button(network_frame, text="🔄 Refresh Network Status", style='Primary.TButton',
                  command=self.refresh_network_status).pack(anchor=tk.W, pady=(0, 10))

        ttk.Button(network_frame, text="🌐 View Network Information", style='Primary.TButton',
                  command=self.show_network_info).pack(anchor=tk.W)

        # Save settings button
        save_btn = tk.Button(settings_frame, text="Save Settings",
                           bg=self.colors['success'], fg=self.colors['text_primary'],
                           font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                           padx=20, pady=10, command=self.save_settings)
        save_btn.pack(pady=20)

        # Back button
        ttk.Button(frame, text="← Back to Dashboard", style='Primary.TButton',
                  command=lambda: self.show_frame("dashboard")).pack(pady=(0, 20))

    def create_status_bar(self):
        """Create the status bar at the bottom with chrome styling."""
        self.status_frame = tk.Frame(self.root, bg=self.colors['bg_tertiary'],
                                    relief='ridge', bd=2, height=35)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        self.status_frame.pack_propagate(False)

        # Clean status bar without gradients

        self.status_label = tk.Label(self.status_frame, text="🔥 Ready",
                                    bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                                    font=('Segoe UI', 9, 'bold'))
        self.status_label.place(x=15, y=8)

        self.network_status_label = tk.Label(self.status_frame, text="🌐 Network: Connected",
                                           bg=self.colors['bg_tertiary'], fg=self.colors['accent_secondary'],
                                           font=('Segoe UI', 9))
        self.network_status_label.place(relx=1.0, x=-15, y=8, anchor='ne')

    def show_frame(self, frame_name):
        """Show the specified frame and hide others."""
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(fill=tk.BOTH, expand=True)

        # Update status
        self.status_label.config(text=f"Viewing: {frame_name.title()}")

    def apply_theme(self):
        """Apply the current theme to the application."""
        # This would apply theme colors to all widgets
        # For now, we'll keep it simple with the dark theme
        pass

    def create_new_wallet(self):
        """Create a new wallet."""
        if messagebox.askyesno("Create New Wallet",
                             "This will create a new wallet. Any existing wallet data will be lost. Continue?"):
            self.generate_wallet()
            self.save_wallet()
            self.update_display()
            messagebox.showinfo("Success", "New wallet created successfully!")

    def generate_wallet(self):
        """Generate a new wallet with address and keys."""
        # Generate a random private key (simplified for demo)
        private_key = secrets.token_hex(32)

        # Generate address from private key (simplified hash)
        address_hash = hashlib.sha256(private_key.encode()).hexdigest()
        address = "TOR" + address_hash[:40].upper()

        self.wallet_data["private_key"] = private_key
        self.wallet_data["address"] = address
        self.wallet_data["balance"] = 0.0
        self.wallet_data["transactions"] = []

    def open_wallet(self):
        """Open an existing wallet file."""
        filename = filedialog.askopenfilename(
            title="Open Wallet File",
            filetypes=[("Wallet files", "*.torwallet"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.wallet_data = json.load(f)
                self.update_display()
                messagebox.showinfo("Success", "Wallet opened successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open wallet: {e}")

    def save_wallet(self):
        """Save the current wallet to a file."""
        if not self.wallet_data["address"]:
            messagebox.showwarning("Warning", "No wallet to save. Create a new wallet first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Wallet File",
            defaultextension=".torwallet",
            filetypes=[("Wallet files", "*.torwallet"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.wallet_data, f, indent=4)
                messagebox.showinfo("Success", "Wallet saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save wallet: {e}")

    def backup_wallet(self):
        """Create a backup of the wallet."""
        if not self.wallet_data["address"]:
            messagebox.showwarning("Warning", "No wallet to backup.")
            return

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"torcoin_wallet_backup_{timestamp}.torwallet"

        try:
            with open(backup_filename, 'w') as f:
                json.dump(self.wallet_data, f, indent=4)
            messagebox.showinfo("Success", f"Wallet backed up as:\n{backup_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")

    def load_wallet(self):
        """Load wallet from default location if it exists."""
        if os.path.exists("wallet.torwallet"):
            try:
                with open("wallet.torwallet", 'r') as f:
                    self.wallet_data = json.load(f)
            except:
                # If loading fails, generate new wallet
                self.generate_wallet()

        if not self.wallet_data["address"]:
            self.generate_wallet()

    def update_display(self):
        """Update all display elements with current wallet data."""
        self.balance_label.config(text=".2f")
        self.update_address_display()
        self.update_recent_transactions()
        self.update_transactions_display()

    def update_address_display(self):
        """Update the address display in receive frame."""
        if hasattr(self, 'address_label'):
            self.address_label.config(state='normal')
            self.address_label.delete(1.0, tk.END)
            self.address_label.insert(1.0, self.wallet_data["address"])
            self.address_label.config(state='disabled')

    def update_datetime(self):
        """Update the live date/time display."""
        if hasattr(self, 'datetime_label'):
            current_time = datetime.now().strftime("%A, %B %d, %Y • %I:%M:%S %p")
            self.datetime_label.config(text=current_time)
            # Update every second
            self.root.after(1000, self.update_datetime)

    def update_recent_transactions(self):
        """Update the recent transactions preview."""
        if hasattr(self, 'recent_transactions_frame'):
            # Clear existing
            for widget in self.recent_transactions_frame.winfo_children():
                widget.destroy()

            # Show last 5 transactions
            recent_txs = self.wallet_data["transactions"][-5:]

            if not recent_txs:
                ttk.Label(self.recent_transactions_frame,
                         text="No transactions yet.\nSend or receive TorCOIN to see transactions here.",
                         style='Primary.TLabel').pack(pady=20)
            else:
                for tx in reversed(recent_txs):
                    tx_frame = tk.Frame(self.recent_transactions_frame, bg=self.colors['bg_tertiary'])
                    tx_frame.pack(fill=tk.X, pady=2, padx=10)

                    amount_color = self.colors['success'] if tx['type'] == 'received' else self.colors['error']
                    amount_prefix = "+" if tx['type'] == 'received' else "-"

                    ttk.Label(tx_frame, text=".2f",
                             foreground=amount_color, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
                    ttk.Label(tx_frame, text=f"{tx['type'].title()} • {tx['date']}",
                             style='Primary.TLabel').pack(side=tk.RIGHT, padx=10)

    def update_transactions_display(self, filter_type="all"):
        """Update the full transactions display with optional filtering."""
        if hasattr(self, 'transactions_text'):
            self.transactions_text.delete(1.0, tk.END)

            transactions = self.wallet_data["transactions"]

            # Apply filter
            if filter_type == "sent":
                transactions = [tx for tx in transactions if tx['type'] == 'sent']
            elif filter_type == "received":
                transactions = [tx for tx in transactions if tx['type'] == 'received']

            if not transactions:
                filter_msg = " transactions" if filter_type != "all" else ""
                self.transactions_text.insert(tk.END, f"No {filter_type}{filter_msg} transactions found.\n\nSend or receive TorCOIN to see transactions here.")
            else:
                for tx in reversed(transactions):
                    self.transactions_text.insert(tk.END,
                        f"Date: {tx['date']}\n"
                        f"Type: {tx['type'].title()}\n"
                        f"Amount: {tx['amount']:.2f} TOR\n"
                        f"Address: {tx['address'][:20]}...\n"
                        f"Status: {tx['status']}\n"
                        f"{'─' * 50}\n\n"
                    )

    def send_transaction(self):
        """Send a TorCOIN transaction."""
        address = self.send_address_entry.get(1.0, tk.END).strip()
        amount_text = self.send_amount_entry.get().strip()

        if not address:
            messagebox.showerror("Error", "Please enter a recipient address.")
            return

        if not amount_text:
            messagebox.showerror("Error", "Please enter an amount.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than 0.")
            return

        if amount > self.wallet_data["balance"]:
            messagebox.showerror("Error", "Insufficient balance.")
            return

        # Simulate transaction
        fee = {"slow": 0.001, "standard": 0.01, "fast": 0.1}[self.fee_var.get()]
        total_cost = amount + fee

        if total_cost > self.wallet_data["balance"]:
            messagebox.showerror("Error", "Insufficient balance including fees.")
            return

        # Add transaction to history
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "sent",
            "amount": amount,
            "address": address,
            "fee": fee,
            "status": "confirmed"
        }

        self.wallet_data["transactions"].append(transaction)
        self.wallet_data["balance"] -= total_cost

        self.update_display()
        self.save_wallet()

        # Clear form
        self.send_address_entry.delete(1.0, tk.END)
        self.send_amount_entry.delete(0, tk.END)

        messagebox.showinfo("Success",
                          f"Transaction sent successfully!\n\n"
                          f"Amount: {amount:.2f} TOR\n"
                          f"Fee: {fee:.3f} TOR\n"
                          f"Total: {total_cost:.2f} TOR\n\n"
                          f"Recipient: {address[:20]}...")

    def set_max_amount(self):
        """Set the maximum sendable amount."""
        # Reserve some for fees (0.01 TOR)
        max_amount = max(0, self.wallet_data["balance"] - 0.01)
        if hasattr(self, 'send_amount_entry'):
            self.send_amount_entry.delete(0, tk.END)
            self.send_amount_entry.insert(0, f"{max_amount:.2f}")

    def copy_address(self):
        """Copy the wallet address to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.wallet_data["address"])
        messagebox.showinfo("Success", "Address copied to clipboard!")

    def generate_new_address(self):
        """Generate a new wallet address."""
        if messagebox.askyesno("Generate New Address",
                             "This will create a new address. Your old address will still work. Continue?"):
            self.generate_wallet()
            self.update_display()
            messagebox.showinfo("Success", "New address generated!")

    def generate_payment_link(self):
        """Generate a payment request link."""
        amount = self.request_amount_entry.get().strip()
        if not amount:
            messagebox.showerror("Error", "Please enter an amount.")
            return

        try:
            float(amount)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        link = f"torcoin:{self.wallet_data['address']}?amount={amount}"
        self.root.clipboard_clear()
        self.root.clipboard_append(link)
        messagebox.showinfo("Success", f"Payment link copied:\n\n{link}")

    def filter_transactions(self, filter_type):
        """Filter transactions by type."""
        self.update_transactions_display(filter_type)

    def save_settings(self):
        """Save the current settings."""
        if hasattr(self, 'theme_var'):
            self.wallet_data["settings"]["theme"] = self.theme_var.get()
        if hasattr(self, 'auto_backup_var'):
            self.wallet_data["settings"]["auto_backup"] = self.auto_backup_var.get()
        if hasattr(self, 'notifications_var'):
            self.wallet_data["settings"]["notifications"] = self.notifications_var.get()

        self.save_wallet()
        messagebox.showinfo("Success", "Settings saved successfully!")

    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Success", "Copied to clipboard!")

    def start_balance_updates(self):
        """Start background balance update thread."""
        def update_balance():
            while True:
                time.sleep(30)  # Update every 30 seconds
                # Simulate balance updates (in real app, would query network)
                if secrets.choice([True, False]):  # Random chance of receiving TOR
                    amount = secrets.uniform(0.01, 1.0)
                    self.wallet_data["balance"] += amount
                    transaction = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "received",
                        "amount": amount,
                        "address": "TOR" + secrets.token_hex(20).upper(),
                        "status": "confirmed"
                    }
                    self.wallet_data["transactions"].append(transaction)
                    self.update_display()

        thread = threading.Thread(target=update_balance, daemon=True)
        thread.start()

    def refresh_network_status(self):
        """Refresh the network status."""
        self.network_status_label.config(text="Network: Connected")
        messagebox.showinfo("Network Status", "TorCOIN network is online and operational!")

    def show_network_info(self):
        """Show network information."""
        info = """
TorCOIN Network Information:

• Network Status: Online
• Block Height: 1,234,567
• Active Nodes: 1,245
• Hash Rate: 2.5 TH/s
• Difficulty: 1,234,567
• Next Halving: Block 2,100,000

Privacy Features:
• Zero-Knowledge Proofs: Enabled
• Ring Signatures: Active
• Stealth Addresses: Supported
• View Keys: Available
        """
        messagebox.showinfo("Network Info", info)

    def show_address_book(self):
        """Show the address book with saved contacts."""
        address_window = tk.Toplevel(self.root)
        address_window.title("TorCOIN Address Book")
        address_window.geometry("500x400")
        address_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_label = ttk.Label(address_window, text="Address Book", style='Header.TLabel')
        header_label.pack(pady=20)

        # Address list
        list_frame = tk.Frame(address_window, bg=self.colors['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Sample addresses (in real app, this would be loaded from file)
        addresses = [
            {"name": "Alice Johnson", "address": "TOR1234567890ABCDEF1234567890ABCDEF"},
            {"name": "Bob Smith", "address": "TOR0987654321FEDCBA0987654321FEDCBA"},
            {"name": "Carol Davis", "address": "TOR111111111122222222223333333333"},
        ]

        for addr in addresses:
            addr_frame = tk.Frame(list_frame, bg=self.colors['bg_panel'], relief='raised', bd=1)
            addr_frame.pack(fill=tk.X, pady=5)

            ttk.Label(addr_frame, text=addr['name'], style='Header.TLabel',
                     background=self.colors['bg_panel']).pack(anchor=tk.W, padx=10, pady=5)
            ttk.Label(addr_frame, text=f"{addr['address'][:20]}...",
                     style='Primary.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W, padx=10, pady=(0, 5))

            # Copy button
            copy_btn = tk.Button(addr_frame, text="Copy",
                               bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                               font=('Segoe UI', 8), relief='flat',
                               command=lambda a=addr['address']: self.copy_to_clipboard(a))
            copy_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # Add new contact button
        add_btn = tk.Button(address_window, text="Add New Contact",
                          bg=self.colors['success'], fg=self.colors['text_primary'],
                          font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                          padx=20, pady=10,
                          command=lambda: self.add_new_contact(address_window))
        add_btn.pack(pady=20)

    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Address copied to clipboard!")

    def add_new_contact(self, parent_window):
        """Add a new contact to the address book."""
        add_window = tk.Toplevel(parent_window)
        add_window.title("Add New Contact")
        add_window.geometry("400x200")
        add_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(add_window, text="Contact Name:").pack(pady=(20, 5))
        name_entry = tk.Entry(add_window, font=('Segoe UI', 10))
        name_entry.pack(pady=(0, 10))

        ttk.Label(add_window, text="TorCOIN Address:").pack(pady=(0, 5))
        addr_entry = tk.Entry(add_window, font=('Segoe UI', 10))
        addr_entry.pack(pady=(0, 20))

        def save_contact():
            name = name_entry.get().strip()
            address = addr_entry.get().strip()
            if name and address:
                # In real app, save to file/database
                messagebox.showinfo("Success", f"Contact '{name}' added!")
                add_window.destroy()
            else:
                messagebox.showerror("Error", "Please fill in all fields")

        tk.Button(add_window, text="Save Contact",
                 bg=self.colors['success'], fg=self.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                 command=save_contact).pack()

    def show_price_calculator(self):
        """Show the price calculator for currency conversion."""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("TorCOIN Price Calculator")
        calc_window.geometry("400x300")
        calc_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_label = ttk.Label(calc_window, text="Price Calculator", style='Header.TLabel')
        header_label.pack(pady=20)

        # Calculator frame
        calc_frame = tk.Frame(calc_window, bg=self.colors['bg_secondary'], relief='raised', bd=2)
        calc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # TOR amount input
        ttk.Label(calc_frame, text="TOR Amount:", style='Primary.TLabel',
                 background=self.colors['bg_secondary']).pack(pady=(20, 5))
        tor_entry = tk.Entry(calc_frame, font=('Segoe UI', 12), justify='center')
        tor_entry.pack(pady=(0, 15))
        tor_entry.insert(0, "1.00")

        # Currency selection
        ttk.Label(calc_frame, text="Convert to:", style='Primary.TLabel',
                 background=self.colors['bg_secondary']).pack(pady=(0, 5))

        currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(calc_frame, textvariable=currency_var,
                                    values=["USD", "EUR", "GBP", "JPY", "BTC"],
                                    state="readonly", justify='center')
        currency_combo.pack(pady=(0, 15))

        # Result display
        result_label = ttk.Label(calc_frame, text="$0.00", style='Balance.TLabel',
                               background=self.colors['bg_secondary'])
        result_label.pack(pady=(0, 20))

        # Calculate button
        def calculate():
            try:
                tor_amount = float(tor_entry.get())
                currency = currency_var.get()

                # Mock exchange rates (in real app, fetch from API)
                rates = {
                    "USD": 0.85,
                    "EUR": 0.78,
                    "GBP": 0.67,
                    "JPY": 110.50,
                    "BTC": 0.000025
                }

                result = tor_amount * rates.get(currency, 1)
                if currency == "JPY":
                    result_label.config(text=f"¥{result:,.0f}")
                elif currency == "BTC":
                    result_label.config(text=f"₿{result:.8f}")
                else:
                    result_label.config(text=f"{currency} {result:.2f}")

            except ValueError:
                result_label.config(text="Invalid amount")

        calc_btn = tk.Button(calc_frame, text="Calculate",
                           bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                           font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                           padx=20, pady=8, command=calculate)
        calc_btn.pack(pady=(0, 20))

        # Auto-calculate when values change
        def auto_calc(*args):
            if tor_entry.get():
                calculate()

        tor_entry.bind('<KeyRelease>', auto_calc)
        currency_var.trace('w', auto_calc)

        # Initial calculation
        calculate()

    def show_network_status(self):
        """Show detailed network status in a window."""
        network_window = tk.Toplevel(self.root)
        network_window.title("TorCOIN Network Status")
        network_window.geometry("500x400")
        network_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_label = ttk.Label(network_window, text="Network Status", style='Header.TLabel')
        header_label.pack(pady=20)

        # Status frame
        status_frame = tk.Frame(network_window, bg=self.colors['bg_secondary'], relief='raised', bd=2)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Network info
        info_text = tk.Text(status_frame, wrap=tk.WORD, font=('Consolas', 10),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          relief='flat', padx=15, pady=15)
        info_text.pack(fill=tk.BOTH, expand=True)

        # Insert network information
        network_info = """TorCOIN Network Status
═══════════════════════════

🟢 Network Status: ONLINE
🌐 Connected Nodes: 1,247
⛏️  Active Miners: 892
📊 Hash Rate: 2.4 TH/s
🎯 Difficulty: 1,345,678
📈 Block Height: 1,234,567
⏰ Next Halving: Block 2,100,000

💰 Market Data:
• TOR/USD: $0.85
• 24h Change: +2.3%
• Market Cap: $85.2M
• Volume (24h): $12.4M

🔒 Security:
• Active Addresses: 45,231
• Transactions (24h): 8,942
• Average Fee: 0.0012 TOR
• Network Load: 67%

📡 Your Connection:
• Status: Connected
• Latency: 23ms
• Peers: 8
• Version: v1.1.1"""
        info_text.insert(tk.END, network_info)
        info_text.config(state='disabled')

        # Refresh button
        refresh_btn = tk.Button(network_window, text="Refresh Status",
                              bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                              font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                              padx=20, pady=10, command=lambda: self.refresh_network_info(info_text))
        refresh_btn.pack(pady=20)

    def refresh_network_info(self, text_widget):
        """Refresh the network information display."""
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)

        # Simulate updated network info
        updated_info = """TorCOIN Network Status (Updated)
═══════════════════════════

🟢 Network Status: ONLINE
🌐 Connected Nodes: 1,253
⛏️  Active Miners: 901
📊 Hash Rate: 2.5 TH/s
🎯 Difficulty: 1,356,789
📈 Block Height: 1,234,578
⏰ Next Halving: Block 2,100,000

💰 Market Data:
• TOR/USD: $0.87
• 24h Change: +3.1%
• Market Cap: $87.1M
• Volume (24h): $13.2M

🔒 Security:
• Active Addresses: 45,312
• Transactions (24h): 9,123
• Average Fee: 0.0011 TOR
• Network Load: 71%

📡 Your Connection:
• Status: Connected
• Latency: 19ms
• Peers: 9
• Version: v1.1.1

Last updated: """ + datetime.now().strftime("%H:%M:%S")

        text_widget.insert(tk.END, updated_info)
        text_widget.config(state='disabled')

    def show_documentation(self):
        """Show built-in documentation."""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("TorCOIN Documentation")
        doc_window.geometry("700x500")
        doc_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_label = ttk.Label(doc_window, text="TorCOIN Documentation", style='Header.TLabel')
        header_label.pack(pady=20)

        # Documentation content
        doc_frame = tk.Frame(doc_window, bg=self.colors['bg_secondary'], relief='raised', bd=2)
        doc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        doc_text = tk.Text(doc_frame, wrap=tk.WORD, font=('Segoe UI', 10),
                         bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                         relief='flat', padx=15, pady=15)
        doc_text.pack(fill=tk.BOTH, expand=True)

        documentation = """TorCOIN User Guide
═══════════════════════════════

Getting Started
───────────────
1. Launch TorCOIN Wallet
2. Create a new wallet or import existing
3. Backup your wallet file securely
4. Start sending and receiving TorCOIN

Wallet Management
─────────────────
• Dashboard: Overview of balance and recent transactions
• Send: Transfer TorCOIN to other addresses
• Receive: Generate addresses to receive payments
• Transactions: View complete transaction history

Security Best Practices
───────────────────────
• Never share your private keys
• Use strong passwords
• Enable wallet encryption
• Backup regularly
• Verify addresses before sending

Network Features
────────────────
• Decentralized peer-to-peer network
• Fast transactions with low fees
• Privacy-focused design
• Community governance

Troubleshooting
───────────────
• Wallet won't open: Check file permissions
• Transaction failed: Verify address and balance
• Network issues: Check internet connection
• Lost password: Recovery not possible - keep backups safe

For more help, visit: https://www.torcoin.cnet/support"""

        doc_text.insert(tk.END, documentation)
        doc_text.config(state='disabled')

        # Scrollbar
        scrollbar = tk.Scrollbar(doc_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        doc_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=doc_text.yview)

    def show_security_tips(self):
        """Show comprehensive security tips in a window."""
        tips_window = tk.Toplevel(self.root)
        tips_window.title("TorCOIN Security Tips")
        tips_window.geometry("600x500")
        tips_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_label = ttk.Label(tips_window, text="Security Best Practices", style='Header.TLabel')
        header_label.pack(pady=20)

        # Tips frame
        tips_frame = tk.Frame(tips_window, bg=self.colors['bg_secondary'], relief='raised', bd=2)
        tips_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tips_text = tk.Text(tips_frame, wrap=tk.WORD, font=('Segoe UI', 10),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          relief='flat', padx=15, pady=15)
        tips_text.pack(fill=tk.BOTH, expand=True)

        security_tips = """TorCOIN Security Best Practices
═══════════════════════════════════════════

🔐 WALLET SECURITY
──────────────────
• Never share your private keys or seed phrases
• Use strong, unique passwords (12+ characters)
• Enable wallet encryption when available
• Create regular wallet backups
• Store backups in multiple secure locations
• Use hardware wallets for large amounts

🔒 TRANSACTION SAFETY
─────────────────────
• Always verify recipient addresses
• Double-check amounts before sending
• Start with small test transactions
• Use appropriate transaction fees
• Wait for network confirmations
• Keep transaction records

🛡️ PRIVACY PROTECTION
─────────────────────
• Use new addresses for each transaction
• Avoid address reuse
• Understand privacy implications
• Consider privacy-enhancing techniques
• Be aware of blockchain analysis tools
• Use Tor network when possible

🚨 SCAM PREVENTION
──────────────────
• Only download from official sources
• Verify file signatures and hashes
• Never click suspicious links
• Be wary of "too good to be true" offers
• Report suspicious activity to community
• Use official communication channels

🔑 RECOVERY PREPARATION
───────────────────────
• Create wallet recovery phrases
• Test recovery procedures
• Store recovery info securely
• Never store on internet-connected devices
• Have multiple recovery copies
• Update recovery info when needed

🌐 NETWORK SECURITY
───────────────────
• Use secure internet connections
• Avoid public Wi-Fi for sensitive operations
• Keep wallet software updated
• Monitor for security advisories
• Use reputable antivirus software
• Enable firewall and security features

💡 GENERAL ADVICE
─────────────────
• Never invest more than you can afford to lose
• Do your own research
• Stay informed about cryptocurrency developments
• Join official community channels
• Learn continuously about security
• Trust but verify"""

        tips_text.insert(tk.END, security_tips)
        tips_text.config(state='disabled')

        # Scrollbar
        scrollbar = tk.Scrollbar(tips_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tips_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=tips_text.yview)

        # Close button
        close_btn = tk.Button(tips_window, text="Close",
                            bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                            font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                            padx=20, pady=8, command=tips_window.destroy)
        close_btn.pack(pady=20)

    def show_about(self):
        """Show detailed about information in a window."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About TorCOIN Wallet")
        about_window.geometry("500x400")
        about_window.configure(bg=self.colors['bg_primary'])
        about_window.resizable(False, False)

        # Header
        header_label = ttk.Label(about_window, text="TorCOIN Wallet", style='Title.TLabel')
        header_label.pack(pady=20)

        # Logo placeholder
        logo_frame = tk.Frame(about_window, bg=self.colors['accent_primary'], width=100, height=100)
        logo_frame.pack(pady=(0, 20))
        logo_frame.pack_propagate(False)

        logo_label = tk.Label(logo_frame, text="TOR", font=('Segoe UI', 36, 'bold'),
                            bg=self.colors['accent_primary'], fg=self.colors['text_primary'])
        logo_label.pack(expand=True)

        # Version info
        version_label = ttk.Label(about_window, text="Version 1.1.1 - Clean Black Text Edition",
                                style='Header.TLabel')
        version_label.pack(pady=(0, 10))

        # Description
        desc_text = """The official desktop wallet for TorCOIN,
the privacy-first digital currency.

Built with security and usability in mind."""
        desc_label = tk.Label(about_window, text=desc_text, bg=self.colors['bg_primary'],
                            fg=self.colors['text_primary'], font=('Segoe UI', 10),
                            justify='center')
        desc_label.pack(pady=(0, 20))

        # Features list
        features_frame = tk.Frame(about_window, bg=self.colors['bg_secondary'], relief='raised', bd=2)
        features_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        features_title = ttk.Label(features_frame, text="Key Features:", style='Header.TLabel',
                                 background=self.colors['bg_secondary'])
        features_title.pack(pady=(15, 10))

        features = [
            "• Secure wallet management",
            "• Send & receive TorCOIN",
            "• Transaction history",
            "• Address book",
            "• Price calculator",
            "• Network monitoring",
            "• Privacy-focused design",
            "• Cross-platform compatibility"
        ]

        for feature in features:
            feature_label = tk.Label(features_frame, text=feature,
                                   bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                   font=('Segoe UI', 9), anchor='w')
            feature_label.pack(fill=tk.X, padx=20, pady=2)

        # Footer
        footer_frame = tk.Frame(about_window, bg=self.colors['bg_primary'])
        footer_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        website_label = tk.Label(footer_frame, text="https://www.torcoin.cnet",
                               bg=self.colors['bg_primary'], fg=self.colors['accent_primary'],
                               font=('Segoe UI', 9, 'underline'), cursor='hand2')
        website_label.pack(pady=(0, 5))
        website_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.torcoin.cnet"))

        copyright_label = tk.Label(about_window, text="© 2024 TorCOIN Project\nPrivacy Through Innovation",
                                 bg=self.colors['bg_primary'], fg=self.colors['text_secondary'],
                                 font=('Segoe UI', 8), justify='center')
        copyright_label.pack(pady=(0, 20))

        # Close button
        close_btn = tk.Button(about_window, text="Close",
                            bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                            font=('Segoe UI', 10, 'bold'), relief='raised', bd=2,
                            padx=20, pady=8, command=about_window.destroy)
        close_btn.pack()

    # Removed 3D effect functions for clean black text theme

    def on_closing(self):
        """Handle application closing."""
        if messagebox.askyesno("Quit", "Do you want to save your wallet before quitting?"):
            self.save_wallet()
        self.root.quit()

def main():
    """Main application entry point."""
    root = tk.Tk()
    app = TorCOINWallet(root)

    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
