from mcp.server.fastmcp import FastMCP
from typing import List
from dotenv import load_dotenv
import ollama
import os
import smtplib
from email.mime.text import MIMEText

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ----------------------------
# Mock database
# ----------------------------
employee_leaves = {
    "E001": {
        "balance": 18,
        "history": ["2024-12-25", "2025-01-01"],
        "email": "employee1@gmail.com"
    },
    "E002": {
        "balance": 20,
        "history": [],
        "email": "employee2@gmail.com"
    }
}

# ----------------------------
# MCP Server
# ----------------------------
mcp = FastMCP("LeaveManager")

# ----------------------------
# LLM helper (STRICT JSON)
# ----------------------------
def ask_llm(prompt: str) -> dict:
    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": """
You are a STRICT HR router.

Return ONLY valid JSON.

Allowed actions:
- balance
- apply
- history

Format:
{
  "action": "balance | apply | history",
  "employee_id": "E001",
  "leave_dates": []
}

Rules:
- No explanations
- No markdown
- No extra text
"""
            },
            {"role": "user", "content": prompt}
        ]
    )

    import json
    return json.loads(response["message"]["content"])

# ----------------------------
# Email helper
# ----------------------------
def send_email(to_email: str, subject: str, body: str):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "Email not configured"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# ----------------------------
# Tools (PURE business logic)
# ----------------------------
@mcp.tool()
def get_leave_balance(employee_id: str) -> str:
    data = employee_leaves.get(employee_id)
    if not data:
        return "Employee not found"
    return f"{employee_id} has {data['balance']} leave days remaining."


@mcp.tool()
def apply_leave(employee_id: str, leave_dates: List[str]) -> str:
    data = employee_leaves.get(employee_id)
    if not data:
        return "Employee not found"

    requested = len(leave_dates)

    if data["balance"] < requested:
        return "Insufficient balance"

    data["balance"] -= requested
    data["history"].extend(leave_dates)

    send_email(
        data["email"],
        "Leave Approved",
        f"Approved: {leave_dates}"
    )

    return f"Leave approved. Remaining balance: {data['balance']}"


@mcp.tool()
def get_leave_history(employee_id: str) -> str:
    data = employee_leaves.get(employee_id)
    if not data:
        return "Employee not found"

    return ", ".join(data["history"]) or "No history"

# ----------------------------
# AI TOOL (decides ONLY)
# ----------------------------
@mcp.tool()
def ai_route_leave(employee_id: str, leave_dates: List[str]) -> str:
    prompt = f"""
Employee: {employee_id}
Balance: {employee_leaves[employee_id]["balance"]}
Dates: {leave_dates}
"""

    decision = ask_llm(prompt)

    action = decision.get("action")

    if action == "balance":
        return get_leave_balance(employee_id)

    if action == "apply":
        return apply_leave(employee_id, leave_dates)

    if action == "history":
        return get_leave_history(employee_id)

    return f"Unknown action: {action}"

# ----------------------------
# Resource
# ----------------------------
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello {name}, welcome to LeaveManager"

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    mcp.run()