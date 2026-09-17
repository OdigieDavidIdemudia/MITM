from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from functools import wraps
import datetime
import subprocess
import os
import json
import re

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
SQUID_DIR = "/etc/squid"
LISTS = {
    "ads": os.path.join(SQUID_DIR, "dynamic_ads.txt"),
    "streaming": os.path.join(SQUID_DIR, "streaming.txt"),
    "whitelist": os.path.join(SQUID_DIR, "whitelist.txt")
}
HTPASSWD_FILE = os.path.join(SQUID_DIR, "passwd")
DB_FILE = "telemetry.json"
SQUIDGUARD_CONF = "/etc/squidguard/squidGuard.conf"

# Ensure files exist
for name, path in LISTS.items():
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"suggestions": [], "logs": []}, f)

# --- AUTHENTICATION ---
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

# --- HELPERS ---
def read_list(category):
    path = LISTS.get(category)
    if not path or not os.path.exists(path): return []
    with open(path, 'r') as f:
        return [line.strip().lstrip('.') for line in f.readlines() if line.strip()]

def write_list(category, domains):
    path = LISTS.get(category)
    if not path: return
    with open(path, 'w') as f:
        for domain in domains:
            if domain: f.write(f".{domain}\n" if category != "whitelist" else f"{domain}\n")

def read_db():
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except:
        return {"suggestions": [], "logs": []}

def write_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=2)

def reload_squid():
    subprocess.run(["sudo", "systemctl", "reload", "squid"], check=False)

def restart_squid():
    subprocess.run(["sudo", "systemctl", "restart", "squid"], check=False)

def clear_squid_cache():
    subprocess.run(["sudo", "systemctl", "stop", "squid"], check=False)
    subprocess.run(["sudo", "rm", "-rf", "/var/spool/squid/*"], check=False)
    subprocess.run(["sudo", "squid", "-z"], check=False)
    subprocess.run(["sudo", "systemctl", "start", "squid"], check=False)

# --- WEB GUI ROUTES ---
@app.route('/', methods=['GET'])
@requires_auth
def dashboard():
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
@requires_auth
def get_stats():
    stats = {cat: len(read_list(cat)) for cat in LISTS.keys()}
    db = read_db()
    stats['suggestions'] = len(db.get('suggestions', []))
    return jsonify(stats)

@app.route('/api/all_rules', methods=['GET'])
@requires_auth
def get_all_rules():
    rules = []
    for cat in LISTS.keys():
        policy = "allowed" if cat == "whitelist" else "blocked"
        for dom in read_list(cat):
            rules.append({"domain": dom, "category": cat, "policy": policy})
    return jsonify({"rules": rules})

@app.route('/api/lists/<category>', methods=['GET', 'POST', 'DELETE'])
@requires_auth
def manage_lists(category):
    if category not in LISTS: return jsonify({"error": "Invalid category"}), 400
    domains = read_list(category)
    
    if request.method == 'GET':
        return jsonify({"domains": domains})
    
    domain = request.json.get('domain', '').strip()
    if not domain: return jsonify({"error": "No domain provided"}), 400

    if request.method == 'POST':
        if domain not in domains:
            domains.append(domain)
            write_list(category, domains)
            reload_squid()
        return jsonify({"status": "added"})
        
    if request.method == 'DELETE':
        if domain in domains:
            domains.remove(domain)
            write_list(category, domains)
            reload_squid()
        return jsonify({"status": "removed"})

