from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import subprocess
import os

app = Flask(__name__)
# Allow the Chrome extension to send data
CORS(app)

# The file where Squid looks for domains to block
SQUID_BLOCKLIST = "/etc/squid/dynamic_ads.txt"

@app.route('/report-ad', methods=['POST'])
def report_ad():
    data = request.json
    domain = data.get('domain')
    
    if not domain or domain in ['unknown', '', 'about:blank']:
        return jsonify({"status": "ignored"}), 400
        
    print(f"[{datetime.datetime.now()}] 🚨 MITM EXTENSION REPORTED AD: {domain}")
    
    # 1. Check if we already blocked this domain
    try:
        if os.path.exists(SQUID_BLOCKLIST):
            with open(SQUID_BLOCKLIST, 'r') as f:
                if domain in f.read():
                    print(f"[*] {domain} is already in the blocklist.")
                    return jsonify({"status": "already_blocked"}), 200
    except Exception as e:
        pass

    # 2. Append the new domain to Squid's blocklist
    try:
        with open(SQUID_BLOCKLIST, 'a') as f:
            # Squid dstdomain format (adding a dot blocks all subdomains too)
            f.write(f".{domain}\n")
        
        # 3. Reload Squid so the new rule takes effect immediately!
        # Note: The python script must be run with sudo, or the user needs sudo privileges
        subprocess.run(["sudo", "systemctl", "reload", "squid"], check=True)
        
        print(f"✅ BANNED: Added {domain} to Squid and reloaded proxy.")
        return jsonify({"status": "blocked_network_wide", "domain": domain}), 200
        
    except Exception as e:
        print(f"❌ Error updating Squid: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "online", "message": "MITM Server is listening"}), 200

if __name__ == '__main__':
    # Listen on all network interfaces on port 5000
    app.run(host='0.0.0.0', port=5000)
