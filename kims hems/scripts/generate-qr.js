const QRCode = require("qrcode");
const path = require("path");

const vcard = [
  "BEGIN:VCARD",
  "VERSION:3.0",
  "N:Carroll;Kim;;;",
  "FN:Kim Carroll",
  "ORG:Kim's Hems",
  "TITLE:Alterations Specialist",
  "TEL;TYPE=CELL:+1 404-819-2045",
  "EMAIL:kim@kimshems.com",
  "URL:https://kimshems.com",
  "ADR;TYPE=WORK:;;616 Huntwood Cir;Temple;GA;30179;USA",
  "END:VCARD"
].join("\n");

const out = path.join(__dirname, "..", "qr-contact.png");

QRCode.toFile(out, vcard, { width: 600, margin: 2 }, (err) => {
  if (err) {
    console.error("Failed to generate QR code:", err);
    process.exit(1);
  }
  console.log("QR code written to", out);
});