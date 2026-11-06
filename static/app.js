const $ = (s) => document.querySelector(s);

const esc = (value) => String(value).replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));

const money = (value) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD"
}).format(Number(value || 0));

function renderMarkdown(markdown) {
  const lines = String(markdown || "").replace(/\r/g, "").split("\n");
  const html = [];
  let listType = null;
  let tableRows = [];
  const inline = (value) => esc(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  const closeList = () => {
    if (listType) { html.push(listType === "ul" ? "</ul>" : "</ol>"); listType = null; }
  };
  const flushTable = () => {
    if (!tableRows.length) return;
    const rows = tableRows.filter((row) => !row.every((cell) => /^\s*:?-{3,}:?\s*$/.test(cell)));
    if (rows.length) {
      html.push("<div class='answer-table-wrap'><table class='answer-table'><tbody>");
      rows.forEach((row, index) => {
        html.push("<tr>" + row.map((cell) => {
          const tag = index === 0 ? "th" : "td";
          return "<" + tag + ">" + inline(cell.trim()) + "</" + tag + ">";
        }).join("") + "</tr>");
      });
      html.push("</tbody></table></div>");
    }
    tableRows = [];
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (line.startsWith("|") && line.endsWith("|")) { closeList(); tableRows.push(line.slice(1, -1).split("|")); continue; }
    flushTable();
    if (!line) { closeList(); continue; }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    const bullet = line.match(/^[-*]\s+(.+)$/);
    const numbered = line.match(/^\d+[.)]\s+(.+)$/);
    if (heading) { closeList(); const level = Math.min(heading[1].length + 2, 5); html.push("<h" + level + ">" + inline(heading[2]) + "</h" + level + ">"); }
    else if (bullet || numbered) {
      const nextType = bullet ? "ul" : "ol";
      if (listType !== nextType) { closeList(); listType = nextType; html.push("<" + listType + ">"); }
      html.push("<li>" + inline((bullet || numbered)[1]) + "</li>");
    } else { closeList(); html.push("<p>" + inline(line) + "</p>"); }
  }
  flushTable(); closeList();
  return html.join("");
}

async function load() {
  try {
    const response = await fetch("/api/summary");
    const data = await response.json();
    $("#revenue").textContent = money(data.revenue);
    $("#count").textContent = data.order_count ?? 0;
    $("#pending").textContent = data.pending ?? 0;
    $("#deliveredOrders").textContent = data.delivered_orders ?? 0;
    $("#pipelineValue").textContent = money(data.pipeline_value);
    $("#cancelledOrders").textContent = data.cancelled_orders ?? 0;
    $("#averageOrderValue").textContent = money(data.average_delivered_order_value);
    $("#orderRows").innerHTML = data.orders.map((o) =>
      "<tr><td>" + esc(o.customer) + "</td><td>" + esc(o.product) +
      "</td><td class='amount'>" + money(o.amount) +
      "</td><td><span class='tag " + esc(o.status) + "'>" + esc(o.status) +
      "</span></td><td class='actions'><select aria-label='New status for " + esc(o.product) +
      "' data-status-select='" + Number(o.id) + "'>" +
      ["Pending", "Processing", "Delivered", "Cancelled"].map((status) =>
        "<option value='" + status + "'" + (o.status === status ? " selected" : "") + ">" + status + "</option>"
      ).join("") + "</select><button class='save-status' data-save-id='" + Number(o.id) + "'>Save</button></td></tr>"
    ).join("");
  } catch (_) {
    $("#orderRows").innerHTML = "<tr><td colspan='5'>Could not load orders. Refresh the page.</td></tr>";
  }
}

$("#toggle").onclick = () => { $("#orderform").hidden = !$("#orderform").hidden; };

$("#orderform").onsubmit = async (event) => {
  event.preventDefault();
  const response = await fetch("/api/orders", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.fromEntries(new FormData(event.target)))
  });
  const data = await response.json();
  if (!response.ok) return alert(data.error || "Could not save order.");
  event.target.reset(); event.target.hidden = true; 
