import logging
import sys
import os
import subprocess
import requests
import nmap # For advanced port scanning
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ----------------------------------------------------
# --- CONFIGURATION ----------------------------------
# ----------------------------------------------------
TOKEN = '8531821353:AAExuhXC2_OSjf-6TiaB7d8yG3UxOxoXFg4'
BOT_USERNAME = "@IX_SNIFF_BOT aka @cwrq1"

# --- حقوق الملكية تم إزالتها من الردود لوضعها في البروفايل ---

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# --- CYBERSECURITY COMMANDS (Advanced Features) -----
# ----------------------------------------------------

async def ping_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار الاتصال (Ping) باستخدام subprocess."""
    if not context.args:
        await update.message.reply_text("Usage: /ping <IP_ADDRESS_OR_DOMAIN>")
        return

    target = context.args[0]
    await update.message.reply_text(f"Starting Ping test on `{target}`...", parse_mode='Markdown')

    if sys.platform.startswith('win'):
        command = ['ping', '-n', '1', target]
    else:
        command = ['ping', '-c', '1', target]
        
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=False
        )
        
        output = result.stdout.strip()
        
        if "TTL" in output or "time=" in output or result.returncode == 0:
            reply_text = f"✅ Ping Successful for `{target}`:\n\n```\n{output}\n```"
        else:
            reply_text = f"⚠️ Ping Failed or Timed Out for `{target}`.\n\n```\n{output}\n```"
        
    except Exception as e:
        reply_text = f"❌ System Error during Ping test: {e}"

    await update.message.reply_text(reply_text, parse_mode='Markdown')


async def ip_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب معلومات الـ IP (المدينة، الدولة، ISP، فحص VPN/Proxy) باستخدام ip-api.com."""
    if not context.args:
        await update.message.reply_text("Usage: /lookup <IP_ADDRESS>")
        return

    ip_address = context.args[0]
    await update.message.reply_text(f"Fetching GeoIP and security details for `{ip_address}`...", parse_mode='Markdown')

    url = f"http://ip-api.com/json/{ip_address}?fields=country,city,isp,reverse,hosting,proxy,query,status,message"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            is_proxy_or_hosting = data.get('hosting', False) or data.get('proxy', False)
            vpn_status = "⚠️ YES (Proxy/Hosting Detected)" if is_proxy_or_hosting else "✅ NO (Appears Clean)"

            reply_text = (
                f"🌐 IP Intelligence Results for `{ip_address}`:\n"
                f"• City: {data.get('city', 'N/A')}\n"
                f"• Country: {data.get('country', 'N/A')}\n"
                f"• ISP/Org: {data.get('isp', 'N/A')}\n"
                f"• Reverse DNS: {data.get('reverse', 'N/A')}\n"
                f"• VPN/Proxy Status: **{vpn_status}**"
            )
        else:
             reply_text = f"❌ Lookup failed for `{ip_address}`. Reason: {data.get('message', 'Unknown Error')}"

    except requests.exceptions.RequestException as e:
        reply_text = f"❌ API Connection Error: {e}"
    except Exception as e:
        reply_text = f"❌ An unexpected error occurred: {e}"

    await update.message.reply_text(reply_text, parse_mode='Markdown')


async def run_port_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, ports_to_scan):
    """تنفيذ فحص البورتات باستخدام nmap."""
    if not context.args:
        await update.message.reply_text(f"Usage: /{context.command} <IP_ADDRESS> [start_port] [end_port]")
        return

    ip_address = context.args[0]
    
    # التحقق من توفر Nmap قبل بدء الفحص
    try:
        nmap.PortScanner()
    except nmap.PortScannerError:
        await update.message.reply_text(
            "❌ Nmap Error: The Nmap program is not found. "
            "Port scanning commands require **Nmap** to be installed on your operating system (not just the Python wrapper)."
        )
        return
        
    await update.message.reply_text(f"Starting port scan on `{ip_address}` for ports `{ports_to_scan}`... (May take time)", parse_mode='Markdown')

    try:
        nm = nmap.PortScanner()
        nm.scan(ip_address, ports=ports_to_scan, arguments='-sT -Pn -T4') 
        
        scan_results = []
        open_count = 0

        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                ports = nm[host][proto].keys()
                for port in ports:
                    state = nm[host][proto][port]['state']
                    service = nm[host][proto][port]['name']
                    if state == 'open':
                        open_count += 1
                        scan_results.append(f"• Port: {port}/{proto} - Service: {service}")

        if scan_results:
            reply_text = (
                f"✅ Scan Complete. Found {open_count} open ports:\n\n"
                f"**Target IP:** `{ip_address}`\n\n"
                f"Open Ports:\n" + "\n".join(scan_results)
            )
        else:
            reply_text = f"✅ Scan Complete. No open ports found in the range `{ports_to_scan}`."

    except nmap.PortScannerError as e:
        reply_text = f"❌ Scan Error (Nmap): Failed to scan the IP/range. Error: {e}"
    except Exception as e:
        reply_text = f"❌ An unexpected error occurred during scan: {e}"

    await update.message.reply_text(reply_text, parse_mode='Markdown')


