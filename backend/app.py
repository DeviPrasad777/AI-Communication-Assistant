# backend/app.py
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="AI Communication Assistant", layout="wide")

# ---------- Demo seed emails (will be stored in session) ----------
seed_emails = [
    {
        "id": 1,
        "sender": "alice@example.com",
        "subject": "Cannot access my account - urgent",
        "body": "I cannot access my account since yesterday. It says login failed. Please help immediately, this is urgent.",
        "received_at": "2025-09-06 08:12",
        "status": "pending"
    },
    {
        "id": 2,
        "sender": "bob@company.com",
        "subject": "Query about enterprise plan pricing",
        "body": "Hi team, could you share enterprise pricing and SLAs? We're evaluating vendors.",
        "received_at": "2025-09-06 09:05",
        "status": "pending"
    },
    {
        "id": 3,
        "sender": "charlie@shop.com",
        "subject": "Request refund for order #1234",
        "body": "My order arrived damaged. I need a refund or replacement. Please advise the process.",
        "received_at": "2025-09-05 17:42",
        "status": "pending"
    }
]

# ---------- Helpers: sentiment & priority (simple rule-based) ----------
NEGATIVE_WORDS = {"cannot", "can't", "unable", "failed", "error", "urgent", "immediately", "angry", "frustrated", "damage", "damaged", "refund"}
POSITIVE_WORDS = {"thank", "thanks", "great", "good", "happy", "appreciate", "resolved"}
URGENT_KEYWORDS = {"urgent", "immediately", "asap", "can't access", "cannot access", "down", "critical", "failed payment", "lost access", "cannot"}

def detect_sentiment(text):
    text_l = text.lower()
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_l)
    pos = sum(1 for w in POSITIVE_WORDS if w in text_l)
    if neg > pos:
        return "Negative"
    if pos > neg:
        return "Positive"
    return "Neutral"

def detect_priority(text):
    text_l = text.lower()
    return "Urgent" if any(k in text_l for k in URGENT_KEYWORDS) else "Normal"

def simple_summary(text, max_chars=180):
    txt = text.strip().replace("\n", " ")
    return (txt[:max_chars] + "...") if len(txt) > max_chars else txt

def generate_draft(email):
    sentiment = detect_sentiment(email["body"])
    urgent = detect_priority(email["body"]) == "Urgent"
    greeting = "Hi"  # you can customize to use sender name
    ack = "We're sorry you're facing this" if sentiment == "Negative" else "Thanks for reaching out"
    urgency_line = " We will prioritize this and respond within 1 business hour." if urgent else ""
    body = (
        f"{greeting} {email['sender'].split('@')[0].capitalize()},\n\n"
        f"{ack} regarding \"{email['subject']}\". {simple_summary(email['body'], max_chars=200)}\n\n"
        f"Our team is looking into this now.{urgency_line}\n\n"
        "Could you please confirm any order/username/reference if applicable? This helps us resolve faster.\n\n"
        "Regards,\nSupport Team"
    )
    return body

# ---------- Session state initialization ----------
if "emails" not in st.session_state:
    st.session_state["emails"] = seed_emails.copy()
if "selected_id" not in st.session_state:
    st.session_state["selected_id"] = None
if "drafts" not in st.session_state:
    st.session_state["drafts"] = {}

# ---------- Layout ----------
st.title("AI-Powered Communication Assistant (MVP)")

left, mid, right = st.columns([2, 3, 3])

# Left: Inbox list with filters
with left:
    st.subheader("Inbox")
    filter_text = st.text_input("Filter subject/sender (optional)")
    show_only_pending = st.checkbox("Show only pending", value=True)

    def list_emails():
        emails = st.session_state["emails"]
        filtered = []
        for e in emails:
            if filter_text and filter_text.lower() not in (e["subject"]+e["sender"]).lower():
                continue
            if show_only_pending and e.get("status") != "pending":
                continue
            filtered.append(e)
        # sort: urgent first, then newest
        filtered.sort(key=lambda x: (detect_priority(x["body"])!="Urgent", x["received_at"]), reverse=True)
        return filtered

    displayed = list_emails()
    for e in displayed:
        sentiment = detect_sentiment(e["body"])
        priority = detect_priority(e["body"])
        col1, col2 = st.columns([4,1])
        with col1:
            if st.button(f"{e['subject']} — {e['sender']}", key=f"sel_{e['id']}"):
                st.session_state["selected_id"] = e["id"]
            st.write(f"**{e['subject']}**")
            st.write(f"{e['sender']} • {e['received_at']}")
        with col2:
            st.write(f"**{priority}**")
            st.write(f"{sentiment}")

# Middle: Email content & extracted info
with mid:
    st.subheader("Email Detail")
    sel = next((x for x in st.session_state["emails"] if x["id"]==st.session_state["selected_id"]), None)
    if sel:
        st.markdown(f"**From:** {sel['sender']}")
        st.markdown(f"**Subject:** {sel['subject']}")
        st.markdown(f"**Received:** {sel['received_at']}")
        st.markdown("**Body:**")
        st.write(sel["body"])
        st.markdown("---")
        st.write("**Extracted Info**")
        st.write({
            "Sentiment": detect_sentiment(sel["body"]),
            "Priority": detect_priority(sel["body"]),
            "Summary": simple_summary(sel["body"], 200)
        })
    else:
        st.write("Select an email from the left to see details.")

# Right: AI Draft and actions
with right:
    st.subheader("AI Draft")
    if sel:
        if st.button("Generate Draft"):
            st.session_state["drafts"][sel["id"]] = generate_draft(sel)
        draft_text = st.session_state["drafts"].get(sel["id"], "")
        new_text = st.text_area("Draft (edit before send)", value=draft_text, height=320, key=f"draft_{sel['id']}")
        if st.button("Send Draft"):
            # simulate sending
            for e in st.session_state["emails"]:
                if e["id"] == sel["id"]:
                    e["status"] = "sent"
                    e["sent_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("Draft marked as SENT (simulated).")
                    break
    else:
        st.write("No email selected.")

# Footer: small analytics
st.sidebar.subheader("Analytics (demo)")
emails = st.session_state["emails"]
total = len(emails)
pending = len([e for e in emails if e["status"]=="pending"])
sent = len([e for e in emails if e["status"]=="sent"])
urgent_count = len([e for e in emails if detect_priority(e["body"])=="Urgent"])
st.sidebar.write(f"Total: {total}")
st.sidebar.write(f"Pending: {pending}")
st.sidebar.write(f"Sent: {sent}")
st.sidebar.write(f"Urgent: {urgent_count}")
