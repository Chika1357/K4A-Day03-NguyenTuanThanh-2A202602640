const elements = {
  home: document.querySelector("#home-view"),
  conversation: document.querySelector("#conversation-view"),
  messages: document.querySelector("#messages"),
  heroForm: document.querySelector("#hero-form"),
  heroInput: document.querySelector("#hero-input"),
  chatForm: document.querySelector("#chat-form"),
  chatInput: document.querySelector("#chat-input"),
  tracePanel: document.querySelector("#trace-panel"),
  traceLog: document.querySelector("#trace-log"),
  traceEmpty: document.querySelector("#trace-empty"),
  traceModel: document.querySelector("#trace-model"),
  backdrop: document.querySelector("#mobile-backdrop"),
  inspector: document.querySelector("#inspector"),
  inspectorBody: document.querySelector("#inspector-body"),
  connection: document.querySelector("#connection-state"),
  providerLabel: document.querySelector("#provider-label"),
  catalogCount: document.querySelector("#catalog-count"),
};

let isLoading = false;

function icon(name) {
  const element = document.createElement("i");
  element.setAttribute("data-lucide", name);
  return element;
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  }
}

function formatPrice(value) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function cleanAnswerText(value) {
  return String(value || "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .trim();
}

function clockTime() {
  return new Date().toLocaleTimeString("vi-VN", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 130)}px`;
}

function showConversation() {
  elements.home.classList.add("is-hidden");
  elements.conversation.classList.remove("is-hidden");
}

function newMessage(role, metaText) {
  const article = document.createElement("article");
  article.className = `message ${role}-message`;
  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = `${metaText} // ${clockTime()}`;
  article.append(meta);
  return article;
}

function appendUserMessage(message) {
  const article = newMessage("user", "QUERY");
  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = `“${message}”`;
  article.append(content);
  elements.messages.append(article);
  scrollMessages();
}

function appendLoadingMessage() {
  const fragment = document.querySelector("#loading-template").content.cloneNode(true);
  const loading = fragment.querySelector(".loading-message");
  loading.id = "active-loading";
  elements.messages.append(fragment);
  scrollMessages();
}

function removeLoadingMessage() {
  document.querySelector("#active-loading")?.remove();
}

function makeSectionLabel(iconName, text) {
  const label = document.createElement("div");
  label.className = "section-label";
  label.append(icon(iconName));
  const span = document.createElement("span");
  span.textContent = text;
  label.append(span);
  return label;
}

function buildProductCard(product) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "product-card";
  card.setAttribute("aria-label", `Xem chi tiết ${product.name}`);

  const top = document.createElement("div");
  top.className = "product-card-top";
  const productIcon = document.createElement("span");
  productIcon.className = "product-icon";
  productIcon.append(icon(product.category === "laptop" ? "laptop" : "smartphone"));
  const productId = document.createElement("span");
  productId.className = "product-id";
  productId.textContent = product.product_id;
  top.append(productIcon, productId);

  const title = document.createElement("h3");
  title.textContent = product.name;
  const specs = document.createElement("p");
  specs.className = "product-spec";
  specs.textContent = [
    product.cpu,
    product.ram_gb ? `${product.ram_gb} GB RAM` : null,
    product.storage_gb ? `${product.storage_gb} GB` : null,
  ].filter(Boolean).join(" · ");
  const price = document.createElement("div");
  price.className = "product-price";
  price.textContent = formatPrice(product.price_vnd);

  card.append(top, title, specs, price);
  card.addEventListener("click", () => openInspector(product));
  return card;
}

function renderProducts(products) {
  if (!products?.length) return null;
  const section = document.createElement("section");
  section.className = "result-section";
  section.append(makeSectionLabel("database", `CATALOG_RESULTS // ${products.length}`));
  const grid = document.createElement("div");
  grid.className = "product-grid";
  products.forEach((product) => grid.append(buildProductCard(product)));
  section.append(grid);
  return section;
}

