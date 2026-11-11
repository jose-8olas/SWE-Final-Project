"""Role-based access control (NFR-02, NFR-08, T-05).

Two roles:
  Store Manager      - upload, view, see confidential fields (supplier cost), review.
  Inventory Employee - upload and view permitted data only. Cannot review or see supplier cost.

Passwords are stored as salted hashes, never as plain text. The two demo accounts are
manager / manager123 and employee / employee123 (for the prototype only).
Every permission check is written to an access log as allowed or denied.
"""
import getpass
import hashlib
import hmac
from datetime import datetime

ROLE_MANAGER = "Store Manager"
ROLE_EMPLOYEE = "Inventory Employee"

ACTION_UPLOAD = "upload"
ACTION_VIEW = "view"
ACTION_VIEW_CONFIDENTIAL = "view confidential data"
ACTION_REVIEW = "review recommendations"

PERMISSIONS = {
    ROLE_MANAGER: {ACTION_UPLOAD, ACTION_VIEW, ACTION_VIEW_CONFIDENTIAL, ACTION_REVIEW},
    ROLE_EMPLOYEE: {ACTION_UPLOAD, ACTION_VIEW},
}

CONFIDENTIAL_FIELDS = ("supplier_cost",)
HASH_ROUNDS = 100_000

USERS = {
    "manager": {
        "role": ROLE_MANAGER,
        "salt": "fefd2dd3624b9eca",
        "hash": "b9c17bdcc83bc655fc824488494fc4c1e792134cc4546f324574bdadd7dd5560",
    },
    "employee": {
        "role": ROLE_EMPLOYEE,
        "salt": "0b296017cbbf883a",
        "hash": "3575899e17123297ba29ba9961c5cd3cfde78629aba0971c52716b45d29f8fee",
    },
}


def hash_password(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), HASH_ROUNDS
    ).hex()


def authenticate(username, password, users=USERS):
    """Return {"username", "role"} for a correct login, otherwise None."""
    record = users.get((username or "").strip().lower())
    # Hash even for an unknown user so both cases take about the same time.
    salt = record["salt"] if record else "00" * 8
    attempt = hash_password(password or "", salt)
    if record and hmac.compare_digest(attempt, record["hash"]):
        return {"username": username.strip().lower(), "role": record["role"]}
    return None


def login(ask=input, ask_password=getpass.getpass, show=print, max_attempts=3, users=USERS):
    """Ask for a username and password. Returns the user, or None after too many failures."""
    for _ in range(max_attempts):
        try:
            username = ask("Username: ")
            password = ask_password("Password: ")
        except EOFError:
            return None
        user = authenticate(username, password, users)
        if user:
            return user
        show("Incorrect username or password.")
    return None


def can(user, action):
    return action in PERMISSIONS.get(user["role"], set())


def require(user, action, access_log):
    """Check permission BEFORE a protected action. Logs the result.
    Raises PermissionError (and the caller must not continue) when denied."""
    allowed = can(user, action)
    access_log.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "username": user["username"],
        "role": user["role"],
        "action": action,
        "result": "allowed" if allowed else "denied",
    })
    if not allowed:
        raise PermissionError(
            f"Access denied: the {user['role']} role cannot {action}."
        )


def filter_item(item, user):
    """Copy of an inventory item with confidential fields removed unless the role may see them."""
    if can(user, ACTION_VIEW_CONFIDENTIAL):
        return dict(item)
    return {key: value for key, value in item.items() if key not in CONFIDENTIAL_FIELDS}


def show_access_log(access_log, show=print):
    show("\n--- ACCESS LOG ---")
    for entry in access_log:
        show(f"{entry['timestamp']} | {entry['username']} ({entry['role']}) | "
             f"{entry['action']} | {entry['result']}")