import ollama
import json

from main import (
    get_leave_balance,
    apply_leave,
    get_leave_history
)

# ----------------------------
# STRICT LLM CALL
# ----------------------------
def ask_llm(prompt: str):
    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": """
You are an HR assistant acting as a JSON router.

CRITICAL RULES:
- Output ONLY valid JSON
- NO explanations
- NO markdown
- NO extra text

Allowed actions ONLY:
- balance
- apply
- history

OUTPUT FORMAT:
{
  "action": "balance | apply | history",
  "employee_id": "E001",
  "leave_dates": []
}
"""
            },
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]

# ----------------------------
# SAFE JSON PARSER
# ----------------------------
def safe_parse(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # fallback: try to extract JSON block
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

# ----------------------------
# ROUTER
# ----------------------------
def run_agent(user_input: str):
    result = ask_llm(user_input)

    print("\nLLM OUTPUT:\n", result)

    data = safe_parse(result)

    if not data:
        return "Invalid AI response format"

    action = data.get("action", "").lower()
    emp = data.get("employee_id")
    dates = data.get("leave_dates", [])

    # ----------------------------
    # NORMALIZE ACTIONS (IMPORTANT)
    # ----------------------------
    action_map = {
        "check_leave_balance": "balance",
        "leave_balance": "balance",
        "get_balance": "balance",
        "apply_leave": "apply",
        "get_history": "history"
    }

    action = action_map.get(action, action)

    # ----------------------------
    # EXECUTION
    # ----------------------------
    if action == "balance":
        return get_leave_balance(emp)

    elif action == "apply":
        return apply_leave(emp, dates)

    elif action == "history":
        return get_leave_history(emp)

    return f"Unknown action: {action}"


# ----------------------------
# CLI LOOP
# ----------------------------
if __name__ == "__main__":
    print("HR Agent CLI Ready (type 'exit' to quit)\n")

    while True:
        user_input = input(">> ")

        if user_input.lower() == "exit":
            break

        output = run_agent(user_input)

        print("\nRESULT:\n", output)