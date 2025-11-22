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

        title_label = ttk.Label(header_frame, text="🪙 TorCOIN Wallet", style='Title.TLabel',
                               background=self.colors['bg_secondary'])
        title_label.pack(pady=25)

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
        ttk.Button(settings_frame, text="💾 Save Settings", style='Success.TButton',
                  command=self.save_settings).pack(pady=20)

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

    def update_recent_transactions(self):
        """Update the recent transactions preview."""
        if hasattr(self, 'recent_transactions_frame'):
            # Clear existing
            for widget in self.recent_transactions_frame.winfo_children():
                widget.destroy()

            # Show last 3 transactions
            recent_txs = self.wallet_data["transactions"][-3:]

            if not recent_txs:
                ttk.Label(self.recent_transactions_frame,
                         text="No transactions yet",
                         style='Primary.TLabel').pack(pady=20)
            else:
                for tx in reversed(recent_txs):
                    tx_frame = tk.Frame(self.recent_transactions_frame, bg=self.colors['bg_tertiary'])
                    tx_frame.pack(fill=tk.X, pady=2)

                    amount_color = self.colors['success'] if tx['type'] == 'received' else self.colors['error']
                    amount_prefix = "+" if tx['type'] == 'received' else "-"

                    ttk.Label(tx_frame, text=".2f",
                             foreground=amount_color, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
                    ttk.Label(tx_frame, text=f"{tx['type'].title()} • {tx['date']}",
                             style='Primary.TLabel').pack(side=tk.RIGHT, padx=10)

    def update_transactions_display(self):
        """Update the full transactions display."""
        if hasattr(self, 'transactions_text'):
            self.transactions_text.delete(1.0, tk.END)

            if not self.wallet_data["transactions"]:
                self.transactions_text.insert(tk.END, "No transactions found.\n\nSend or receive TorCOIN to see transactions here.")
            else:
                for tx in reversed(self.wallet_data["transactions"]):
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
        # Reserve some for fees
        max_amount = max(0, self.wallet_data["balance"] - 0.01)
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
        # This would implement filtering logic
        messagebox.showinfo("Info", f"Filtering by: {filter_type}")

    def save_settings(self):
        """Save the current settings."""
        self.wallet_data["settings"]["theme"] = self.theme_var.get()
        self.wallet_data["settings"]["auto_backup"] = self.auto_backup_var.get()
        self.wallet_data["settings"]["notifications"] = self.notifications_var.get()
        self.save_wallet()
        messagebox.showinfo("Success", "Settings saved!")

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
        """Show the address book."""
        messagebox.showinfo("Address Book", "Address book feature coming soon!")

    def show_price_calculator(self):
        """Show the price calculator."""
        messagebox.showinfo("Price Calculator", "Price calculator feature coming soon!")

    def show_network_status(self):
        """Show detailed network status."""
        self.refresh_network_status()

    def show_documentation(self):
        """Show documentation."""
        webbrowser.open("https://www.torcoin.cnet/docs")

    def show_security_tips(self):
        """Show security tips."""
        tips = """
TorCOIN Security Best Practices:

🔐 Wallet Security:
• Never share your private key
• Use strong passwords
• Enable 2FA when available
• Backup your wallet regularly

🔒 Transaction Safety:
• Verify addresses before sending
• Start with small amounts
• Use appropriate fee levels
• Wait for confirmations

🛡️ Privacy Protection:
• Use new addresses for each transaction
• Avoid address reuse
• Consider using mixing services
• Be aware of blockchain analysis

🚨 Scam Prevention:
• Only download from official sources
• Verify signatures on releases
• Be suspicious of "too good to be true" offers
• Report suspicious activity
        """
        messagebox.showinfo("Security Tips", tips)

    def show_about(self):
        """Show about information."""
        about_text = """
TorCOIN Wallet v1.0

The official desktop wallet for TorCOIN,
the privacy-first digital currency.

Features:
• Secure wallet management
• Send & receive TorCOIN
• Transaction history
• Privacy-focused design
• Cross-platform compatibility

For more information, visit:
https://www.torcoin.cnet

© 2024 TorCOIN Project
Privacy Through Innovation
        """
        messagebox.showinfo("About TorCOIN Wallet", about_text)

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
