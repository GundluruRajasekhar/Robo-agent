"""Tool registry. Each tool = JSON schema (for the LLM) + a Python function."""
import ast, ipaddress, operator, os, socket
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests

WORKSPACE = os.path.abspath(os.getenv("WORKSPACE", "workspace"))
os.makedirs(WORKSPACE, exist_ok=True)


def _safe_path(name: str) -> str:
    p = os.path.abspath(os.path.join(WORKSPACE, name))
    if not p.startswith(WORKSPACE + os.sep):
        raise ValueError("Path is outside the workspace")
    return p


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg, ast.Mod: operator.mod}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    return str(_eval(ast.parse(expression, mode="eval").body))


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_files() -> str:
    return "\n".join(sorted(os.listdir(WORKSPACE))) or "(empty)"


def read_file(name: str) -> str:
    with open(_safe_path(name), encoding="utf-8") as f:
        return f.read()[:20000]


def write_file(name: str, content: str) -> str:
    with open(_safe_path(name), "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {name}"


def http_get(url: str) -> str:
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("Only http/https URLs are allowed")
    ip = ipaddress.ip_address(socket.gethostbyname(u.hostname))
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        raise ValueError("Private addresses are blocked")
    r = requests.get(url, timeout=10, headers={"User-Agent": "robo-agent/1.0"})
    return f"HTTP {r.status_code}\n{r.text[:8000]}"


def _schema(name, desc, props, required):
    return {"name": name, "description": desc,
            "input_schema": {"type": "object", "properties": props, "required": required}}


S = {"type": "string"}
TOOLS = {
    "calculator": {"fn": calculator, "schema": _schema("calculator", "Evaluate an arithmetic expression.", {"expression": S}, ["expression"])},
    "current_time": {"fn": current_time, "schema": _schema("current_time", "Get the current UTC time.", {}, [])},
    "list_files": {"fn": list_files, "schema": _schema("list_files", "List files in the agent workspace.", {}, [])},
    "read_file": {"fn": read_file, "schema": _schema("read_file", "Read a text file from the workspace.", {"name": S}, ["name"])},
    "write_file": {"fn": write_file, "schema": _schema("write_file", "Write a text file to the workspace.", {"name": S, "content": S}, ["name", "content"])},
    "http_get": {"fn": http_get, "schema": _schema("http_get", "Fetch a public web page or API by URL.", {"url": S}, ["url"])},
}


def run_tool(name: str, args: dict) -> str:
    """Never raise: return errors as text so the agent can observe them and re-plan."""
    if name not in TOOLS:
        return f"Error: unknown tool '{name}'"
    try:
        return str(TOOLS[name]["fn"](**args))
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"
