# TorCOIN - Privacy-First Digital Currency

A complete cryptocurrency platform featuring a professional website, GUI wallet application, and comprehensive server infrastructure.

## 🌐 Live Repositories

- **Main Repository**: https://github.com/LilToreyFTW/TorCOIN
- **Wallet Repository**: https://github.com/LilToreyFTW/TorCOIN-Wallet
- **Live Website**: http://www.torcoin.cnet

## Files

- `torcoin_website.html` - Full TorCOIN website with wallet downloads
- `torcoin_wallet.py` - Complete GUI wallet application
- `create_wallet_installer.bat` - Creates downloadable wallet installer
- `coin_server.py` - Production Python web server script (serves torcoin_website.html)
- `start_coin_server.bat` - Production Windows batch file to start the server
- `test_server.py` - Local test Python web server script (uses localhost:50129)
- `test_server.bat` - Local test Windows batch file
- `configure_cloudflare_dns.bat` - Configure system to use Cloudflare DNS (1.1.1.1)
- `setup_domain.bat` - Add www.torcoin.cnet to hosts file
- `server.bat` - START TorCOIN server ecosystem (24/7 monitoring)
- `stop_server.bat` - STOP all TorCOIN services
- `restart_server.bat` - RESTART TorCOIN server ecosystem
- `full_setup.bat` - COMPLETE setup (DNS + Domain + Server + Security + Proxy)
- `strict_firewall.bat` - Ultra-strict firewall (only TorCOIN traffic)
- `torcoin_proxy.py` - Secure self-proxy server (TorCOIN only)
- `start_secure_proxy.bat` - Start the secure proxy server
- `ultimate_security_setup.bat` - MAX security (firewall + proxy)
- `restore_firewall.bat` - Restore normal firewall settings
- `README.md` - This documentation

## Quick Start

### 🚀 ONE-CLICK COMPLETE SETUP (Recommended)
1. **Run as Administrator**: Double-click `full_setup.bat`
2. Wait for complete setup (DNS + Domain + Server + Security + Proxy)
3. Access your ULTRA-SECURE coin at: **http://www.torcoin.cnet**

### Manual Setup Steps

#### Testing Locally First
1. Double-click `test_server.bat` or run: `python test_server.py`
2. Open http://127.0.0.1:50129/ in your browser
3. Verify your coin works locally

#### Production Deployment
1. **Configure DNS**: Run `configure_cloudflare_dns.bat` (as Administrator)
2. **Setup Domain**: Run `setup_domain.bat` (as Administrator)
3. **Start Server**: Double-click `start_coin_server.bat` or run: `python coin_server.py`
4. **Access Coin**: **https://www.torcoin.cnet**

### Manual Start
```bash
python coin_server.py
```

## Server Details

- **Server Binding**: 0.0.0.0:50129 (binds to all interfaces)
- **Ultra Hardcoded Display URL**: https://www.torcoin.cnet
- **DNS**: Configured for Cloudflare (1.1.1.1, 1.0.0.1)
- **Domain Resolution**: www.torcoin.cnet → 127.0.0.1 (local)
- **HTTPS Note**: Currently serves HTTP. For HTTPS, use a reverse proxy (nginx/apache) with SSL certificates

## DNS Configuration

The setup uses **Cloudflare's fast DNS servers**:
- **Primary DNS**: `1.1.1.1`
- **Secondary DNS**: `1.0.0.1`

Benefits:
- ⚡ Faster DNS resolution
- 🔒 Encrypted DNS queries
- 🛡️ Malware protection
- 📊 Query logging disabled

## Features

- Serves the 3D animated coin page
- Redirects all requests to the main coin page
- Simple and lightweight
- Error handling for missing files
- Custom logging

## Access Your Coin

Once the server is running, share this ULTRA HARDCODED link with users:
**http://www.torcoin.cnet**

*(Configure domain DNS or add to hosts file: `127.0.0.1 www.torcoin.cnet`)*

## Troubleshooting

### Permission Denied
If you get "Permission denied" on port 80, run with administrator privileges:
- Right-click `start_coin_server.bat` and "Run as administrator"
- Or use a different port (currently set to 50129)

### Port Already in Use
Change the PORT in `coin_server.py` to an available port (e.g., 8080)

### File Not Found
Make sure `torcoin.html` is in the same directory as `coin_server.py`

## Troubleshooting