async def full_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص جميع البورتات (1-1000)."""
    if not context.args:
        await update.message.reply_text("Usage: /fullscan <IP_ADDRESS>")
        return
        
    await run_port_scan(update, context, '1-1000')

async def range_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص نطاق محدد من البورتات."""
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /rangescan <IP> <start_port> <end_port>")
        return

    ip_address = context.args[0]
    start_port = context.args[1]
    end_port = context.args[2]
    ports = f"{start_port}-{end_port}"
    
    try:
        s = int(start_port)
        e = int(end_port)
        if not (1 <= s <= 65535 and 1 <= e <= 65535 and s <= e):
             raise ValueError("Invalid port range.")
    except ValueError:
        await update.message.reply_text("❌ Invalid port range. Ports must be between 1 and 65535, and start port must be less than or equal to end port.")
        return

    await run_port_scan(update, context, ports)


# ----------------------------------------------------
# --- BASIC HANDLERS (No Copyright Footer) -----------
# ----------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    welcome_message = (
        f"Hello, {user.first_name}!\n\n"
        f"Welcome to the **{BOT_USERNAME}** instance. This bot is an advanced "
        f"network security and intelligence tool. Use `/help` to see commands."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command. **INCLUDES HINT**"""
    help_text = (
        "**Advanced Cybersecurity Commands:**\n"
        "• `/lookup <IP>`: Get GeoIP (City, Country, ISP) and **VPN/Proxy** status.\n"
        "• `/ping <IP>`: Perform a basic Ping test (ICMP status).\n"
        "• `/rangescan <IP> <start> <end>`: Scan a specific range of TCP ports (e.g., 80 1000).\n"
        "• `/fullscan <IP>`: Scan ports 1-1000 (Avoids timeout for the massive 0-65535 scan).\n\n"
        
        "**⚠️ HINT / TANNBEH ⚠️**\n"
        "All scanning features (`/rangescan`, `/fullscan`) require two things to be installed on the host machine running the bot:\n"
        "1. **Python Libraries:** `pip install requests python-nmap`\n"
        "2. **The Nmap Program:** The official **Nmap** program must be installed on your system (get it from nmap.org)."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages and repeats them."""
    if update.effective_user.id == context.bot.id:
        return
    
    text_to_reply = "You said: " + update.message.text
    await update.message.reply_text(text_to_reply)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands for all users."""
    await update.message.reply_text(
        "Sorry, I don't recognize that command. Please use /help."
    )

# ----------------------------------------------------
# --- MAIN FUNCTION TO RUN THE BOT -------------------
# ----------------------------------------------------
def main():
    """Starts the bot."""
    # HINT/TANNBEH on the console
    print("================================================================")
    print("⚠️ TANNBEH: For full scanning to work, ensure the Nmap program")
    print("is installed on your system (not just the Python library).")
    print("================================================================")
    print("Bot is starting. Press Ctrl-C to stop.")
    
    application = Application.builder().token(TOKEN).build()

    # Register Advanced Handlers
    application.add_handler(CommandHandler("lookup", ip_lookup))
    application.add_handler(CommandHandler("ping", ping_test))
    application.add_handler(CommandHandler("fullscan", full_scan))
    application.add_handler(CommandHandler("rangescan", range_scan))
    
    # Register Basic Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    application.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
