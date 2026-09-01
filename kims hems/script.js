document.getElementById("year").textContent = new Date().getFullYear();

const toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");

toggle.addEventListener("click", () => {
  const open = links.classList.toggle("open");
  toggle.classList.toggle("open", open);
  toggle.setAttribute("aria-expanded", open);
});

links.addEventListener("click", (e) => {
  if (e.target.tagName === "A") {
    links.classList.remove("open");
    toggle.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  }
});

async function postForm(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!res.ok && res.status !== 400) throw new Error("Request failed");
  return res.json();
}

function setStatus(el, text, kind) {
  el.textContent = text;
  el.className = `form-status${kind ? ` ${kind}` : ""}`;
}

function setupContactForm(formId, statusId) {
  const form = document.getElementById(formId);
  const status = document.getElementById(statusId);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      name: form.name.value.trim(),
      email: form.email.value.trim(),
      service: form.service.value,
      message: form.message.value.trim()
    };

    if (!data.name || !data.email) {
      setStatus(status, "Please fill in your name and email.", "error");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
      setStatus(status, "Please enter a valid email address.", "error");
      return;
    }

    setStatus(status, "Sending...", "");

    try {
      const res = await postForm("/api/contact", data);
      if (!res.ok) throw new Error(res.error || "Request failed");

      setStatus(status, "Thank you! Your message has been sent. We'll be in touch.", "success");
      form.reset();
    } catch (err) {
      setStatus(status, "Sorry, something went wrong. Please call us at (404) 819-2045 or email kim@kimshems.com.", "error");
    }
  });
}

setupContactForm("contact-form", "form-status");

const bookingForm = document.getElementById("booking-form");
const bookingStatus = document.getElementById("booking-status");

bookingForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    name: bookingForm.name.value.trim(),
    email: bookingForm.email.value.trim(),
    phone: bookingForm.phone.value.trim(),
    service: bookingForm.service.value,
    date: bookingForm.date.value,
    time: bookingForm.time.value,
    notes: bookingForm.notes.value.trim()
  };

  if (!data.name || !data.email || !data.date || !data.time) {
    setStatus(bookingStatus, "Please fill in your name, email, date and time.", "error");
    return;
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    setStatus(bookingStatus, "Please enter a valid email address.", "error");
    return;
  }

  setStatus(bookingStatus, "Sending...", "");

  try {
    const res = await postForm("/api/book", data);
    if (!res.ok) throw new Error(res.error || "Request failed");

    setStatus(bookingStatus, "Thank you! Your appointment request has been sent. We'll confirm your time shortly.", "success");
    bookingForm.reset();
  } catch (err) {
    setStatus(bookingStatus, "Sorry, something went wrong. Please call us at (404) 819-2045 to book.", "error");
  }
});

bookingForm.date.min = new Date().toISOString().split("T")[0];