function renderReport(report) {
  if (!report) return null;
  const section = document.createElement("section");
  section.className = "result-section";
  section.append(makeSectionLabel("table-properties", "COMPARISON_ARTIFACT"));

  const block = document.createElement("div");
  block.className = "report-block";
  const heading = document.createElement("div");
  heading.className = "report-heading";
  const title = document.createElement("strong");
  title.textContent = report.title;
  const reportId = document.createElement("span");
  reportId.textContent = report.report_id;
  heading.append(title, reportId);

  const scroll = document.createElement("div");
  scroll.className = "report-scroll";
  const table = document.createElement("table");
  table.className = "report-table";
  const headers = ["Sản phẩm", "CPU", "RAM", "Lưu trữ", "Màn hình", "Giá"];
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headers.forEach((header) => {
    const th = document.createElement("th");
    th.textContent = header;
    headerRow.append(th);
  });
  thead.append(headerRow);

  const tbody = document.createElement("tbody");
  report.products.forEach((product) => {
    const row = document.createElement("tr");
    const values = [
      `${product.product_id} · ${product.name}`,
      product.cpu || "—",
      product.ram_gb ? `${product.ram_gb} GB` : "—",
      product.storage_gb ? `${product.storage_gb} GB` : "—",
      product.display || "—",
      formatPrice(product.price_vnd),
    ];
    values.forEach((value, index) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (index === 5 && product.product_id === report.summary?.lowest_price_product_id) {
        cell.className = "best-price";
      }
      row.append(cell);
    });
    tbody.append(row);
  });
  table.append(thead, tbody);
  scroll.append(table);
  block.append(heading, scroll);
  section.append(block);
  return section;
}

function appendAssistantResponse(response) {
  const article = newMessage("assistant", "SYNTHESIS");
  const answer = document.createElement("div");
  answer.className = "assistant-answer";
  answer.textContent = cleanAnswerText(
    response.answer || response.error || "Không nhận được phản hồi từ agent."
  );
  article.append(answer);

  const products = renderProducts(response.products);
  const report = renderReport(response.report);
  if (products) article.append(products);
  if (report) article.append(report);
  elements.messages.append(article);
  refreshIcons();
  scrollMessages();
}

function scrollMessages() {
  requestAnimationFrame(() => {
    elements.messages.scrollTop = elements.messages.scrollHeight;
  });
}

function addTraceEntry(lines, latency) {
  elements.traceEmpty?.remove();
  const entry = document.createElement("div");
  entry.className = "trace-entry";
  const time = document.createElement("div");
  time.className = "trace-time";
  time.textContent = clockTime();
  const content = document.createElement("div");
  content.className = "trace-content";
  lines.forEach(({ text, type = "info" }) => {
    const line = document.createElement("div");
    line.className = `trace-line ${type}`;
    line.textContent = text;
    content.append(line);
  });
  if (latency !== undefined && latency !== null) {
    const metric = document.createElement("div");
    metric.className = "trace-latency";
    metric.textContent = `${latency} ms`;
    content.append(metric);
  }
  entry.append(time, content);
  elements.traceLog.append(entry);
  elements.traceLog.scrollTop = elements.traceLog.scrollHeight;
}

function renderTrace(trace, totalMs) {
  (trace || []).forEach((event, index) => {
    window.setTimeout(() => {
      const lines = [];
      if (event.thought) {
        lines.push({ text: `Decision: ${event.thought}` });
      }
      if (event.action_type === "TOOL_EXECUTION") {
        lines.push({
          text: `Action → ${event.tool_name}(${JSON.stringify(event.arguments)})`,
          type: "action",
        });
        const status = event.observation?.status || "UNKNOWN";
        lines.push({
          text: `Observation → ${status}`,
          type: status === "SUCCESS" ? "success" : "warning",
        });
      } else if (event.action_type === "FINAL_ANSWER") {
        lines.push({ text: "Final answer emitted", type: "success" });
      } else if (event.action_type !== "FINAL_ANSWER") {
        lines.push({ text: event.action_type, type: "warning" });
      }
      const latency = event.llm_latency_ms ?? event.tool_latency_ms;
      addTraceEntry(lines, latency);
      if (index === trace.length - 1) {
        addTraceEntry([{ text: `Request complete · ${totalMs} ms`, type: "success" }]);
      }
    }, index * 130);
  });
}

