const fs = require("fs");
const path = require("path");

function loadEnv(file) {
  try {
    const content = fs.readFileSync(file, "utf8");
    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq === -1) continue;
      const key = trimmed.slice(0, eq).trim();
      const value = trimmed.slice(eq + 1).trim();
      if (!(key in process.env)) process.env[key] = value;
    }
  } catch {
    /* no .env file */
  }
}

loadEnv(path.join(__dirname, ".env"));

const express = require("express");
const nodemailer = require("nodemailer");
const crypto = require("crypto");

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, "data");
const CONTACTS_FILE = path.join(DATA_DIR, "contacts.json");
const BOOKINGS_FILE = path.join(DATA_DIR, "bookings.json");

fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(CONTACTS_FILE)) fs.writeFileSync(CONTACTS_FILE, "[]");
if (!fs.existsSync(BOOKINGS_FILE)) fs.writeFileSync(BOOKINGS_FILE, "[]");

app.use(express.json());
app.use(express.static(path.join(__dirname)));

const SMTP_ENABLED =
  process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS;

let transporter = null;
if (SMTP_ENABLED) {
  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 465),
    secure: String(process.env.SMTP_SECURE || "true").toLowerCase() === "true",
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function writeJson(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + "\n");
}

function sendEmail(subject, text, replyTo) {
  if (!SMTP_ENABLED) return Promise.resolve(false);
  return transporter.sendMail({
    from: `"${process.env.NOTIFY_NAME || "Kim's Hems"}" <${process.env.NOTIFY_EMAIL || process.env.SMTP_USER}>`,
    to: process.env.NOTIFY_EMAIL || process.env.SMTP_USER,
    replyTo: replyTo || process.env.NOTIFY_EMAIL,
    subject,
    text
  });
}

function handleError(name) {
  console.error(`[${name}] Failed to process submission`);
  return { ok: false, error: "Something went wrong. Please try again later." };
}

app.post("/api/contact", (req, res) => {
  const { name, email, service, message } = req.body || {};

  if (!name || !email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ ok: false, error: "Name and a valid email are required." });
  }

  const entry = {
    id: crypto.randomUUID(),
    type: "contact",
    name: String(name).trim(),
    email: String(email).trim(),
    service: String(service || ""),
    message: String(message || "").trim(),
    createdAt: new Date().toISOString()
  };

  try {
    const records = readJson(CONTACTS_FILE);
    records.push(entry);
    writeJson(CONTACTS_FILE, records);
  } catch (err) {
    console.error(err);
    return res.status(500).json(handleError("contact"));
  }

  sendEmail(
    `New contact message from ${entry.name}`,
    `Name: ${entry.name}\nEmail: ${entry.email}\nService: ${entry.service || "n/a"}\n\nMessage:\n${entry.message || "(no message)"}`,
    entry.email
  ).catch((err) => console.error("[contact] email failed:", err.message));

  res.json({ ok: true });
});

app.post("/api/book", (req, res) => {
  const { name, email, phone, service, date, time, notes } = req.body || {};

  if (!name || !email || !date || !time) {
    return res.status(400).json({ ok: false, error: "Name, email, date and time are required." });
  }

  const entry = {
    id: crypto.randomUUID(),
    type: "booking",
    name: String(name).trim(),
    email: String(email).trim(),
    phone: String(phone || "").trim(),
    service: String(service || ""),
    date: String(date),
    time: String(time),
    notes: String(notes || "").trim(),
    createdAt: new Date().toISOString()
  };

  try {
    const records = readJson(BOOKINGS_FILE);
    records.push(entry);
    writeJson(BOOKINGS_FILE, records);
  } catch (err) {
    console.error(err);
    return res.status(500).json(handleError("booking"));
  }

  sendEmail(
    `New fitting request: ${entry.name} on ${entry.date} at ${entry.time}`,
    `Name: ${entry.name}\nEmail: ${entry.email}\nPhone: ${entry.phone || "n/a"}\nService: ${entry.service || "n/a"}\n\nPreferred date: ${entry.date}\nPreferred time: ${entry.time}\n\nNotes:\n${entry.notes || "(none)"}`,
    entry.email
  ).catch((err) => console.error("[booking] email failed:", err.message));

  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`Kim's Hems site running at http://localhost:${PORT}`);
  console.log(SMTP_ENABLED ? "SMTP notifications enabled." : "SMTP not configured — submissions saved to /data only.");
});