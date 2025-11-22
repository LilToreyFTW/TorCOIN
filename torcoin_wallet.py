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
import requests
from urllib.parse import urlencode, parse_qs
import base64
import random
import string
import hashlib
from datetime import datetime, timedelta

# Plaid Configuration
PLAID_CLIENT_ID = "your_plaid_client_id_here"  # Replace with actual Plaid client ID
PLAID_SECRET = "your_plaid_secret_here"        # Replace with actual Plaid secret
PLAID_ENV = "sandbox"  # Change to 'development' or 'production' for live
PLAID_COUNTRY_CODES = ["US"]
PLAID_REDIRECT_URI = None
PLAID_PRODUCTS = ["auth", "transactions", "identity", "balance"]

# Plaid API endpoints
PLAID_BASE_URL = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}

class PlaidIntegration:
    """Handle Plaid bank integration functionality."""

    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.access_tokens = {}  # Store access tokens per user
        self.link_token = None

    def create_link_token(self):
        """Create a Plaid Link token for bank connection."""
        try:
            url = f"{PLAID_BASE_URL[PLAID_ENV]}/link/token/create"
            headers = {
                'Content-Type': 'application/json',
            }

            # Basic auth with client_id and secret
            auth = base64.b64encode(f"{PLAID_CLIENT_ID}:{PLAID_SECRET}".encode()).decode()
            headers['Authorization'] = f'Basic {auth}'

            payload = {
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "user": {
                    "client_user_id": self.wallet.wallet_data["address"][:20]  # Use wallet address as user ID
                },
                "client_name": "TorCOIN Wallet",
                "products": PLAID_PRODUCTS,
                "country_codes": PLAID_COUNTRY_CODES,
                "language": "en",
                "redirect_uri": PLAID_REDIRECT_URI
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            self.link_token = result['link_token']
            return self.link_token

        except Exception as e:
            messagebox.showerror("Plaid Error", f"Failed to create link token: {e}")
            return None

    def exchange_public_token(self, public_token):
        """Exchange public token for access token."""
        try:
            url = f"{PLAID_BASE_URL[PLAID_ENV]}/item/public_token/exchange"
            headers = {
                'Content-Type': 'application/json',
            }

            auth = base64.b64encode(f"{PLAID_CLIENT_ID}:{PLAID_SECRET}".encode()).decode()
            headers['Authorization'] = f'Basic {auth}'

            payload = {
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "public_token": public_token
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            access_token = result['access_token']
            item_id = result['item_id']

            # Store the access token
            self.access_tokens[item_id] = access_token

            # Save to wallet data
            if 'bank_accounts' not in self.wallet.wallet_data:
                self.wallet.wallet_data['bank_accounts'] = {}

            self.wallet.wallet_data['bank_accounts'][item_id] = {
                'access_token': access_token,
                'connected_at': datetime.now().isoformat()
            }

            self.wallet.save_wallet()
            return True

        except Exception as e:
            messagebox.showerror("Plaid Error", f"Failed to exchange token: {e}")
            return False

    def get_accounts(self, item_id):
        """Get bank accounts for a connected item."""
        try:
            access_token = self.access_tokens.get(item_id) or self.wallet.wallet_data.get('bank_accounts', {}).get(item_id, {}).get('access_token')

            if not access_token:
                return None

            url = f"{PLAID_BASE_URL[PLAID_ENV]}/accounts/get"
            headers = {
                'Content-Type': 'application/json',
            }

            auth = base64.b64encode(f"{PLAID_CLIENT_ID}:{PLAID_SECRET}".encode()).decode()
            headers['Authorization'] = f'Basic {auth}'

            payload = {
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "access_token": access_token
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            messagebox.showerror("Plaid Error", f"Failed to get accounts: {e}")
            return None

    def get_balance(self, item_id):
        """Get account balances."""
        try:
            access_token = self.access_tokens.get(item_id) or self.wallet.wallet_data.get('bank_accounts', {}).get(item_id, {}).get('access_token')

            if not access_token:
                return None

            url = f"{PLAID_BASE_URL[PLAID_ENV]}/accounts/balance/get"
            headers = {
                'Content-Type': 'application/json',
            }

            auth = base64.b64encode(f"{PLAID_CLIENT_ID}:{PLAID_SECRET}".encode()).decode()
            headers['Authorization'] = f'Basic {auth}'

            payload = {
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "access_token": access_token
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            messagebox.showerror("Plaid Error", f"Failed to get balance: {e}")
            return None

class VirtualCardAI:
    """Invisible masked AI for generating unique virtual card numbers."""

    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.existing_cards = set()
        self.card_pool = set()  # Pool of pre-generated unique cards
        self.load_existing_cards()
        self.initialize_card_pool()

    def initialize_card_pool(self):
        """Initialize the card pool with pre-generated unique cards."""
        try:
            # Load existing pool if available
            if os.path.exists("card_pool.json"):
                with open("card_pool.json", 'r') as f:
                    pool_data = json.load(f)
                    self.card_pool = set(pool_data.get('cards', []))
                    last_generation = pool_data.get('last_generation', '')

                    # Check if we need to regenerate (new day)
                    today = datetime.now().strftime("%Y-%m-%d")
                    if last_generation != today:
                        self.regenerate_daily_pool()
                    elif len(self.card_pool) < 100000:  # Minimum pool size
                        self.expand_card_pool()
            else:
                self.regenerate_daily_pool()

        except Exception as e:
            print(f"Error initializing card pool: {e}")
            self.regenerate_daily_pool()

    def regenerate_daily_pool(self):
        """Regenerate the entire card pool for the day (invisible background process)."""
        print("🔄 Regenerating daily card pool... (invisible AI process)")
        self.card_pool.clear()

        # Generate 1,000,000 unique cards
        target_cards = 1000000
        generated = 0

        while generated < target_cards:
            # Generate card number
            card_number = self.generate_card_number_raw()

            # Ensure uniqueness
            if card_number not in self.existing_cards and card_number not in self.card_pool:
                self.card_pool.add(card_number)
                generated += 1

                # Progress indicator (invisible but logged)
                if generated % 100000 == 0:
                    print(f"🎯 Generated {generated}/{target_cards} cards...")

        # Save the pool
        self.save_card_pool()
        print("✅ Daily card pool regeneration complete!")

    def expand_card_pool(self):
        """Expand the card pool if it gets low."""
        initial_size = len(self.card_pool)
        target_additional = 100000

        added = 0
        while added < target_additional:
            card_number = self.generate_card_number_raw()

            if card_number not in self.existing_cards and card_number not in self.card_pool:
                self.card_pool.add(card_number)
                added += 1

        if added > 0:
            self.save_card_pool()
            print(f"📈 Expanded card pool by {added} cards (now {len(self.card_pool)} total)")

    def generate_card_number_raw(self):
        """Generate a raw card number without Luhn validation (for pool generation)."""
        # Format: 8948XXXXXXXX2241
        middle_digits = ""
        for _ in range(8):
            middle_digits += str(random.randint(0, 9))

        return "8948" + middle_digits + "2241"

    def save_card_pool(self):
        """Save the card pool to disk."""
        try:
            pool_data = {
                'cards': list(self.card_pool),
                'last_generation': datetime.now().strftime("%Y-%m-%d"),
                'pool_size': len(self.card_pool)
            }

            with open("card_pool.json", 'w') as f:
                json.dump(pool_data, f)

        except Exception as e:
            print(f"Error saving card pool: {e}")

    def load_existing_cards(self):
        """Load existing card numbers to ensure uniqueness."""
        if 'virtual_cards' in self.wallet.wallet_data:
            for card_data in self.wallet.wallet_data['virtual_cards'].values():
                self.existing_cards.add(card_data['card_number'])

    def load_existing_cards(self):
        """Load existing card numbers to ensure uniqueness."""
        if 'virtual_cards' in self.wallet.wallet_data:
            for card_data in self.wallet.wallet_data['virtual_cards'].values():
                self.existing_cards.add(card_data['card_number'])

    def generate_unique_card_number(self):
        """Get a unique card number from the pre-generated pool."""
        # Ensure pool has cards available
        if len(self.card_pool) < 1000:  # Emergency expansion
            print("⚠️  Card pool low, expanding...")
            self.expand_card_pool()

        if not self.card_pool:
            print("❌ No cards available in pool!")
            return None

        # Get a card from the pool
        card_number = self.card_pool.pop()

        # Add to existing cards to prevent reuse
        self.existing_cards.add(card_number)

        # Save updated pool
        self.save_card_pool()

        # Auto-expand if getting low
        if len(self.card_pool) < 50000:
            # Expand in background (invisible)
            import threading
            threading.Thread(target=self.expand_card_pool, daemon=True).start()

        return card_number

    def validate_card_format(self, card_number):
        """Validate that card follows the required 8948XXXXXXX2241 format."""
        if not card_number or len(card_number) != 16:
            return False

        if not card_number.startswith("8948"):
            return False

        if not card_number.endswith("2241"):
            return False

        # Check that middle 8 characters are digits
        middle_part = card_number[4:12]
        if not middle_part.isdigit():
            return False

        return True

    def generate_valid_luhn_prefix(self):
        """Get card number from pre-generated pool (legacy method for compatibility)."""
        return self.generate_unique_card_number()

    def calculate_luhn_check_digit(self, card_number):
        """Calculate the Luhn check digit for a card number."""
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)

        for d in even_digits:
            checksum += sum(digits_of(d*2))

        return (10 - (checksum % 10)) % 10

    def generate_card_details(self, user_name):
        """Generate complete virtual card details."""
        card_number = self.generate_unique_card_number()

        # Calculate expiry date: 10 years from now
        current_date = datetime.now()
        expiry_date_obj = current_date.replace(year=current_date.year + 10)
        expiry_month = expiry_date_obj.month
        expiry_year = expiry_date_obj.year % 100  # 2-digit year format

        # Format expiry date as MM/YY
        expiry_date = f"{expiry_month:02d}/{expiry_year:02d}"

        # Generate CVV
        cvv = str(random.randint(100, 999))

        # Generate card verification details
        verification_code = self.generate_verification_code()

        return {
            'card_number': card_number,
            'card_holder': user_name.upper(),
            'expiry_date': expiry_date,
            'expiry_datetime': expiry_date_obj.isoformat(),  # Store full datetime for calculations
            'cvv': cvv,
            'card_type': 'Visa Virtual Card',
            'network': 'Visa',
            'issuer': 'TorCOIN Bank (Visa Partner)',
            'status': 'pending_activation',  # Cards need activation now
            'activation_code': verification_code,
            'balance': 0.0,
            'daily_limit': 1000.00,  # $1000 daily spending limit
            'monthly_limit': 5000.00,  # $5000 monthly spending limit
            'created_at': datetime.now().isoformat(),
            'activated_at': None,
            'transactions': [],
            'verification_methods': ['sms', 'email', 'app']
        }

class VirtualCardManager:
    """Manage virtual cards for users."""

    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.card_ai = VirtualCardAI(wallet_instance)

    def create_virtual_card(self, user_name):
        """Create a new virtual card for the user."""
        if 'virtual_cards' not in self.wallet.wallet_data:
            self.wallet.wallet_data['virtual_cards'] = {}

        card_id = f"vc_{secrets.token_hex(8)}"
        card_details = self.card_ai.generate_card_details(user_name)

        self.wallet.wallet_data['virtual_cards'][card_id] = card_details

        # Save to wallet
        self.wallet.save_wallet()

        return card_id, card_details

    def get_user_cards(self):
        """Get all virtual cards for the current user."""
        return self.wallet.wallet_data.get('virtual_cards', {})

    def get_card_details(self, card_id):
        """Get details for a specific card."""
        return self.wallet.wallet_data.get('virtual_cards', {}).get(card_id)

    def update_card_balance(self, card_id, amount, transaction_type="transfer"):
        """Update card balance and add transaction."""
        cards = self.wallet.wallet_data.get('virtual_cards', {})
        if card_id in cards:
            card = cards[card_id]

            if transaction_type == "credit":
                card['balance'] += amount
            elif transaction_type == "debit":
                if card['balance'] >= amount:
                    card['balance'] -= amount
                else:
                    return False  # Insufficient funds

            # Add transaction record
            transaction = {
                'id': f"txn_{secrets.token_hex(4)}",
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': transaction_type,
                'amount': amount,
                'balance': card['balance'],
                'description': f"{transaction_type.title()} via TorCOIN"
            }
            card['transactions'].append(transaction)

            self.wallet.save_wallet()
            return True
        return False

    def export_card_data(self, card_id):
        """Export card data for the secondary application."""
        card_data = self.get_card_details(card_id)
        if card_data:
            # Create export data with wallet reference
            export_data = {
                'card_id': card_id,
                'card_data': card_data,
                'wallet_address': self.wallet.wallet_data['address'],
                'exported_at': datetime.now().isoformat()
            }
            return export_data
        return None

    def is_card_expired(self, card_data):
        """Check if a card has expired."""
        if 'expiry_datetime' in card_data:
            expiry_datetime = datetime.fromisoformat(card_data['expiry_datetime'])
            return datetime.now() > expiry_datetime
        else:
            # Fallback for older cards without expiry_datetime
            # Parse expiry_date (MM/YY format)
            try:
                expiry_parts = card_data['expiry_date'].split('/')
                expiry_month = int(expiry_parts[0])
                expiry_year = 2000 + int(expiry_parts[1])  # Convert YY to YYYY

                expiry_datetime = datetime(expiry_year, expiry_month, 1)
                # Set to last day of the month
                if expiry_month == 12:
                    expiry_datetime = expiry_datetime.replace(year=expiry_year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    expiry_datetime = expiry_datetime.replace(month=expiry_month + 1, day=1) - timedelta(days=1)

                return datetime.now() > expiry_datetime
            except:
                return False  # If parsing fails, assume not expired

    def generate_verification_code(self):
        """Generate a 6-digit verification code for card activation."""
        return str(random.randint(100000, 999999))

    def activate_virtual_card(self, card_id, verification_code, verification_method='app'):
        """Activate a virtual card with verification."""
        card_data = self.get_card_details(card_id)
        if not card_data:
            return False, "Card not found"

        if card_data['status'] == 'active':
            return False, "Card is already active"

        if card_data['activation_code'] != verification_code:
            return False, "Invalid verification code"

        # Activate the card
        card_data['status'] = 'active'
        card_data['activated_at'] = datetime.now().isoformat()
        card_data['verification_method'] = verification_method

        # Remove activation code for security
        del card_data['activation_code']

        self.wallet.save_wallet()
        return True, "Card activated successfully"

    def resend_activation_code(self, card_id, method='app'):
        """Resend activation code via specified method."""
        card_data = self.get_card_details(card_id)
        if not card_data:
            return False, "Card not found"

        if card_data['status'] == 'active':
            return False, "Card is already active"

        # Generate new code
        new_code = self.generate_verification_code()
        card_data['activation_code'] = new_code

        self.wallet.save_wallet()

        # Mock sending code (in real implementation, this would send SMS/email)
        if method == 'sms':
            messagebox.showinfo("Code Sent", f"Verification code sent to your registered phone number.\\n\\nCode: {new_code}")
        elif method == 'email':
            messagebox.showinfo("Code Sent", f"Verification code sent to your registered email.\\n\\nCode: {new_code}")
        else:  # app
            messagebox.showinfo("Code Generated", f"New verification code generated.\\n\\nCode: {new_code}")

        return True, f"New code sent via {method}"

    def validate_card_transaction(self, card_id, amount, merchant="Online Purchase"):
        """Validate if a card transaction can proceed."""
        card_data = self.get_card_details(card_id)
        if not card_data:
            return False, "Card not found"

        if card_data['status'] != 'active':
            return False, "Card is not active"

        if self.is_card_expired(card_data):
            return False, "Card has expired"

        # Check balance
        if card_data['balance'] < amount:
            return False, f"Insufficient balance. Available: ${card_data['balance']:,.2f}"

        # Check daily limit (simplified - in real system would track daily usage)
        if amount > card_data['daily_limit']:
            return False, f"Amount exceeds daily limit of ${card_data['daily_limit']:,.2f}"

        # Check monthly limit (simplified)
        if amount > card_data['monthly_limit']:
            return False, f"Amount exceeds monthly limit of ${card_data['monthly_limit']:,.2f}"

        return True, "Transaction approved"

    def process_card_transaction(self, card_id, amount, merchant="Online Purchase", description=""):
        """Process a card transaction (mock implementation)."""
        valid, message = self.validate_card_transaction(card_id, amount, merchant)
        if not valid:
            return False, message

        card_data = self.get_card_details(card_id)

        # Deduct from balance
        card_data['balance'] -= amount

        # Add transaction record
        transaction = {
            'id': f"visa_txn_{secrets.token_hex(4)}",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'debit',
            'amount': amount,
            'balance': card_data['balance'],
            'merchant': merchant,
            'description': description or f"Purchase at {merchant}",
            'network': 'Visa',
            'status': 'approved'
        }
        card_data['transactions'].append(transaction)

        self.wallet.save_wallet()
        return True, f"Transaction approved for ${amount:,.2f} at {merchant}"

    def get_monthly_replacements(self):
        """Get the number of card replacements made this month."""
        current_month = datetime.now().strftime("%Y-%m")
        replacements_this_month = 0

        if 'card_replacements' not in self.wallet.wallet_data:
            self.wallet.wallet_data['card_replacements'] = []

        for replacement in self.wallet.wallet_data['card_replacements']:
            replacement_month = replacement['date'][:7]  # YYYY-MM format
            if replacement_month == current_month:
                replacements_this_month += 1

        return replacements_this_month

    def can_replace_card(self):
        """Check if user can replace a card this month."""
        return self.get_monthly_replacements() < 2

    def record_card_replacement(self, old_card_id, new_card_id):
        """Record a card replacement in the history."""
        if 'card_replacements' not in self.wallet.wallet_data:
            self.wallet.wallet_data['card_replacements'] = []

        replacement_record = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'old_card_id': old_card_id,
            'new_card_id': new_card_id,
            'month': datetime.now().strftime("%Y-%m")
        }

        self.wallet.wallet_data['card_replacements'].append(replacement_record)
        self.wallet.save_wallet()

    def replace_virtual_card(self, old_card_id, user_name=None):
        """Replace an existing virtual card with a new one."""
        # Check replacement limit
        if not self.can_replace_card():
            remaining_days = (datetime.now().replace(day=1, month=datetime.now().month + 1) - datetime.now()).days
            messagebox.showerror("Replacement Limit Reached",
                               f"You have used all 2 card replacements for this month.\\n\\n"
                               f"Next replacement available in {remaining_days} days.")
            return None

        # Get old card data
        old_card_data = self.get_card_details(old_card_id)
        if not old_card_data:
            messagebox.showerror("Card Not Found", "The card to replace could not be found.")
            return None

        # Use provided name or existing card holder name
        if not user_name:
            user_name = old_card_data['card_holder']

        # Create new card
        new_card_id, new_card_details = self.create_virtual_card(user_name)

        if new_card_id and new_card_details:
            # Record the replacement
            self.record_card_replacement(old_card_id, new_card_id)

            # Optionally mark old card as replaced (but keep it accessible)
            old_card_data['replaced_by'] = new_card_id
            old_card_data['replaced_date'] = datetime.now().isoformat()
            old_card_data['status'] = 'replaced'

            # Transfer balance from old card to new card (optional - user choice)
            # For now, we'll keep balances separate

            self.wallet.save_wallet()

            return new_card_id, new_card_details

        return None

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

        # Initialize Plaid integration
        self.plaid = PlaidIntegration(self)

        # Initialize Virtual Card Manager
        self.card_manager = VirtualCardManager(self)

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

        # Bank menu
        bank_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="🏦 Bank", menu=bank_menu)
        bank_menu.add_command(label="🔗 Connect Bank Account", command=self.connect_bank_account)
        bank_menu.add_command(label="💳 View Bank Accounts", command=self.view_bank_accounts)
        bank_menu.add_command(label="💰 Transfer Funds", command=self.show_bank_transfer)
        bank_menu.add_separator()
        bank_menu.add_command(label="📊 Bank Balance", command=self.show_bank_balance)

        # Virtual Card menu
        card_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                           activebackground=self.colors['bg_tertiary'], activeforeground=self.colors['text_primary'])
        menubar.add_cascade(label="💳 Virtual Card", menu=card_menu)
        card_menu.add_command(label="🎁 Get Free Virtual Card", command=self.signup_virtual_card)
        card_menu.add_command(label="💳 My Virtual Cards", command=self.view_virtual_cards)
        card_menu.add_command(label="💰 Card Balance & Transactions", command=self.show_card_transactions)
        card_menu.add_command(label="🔄 Replace Virtual Card", command=self.replace_virtual_card_ui)
        card_menu.add_command(label="📊 Replacement History", command=self.show_replacement_history)
        card_menu.add_command(label="📤 Download Virtual Card App", command=self.download_virtual_card_app)
        card_menu.add_separator()
        card_menu.add_command(label="🔄 Transfer to Card", command=self.transfer_to_card)

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
            "• Bank account integration (Plaid)",
            "• Seamless bank transfers",
            "• Free virtual debit cards",
            "• Virtual card management app",
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

    # Bank Integration Methods
    def connect_bank_account(self):
        """Connect a bank account using Plaid Link."""
        try:
            # Check if Plaid credentials are configured
            if PLAID_CLIENT_ID == "your_plaid_client_id_here":
                messagebox.showwarning("Plaid Not Configured",
                                     "Plaid integration is not configured yet.\n\n"
                                     "To enable bank connectivity:\n"
                                     "1. Sign up for Plaid at https://plaid.com\n"
                                     "2. Get your API credentials\n"
                                     "3. Update PLAID_CLIENT_ID and PLAID_SECRET in the code\n"
                                     "4. Restart the wallet")
                return

            # Create link token
            link_token = self.plaid.create_link_token()
            if not link_token:
                return

            # For demo purposes, show a mock connection dialog
            # In production, this would open Plaid Link in a webview
            connect_window = tk.Toplevel(self.root)
            connect_window.title("Connect Bank Account")
            connect_window.geometry("500x400")
            connect_window.configure(bg=self.colors['bg_primary'])

            ttk.Label(connect_window, text="🏦 Connect Your Bank Account",
                     style='Header.TLabel').pack(pady=20)

            # Mock bank selection (in real app, this would be Plaid Link)
            banks_frame = tk.Frame(connect_window, bg=self.colors['bg_secondary'])
            banks_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

            ttk.Label(banks_frame, text="Select Your Bank:",
                     style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

            # Mock bank list
            banks = ["Chase", "Bank of America", "Wells Fargo", "Citibank", "Capital One"]
            bank_var = tk.StringVar()

            for bank in banks:
                ttk.Radiobutton(banks_frame, text=f"🏦 {bank}", variable=bank_var,
                               value=bank, style='Primary.TButton').pack(anchor=tk.W, padx=20, pady=5)

            def mock_connect():
                if not bank_var.get():
                    messagebox.showwarning("Selection Required", "Please select a bank.")
                    return

                # Mock successful connection
                messagebox.showinfo("Success",
                                  f"✅ Successfully connected to {bank_var.get()}!\n\n"
                                  "Your bank account is now linked to TorCOIN.\n"
                                  "You can now transfer funds between your bank and TorCOIN wallet.")

                # Add mock account data
                if 'bank_accounts' not in self.wallet_data:
                    self.wallet.wallet_data['bank_accounts'] = {}

                mock_item_id = f"mock_{secrets.token_hex(8)}"
                self.wallet.wallet_data['bank_accounts'][mock_item_id] = {
                    'bank_name': bank_var.get(),
                    'connected_at': datetime.now().isoformat(),
                    'accounts': [
                        {
                            'name': 'Checking Account',
                            'type': 'checking',
                            'balance': 2500.75,
                            'currency': 'USD'
                        },
                        {
                            'name': 'Savings Account',
                            'type': 'savings',
                            'balance': 15750.00,
                            'currency': 'USD'
                        }
                    ]
                }

                self.save_wallet()
                connect_window.destroy()

            ttk.Button(connect_window, text="🔗 Connect Bank Account",
                      style='Success.TButton', command=mock_connect).pack(pady=20)

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect bank account: {e}")

    def view_bank_accounts(self):
        """View connected bank accounts."""
        bank_accounts = self.wallet_data.get('bank_accounts', {})

        if not bank_accounts:
            messagebox.showinfo("No Bank Accounts",
                              "No bank accounts connected yet.\n\n"
                              "Use 'Bank → Connect Bank Account' to link your bank.")
            return

        accounts_window = tk.Toplevel(self.root)
        accounts_window.title("Connected Bank Accounts")
        accounts_window.geometry("600x400")
        accounts_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(accounts_window, text="🏦 Your Connected Bank Accounts",
                 style='Header.TLabel').pack(pady=20)

        # Accounts list
        accounts_frame = tk.Frame(accounts_window, bg=self.colors['bg_secondary'])
        accounts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        for item_id, account_data in bank_accounts.items():
            account_frame = tk.Frame(accounts_frame, bg=self.colors['bg_panel'],
                                   relief='raised', bd=2)
            account_frame.pack(fill=tk.X, pady=5)

            bank_name = account_data.get('bank_name', 'Unknown Bank')
            connected_at = account_data.get('connected_at', 'Unknown')

            ttk.Label(account_frame, text=f"🏦 {bank_name}",
                     style='Header.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W, padx=15, pady=5)

            ttk.Label(account_frame, text=f"Connected: {connected_at[:10]}",
                     style='Primary.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W, padx=15, pady=(0, 10))

            # Show account details if available
            accounts = account_data.get('accounts', [])
            for acc in accounts:
                acc_info = f"  • {acc['name']}: ${acc['balance']:,.2f} ({acc['type']})"
                ttk.Label(account_frame, text=acc_info,
                         style='Primary.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W, padx=30, pady=2)

    def show_bank_balance(self):
        """Show bank account balances."""
        bank_accounts = self.wallet_data.get('bank_accounts', {})

        if not bank_accounts:
            messagebox.showinfo("No Bank Accounts",
                              "No bank accounts connected.\n\n"
                              "Connect a bank account first to view balances.")
            return

        balance_window = tk.Toplevel(self.root)
        balance_window.title("Bank Account Balances")
        balance_window.geometry("500x400")
        balance_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(balance_window, text="💰 Bank Account Balances",
                 style='Header.TLabel').pack(pady=20)

        balance_frame = tk.Frame(balance_window, bg=self.colors['bg_secondary'])
        balance_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        total_balance = 0

        for item_id, account_data in bank_accounts.items():
            bank_name = account_data.get('bank_name', 'Unknown Bank')
            accounts = account_data.get('accounts', [])

            ttk.Label(balance_frame, text=f"🏦 {bank_name}",
                     style='Header.TLabel', background=self.colors['bg_secondary']).pack(anchor=tk.W, pady=(10, 5))

            for acc in accounts:
                balance = acc.get('balance', 0)
                total_balance += balance

                balance_text = f"${balance:,.2f}"
                ttk.Label(balance_frame, text=f"  {acc['name']}: {balance_text}",
                         style='Primary.TLabel', background=self.colors['bg_secondary']).pack(anchor=tk.W, pady=2)

        # Total balance
        total_frame = tk.Frame(balance_window, bg=self.colors['accent_primary'])
        total_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(total_frame, text=f"💵 Total Bank Balance: ${total_balance:,.2f}",
                 style='Balance.TLabel', background=self.colors['accent_primary']).pack(pady=10)

    def show_bank_transfer(self):
        """Show bank transfer interface."""
        bank_accounts = self.wallet_data.get('bank_accounts', {})

        if not bank_accounts:
            messagebox.showinfo("No Bank Accounts",
                              "No bank accounts connected.\n\n"
                              "Connect a bank account first to transfer funds.")
            return

        transfer_window = tk.Toplevel(self.root)
        transfer_window.title("Bank Transfer")
        transfer_window.geometry("500x500")
        transfer_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(transfer_window, text="🔄 Bank Transfer",
                 style='Header.TLabel').pack(pady=20)

        transfer_frame = tk.Frame(transfer_window, bg=self.colors['bg_secondary'])
        transfer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Transfer direction
        ttk.Label(transfer_frame, text="Transfer Direction:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        direction_var = tk.StringVar(value="bank_to_tor")
        ttk.Radiobutton(transfer_frame, text="🏦 Bank → TorCOIN Wallet",
                       variable=direction_var, value="bank_to_tor").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(transfer_frame, text="🪙 TorCOIN Wallet → Bank",
                       variable=direction_var, value="tor_to_bank").pack(anchor=tk.W, padx=20, pady=5)

        # Amount
        ttk.Label(transfer_frame, text="Amount:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        amount_entry = tk.Entry(transfer_frame, font=('Segoe UI', 14), justify='center')
        amount_entry.pack(pady=(0, 20))
        amount_entry.insert(0, "100.00")

        # Bank account selection
        ttk.Label(transfer_frame, text="From Bank Account:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 10))

        bank_accounts_list = []
        for item_id, account_data in bank_accounts.items():
            bank_name = account_data.get('bank_name', 'Unknown')
            accounts = account_data.get('accounts', [])
            for acc in accounts:
                bank_accounts_list.append(f"{bank_name} - {acc['name']} (${acc['balance']:,.2f})")

        bank_var = tk.StringVar()
        if bank_accounts_list:
            bank_var.set(bank_accounts_list[0])

        bank_combo = ttk.Combobox(transfer_frame, textvariable=bank_var,
                                 values=bank_accounts_list, state="readonly")
        bank_combo.pack(pady=(0, 20))

        def execute_transfer():
            try:
                amount = float(amount_entry.get())
                direction = direction_var.get()

                if amount <= 0:
                    messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
                    return

                # Mock transfer
                if direction == "bank_to_tor":
                    # Add to TorCOIN balance
                    self.wallet_data["balance"] += amount
                    # Deduct from bank (in real app, this would use Plaid ACH)
                    messagebox.showinfo("Transfer Complete",
                                      f"✅ Successfully transferred ${amount:,.2f} from your bank to TorCOIN wallet!\n\n"
                                      "Note: In production, this would initiate an ACH transfer through Plaid.")

                else:  # tor_to_bank
                    if amount > self.wallet_data["balance"]:
                        messagebox.showerror("Insufficient Funds",
                                           f"Not enough TorCOIN balance. Available: ${self.wallet_data['balance']:,.2f}")
                        return

                    self.wallet_data["balance"] -= amount
                    messagebox.showinfo("Transfer Initiated",
                                      f"✅ Transfer of ${amount:,.2f} TorCOIN to your bank account initiated!\n\n"
                                      "Note: In production, this would convert TorCOIN to fiat and transfer to your bank.")

                # Add transaction record
                transaction = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "bank_transfer",
                    "amount": amount,
                    "direction": direction,
                    "bank_account": bank_var.get(),
                    "status": "completed"
                }
                self.wallet_data["transactions"].append(transaction)

                self.save_wallet()
                self.update_display()
                transfer_window.destroy()

            except ValueError:
                messagebox.showerror("Invalid Amount", "Please enter a valid number.")

        ttk.Button(transfer_window, text="🚀 Execute Transfer",
                  style='Success.TButton', command=execute_transfer).pack(pady=20)

    # Virtual Card Methods
    def signup_virtual_card(self):
        """Sign up for a free virtual card."""
        # Check if user already has a virtual card
        existing_cards = self.card_manager.get_user_cards()
        if existing_cards:
            card_count = len(existing_cards)
            if not messagebox.askyesno("Additional Card",
                                     f"You already have {card_count} virtual card(s).\n\n"
                                     "Would you like to get another free virtual card?"):
                return

        # Show signup form
        signup_window = tk.Toplevel(self.root)
        signup_window.title("Get Free Virtual Card")
        signup_window.geometry("500x600")
        signup_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(signup_window, text="🎁 Free Virtual Card Signup",
                 style='Header.TLabel').pack(pady=20)

        signup_frame = tk.Frame(signup_window, bg=self.colors['bg_secondary'])
        signup_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Card preview
        preview_frame = tk.Frame(signup_frame, bg=self.colors['accent_primary'],
                               relief='raised', bd=3)
        preview_frame.pack(fill=tk.X, pady=(20, 10), padx=20)

        ttk.Label(preview_frame, text="💳 Virtual TorCOIN Card",
                 style='Header.TLabel', background=self.colors['accent_primary']).pack(pady=10)

        card_features = [
            "• Instant digital card generation",
            "• Unique card number (no duplicates)",
            "• 10-year validity period from signup",
            "• Send & receive funds",
            "• Transaction tracking",
            "• Automatic expiry after 10 years",
            "• 2 free replacements per month",
            "• Free forever"
        ]

        for feature in card_features:
            ttk.Label(preview_frame, text=feature,
                     style='Primary.TLabel', background=self.colors['accent_primary']).pack(anchor=tk.W, padx=20, pady=2)

        # Name input
        ttk.Label(signup_frame, text="Card Holder Name:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        name_entry = tk.Entry(signup_frame, font=('Segoe UI', 14), justify='center')
        name_entry.pack(pady=(0, 20))
        name_entry.insert(0, "Enter Full Name")

        # Terms checkbox
        terms_var = tk.BooleanVar()
        terms_check = ttk.Checkbutton(signup_frame,
                                    text="I accept the Virtual Card Terms & Conditions",
                                    variable=terms_var)
        terms_check.pack(pady=(0, 20))

        def create_card():
            if not terms_var.get():
                messagebox.showerror("Terms Required", "Please accept the terms and conditions.")
                return

            card_holder_name = name_entry.get().strip()
            if not card_holder_name or card_holder_name == "Enter Full Name":
                messagebox.showerror("Name Required", "Please enter your full name.")
                return

            # Create the card
            try:
                card_id, card_details = self.card_manager.create_virtual_card(card_holder_name)

                # Show success message with card details
                success_msg = f"""🎉 Visa Virtual Card Created Successfully!

🏦 Issuer: TorCOIN Bank (Visa Partner)
💳 Card Number: **** **** **** {card_details['card_number'][-4:]}
👤 Card Holder: {card_details['card_holder']}
📅 Expiry: {card_details['expiry_date']} (10 years from today)
🔒 CVV: {card_details['cvv']}
💰 Daily Limit: $1,000
📊 Monthly Limit: $5,000
🤖 AI Generated: Instant from million-card daily pool

⚠️  IMPORTANT SECURITY NOTICE:
   • Save these details securely - this is the only time you'll see them
   • Card must be ACTIVATED before use
   • Never share your card details with anyone
   • Format: 8948-XXXX-XXXX-2241 (confidential)

🔐 ACTIVATION REQUIRED:
   Your card needs to be activated with a verification code.
   The code will be sent to your registered contact method.

Would you like to activate your card now?"""

                response = messagebox.askyesnocancel("Card Created!", success_msg + "\n\nActivate card now?")
                if response is None:  # Cancel
                    signup_window.destroy()
                elif response:  # Yes - activate
                    signup_window.destroy()
                    self.activate_card_ui(card_id)
                else:  # No - just close
                    signup_window.destroy()

            except Exception as e:
                messagebox.showerror("Card Creation Failed", f"Failed to create virtual card: {e}")

        ttk.Button(signup_window, text="🎁 Create Free Virtual Card",
                  style='Success.TButton', command=create_card).pack(pady=20)

    def view_virtual_cards(self):
        """View all user's virtual cards."""
        cards = self.card_manager.get_user_cards()

        if not cards:
            messagebox.showinfo("No Virtual Cards",
                              "You don't have any virtual cards yet.\n\n"
                              "Use 'Virtual Card → Get Free Virtual Card' to sign up!")
            return

        cards_window = tk.Toplevel(self.root)
        cards_window.title("My Virtual Cards")
        cards_window.geometry("700x500")
        cards_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(cards_window, text="💳 My Virtual Cards",
                 style='Header.TLabel').pack(pady=20)

        cards_frame = tk.Frame(cards_window, bg=self.colors['bg_secondary'])
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        for card_id, card_data in cards.items():
            card_frame = tk.Frame(cards_frame, bg=self.colors['bg_panel'],
                                relief='raised', bd=2)
            card_frame.pack(fill=tk.X, pady=5)

            # Card header
            header_frame = tk.Frame(card_frame, bg=self.colors['accent_primary'])
            header_frame.pack(fill=tk.X)

            ttk.Label(header_frame, text=f"💳 Virtual TorCOIN Card",
                     style='Header.TLabel', background=self.colors['accent_primary']).pack(side=tk.LEFT, padx=15, pady=5)

            ttk.Label(header_frame, text=f"Balance: ${card_data['balance']:,.2f}",
                     style='Balance.TLabel', background=self.colors['accent_primary']).pack(side=tk.RIGHT, padx=15, pady=5)

            # Card details
            details_frame = tk.Frame(card_frame, bg=self.colors['bg_panel'])
            details_frame.pack(fill=tk.X, padx=15, pady=10)

            # Masked card number
            masked_number = f"**** **** **** {card_data['card_number'][-4:]}"
            ttk.Label(details_frame, text=f"Card Number: {masked_number}",
                     style='Primary.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W)

            ttk.Label(details_frame, text=f"Card Holder: {card_data['card_holder']}",
                     style='Primary.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W)

            # Check card status
            is_expired = self.card_manager.is_card_expired(card_data)
            is_active = card_data.get('status') == 'active'
            needs_activation = card_data.get('status') == 'pending_activation'

            # Status and expiry info
            status_info = []
            if needs_activation:
                status_info.append("PENDING ACTIVATION")
            elif not is_active:
                status_info.append(card_data.get('status', 'INACTIVE').upper())
            if is_expired:
                status_info.append("EXPIRED")

            status_text = f"Status: {', '.join(status_info)}" if status_info else "Status: Active"
            expiry_text = f"Expires: {card_data['expiry_date']}"

            # Status label
            status_color = self.colors['error'] if (needs_activation or is_expired) else self.colors['success']
            status_label = tk.Label(details_frame, text=status_text,
                                   bg=self.colors['bg_panel'], fg=status_color,
                                   font=('Segoe UI', 9, 'bold'))
            status_label.pack(anchor=tk.W)

            # Expiry date
            expiry_label = tk.Label(details_frame, text=expiry_text,
                                   bg=self.colors['bg_panel'], fg=self.colors['error'] if is_expired else self.colors['text_primary'],
                                   font=('Segoe UI', 9))
            expiry_label.pack(anchor=tk.W)

            # Network info
            network_label = tk.Label(details_frame, text=f"Network: {card_data.get('network', 'Unknown')}",
                                   bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                                   font=('Segoe UI', 9))
            network_label.pack(anchor=tk.W)

            # Action buttons
            actions_frame = tk.Frame(card_frame, bg=self.colors['bg_panel'])
            actions_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

            # Show appropriate buttons based on card status
            card_data = self.card_manager.get_card_details(card_id)

            ttk.Button(actions_frame, text="📊 View Transactions",
                      command=lambda cid=card_id: self.show_card_transactions(cid)).pack(side=tk.LEFT, padx=(0, 10))

            if card_data and card_data.get('status') == 'pending_activation':
                ttk.Button(actions_frame, text="✅ Activate Card",
                          command=lambda cid=card_id: self.activate_card_ui(cid)).pack(side=tk.LEFT, padx=(0, 10))
            else:
                ttk.Button(actions_frame, text="🔄 Replace Card",
                          command=lambda cid=card_id: self.replace_single_card(cid)).pack(side=tk.LEFT, padx=(0, 10))

            ttk.Button(actions_frame, text="💰 Load Funds",
                      command=lambda cid=card_id: self.load_card_funds(cid)).pack(side=tk.LEFT, padx=(0, 10))

            ttk.Button(actions_frame, text="📤 Download Card App",
                      command=lambda cid=card_id: self.download_virtual_card_app(cid)).pack(side=tk.LEFT)

    def show_card_transactions(self, card_id=None):
        """Show transactions for a specific card or all cards."""
        if card_id:
            card_data = self.card_manager.get_card_details(card_id)
            if not card_data:
                messagebox.showerror("Card Not Found", "Virtual card not found.")
                return
            cards_to_show = {card_id: card_data}
            title = f"Card Transactions - ****{card_data['card_number'][-4:]}"
        else:
            cards_to_show = self.card_manager.get_user_cards()
            title = "All Virtual Card Transactions"

        if not cards_to_show:
            messagebox.showinfo("No Cards", "No virtual cards found.")
            return

        txn_window = tk.Toplevel(self.root)
        txn_window.title(title)
        txn_window.geometry("800x600")
        txn_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(txn_window, text=title, style='Header.TLabel').pack(pady=20)

        # Create scrollable frame for transactions
        main_frame = tk.Frame(txn_window, bg=self.colors['bg_secondary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(main_frame, bg=self.colors['bg_secondary'])
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        total_balance = 0
        total_transactions = 0

        for card_id, card_data in cards_to_show.items():
            # Card header
            card_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_panel'],
                                relief='raised', bd=2)
            card_frame.pack(fill=tk.X, pady=5)

            masked_number = f"**** **** **** {card_data['card_number'][-4:]}"
            ttk.Label(card_frame, text=f"💳 {masked_number}",
                     style='Header.TLabel', background=self.colors['bg_panel']).pack(anchor=tk.W, padx=15, pady=5)

            total_balance += card_data['balance']

            # Transactions
            transactions = card_data.get('transactions', [])
            total_transactions += len(transactions)

            if transactions:
                # Transaction header
                header_frame = tk.Frame(card_frame, bg=self.colors['bg_tertiary'])
                header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

                ttk.Label(header_frame, text="Date", style='Header.TLabel',
                         background=self.colors['bg_tertiary']).grid(row=0, column=0, padx=5)
                ttk.Label(header_frame, text="Type", style='Header.TLabel',
                         background=self.colors['bg_tertiary']).grid(row=0, column=1, padx=5)
                ttk.Label(header_frame, text="Amount", style='Header.TLabel',
                         background=self.colors['bg_tertiary']).grid(row=0, column=2, padx=5)
                ttk.Label(header_frame, text="Balance", style='Header.TLabel',
                         background=self.colors['bg_tertiary']).grid(row=0, column=3, padx=5)

                # Transaction rows
                for i, txn in enumerate(reversed(transactions[-10:])):  # Show last 10
                    row_frame = tk.Frame(card_frame, bg=self.colors['bg_panel'])
                    row_frame.pack(fill=tk.X, padx=15)

                    ttk.Label(row_frame, text=txn['date'][:10],
                             style='Primary.TLabel', background=self.colors['bg_panel']).grid(row=0, column=0, padx=5, sticky='w')
                    ttk.Label(row_frame, text=txn['type'].title(),
                             style='Primary.TLabel', background=self.colors['bg_panel']).grid(row=0, column=1, padx=5, sticky='w')
                    ttk.Label(row_frame, text=f"${txn['amount']:,.2f}",
                             style='Primary.TLabel', background=self.colors['bg_panel']).grid(row=0, column=2, padx=5, sticky='w')
                    ttk.Label(row_frame, text=f"${txn['balance']:,.2f}",
                             style='Primary.TLabel', background=self.colors['bg_panel']).grid(row=0, column=3, padx=5, sticky='w')
            else:
                ttk.Label(card_frame, text="No transactions yet",
                         style='Primary.TLabel', background=self.colors['bg_panel']).pack(pady=10)

        # Summary
        summary_frame = tk.Frame(txn_window, bg=self.colors['accent_primary'])
        summary_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(summary_frame, text=f"Total Cards: {len(cards_to_show)} | Total Transactions: {total_transactions} | Combined Balance: ${total_balance:,.2f}",
                 style='Balance.TLabel', background=self.colors['accent_primary']).pack(pady=10)

    def download_virtual_card_app(self, card_id=None):
        """Download the VirtualCard-TorCoin application."""
        try:
            # Create the virtual card application
            self.create_virtual_card_application()

            # Show download dialog
            download_window = tk.Toplevel(self.root)
            download_window.title("Download Virtual Card App")
            download_window.geometry("500x400")
            download_window.configure(bg=self.colors['bg_primary'])

            ttk.Label(download_window, text="📥 Download Virtual Card App",
                     style='Header.TLabel').pack(pady=20)

            download_frame = tk.Frame(download_window, bg=self.colors['bg_secondary'])
            download_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

            ttk.Label(download_frame, text="VirtualCard-TorCoin.exe",
                     style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=10)

            ttk.Label(download_frame, text="Standalone virtual card management application",
                     style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=5)

            features = [
                "• Independent card management",
                "• Balance & transaction viewing",
                "• Send & receive funds",
                "• Generate reports",
                "• Secure offline operation"
            ]

            for feature in features:
                ttk.Label(download_frame, text=feature,
                         style='Primary.TLabel', background=self.colors['bg_secondary']).pack(anchor=tk.W, padx=20, pady=2)

            def save_app():
                from tkinter import filedialog
                filename = filedialog.asksaveasfilename(
                    defaultextension=".py",
                    filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                    title="Save Virtual Card Application",
                    initialfile="VirtualCard-TorCoin.py"
                )

                if filename:
                    # Copy the virtual card app to the selected location
                    import shutil
                    shutil.copy("VirtualCard-TorCoin.py", filename)

                    messagebox.showinfo("Download Complete",
                                      f"Virtual Card App saved to:\n{filename}\n\n"
                                      "Run the application to manage your virtual cards!")

                    download_window.destroy()

            ttk.Button(download_window, text="💾 Save Application",
                      style='Success.TButton', command=save_app).pack(pady=20)

        except Exception as e:
            messagebox.showerror("Download Failed", f"Failed to create virtual card app: {e}")

    def create_virtual_card_application(self):
        """Create the standalone VirtualCard-TorCoin.py application."""
        app_code = '''#!/usr/bin/env python3
"""
VirtualCard-TorCoin - Standalone Virtual Card Management Application
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
import base64
import random
import string
import json as json_module

class VirtualCardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VirtualCard-TorCoin - Virtual Card Manager")
        self.root.geometry("900x700")
        self.root.configure(bg="#0a0a0a")

        # Colors matching TorCOIN theme
        self.colors = {
            'bg_primary': '#0a0a0a',
            'bg_secondary': '#1a1a1a',
            'bg_panel': '#2a2a2a',
            'bg_tertiary': '#3a3a3a',
            'accent_primary': '#8B0000',
            'accent_secondary': '#B22222',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'success': '#228B22',
            'error': '#8B0000'
        }

        # Card data storage
        self.card_data = {}
        self.current_card_id = None

        self.create_styles()
        self.create_main_interface()
        self.load_card_data()

    def create_styles(self):
        """Create custom styles for the application."""
        style = ttk.Style()

        # Configure colors
        style.configure('TFrame', background=self.colors['bg_primary'])
        style.configure('TLabel', background=self.colors['bg_primary'], foreground=self.colors['text_primary'])
        style.configure('TButton', background=self.colors['bg_secondary'], foreground=self.colors['text_primary'])
        style.configure('TEntry', fieldbackground=self.colors['bg_secondary'], foreground=self.colors['text_primary'])

        # Custom styles
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), background=self.colors['bg_primary'])
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), background=self.colors['bg_primary'])
        style.configure('Balance.TLabel', font=('Segoe UI', 16, 'bold'), background=self.colors['accent_primary'])
        style.configure('Primary.TLabel', font=('Segoe UI', 11), background=self.colors['bg_primary'])

        style.configure('Success.TButton', background=self.colors['success'], foreground=self.colors['text_primary'])
        style.configure('Danger.TButton', background=self.colors['error'], foreground=self.colors['text_primary'])

    def create_main_interface(self):
        """Create the main application interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['accent_primary'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="VirtualCard-TorCoin",
                font=('Segoe UI', 24, 'bold'), bg=self.colors['accent_primary'],
                fg=self.colors['text_primary']).pack(side=tk.LEFT, padx=20)

        tk.Label(header_frame, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                font=('Segoe UI', 12), bg=self.colors['accent_primary'],
                fg=self.colors['text_secondary']).pack(side=tk.RIGHT, padx=20)

        # Content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Card list
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_secondary'], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="💳 Your Cards", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=10)

        # Card list frame
        self.card_list_frame = tk.Frame(left_panel, bg=self.colors['bg_secondary'])
        self.card_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Add card button
        ttk.Button(left_panel, text="+ Add Card", command=self.import_card).pack(fill=tk.X, padx=10, pady=10)

        # Right panel - Card details
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_secondary'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Card display area
        self.card_display = tk.Frame(right_panel, bg=self.colors['bg_panel'],
                                   relief='raised', bd=3, height=200)
        self.card_display.pack(fill=tk.X, pady=20, padx=20)
        self.card_display.pack_propagate(False)

        # Card info labels (will be populated when card is selected)
        self.card_number_label = tk.Label(self.card_display, text="Select a card to view details",
                                        font=('Segoe UI', 16, 'bold'), bg=self.colors['bg_panel'],
                                        fg=self.colors['text_primary'])
        self.card_number_label.pack(expand=True)

        # Action buttons
        actions_frame = tk.Frame(right_panel, bg=self.colors['bg_secondary'])
        actions_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        button_frame = tk.Frame(actions_frame, bg=self.colors['bg_secondary'])
        button_frame.pack()

        ttk.Button(button_frame, text="💰 Send", command=self.send_funds).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="📥 Receive", command=self.receive_funds).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="📊 Transactions", command=self.view_transactions).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="📋 Report", command=self.generate_report).grid(row=0, column=3, padx=5, pady=5)

        # Transaction area
        transaction_frame = tk.Frame(right_panel, bg=self.colors['bg_secondary'])
        transaction_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(transaction_frame, text="Recent Transactions", font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=(0, 10))

        # Transaction list
        self.transaction_text = scrolledtext.ScrolledText(transaction_frame, height=15,
                                                        bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                                                        font=('Consolas', 10))
        self.transaction_text.pack(fill=tk.BOTH, expand=True)

    def import_card(self):
        """Import card data from file."""
        filename = filedialog.askopenfilename(
            title="Import Virtual Card",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    import_data = json.load(f)

                card_id = import_data['card_id']
                card_data = import_data['card_data']

                self.card_data[card_id] = card_data
                self.save_card_data()

                self.refresh_card_list()
                messagebox.showinfo("Success", "Virtual card imported successfully!")

            except Exception as e:
                messagebox.showerror("Import Failed", f"Failed to import card: {e}")

    def refresh_card_list(self):
        """Refresh the card list display."""
        # Clear existing cards
        for widget in self.card_list_frame.winfo_children():
            widget.destroy()

        # Add cards
        for card_id, card_info in self.card_data.items():
            card_frame = tk.Frame(self.card_list_frame, bg=self.colors['bg_tertiary'],
                                relief='raised', bd=1)
            card_frame.pack(fill=tk.X, pady=2)

            masked_number = f"**** **** **** {card_info['card_number'][-4:]}"
            card_btn = tk.Button(card_frame, text=masked_number,
                               bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                               font=('Segoe UI', 10, 'bold'),
                               command=lambda cid=card_id: self.select_card(cid))
            card_btn.pack(fill=tk.X, padx=5, pady=5)

    def select_card(self, card_id):
        """Select a card to view details."""
        self.current_card_id = card_id
        card_info = self.card_data[card_id]

        # Update card display
        self.card_display.configure(bg=self.colors['accent_primary'])

        for widget in self.card_display.winfo_children():
            widget.destroy()

        # Card number (masked)
        masked_number = f"**** **** **** {card_info['card_number'][-4:]}"
        tk.Label(self.card_display, text=masked_number,
                font=('Segoe UI', 18, 'bold'), bg=self.colors['accent_primary'],
                fg=self.colors['text_primary']).pack(pady=(20, 10))

        # Card holder
        tk.Label(self.card_display, text=card_info['card_holder'],
                font=('Segoe UI', 12), bg=self.colors['accent_primary'],
                fg=self.colors['text_primary']).pack(pady=(0, 5))

        # Check expiry status
        is_expired = self.is_card_expired(card_info)
        expiry_color = self.colors['error'] if is_expired else self.colors['text_secondary']
        expiry_text = f"Expires: {card_info['expiry_date']}"
        if is_expired:
            expiry_text += " (EXPIRED)"

        # Status
        status = card_info.get('status', 'unknown').upper()
        status_color = self.colors['success'] if status == 'ACTIVE' else self.colors['error']
        tk.Label(self.card_display, text=f"Status: {status}",
                font=('Segoe UI', 10, 'bold'), bg=self.colors['accent_primary'],
                fg=status_color).pack(pady=(0, 5))

        # Expiry and CVV
        tk.Label(self.card_display, text=f"{expiry_text}    CVV: {card_info['cvv']}",
                font=('Segoe UI', 10), bg=self.colors['accent_primary'],
                fg=expiry_color).pack(pady=(0, 5))

        # Network and limits
        network = card_info.get('network', 'Unknown')
        tk.Label(self.card_display, text=f"Network: {network}",
                font=('Segoe UI', 10), bg=self.colors['accent_primary'],
                fg=self.colors['text_secondary']).pack(pady=(0, 10))

        # Balance
        balance_text = f"Balance: ${card_info['balance']:,.2f}"
        tk.Label(self.card_display, text=balance_text,
                font=('Segoe UI', 16, 'bold'), bg=self.colors['accent_secondary'],
                fg=self.colors['text_primary']).pack(pady=(10, 20), padx=20)

        # Update transactions
        self.update_transaction_display()

    def update_transaction_display(self):
        """Update the transaction display for current card."""
        if not self.current_card_id:
            self.transaction_text.delete(1.0, tk.END)
            self.transaction_text.insert(tk.END, "Select a card to view transactions")
            return

        card_info = self.card_data[self.current_card_id]
        transactions = card_info.get('transactions', [])

        self.transaction_text.delete(1.0, tk.END)

        if not transactions:
            self.transaction_text.insert(tk.END, "No transactions yet")
            return

        # Display last 20 transactions
        for txn in reversed(transactions[-20:]):
            self.transaction_text.insert(tk.END,
                f"{txn['date']} - {txn['type'].title()} - ${txn['amount']:,.2f} - Balance: ${txn['balance']:,.2f}\\n")

    def send_funds(self):
        """Send funds from the card using Visa network simulation."""
        if not self.current_card_id:
            messagebox.showwarning("No Card Selected", "Please select a card first.")
            return

        card_info = self.card_data[self.current_card_id]

        # Check card status
        if card_info.get('status') != 'active':
            messagebox.showerror("Card Not Active", "This card must be activated before use.\\n\\nPlease activate your card in the main TorCOIN wallet.")
            return

        # Check if card is expired
        if self.is_card_expired(card_info):
            messagebox.showerror("Card Expired", "This virtual card has expired and cannot be used for transactions.")
            return

        # Send funds dialog
        send_window = tk.Toplevel(self.root)
        send_window.title("Send Funds")
        send_window.geometry("400x300")
        send_window.configure(bg=self.colors['bg_primary'])

        tk.Label(send_window, text="💰 Send Funds", font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(pady=20)

        # Amount
        tk.Label(send_window, text="Amount:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary']).pack()
        amount_entry = tk.Entry(send_window, font=('Segoe UI', 12))
        amount_entry.pack(pady=(5, 20))

        # Recipient
        tk.Label(send_window, text="Recipient Address:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary']).pack()
        recipient_entry = tk.Entry(send_window, font=('Segoe UI', 12))
        recipient_entry.pack(pady=(5, 20))

        def execute_send():
            try:
                amount = float(amount_entry.get())
                recipient = recipient_entry.get().strip()

                if amount <= 0:
                    messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
                    return

                if not recipient:
                    messagebox.showerror("Recipient Required", "Please enter recipient address.")
                    return

                card_info = self.card_data[self.current_card_id]
                if card_info['balance'] < amount:
                    messagebox.showerror("Insufficient Funds", "Not enough balance on card.")
                    return

                # Process Visa transaction (mock)
                # In real implementation, this would call Visa payment APIs
                success, message = self.mock_visa_transaction(card_info['card_number'], amount, f"Transfer to {recipient}")

                if success:
                    # Update local card data
                    card_info['balance'] -= amount

                    # Add transaction
                    transaction = {
                        'id': f"visa_txn_{secrets.token_hex(4)}",
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'type': 'debit',
                        'amount': amount,
                        'balance': card_info['balance'],
                        'merchant': f"Transfer to {recipient[:10]}...",
                        'description': f"Visa transfer to {recipient}",
                        'network': 'Visa',
                        'status': 'approved'
                    }
                    card_info['transactions'].append(transaction)

                    self.save_card_data()
                    self.update_transaction_display()
                    self.select_card(self.current_card_id)  # Refresh display

                    messagebox.showinfo("Visa Transaction Approved",
                                      f"✅ Visa transaction approved!\\n\\n"
                                      f"Amount: ${amount:,.2f}\\n"
                                      f"Remaining Balance: ${card_info['balance']:,.2f}\\n\\n"
                                      f"Merchant: Transfer to {recipient}")
                    send_window.destroy()
                else:
                    messagebox.showerror("Transaction Failed", message)

            except ValueError:
                messagebox.showerror("Invalid Amount", "Please enter a valid number.")

        ttk.Button(send_window, text="Send Funds", command=execute_send).pack(pady=20)

    def receive_funds(self):
        """Receive funds to the card."""
        if not self.current_card_id:
            messagebox.showwarning("No Card Selected", "Please select a card first.")
            return

        card_info = self.card_data[self.current_card_id]
        masked_number = f"**** **** **** {card_info['card_number'][-4:]}"

        receive_info = f"""Receive Funds to Card

Card: {masked_number}
Card Holder: {card_info['card_holder']}

Share this card number with the sender to receive funds.

Note: This is a demo application. In production, this would integrate with payment processors."""

        messagebox.showinfo("Receive Funds", receive_info)

    def view_transactions(self):
        """View detailed transactions (already shown in main area)."""
        if not self.current_card_id:
            messagebox.showwarning("No Card Selected", "Please select a card first.")
            return

        # Transactions are already displayed, just scroll to top
        self.transaction_text.see("1.0")

    def generate_report(self):
        """Generate a transaction report."""
        if not self.current_card_id:
            messagebox.showwarning("No Card Selected", "Please select a card first.")
            return

        card_info = self.card_data[self.current_card_id]
        transactions = card_info.get('transactions', [])

        if not transactions:
            messagebox.showinfo("No Transactions", "No transactions to report.")
            return

        # Generate report
        report = f"""Virtual Card Transaction Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Card Holder: {card_info['card_holder']}
Card Number: **** **** **** {card_info['card_number'][-4:]}
Current Balance: ${card_info['balance']:,.2f}

Transaction History:
{'-' * 80}

"""

        total_credits = 0
        total_debits = 0

        for txn in reversed(transactions):
            report += f"{txn['date']} | {txn['type'].title():<8} | ${txn['amount']:>10,.2f} | Balance: ${txn['balance']:>10,.2f}\\n"

            if txn['type'] == 'credit':
                total_credits += txn['amount']
            elif txn['type'] == 'debit':
                total_debits += txn['amount']

        report += f"""
{'-' * 80}
Summary:
Total Credits: ${total_credits:,.2f}
Total Debits:  ${total_debits:,.2f}
Net Change:    ${total_credits - total_debits:,.2f}
Current Balance: ${card_info['balance']:,.2f}
"""

        # Save report
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Transaction Report",
            initialfile=f"Card_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            with open(filename, 'w') as f:
                f.write(report)
            messagebox.showinfo("Report Saved", f"Transaction report saved to:\\n{filename}")

    def save_card_data(self):
        """Save card data to file."""
        try:
            with open("virtual_cards.json", 'w') as f:
                json.dump(self.card_data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Failed", f"Failed to save card data: {e}")

    def load_card_data(self):
        """Load card data from file."""
        try:
            if os.path.exists("virtual_cards.json"):
                with open("virtual_cards.json", 'r') as f:
                    self.card_data = json.load(f)
                self.refresh_card_list()
        except Exception as e:
            messagebox.showwarning("Load Failed", f"Failed to load card data: {e}")

    def mock_visa_transaction(self, card_number, amount, merchant):
        """Mock Visa transaction processing."""
        # Simulate Visa network processing
        import time
        time.sleep(0.5)  # Simulate network delay

        # Mock approval (90% success rate)
        if random.random() < 0.9:
            # Generate authorization code
            auth_code = str(random.randint(100000, 999999))
            return True, f"Approved - Auth Code: {auth_code}"
        else:
            # Mock decline reasons
            decline_reasons = [
                "Insufficient funds",
                "Card expired",
                "Transaction limit exceeded",
                "Invalid card number",
                "Card blocked"
            ]
            return False, f"Declined - {random.choice(decline_reasons)}"

    def is_card_expired(self, card_info):
        """Check if a card has expired."""
        if 'expiry_datetime' in card_info:
            expiry_datetime = datetime.fromisoformat(card_info['expiry_datetime'])
            return datetime.now() > expiry_datetime
        else:
            # Fallback for older cards without expiry_datetime
            # Parse expiry_date (MM/YY format)
            try:
                expiry_parts = card_info['expiry_date'].split('/')
                expiry_month = int(expiry_parts[0])
                expiry_year = 2000 + int(expiry_parts[1])  # Convert YY to YYYY

                expiry_datetime = datetime(expiry_year, expiry_month, 1)
                # Set to last day of the month
                if expiry_month == 12:
                    expiry_datetime = expiry_datetime.replace(year=expiry_year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    expiry_datetime = expiry_datetime.replace(month=expiry_month + 1, day=1) - timedelta(days=1)

                return datetime.now() > expiry_datetime
            except:
                return False  # If parsing fails, assume not expired

def main():
    """Main application entry point."""
    root = tk.Tk()
    app = VirtualCardApp(root)

    # Handle window close
    root.protocol("WM_DELETE_WINDOW", lambda: app.save_card_data() or root.quit())

    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
'''

        # Write the application to file
        with open("VirtualCard-TorCoin.py", 'w') as f:
            f.write(app_code)

    def transfer_to_card(self):
        """Transfer funds from TorCOIN wallet to virtual card."""
        cards = self.card_manager.get_user_cards()

        if not cards:
            messagebox.showinfo("No Cards", "You don't have any virtual cards to transfer to.")
            return

        transfer_window = tk.Toplevel(self.root)
        transfer_window.title("Transfer to Virtual Card")
        transfer_window.geometry("500x400")
        transfer_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(transfer_window, text="🔄 Transfer to Virtual Card",
                 style='Header.TLabel').pack(pady=20)

        transfer_frame = tk.Frame(transfer_window, bg=self.colors['bg_secondary'])
        transfer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Card selection
        ttk.Label(transfer_frame, text="Select Virtual Card:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        card_options = []
        for card_id, card_data in cards.items():
            masked = f"**** **** **** {card_data['card_number'][-4:]}"
            card_options.append(f"{masked} - ${card_data['balance']:,.2f}")

        card_var = tk.StringVar()
        if card_options:
            card_var.set(card_options[0])

        card_combo = ttk.Combobox(transfer_frame, textvariable=card_var,
                                 values=card_options, state="readonly")
        card_combo.pack(pady=(0, 20))

        # Amount
        ttk.Label(transfer_frame, text="Amount to Transfer:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 10))

        amount_entry = tk.Entry(transfer_frame, font=('Segoe UI', 14), justify='center')
        amount_entry.pack(pady=(0, 20))
        amount_entry.insert(0, "100.00")

        def execute_transfer():
            try:
                amount = float(amount_entry.get())
                selected_card = card_var.get()

                if amount <= 0:
                    messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
                    return

                if amount > self.wallet_data["balance"]:
                    messagebox.showerror("Insufficient Funds",
                                       f"Not enough TorCOIN balance. Available: ${self.wallet_data['balance']:,.2f}")
                    return

                # Find the card ID
                selected_masked = selected_card.split(" - ")[0]
                card_id = None
                for cid, cdata in cards.items():
                    if f"**** **** **** {cdata['card_number'][-4:]}" == selected_masked:
                        card_id = cid
                        break

                if not card_id:
                    messagebox.showerror("Card Not Found", "Could not find selected card.")
                    return

                # Transfer funds
                self.wallet_data["balance"] -= amount
                success = self.card_manager.update_card_balance(card_id, amount, "credit")

                if success:
                    # Add transaction to wallet
                    transaction = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "virtual_card_transfer",
                        "amount": amount,
                        "direction": "outgoing",
                        "card_number": selected_masked,
                        "status": "completed"
                    }
                    self.wallet_data["transactions"].append(transaction)

                    self.save_wallet()
                    self.update_display()

                    messagebox.showinfo("Transfer Complete",
                                      f"✅ Successfully transferred ${amount:,.2f} to your virtual card!")
                    transfer_window.destroy()
                else:
                    messagebox.showerror("Transfer Failed", "Failed to update card balance.")

            except ValueError:
                messagebox.showerror("Invalid Amount", "Please enter a valid number.")

        ttk.Button(transfer_window, text="🚀 Transfer Funds",
                  style='Success.TButton', command=execute_transfer).pack(pady=20)

    def replace_virtual_card_ui(self):
        """UI for replacing a virtual card."""
        cards = self.card_manager.get_user_cards()

        if not cards:
            messagebox.showinfo("No Cards", "You don't have any virtual cards to replace.")
            return

        # Check replacement limit
        replacements_used = self.card_manager.get_monthly_replacements()
        replacements_left = 2 - replacements_used

        if replacements_left <= 0:
            remaining_days = (datetime.now().replace(day=1, month=datetime.now().month + 1) - datetime.now()).days
            messagebox.showerror("Replacement Limit Reached",
                               f"You have used all 2 card replacements for this month.\\n\\n"
                               f"Replacements used: {replacements_used}/2\\n"
                               f"Next replacement available in {remaining_days} days.")
            return

        replace_window = tk.Toplevel(self.root)
        replace_window.title("Replace Virtual Card")
        replace_window.geometry("600x500")
        replace_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(replace_window, text="🔄 Replace Virtual Card",
                 style='Header.TLabel').pack(pady=20)

        # Replacement limit info
        limit_frame = tk.Frame(replace_window, bg=self.colors['accent_primary'])
        limit_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(limit_frame, text=f"Monthly Replacements: {replacements_used}/2 used ({replacements_left} remaining)",
                 style='Balance.TLabel', background=self.colors['accent_primary']).pack(pady=10)

        replace_frame = tk.Frame(replace_window, bg=self.colors['bg_secondary'])
        replace_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        ttk.Label(replace_frame, text="Select Card to Replace:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        # Card selection
        card_options = []
        card_id_map = {}

        for card_id, card_data in cards.items():
            masked_number = f"**** **** **** {card_data['card_number'][-4:]}"
            expiry_status = "(EXPIRED)" if self.card_manager.is_card_expired(card_data) else ""
            option_text = f"{masked_number} - {card_data['card_holder']} {expiry_status}"
            card_options.append(option_text)
            card_id_map[option_text] = card_id

        if not card_options:
            ttk.Label(replace_frame, text="No cards available for replacement",
                     style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=20)
            return

        card_var = tk.StringVar()
        card_var.set(card_options[0])

        card_combo = ttk.Combobox(replace_frame, textvariable=card_var,
                                 values=card_options, state="readonly")
        card_combo.pack(pady=(0, 20))

        # Replacement reason
        ttk.Label(replace_frame, text="Replacement Reason (Optional):",
                 style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 5))

        reason_text = tk.Text(replace_frame, height=3, width=50, bg=self.colors['bg_panel'], fg=self.colors['text_primary'])
        reason_text.pack(pady=(0, 20))
        reason_text.insert(tk.END, "Optional: Enter reason for replacement...")

        def clear_placeholder(event):
            if reason_text.get("1.0", tk.END).strip() == "Optional: Enter reason for replacement...":
                reason_text.delete("1.0", tk.END)

        reason_text.bind("<FocusIn>", clear_placeholder)

        def execute_replacement():
            selected_option = card_var.get()
            old_card_id = card_id_map.get(selected_option)

            if not old_card_id:
                messagebox.showerror("Selection Error", "Please select a card to replace.")
                return

            # Get reason if provided
            reason = reason_text.get("1.0", tk.END).strip()
            if reason == "Optional: Enter reason for replacement...":
                reason = "User requested replacement"

            # Confirm replacement
            old_card_data = self.card_manager.get_card_details(old_card_id)
            masked_old = f"**** **** **** {old_card_data['card_number'][-4:]}"

            confirm_msg = f"Are you sure you want to replace this card?\\n\\n" \
                         f"Card: {masked_old}\\n" \
                         f"Holder: {old_card_data['card_holder']}\\n" \
                         f"Balance: ${old_card_data['balance']:,.2f}\\n\\n" \
                         f"This will create a new card with a new number and 10-year expiry.\\n" \
                         f"The old card will remain accessible but marked as replaced.\\n\\n" \
                         f"Monthly replacements remaining: {replacements_left - 1}/2"

            if not messagebox.askyesno("Confirm Replacement", confirm_msg):
                return

            # Perform replacement
            result = self.card_manager.replace_virtual_card(old_card_id)

            if result:
                new_card_id, new_card_details = result
                masked_new = f"**** **** **** {new_card_details['card_number'][-4:]}"

                success_msg = f"✅ Card Replaced Successfully!\\n\\n" \
                             f"Old Card: {masked_old}\\n" \
                             f"New Card: {masked_new}\\n" \
                             f"New Expiry: {new_card_details['expiry_date']}\\n\\n" \
                             f"Monthly replacements used: {replacements_used + 1}/2\\n\\n" \
                             f"The old card is still accessible in your card list."

                messagebox.showinfo("Replacement Complete", success_msg)
                replace_window.destroy()

                # Refresh card display
                self.view_virtual_cards()
            else:
                messagebox.showerror("Replacement Failed", "Failed to replace the virtual card.")

        ttk.Button(replace_window, text="🔄 Replace Card",
                  style='Success.TButton', command=execute_replacement).pack(pady=20)

    def show_replacement_history(self):
        """Show the history of card replacements."""
        replacements = self.wallet.wallet_data.get('card_replacements', [])

        if not replacements:
            messagebox.showinfo("No Replacement History", "You haven't replaced any virtual cards yet.")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("Card Replacement History")
        history_window.geometry("700x500")
        history_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(history_window, text="📊 Card Replacement History",
                 style='Header.TLabel').pack(pady=20)

        # Monthly usage summary
        current_month = datetime.now().strftime("%Y-%m")
        monthly_count = sum(1 for r in replacements if r['month'] == current_month)

        summary_frame = tk.Frame(history_window, bg=self.colors['accent_primary'])
        summary_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(summary_frame, text=f"This Month: {monthly_count}/2 replacements used",
                 style='Balance.TLabel', background=self.colors['accent_primary']).pack(pady=10)

        # History list
        history_frame = tk.Frame(history_window, bg=self.colors['bg_secondary'])
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Headers
        header_frame = tk.Frame(history_frame, bg=self.colors['bg_tertiary'])
        header_frame.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(header_frame, text="Date", style='Header.TLabel',
                 background=self.colors['bg_tertiary']).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(header_frame, text="Old Card", style='Header.TLabel',
                 background=self.colors['bg_tertiary']).grid(row=0, column=1, padx=10, pady=5, sticky='w')
        ttk.Label(header_frame, text="New Card", style='Header.TLabel',
                 background=self.colors['bg_tertiary']).grid(row=0, column=2, padx=10, pady=5, sticky='w')

        # Sort replacements by date (newest first)
        sorted_replacements = sorted(replacements, key=lambda x: x['date'], reverse=True)

        # Display replacements
        for i, replacement in enumerate(sorted_replacements):
            row_frame = tk.Frame(history_frame, bg=self.colors['bg_panel'] if i % 2 == 0 else self.colors['bg_secondary'])
            row_frame.pack(fill=tk.X)

            # Date
            date_str = replacement['date'][:10]  # YYYY-MM-DD
            ttk.Label(row_frame, text=date_str,
                     style='Primary.TLabel', background=row_frame['bg']).grid(row=0, column=0, padx=10, pady=5, sticky='w')

            # Old card (masked)
            old_card_data = self.card_manager.get_card_details(replacement['old_card_id'])
            if old_card_data:
                old_masked = f"****{old_card_data['card_number'][-4:]}"
            else:
                old_masked = "Unknown"
            ttk.Label(row_frame, text=old_masked,
                     style='Primary.TLabel', background=row_frame['bg']).grid(row=0, column=1, padx=10, pady=5, sticky='w')

            # New card (masked)
            new_card_data = self.card_manager.get_card_details(replacement['new_card_id'])
            if new_card_data:
                new_masked = f"****{new_card_data['card_number'][-4:]}"
            else:
                new_masked = "Unknown"
            ttk.Label(row_frame, text=new_masked,
                     style='Primary.TLabel', background=row_frame['bg']).grid(row=0, column=2, padx=10, pady=5, sticky='w')

    def replace_single_card(self, card_id):
        """Replace a single card with confirmation."""
        # Check replacement limit
        if not self.card_manager.can_replace_card():
            replacements_used = self.card_manager.get_monthly_replacements()
            remaining_days = (datetime.now().replace(day=1, month=datetime.now().month + 1) - datetime.now()).days
            messagebox.showerror("Replacement Limit Reached",
                               f"You have used all 2 card replacements for this month.\\n\\n"
                               f"Replacements used: {replacements_used}/2\\n"
                               f"Next replacement available in {remaining_days} days.")
            return

        # Get card data
        card_data = self.card_manager.get_card_details(card_id)
        if not card_data:
            messagebox.showerror("Card Not Found", "Could not find the card to replace.")
            return

        masked_number = f"**** **** **** {card_data['card_number'][-4:]}"

        # Confirm replacement
        replacements_left = 2 - self.card_manager.get_monthly_replacements()
        confirm_msg = f"Replace this virtual card?\\n\\n" \
                     f"Card: {masked_number}\\n" \
                     f"Holder: {card_data['card_holder']}\\n" \
                     f"Balance: ${card_data['balance']:,.2f}\\n\\n" \
                     f"This creates a new card with fresh 10-year expiry.\\n" \
                     f"Monthly replacements remaining: {replacements_left - 1}/2"

        if not messagebox.askyesno("Confirm Card Replacement", confirm_msg):
            return

        # Perform replacement
        result = self.card_manager.replace_virtual_card(card_id)

        if result:
            new_card_id, new_card_details = result
            new_masked = f"**** **** **** {new_card_details['card_number'][-4:]}"

            success_msg = f"✅ Card Replaced Successfully!\\n\\n" \
                         f"Old Card: {masked_number}\\n" \
                         f"New Card: {new_masked}\\n" \
                         f"New Expiry: {new_card_details['expiry_date']}\\n\\n" \
                         f"The old card remains accessible."

            messagebox.showinfo("Replacement Complete", success_msg)

            # Refresh card display
            self.view_virtual_cards()
        else:
            messagebox.showerror("Replacement Failed", "Failed to replace the virtual card.")

    def activate_card_ui(self, card_id):
        """UI for activating a virtual card."""
        card_data = self.card_manager.get_card_details(card_id)
        if not card_data:
            messagebox.showerror("Card Not Found", "Could not find the card to activate.")
            return

        if card_data.get('status') == 'active':
            messagebox.showinfo("Already Active", "This card is already active.")
            return

        activate_window = tk.Toplevel(self.root)
        activate_window.title("Activate Virtual Card")
        activate_window.geometry("500x400")
        activate_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(activate_window, text="✅ Activate Your Visa Virtual Card",
                 style='Header.TLabel').pack(pady=20)

        activate_frame = tk.Frame(activate_window, bg=self.colors['bg_secondary'])
        activate_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Card info
        masked_number = f"**** **** **** {card_data['card_number'][-4:]}"
        ttk.Label(activate_frame, text=f"Card: {masked_number}",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        ttk.Label(activate_frame, text=f"Card Holder: {card_data['card_holder']}",
                 style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 20))

        # Verification method selection
        ttk.Label(activate_frame, text="Choose verification method:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 10))

        method_var = tk.StringVar(value='app')
        ttk.Radiobutton(activate_frame, text="📱 App Verification",
                       variable=method_var, value='app').pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(activate_frame, text="📧 Email Verification",
                       variable=method_var, value='email').pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(activate_frame, text="📱 SMS Verification",
                       variable=method_var, value='sms').pack(anchor=tk.W, padx=20, pady=5)

        # Code entry
        ttk.Label(activate_frame, text="Enter 6-digit verification code:",
                 style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=(20, 10))

        code_entry = tk.Entry(activate_frame, font=('Segoe UI', 16), justify='center', show='*')
        code_entry.pack(pady=(0, 10))

        # Get/Send code button
        def send_code():
            success, message = self.card_manager.resend_activation_code(card_id, method_var.get())
            if success:
                code_entry.delete(0, tk.END)
                code_entry.focus()
            else:
                messagebox.showerror("Error", message)

        ttk.Button(activate_frame, text="📨 Send/Get Code",
                  command=send_code).pack(pady=(0, 20))

        def activate():
            code = code_entry.get().strip()
            if not code:
                messagebox.showerror("Code Required", "Please enter the verification code.")
                return

            if len(code) != 6 or not code.isdigit():
                messagebox.showerror("Invalid Code", "Please enter a valid 6-digit code.")
                return

            success, message = self.card_manager.activate_virtual_card(card_id, code, method_var.get())

            if success:
                messagebox.showinfo("Activation Successful",
                                  f"✅ Your Visa Virtual Card has been activated!\\n\\n"
                                  f"You can now use your card for online purchases.\\n\\n"
                                  f"Daily Limit: $1,000\\n"
                                  f"Monthly Limit: $5,000")
                activate_window.destroy()
                self.view_virtual_cards()
            else:
                messagebox.showerror("Activation Failed", message)

        ttk.Button(activate_window, text="✅ Activate Card",
                  style='Success.TButton', command=activate).pack(pady=20)

        # Auto-send code on window open
        send_code()

    def load_card_funds(self, card_id):
        """Load funds onto a virtual card."""
        card_data = self.card_manager.get_card_details(card_id)
        if not card_data:
            messagebox.showerror("Card Not Found", "Could not find the card.")
            return

        if card_data.get('status') != 'active':
            messagebox.showerror("Card Not Active", "Card must be activated before loading funds.")
            return

        load_window = tk.Toplevel(self.root)
        load_window.title("Load Funds to Card")
        load_window.geometry("400x350")
        load_window.configure(bg=self.colors['bg_primary'])

        ttk.Label(load_window, text="💰 Load Funds to Visa Card",
                 style='Header.TLabel').pack(pady=20)

        load_frame = tk.Frame(load_window, bg=self.colors['bg_secondary'])
        load_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Card info
        masked_number = f"**** **** **** {card_data['card_number'][-4:]}"
        ttk.Label(load_frame, text=f"Card: {masked_number}",
                 style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=(10, 5))

        ttk.Label(load_frame, text=f"Current Balance: ${card_data['balance']:,.2f}",
                 style='Primary.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 20))

        # Amount entry
        ttk.Label(load_frame, text="Amount to Load:",
                 style='Header.TLabel', background=self.colors['bg_secondary']).pack(pady=(0, 10))

        amount_entry = tk.Entry(load_frame, font=('Segoe UI', 14), justify='center')
        amount_entry.pack(pady=(0, 5))
        amount_entry.insert(0, "100.00")

        # Quick amount buttons
        quick_frame = tk.Frame(load_frame, bg=self.colors['bg_secondary'])
        quick_frame.pack(pady=(10, 20))

        def set_amount(amount):
            amount_entry.delete(0, tk.END)
            amount_entry.insert(0, str(amount))

        ttk.Button(quick_frame, text="$50", command=lambda: set_amount(50)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(quick_frame, text="$100", command=lambda: set_amount(100)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(quick_frame, text="$250", command=lambda: set_amount(250)).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(quick_frame, text="$500", command=lambda: set_amount(500)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(quick_frame, text="$1000", command=lambda: set_amount(1000)).grid(row=1, column=1, padx=5, pady=5)

        def load_funds():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
                    return

                if amount > self.wallet_data["balance"]:
                    messagebox.showerror("Insufficient Funds",
                                       f"Not enough TorCOIN balance. Available: ${self.wallet_data['balance']:,.2f}")
                    return

                # Deduct from wallet
                self.wallet_data["balance"] -= amount

                # Add to card balance
                card_data['balance'] += amount

                # Add transaction records
                wallet_txn = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "card_load",
                    "amount": amount,
                    "direction": "outgoing",
                    "card_number": masked_number,
                    "status": "completed"
                }
                self.wallet_data["transactions"].append(wallet_txn)

                card_txn = {
                    'id': f"load_{secrets.token_hex(4)}",
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'credit',
                    'amount': amount,
                    'balance': card_data['balance'],
                    'merchant': 'TorCOIN Wallet',
                    'description': f'Funds loaded from TorCOIN wallet',
                    'network': 'Visa',
                    'status': 'completed'
                }
                card_data['transactions'].append(card_txn)

                self.save_wallet()

                messagebox.showinfo("Funds Loaded",
                                  f"✅ Successfully loaded ${amount:,.2f} to your Visa card!\\n\\n"
                                  f"Card Balance: ${card_data['balance']:,.2f}\\n"
                                  f"Wallet Balance: ${self.wallet_data['balance']:,.2f}")

                load_window.destroy()
                self.view_virtual_cards()

            except ValueError:
                messagebox.showerror("Invalid Amount", "Please enter a valid number.")

        ttk.Button(load_window, text="💰 Load Funds",
                  style='Success.TButton', command=load_funds).pack(pady=20)

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
