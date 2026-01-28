let session_id = Math.random().toString(36).substring(7);

async function sendMessage() {
    const input = document.getElementById("messageInput");
    const chat = document.getElementById("chat");

    const message = input.value.trim();
    if (!message) return;

    // Show user message
    chat.innerHTML += `<div class="user-msg">🧑 You: ${message}</div>`;
    input.value = "";

    // Send to backend
    const res = await fetch("/webhook", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            session_id: session_id,
            message: message
        })
    });

    const data = await res.json();

    // Show AI reply
    chat.innerHTML += `<div class="bot-msg">🤖 Bot: ${data.reply}</div>`;

    // Show analysis box
    if (data.analysis) {
        chat.innerHTML += `
            <div class="analysis-box">
                ⚠️ Risk Score: ${data.analysis.risk_score}<br>
                🚨 Type: ${data.analysis.scam_type}<br>
                🔴 Flags: ${data.analysis.red_flags.join(", ")}
            </div>
        `;
    }

    chat.scrollTop = chat.scrollHeight;
}
