from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from functools import wraps
import datetime
import subprocess
import os

app = Flask(__name__)
CORS(app)

SQUID_BLOCKLIST = "/etc/squid/dynamic_ads.txt"

# --- AUTHENTICATION ---
# Default credentials: username 'admin', password 'admin'
def check_auth(username, password):
    return username == 'admin' and password == 'admin'

def authenticate():
    return jsonify({"message": "Authentication required."}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# --- FILE HELPERS ---
def read_blocklist():
    if not os.path.exists(SQUID_BLOCKLIST):
        return []
    with open(SQUID_BLOCKLIST, 'r') as f:
        # Strip the leading dot that squid uses for subdomains
        return [line.strip().lstrip('.') for line in f.readlines() if line.strip()]

def write_blocklist(domains):
    with open(SQUID_BLOCKLIST, 'w') as f:
        for domain in domains:
            if domain:
                f.write(f".{domain}\n")

def reload_squid():
    try:
        subprocess.run(["sudo", "systemctl", "reload", "squid"], check=True)
    except Exception as e:
        print(f"Failed to reload squid: {e}")


# --- WEB GUI ROUTES ---
@app.route('/', methods=['GET'])
@requires_auth
def dashboard():
    return render_template('index.html')

@app.route('/api/rules', methods=['GET'])
@requires_auth
def get_rules():
    return jsonify({"domains": read_blocklist()})

@app.route('/api/rules', methods=['POST'])
@requires_auth
def add_rule():
    domain = request.json.get('domain', '').strip()
    if not domain:
        return jsonify({"error": "No domain provided"}), 400
    
    domains = read_blocklist()
    if domain not in domains:
        domains.append(domain)
        write_blocklist(domains)
        reload_squid()
        return jsonify({"status": "added", "domain": domain})
    
    return jsonify({"status": "exists", "domain": domain})

@app.route('/api/rules', methods=['DELETE'])
@requires_auth
def remove_rule():
    domain = request.json.get('domain', '').strip()
    domains = read_blocklist()
    if domain in domains:
        domains.remove(domain)
        write_blocklist(domains)
        reload_squid()
        return jsonify({"status": "removed", "domain": domain})
    
    return jsonify({"status": "not_found"}), 404


# --- EXTENSION TELEMETRY ROUTES (Unauthenticated so extension can report automatically) ---
@app.route('/report-ad', methods=['POST'])
def report_ad():
    data = request.json
    domain = data.get('domain')
    
    if not domain or domain in ['unknown', '', 'about:blank']:
        return jsonify({"status": "ignored"}), 400
        
    print(f"[{datetime.datetime.now()}] 🚨 MITM EXTENSION REPORTED AD: {domain}")
    
    domains = read_blocklist()
    if domain in domains:
        return jsonify({"status": "already_blocked"}), 200

    try:
        domains.append(domain)
        write_blocklist(domains)
        reload_squid()
        print(f"✅ BANNED: Added {domain} to Squid and reloaded proxy.")
        return jsonify({"status": "blocked_network_wide", "domain": domain}), 200
        
    except Exception as e:
        print(f"❌ Error updating Squid: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "online", "message": "MITM Server is listening"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
