// Backend manzili — boshqa serverda ishlatilsa faqat shu qatorni o'zgartiring
const API_URL = "http://127.0.0.1:8000";

const TIMEZONE = "Asia/Tashkent";

const els = {
  month: document.getElementById("month"),
  summary: document.getElementById("debtors-summary"),
  status: document.getElementById("debtors-status"),
  list: document.getElementById("debtors-list"),
  form: document.getElementById("payment-form"),
  student: document.getElementById("student"),
  amount: document.getElementById("amount"),
  date: document.getElementById("date"),
  submit: document.getElementById("submit-btn"),
  formMessage: document.getElementById("form-message"),
};

// ---------- Yordamchi funksiyalar ----------

// Bugungi sana Toshkent vaqti bo'yicha, "YYYY-MM-DD" (en-CA formati aynan shunday)
function todayInTashkent() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function formatNumber(value) {
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function formatMoney(value) {
  return `${formatNumber(value)} so'm`;
}

function setStatus(el, text, type = "") {
  el.textContent = text;
  el.className = type ? `status ${type}` : "status";
}

// Barcha so'rovlar shu yerdan o'tadi: backend xatosini {"error": {...}} dan o'qiydi
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(API_URL + path, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
  } catch (networkError) {
    throw new Error("Server bilan aloqa yo'q. Backend ishga tushganini tekshiring.");
  }

  if (response.status === 204) {
    return null;
  }

  let data = null;
  try {
    data = await response.json();
  } catch (parseError) {
    data = null;
  }

  if (!response.ok) {
    const message = data && data.error && data.error.message;
    throw new Error(message || `Xato: HTTP ${response.status}`);
  }
  return data;
}

// ---------- Qarzdorlar ro'yxati ----------

// Oy tez-tez almashtirilsa, faqat oxirgi so'rov natijasi ko'rsatiladi
let debtorsRequestId = 0;

async function loadDebtors() {
  const month = els.month.value;
  if (!month) {
    setStatus(els.status, "Oyni tanlang.", "error");
    return;
  }

  const requestId = ++debtorsRequestId;
  setStatus(els.status, "Yuklanmoqda...");
  els.list.setAttribute("aria-busy", "true");

  try {
    const debtors = await request(`/debtors?month=${encodeURIComponent(month)}`);
    if (requestId !== debtorsRequestId) return;
    renderDebtors(debtors);
    setStatus(els.status, debtors.length ? "" : "Bu oyda qarzdorlar yo'q.");
  } catch (error) {
    if (requestId !== debtorsRequestId) return;
    els.list.replaceChildren();
    els.summary.hidden = true;
    setStatus(els.status, error.message, "error");
  } finally {
    if (requestId === debtorsRequestId) {
      els.list.removeAttribute("aria-busy");
    }
  }
}

function renderDebtors(debtors) {
  const items = debtors.map((debtor) => {
    const li = document.createElement("li");
    li.className = "debtor";

    const info = document.createElement("div");

    const name = document.createElement("div");
    name.className = "debtor-name";
    name.textContent = debtor.name;

    const meta = document.createElement("div");
    meta.className = "debtor-meta";
    const phone = document.createElement("a");
    phone.href = `tel:${debtor.phone}`;
    phone.textContent = debtor.phone;
    meta.append(`${debtor.group} · `, phone);

    info.append(name, meta);

    const amount = document.createElement("div");
    amount.className = "debtor-amount";

    const debt = document.createElement("div");
    debt.className = "debtor-debt";
    debt.textContent = formatMoney(debtor.debt);

    const paid = document.createElement("div");
    paid.className = "debtor-paid";
    paid.textContent = `to'landi ${formatNumber(debtor.paid)} / ${formatMoney(debtor.monthly_fee)}`;

    amount.append(debt, paid);
    li.append(info, amount);
    return li;
  });

  els.list.replaceChildren(...items);

  if (debtors.length) {
    const total = debtors.reduce((sum, d) => sum + d.debt, 0);
    els.summary.replaceChildren(
      `${debtors.length} ta qarzdor, jami qarz: `,
      Object.assign(document.createElement("strong"), { textContent: formatMoney(total) })
    );
    els.summary.hidden = false;
  } else {
    els.summary.hidden = true;
  }
}

// ---------- O'quvchilar ro'yxati (select) ----------

async function loadStudents() {
  els.student.disabled = true;
  try {
    const students = await request("/students");
    const placeholder = new Option(
      students.length ? "O'quvchini tanlang" : "O'quvchilar yo'q",
      ""
    );
    const options = students.map(
      (s) => new Option(`${s.name} — ${s.group} (${formatMoney(s.monthly_fee)})`, String(s.id))
    );
    els.student.replaceChildren(placeholder, ...options);
    els.student.disabled = students.length === 0;
  } catch (error) {
    els.student.replaceChildren(new Option("Yuklab bo'lmadi", ""));
    setStatus(els.formMessage, `O'quvchilar ro'yxati: ${error.message}`, "error");
  }
}

// ---------- To'lov qo'shish ----------

function readPaymentForm() {
  const studentId = Number(els.student.value);
  const amountText = els.amount.value.trim();
  const amount = Number(amountText);
  const date = els.date.value;

  if (!studentId) {
    return { error: "O'quvchini tanlang." };
  }
  if (!amountText || !Number.isInteger(amount) || amount <= 0) {
    return { error: "Summa musbat butun son bo'lishi kerak." };
  }
  if (!date) {
    return { error: "Sanani kiriting." };
  }
  return { payload: { student_id: studentId, amount, date } };
}

async function handlePaymentSubmit(event) {
  event.preventDefault();

  const { error, payload } = readPaymentForm();
  if (error) {
    setStatus(els.formMessage, error, "error");
    return;
  }

  els.submit.disabled = true;
  els.submit.textContent = "Saqlanmoqda...";
  setStatus(els.formMessage, "");

  try {
    await request("/payments", { method: "POST", body: JSON.stringify(payload) });
    const studentName = els.student.selectedOptions[0].textContent.split(" — ")[0];
    setStatus(
      els.formMessage,
      `${studentName}: ${formatMoney(payload.amount)} to'lov saqlandi.`,
      "success"
    );
    els.amount.value = "";
    await loadDebtors();
  } catch (requestError) {
    setStatus(els.formMessage, requestError.message, "error");
  } finally {
    els.submit.disabled = false;
    els.submit.textContent = "Saqlash";
  }
}

// ---------- Ishga tushirish ----------

function init() {
  const today = todayInTashkent();
  els.month.value = today.slice(0, 7);
  els.date.value = today;
  els.date.max = today; // backend kelajakdagi sanani qabul qilmaydi

  els.month.addEventListener("change", loadDebtors);
  els.form.addEventListener("submit", handlePaymentSubmit);

  loadDebtors();
  loadStudents();
}

init();