@app.route('/api/squidguard', methods=['GET', 'POST'])
@requires_auth
def manage_squidguard():
    if not os.path.exists(SQUIDGUARD_CONF):
        return jsonify({"error": "squidGuard.conf not found"}), 404

    if request.method == 'GET':
        with open(SQUIDGUARD_CONF, 'r') as f:
            content = f.read()
        
        dests = re.findall(r'dest\s+(\w+)\s*\{', content)
        pass_match = re.search(r'pass\s+(.*?)\n', content)
        pass_rules = pass_match.group(1).split() if pass_match else []
        
        categories = []
        for d in dests:
            categories.append({
                "name": d.capitalize(),
                "id": d,
                "blocked": f"!{d}" in pass_rules
            })
        return jsonify({"categories": categories})
        
    if request.method == 'POST':
        category = request.json.get('category')
        block = request.json.get('block')
        
        with open(SQUIDGUARD_CONF, 'r') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if 'pass ' in line and 'all' in line:
                parts = line.strip().split()
                if block:
                    if f"!{category}" not in parts:
                        parts.insert(1, f"!{category}")
                else:
                    if f"!{category}" in parts:
                        parts.remove(f"!{category}")
                lines[i] = "            " + " ".join(parts) + "\n"
                break
                
        with open(SQUIDGUARD_CONF, 'w') as f:
            f.writelines(lines)
            
        reload_squid()
        return jsonify({"status": "success"})

@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
@requires_auth
def manage_users():
    if not os.path.exists(HTPASSWD_FILE):
        open(HTPASSWD_FILE, 'w').close()
        
    if request.method == 'GET':
        users = []
        with open(HTPASSWD_FILE, 'r') as f:
            for line in f:
                if ':' in line: users.append(line.split(':')[0])
        return jsonify({"users": users})
        
    username = request.json.get('username')
    
    if request.method == 'POST':
        password = request.json.get('password')
        subprocess.run(["sudo", "htpasswd", "-b", HTPASSWD_FILE, username, password], check=False)
        reload_squid()
        return jsonify({"status": "added"})
        
    if request.method == 'DELETE':
        subprocess.run(["sudo", "htpasswd", "-D", HTPASSWD_FILE, username], check=False)
        reload_squid()
        return jsonify({"status": "removed"})

@app.route('/api/ml', methods=['GET', 'POST'])
@requires_auth
def manage_ml():
    db = read_db()
    if request.method == 'GET':
        return jsonify({"suggestions": db.get('suggestions', [])})
        
    action = request.json.get('action')
    domain = request.json.get('domain')
    
    # Remove from suggestions
    db['suggestions'] = [s for s in db['suggestions'] if s['domain'] != domain]
    write_db(db)
    
    if action == 'approve':
        category = request.json.get('category', 'ads')
        domains = read_list(category)
        if domain not in domains:
            domains.append(domain)
            write_list(category, domains)
            reload_squid()
            
    return jsonify({"status": "resolved"})

@app.route('/api/system/<action>', methods=['POST'])
@requires_auth
def system_action(action):
    if action == 'reload': reload_squid()
    elif action == 'restart': restart_squid()
    elif action == 'clear_cache': clear_squid_cache()
    return jsonify({"status": "success"})

# --- EXTENSION TELEMETRY (Unauthenticated) ---
@app.route('/ml-suggest', methods=['POST'])
def ml_suggest():
    data = request.json
    domain = data.get('domain')
    analysis = data.get('analysis')
    
    if not domain: return jsonify({"status": "ignored"}), 400
    
    db = read_db()
    # Check if already blocked in any list
    for cat in LISTS.keys():
        if domain in read_list(cat): return jsonify({"status": "already_blocked"})
        
    # Check if already suggested
    if not any(s['domain'] == domain for s in db.get('suggestions', [])):
        db.setdefault('suggestions', []).append({
            "domain": domain,
            "score": analysis.get('score', 0),
            "flags": analysis.get('flags', []),
            "timestamp": datetime.datetime.now().isoformat()
        })
        write_db(db)
        print(f"🧠 ML flagged new suspicious domain: {domain} (Score: {analysis.get('score')})")
        
    return jsonify({"status": "logged"}), 200

@app.route('/report-ad', methods=['POST'])
def report_ad():
    data = request.json
    domain = data.get('domain')
    if not domain or domain in ['unknown', '', 'about:blank']:
        return jsonify({"status": "ignored"}), 400
        
    # For backward compatibility, push direct reports into 'ads'
    domains = read_list("ads")
    if domain not in domains:
        domains.append(domain)
        write_list("ads", domains)
        reload_squid()
    return jsonify({"status": "blocked_network_wide"}), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "online"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