async function loadPayments() {
  const body = $("#paymentRows");
  try {
    const response = await fetch("/api/payments");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load payments.");
    $("#paypalStatus").textContent = data.configured
      ? "PayPal Sandbox credentials detected. You can create test payments."
      : "PayPal Sandbox is not configured yet. Add PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET to Render environment variables.";
    body.innerHTML = data.payments.length ? data.payments.map((p) =>
      "<tr><td>" + esc(p.description) + "</td><td>" + money(p.amount) +
      "</td><td><code>" + esc(p.paypal_order_id) + "</code></td><td><span class='tag'>" +
      esc(p.status) + "</span></td><td>" + esc(new Date(p.created_at + "Z").toLocaleString()) + "</td></tr>"
    ).join("") : "<tr><td colspan='5'>No Sandbox payments yet. Create your first test payment above.</td></tr>";
  } catch (error) {
    body.innerHTML = "<tr><td colspan='5'>" + esc(error.message) + "</td></tr>";
  }
}

$("#paymentForm").onsubmit = async (event) => {
  event.preventDefault();
  const button = $("#paymentButton");
  const status = $("#paypalStatus");
  button.disabled = true;
  button.textContent = "Connecting to PayPal…";
  status.textContent = "Creating a Sandbox order securely on the server…";
  try {
    const payload = Object.fromEntries(new FormData(event.target));
    const response = await fetch("/api/paypal/create-order", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not create payment.");
    window.location.href = data.approval_url;
  } catch (error) {
    status.textContent = error.message;
    button.disabled = false;
    button.textContent = "Create PayPal test payment ↗";
  }
};

async function handlePayPalReturn() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (params.get("paypal") === "cancel") {
    $("#paypalStatus").textContent = "You cancelled the Sandbox checkout. No payment was captured.";
    history.replaceState({}, "", "/");
    return;
  }
  if (params.get("paypal") !== "return" || !token) return;
  $("#paypalStatus").textContent = "PayPal approval received. Capturing the Sandbox payment…";
  try {
    const response = await fetch("/api/paypal/capture-order", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: token })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Capture failed.");
    $("#paypalStatus").textContent = data.status === "COMPLETED"
      ? "Sandbox payment completed successfully. Capture ID: " + (data.capture_id || "recorded")
      : "PayPal returned status: " + data.status + ". Check the payment record.";
    history.replaceState({}, "", "/");
    await loadPayments();
  } catch (error) {
    $("#paypalStatus").textContent = "Could not capture payment: " + error.message;
  }
}

load();
loadPayments();
handlePayPalReturn();

};

$("#orderRows").onclick = async (event) => {
  const button = event.target.closest("button[data-save-id]");
  if (!button) return;
  const id = button.dataset.saveId;
  const select = document.querySelector("select[data-status-select='" + id + "']");
  button.disabled = true; button.textContent = "Saving…";
  try {
    const response = await fetch("/api/orders/" + id, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: select.value })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not update order.");
    await load();
  } catch (error) {
    alert(error.message);
    button.disabled = false; button.textContent = "Save";
  }
};

$("#chat").onsubmit = async (event) => {
  event.preventDefault();
  const input = $("#question");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  const userBubble = document.createElement("div");
  userBubble.className = "bubble user"; userBubble.textContent = message;
  $("#messages").append(userBubble);
  const answer = document.createElement("div");
  answer.className = "bubble assistant"; answer.textContent = "Thinking…";
  $("#messages").append(answer);
  answer.scrollIntoView({ behavior: "smooth", block: "nearest" });
  try {
    const response = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "AI service unavailable.");
    answer.innerHTML = renderMarkdown(data.reply || "No response");
  } catch (error) { answer.textContent = error.message || "Connection error. Try again."; }
  answer.scrollIntoView({ behavior: "smooth", block: "nearest" });
};

load();