### ❌ "www.torcoin.cnet refused to connect"

This error means the domain resolves but the server isn't running or accessible.

**Quick Fix:**
1. Run `quick_fix.bat` (as Administrator)
2. Or manually:
   - Run `full_setup.bat` (as Administrator)
   - Access via: `http://www.torcoin.cnet`

**Check Status:**
Run `check_status.bat` to diagnose issues.

**Common Causes:**
- Server not running → Run `full_setup.bat`
- Domain not in hosts file → Run `setup_domain.bat`
- DNS not configured → Run `configure_cloudflare_dns.bat`
- Python not installed → Install Python 3.x

## Security Features

### 🛡️ STRICT Firewall (`strict_firewall.bat`)
- **Blocks ALL inbound traffic** except TorCOIN server (port 50129)
- **Blocks ALL outbound traffic** except essentials:
  - DNS resolution (Cloudflare 1.1.1.1, 1.0.0.1)
  - DHCP (IP assignment)
  - Windows Update
  - Local network traffic
- **Creates backup** for easy restoration

### 🛡️ Self Proxy Server (`torcoin_proxy.py`)
- **Only allows access to TorCOIN server** (127.0.0.1:50129)
- **Blocks all other websites** and internet traffic
- **Request/response filtering** and validation
- **Timeout protection** and error handling

### 🚀 Ultimate Security (`ultimate_security_setup.bat`)
Combines both firewall and proxy for maximum protection:
1. Enables strict firewall rules
2. Starts secure proxy server
3. Tests connectivity
4. Provides access instructions

### 🔄 Recovery (`restore_firewall.bat`)
- Restores firewall from backup
- Returns to normal internet access
- Removes all TorCOIN security restrictions

## GitHub Integration

Both repositories are now live and fully synchronized:

- **Main Repository**: https://github.com/LilToreyFTW/TorCOIN
  - Complete TorCOIN ecosystem
  - Website, server, security tools
  - Full project documentation

- **Wallet Repository**: https://github.com/LilToreyFTW/TorCOIN-Wallet
  - TorCOIN GUI Wallet application
  - Wallet installer tools
  - Wallet-specific documentation

### Repository Management
```bash
# Push to both repositories
git push origin master
git push wallet master

# Check status
git remote -v
git status
```

## Server Management

### 🚀 Start Server (24/7 Operation):
```bash
server.bat
```
- Starts TorCOIN server with monitoring
- Applies security measures
- Keeps everything running automatically
- Monitors health and auto-restarts if needed

### 🛑 Stop Server:
```bash
stop_server.bat
```
- Stops all TorCOIN services
- Restores normal firewall settings
- Returns to normal internet access

### 🔄 Restart Server:
```bash
restart_server.bat
```
- Stops and restarts all services
- Fresh start with new logs

## Usage with Security

### Maximum Security Setup:
1. Run `ultimate_security_setup.bat` (as Administrator)
2. Set browser proxy to `localhost:8080`
3. Access `http://www.torcoin.cnet`

### Normal Setup:
1. Run `full_setup.bat` (as Administrator)
2. Access `http://www.torcoin.cnet`

### 24/7 Server Operation:
1. Run `server.bat` (as Administrator)
2. Site stays online indefinitely
3. Use `stop_server.bat` to shutdown

## TorCOIN GUI Wallet

The official desktop wallet application for TorCOIN with a modern graphical interface.

### Features
- **Complete GUI Interface** - User-friendly desktop application
- **Wallet Management** - Create, open, and backup wallets
- **Send & Receive** - Full transaction capabilities
- **Transaction History** - Complete transaction log with filtering
- **Address Management** - Generate and manage addresses
- **Security Features** - Encrypted wallet storage, password protection
- **Network Integration** - Real-time network status and updates
- **Settings & Preferences** - Customizable interface and options

### System Requirements
- **Python 3.8+** required
- **Windows 10+** (Linux/Mac support planned)
- **100MB disk space** for installation
- **512MB RAM** minimum (1GB recommended)

### Installation
1. Download `TorCOIN_Wallet_v1.0.zip` from the website
2. Extract to a folder on your computer
3. Run `Run_TorCOIN_Wallet.bat`
4. Create a new wallet or import existing

### Creating Installer
Run `create_wallet_installer.bat` to create a distributable wallet package for users.

## Stopping the Server

Press `Ctrl+C` in the terminal window to stop the server.