function openInspector(product) {
  elements.inspectorBody.replaceChildren();
  const badge = document.createElement("div");
  badge.className = "inspector-badge";
  badge.textContent = `${product.category.toUpperCase()} // ${product.product_id}`;
  const title = document.createElement("h2");
  title.textContent = product.name;
  const price = document.createElement("div");
  price.className = "inspector-price";
  price.textContent = formatPrice(product.price_vnd);
  const specs = document.createElement("dl");
  specs.className = "spec-list";
  const values = [
    ["Thương hiệu", product.brand],
    ["CPU", product.cpu],
    ["RAM", product.ram_gb ? `${product.ram_gb} GB` : null],
    ["Lưu trữ", product.storage_gb ? `${product.storage_gb} GB` : null],
    ["Màn hình", product.display],
  ];
  values.filter(([, value]) => value).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "spec-row";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    row.append(term, description);
    specs.append(row);
  });
  const notice = document.createElement("div");
  notice.className = "mock-notice";
  notice.textContent = "Dữ liệu minh họa phục vụ bài lab, không phải giá bán thời gian thực hoặc khuyến nghị mua hàng.";
  elements.inspectorBody.append(badge, title, price, specs, notice);
  elements.inspector.classList.add("is-open");
  elements.inspector.setAttribute("aria-hidden", "false");
}

function closeInspector() {
  elements.inspector.classList.remove("is-open");
  elements.inspector.setAttribute("aria-hidden", "true");
}

function setLoading(value) {
  isLoading = value;
  document.querySelectorAll(".send-button").forEach((button) => {
    button.disabled = value;
  });
}

async function submitMessage(message) {
  const normalized = message.trim();
  if (!normalized || isLoading) return;

  showConversation();
  appendUserMessage(normalized);
  appendLoadingMessage();
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: normalized }),
    });
    if (!response.ok) {
      const failure = await response.json().catch(() => ({}));
      throw new Error(failure.detail?.[0]?.msg || `HTTP ${response.status}`);
    }
    const payload = await response.json();
    removeLoadingMessage();
    appendAssistantResponse(payload);
    renderTrace(payload.trace, payload.total_ms);
  } catch (error) {
    removeLoadingMessage();
    appendAssistantResponse({ error: `Không thể kết nối agent: ${error.message}` });
    addTraceEntry([{ text: `Request failed: ${error.message}`, type: "warning" }]);
  } finally {
    setLoading(false);
    elements.chatInput.focus();
  }
}

function resetChat() {
  if (isLoading) return;
  elements.messages.replaceChildren();
  elements.traceLog.replaceChildren();
  const empty = document.createElement("div");
  empty.className = "trace-empty";
  empty.id = "trace-empty";
  empty.append(icon("activity"));
  const label = document.createElement("span");
  label.textContent = "Awaiting query...";
  empty.append(label);
  elements.traceLog.append(empty);
  elements.traceEmpty = empty;
  elements.conversation.classList.add("is-hidden");
  elements.home.classList.remove("is-hidden");
  closeInspector();
  elements.heroInput.focus();
  refreshIcons();
}

function openTrace() {
  elements.tracePanel.classList.add("is-open");
  elements.backdrop.classList.add("is-open");
}

function closeTrace() {
  elements.tracePanel.classList.remove("is-open");
  elements.backdrop.classList.remove("is-open");
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    elements.catalogCount.textContent = `catalog: ${health.catalog_size} items`;
    const provider = health.provider.replace("Provider", "").replace("Offline", "");
    elements.providerLabel.textContent = `${provider.toUpperCase()} // ${health.mode.toUpperCase()}`;
    elements.traceModel.textContent = `${health.mcp_server} · ${health.model}`;
    elements.connection.classList.add("is-online");
  } catch {
    elements.providerLabel.textContent = "BACKEND OFFLINE";
    elements.connection.classList.add("is-error");
    elements.traceModel.textContent = "Backend connection unavailable";
  }
}

elements.heroForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.heroInput.value;
  elements.heroInput.value = "";
  autoResize(elements.heroInput);
  submitMessage(message);
});

elements.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.chatInput.value;
  elements.chatInput.value = "";
  autoResize(elements.chatInput);
  submitMessage(message);
});

[elements.heroInput, elements.chatInput].forEach((textarea) => {
  textarea.addEventListener("input", () => autoResize(textarea));
  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      textarea.closest("form").requestSubmit();
    }
  });
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => submitMessage(button.dataset.query));
});

document.querySelector("#new-chat").addEventListener("click", resetChat);
document.querySelector("#brand-button").addEventListener("click", resetChat);
document.querySelector("#trace-toggle").addEventListener("click", openTrace);
document.querySelector("#trace-close").addEventListener("click", closeTrace);
document.querySelector("#mobile-backdrop").addEventListener("click", closeTrace);
document.querySelector("#inspector-close").addEventListener("click", closeInspector);

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeInspector();
    closeTrace();
  }
});

window.addEventListener("load", () => {
  refreshIcons();
  loadHealth();
  elements.heroInput.focus();
});
