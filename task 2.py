import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime

PORT = 8000

USERS = ["alice", "bob", "charlie", "dana", "eva"]

kudos_feed = []

# Simple admin password for demonstration (in production, use secure auth!)
ADMIN_PASSWORD = "adminpass"

# Moderation log for audit
moderation_log = []


def build_dashboard_html(message=None, error=None):
    options = "\n".join(
        f'<option value="{html.escape(u)}">{html.escape(u.title())}</option>' for u in USERS
    )
    error_html = f'<p style="color: red;">{html.escape(error)}</p>' if error else ""
    message_html = f'<p style="color: green;">{html.escape(message)}</p>' if message else ""


    feed_rows = "\n".join(
        f"<div class='kudos-item'><strong>{html.escape(item['from'].title())}</strong> gave kudos to <strong>{html.escape(item['to'].title())}</strong> <span class='ts'>({item['ts']})</span><p>{html.escape(item['message'])}</p></div>"
        for item in reversed([k for k in kudos_feed if not k.get('hidden')][-20:])
    ) or "<p>No kudos yet. Be the first to recognize a teammate!</p>"
def build_admin_html(message=None, error=None):
    rows = []
    for idx, item in enumerate(reversed(kudos_feed)):
        status = "<em style='color:gray'>(hidden)</em>" if item.get('hidden') else ""
        row = f"""
        <div class='kudos-item'>
            <strong>{html.escape(item['from'].title())}</strong> gave kudos to <strong>{html.escape(item['to'].title())}</strong> <span class='ts'>({item['ts']})</span> {status}
            <p>{html.escape(item['message'])}</p>
            <form method='post' action='/admin/moderate' style='display:inline'>
                <input type='hidden' name='kudos_idx' value='{len(kudos_feed)-1-idx}' />
                <button name='action' value='hide' type='submit'>Hide</button>
                <button name='action' value='delete' type='submit' onclick="return confirm('Delete this kudos?')">Delete</button>
            </form>
        </div>
        """
        rows.append(row)
    feed_rows = "\n".join(rows) or "<p>No kudos yet.</p>"
    error_html = f'<p style="color: red;">{html.escape(error)}</p>' if error else ""
    message_html = f'<p style="color: green;">{html.escape(message)}</p>' if message else ""
    return f"""
<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8' />
    <title>Kudos Admin Moderation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 900px; margin: auto; }}
        .kudos-item {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 12px; padding: 12px; background: #f7f9fc; }}
        .kudos-item .ts {{ font-size: 0.85rem; color: #666; }}
    </style>
</head>
<body>
    <div class='container'>
        <h1>Kudos Moderation (Admin)</h1>
        {message_html}
        {error_html}
        <form method='post' action='/admin/logout'><button type='submit'>Logout</button></form>
        <section style='margin-top:32px;'>
            <h2>All Kudos</h2>
            {feed_rows}
        </section>
    </div>
</body>
</html>
"""

    return f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Datacom Kudos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 900px; margin: auto; }}
        header {{ margin-bottom: 24px; }}
        form input, form select, form textarea, form button {{ width: 100%; margin-top: 8px; padding: 10px; font-size: 1rem; }}
        form textarea {{ height: 100px; resize: vertical; }}
        .kudos-item {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 12px; padding: 12px; background: #f7f9fc; }}
        .kudos-item .ts {{ font-size: 0.85rem; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Datacom Kudos Wall</h1>
            <p>Give kudos to someone on the team and see the public appreciation feed live.</p>
            {message_html}
            {error_html}
        </header>

        <section>
            <h2>Give Kudos</h2>
            <form method="post" action="/kudos">
                <label for="from_user">Your name</label>
                <select id="from_user" name="from_user" required>
                    <option value="">-- choose your name --</option>
                    {options}
                </select>

                <label for="to_user">To</label>
                <select id="to_user" name="to_user" required>
                    <option value="">-- choose colleague --</option>
                    {options}
                </select>

                <label for="message">Message</label>
                <textarea id="message" name="message" maxlength="250" placeholder="What did your colleague do that deserves kudos?" required></textarea>

                <button type="submit">Send Kudos</button>
            </form>
        </section>

        <section style="margin-top: 32px;">
            <h2>Recent Kudos Feed</h2>
            {feed_rows}
        </section>
    </div>
</body>
</html>
"""


class KudosRequestHandler(BaseHTTPRequestHandler):
    def is_admin(self):
        cookie = self.headers.get('Cookie', '')
        return 'admin_auth=1' in cookie

    def do_GET(self):
        if self.path in ("/", "/dashboard"):
            html_content = build_dashboard_html()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        elif self.path == "/admin":
            if not self.is_admin():
                # Show login form
                html_content = """
                <html><body><h2>Admin Login</h2>
                <form method='post' action='/admin/login'>
                    <input type='password' name='password' placeholder='Admin password' required />
                    <button type='submit'>Login</button>
                </form></body></html>
                """
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
            else:
                html_content = build_admin_html()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/kudos":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)

            from_user = data.get("from_user", [""])[0].strip().lower()
            to_user = data.get("to_user", [""])[0].strip().lower()
            message = data.get("message", [""])[0].strip()

            if not from_user or not to_user or not message:
                error_msg = "All fields are required."
                self._render_response_with_message(None, error_msg)
                return

            if from_user == to_user:
                error_msg = "You cannot give kudos to yourself."
                self._render_response_with_message(None, error_msg)
                return

            if from_user not in USERS or to_user not in USERS:
                error_msg = "Invalid user selection."
                self._render_response_with_message(None, error_msg)
                return

            if len(message) > 250:
                error_msg = "Message too long (max 250 characters)."
                self._render_response_with_message(None, error_msg)
                return

            kudos_feed.append({
                "from": from_user,
                "to": to_user,
                "message": message,
                "ts": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            })

            self._render_response_with_message("Kudos sent successfully!", None)
        elif self.path == "/admin/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)
            password = data.get("password", [""])[0]
            if password == ADMIN_PASSWORD:
                self.send_response(302)
                self.send_header('Set-Cookie', 'admin_auth=1; Path=/')
                self.send_header('Location', '/admin')
                self.end_headers()
            else:
                html_content = "<html><body><h2>Admin Login</h2><p style='color:red'>Incorrect password.</p><form method='post' action='/admin/login'><input type='password' name='password' placeholder='Admin password' required /><button type='submit'>Login</button></form></body></html>"
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
        elif self.path == "/admin/logout":
            self.send_response(302)
            self.send_header('Set-Cookie', 'admin_auth=0; Path=/; Max-Age=0')
            self.send_header('Location', '/admin')
            self.end_headers()
        elif self.path == "/admin/moderate":
            if not self.is_admin():
                self.send_response(302)
                self.send_header('Location', '/admin')
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)
            idx = int(data.get('kudos_idx', [-1])[0])
            action = data.get('action', [''])[0]
            if 0 <= idx < len(kudos_feed):
                kudos = kudos_feed[idx]
                if action == 'hide':
                    if not kudos.get('hidden'):
                        kudos['hidden'] = True
                        moderation_log.append({
                            'action': 'hide',
                            'kudos_idx': idx,
                            'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        })
                        msg = "Kudos hidden."
                    else:
                        msg = "Kudos already hidden."
                    html_content = build_admin_html(message=msg)
                elif action == 'delete':
                    moderation_log.append({
                        'action': 'delete',
                        'kudos_idx': idx,
                        'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    })
                    del kudos_feed[idx]
                    msg = "Kudos deleted."
                    html_content = build_admin_html(message=msg)
                else:
                    html_content = build_admin_html(error="Unknown action.")
            else:
                html_content = build_admin_html(error="Invalid kudos index.")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def _render_response_with_message(self, success_msg, error_msg):
        html_content = build_dashboard_html(message=success_msg, error=error_msg)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-length", str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("", PORT), KudosRequestHandler)
    print(f"Kudos app running at http://localhost:{PORT}/")
    print("Press Ctrl+C to quit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()
