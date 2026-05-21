const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  BorderStyle, LevelFormat, HeadingLevel, PageNumber,
  Header, Footer, TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

const gold  = "C9A84C";
const navy  = "152638";
const black = "000000";
const gray  = "555555";

const ruled = {
  border: {
    bottom: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC", space: 1 }
  }
};

const sectionHeading = (text) => new Paragraph({
  spacing: { before: 320, after: 120 },
  ...ruled,
  children: [new TextRun({ text, bold: true, size: 26, color: navy, font: "Arial" })]
});

const body = (text, opts = {}) => new Paragraph({
  spacing: { before: 100, after: 100 },
  children: [new TextRun({ text, size: 22, color: gray, font: "Arial", ...opts })]
});

const boldBody = (label, text) => new Paragraph({
  spacing: { before: 100, after: 100 },
  children: [
    new TextRun({ text: label + " ", bold: true, size: 22, color: black, font: "Arial" }),
    new TextRun({ text, size: 22, color: gray, font: "Arial" })
  ]
});

const blank = () => new Paragraph({ spacing: { before: 60, after: 60 }, children: [new TextRun("")] });

const signatureLine = (label) => [
  new Paragraph({
    spacing: { before: 280, after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999", space: 1 } },
    children: [new TextRun({ text: " ", size: 22, font: "Arial" })]
  }),
  new Paragraph({
    spacing: { before: 60, after: 200 },
    children: [new TextRun({ text: label, size: 20, color: gray, font: "Arial", italics: true })]
  })
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: gold, space: 1 } },
            spacing: { after: 0 },
            children: [
              new TextRun({ text: "PLASTIC TRAVEL", bold: true, size: 20, color: gold, font: "Arial", allCaps: true, characterSpacing: 80 }),
              new TextRun({ text: "\tConsulting Agreement", size: 18, color: gray, font: "Arial", italics: true })
            ]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 1 } },
            children: [
              new TextRun({ text: "Plastic Travel  |  plastictravel.com  |  Confidential", size: 18, color: gray, font: "Arial" }),
              new TextRun({ text: "\tPage ", size: 18, color: gray, font: "Arial" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: gray, font: "Arial" })
            ]
          })
        ]
      })
    },
    children: [

      // Title block
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 80 },
        children: [new TextRun({ text: "CONSULTING SERVICES AGREEMENT", bold: true, size: 36, color: navy, font: "Arial", allCaps: true, characterSpacing: 60 })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Plastic Travel  |  Business Advisory Services", size: 22, color: gold, font: "Arial", italics: true })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 400 },
        children: [new TextRun({ text: "This Agreement is entered into as of the date signed below.", size: 20, color: gray, font: "Arial" })]
      }),

      // Parties
      sectionHeading("1.  PARTIES"),
      boldBody("Service Provider:", "Scott Carroll, operating as Plastic Travel (\"Consultant\"), a management consulting and business advisory service."),
      boldBody("Client:", "The individual or business entity identified by signature below (\"Client\")."),

      // Nature of services
      sectionHeading("2.  NATURE OF SERVICES"),
      body("Plastic Travel provides management consulting and business advisory services focused on credit card rewards strategy, points optimization, and related financial efficiency planning. The Consultant is engaged solely as a business advisor."),
      blank(),
      body("THE CONSULTANT IS NOT A TRAVEL AGENCY, AIRLINE TICKET BROKER, FINANCIAL ADVISOR, OR INVESTMENT ADVISOR. No services provided under this Agreement constitute the purchase, sale, or brokerage of airline tickets, hotel reservations, or any travel product. The Client acknowledges that all services rendered are strictly consulting and advisory in nature.", { bold: false, color: "8B0000" }),

      // Scope of work
      sectionHeading("3.  SCOPE OF WORK"),
      body("Services may include one or more of the following, as agreed upon in writing:"),
      blank(),
      ...[
        "Credit card portfolio analysis and optimization strategy",
        "Points and miles accumulation planning",
        "Transfer partner redemption research and recommendations",
        "Award availability research and itinerary guidance",
        "Custom points strategy sessions (\"Deep Dive\" consultations)"
      ].map(item => new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: item, size: 22, color: gray, font: "Arial" })]
      })),
      blank(),
      body("Any additional scope beyond what is agreed in writing requires a separate written amendment to this Agreement."),

      // Fees
      sectionHeading("4.  FEES AND PAYMENT"),
      body("Fees are established prior to engagement and communicated to the Client in writing. All fees must be paid in full before consulting services commence, unless a separate deposit structure is agreed to in writing."),
      blank(),
      boldBody("Accepted Payment Methods:", "Credit card, debit card, or ACH bank transfer via Stripe."),
      boldBody("Invoicing:", "Invoices are issued via Stripe and are due upon receipt unless otherwise stated."),

      // No refund
      sectionHeading("5.  NO REFUND POLICY"),
      body("ALL FEES ARE NON-REFUNDABLE. Once a consulting session has been scheduled or research has commenced, no refunds will be issued under any circumstances.", { bold: true, color: black }),
      blank(),
      body("The Client acknowledges that consulting services involve the time, expertise, and proprietary methodology of the Consultant, and that value is delivered regardless of whether the Client acts on the recommendations provided."),

      // No guarantee
      sectionHeading("6.  NO GUARANTEE OF RESULTS"),
      body("The Consultant makes no guarantee, warranty, or representation regarding the outcome of any recommendations provided. Points valuations, award availability, transfer partner ratios, and loyalty program terms are subject to change by third-party programs at any time without notice."),
      blank(),
      body("The Client accepts full responsibility for any decisions made based on Consultant recommendations, including but not limited to credit card applications, points transfers, or travel bookings."),

      // Chargeback
      sectionHeading("7.  DISPUTE RESOLUTION — NO CHARGEBACKS"),
      body("The Client agrees that any dispute regarding services rendered must be communicated directly to the Consultant in writing at scott@plastictravel.com within 10 business days of the service date. The parties agree to make a good-faith effort to resolve disputes directly before involving any third party."),
      blank(),
      body("THE CLIENT EXPRESSLY WAIVES THE RIGHT TO INITIATE A CREDIT CARD CHARGEBACK OR PAYMENT DISPUTE WITH THEIR FINANCIAL INSTITUTION FOR SERVICES RENDERED UNDER THIS AGREEMENT. The Client acknowledges that initiating an unauthorized chargeback constitutes a material breach of this Agreement and may result in collection action.", { bold: false, color: "8B0000" }),

      // Confidentiality
      sectionHeading("8.  CONFIDENTIALITY"),
      body("Both parties agree to keep confidential any proprietary information shared during the engagement. The Consultant will not share the Client's financial information, spending data, or travel plans with any third party without written consent."),

      // Limitation of liability
      sectionHeading("9.  LIMITATION OF LIABILITY"),
      body("In no event shall the Consultant's total liability to the Client exceed the total fees paid under this Agreement. The Consultant shall not be liable for any indirect, incidental, or consequential damages arising from the use of or reliance on any advice or recommendations provided."),

      // Governing law
      sectionHeading("10.  GOVERNING LAW"),
      body("This Agreement shall be governed by the laws of the State of Georgia. Any disputes not resolved by direct negotiation shall be submitted to binding arbitration in Georgia before a single arbitrator under the rules of the American Arbitration Association."),

      // Entire agreement
      sectionHeading("11.  ENTIRE AGREEMENT"),
      body("This Agreement constitutes the entire understanding between the parties with respect to the subject matter herein and supersedes all prior discussions, representations, or agreements. Modifications must be made in writing and signed by both parties."),

      // Signatures
      sectionHeading("12.  SIGNATURES"),
      body("By signing below, both parties acknowledge that they have read, understood, and agree to the terms of this Consulting Services Agreement."),
      blank(),
      blank(),

      new Paragraph({
        spacing: { before: 120, after: 0 },
        children: [new TextRun({ text: "SERVICE PROVIDER — Plastic Travel", bold: true, size: 22, color: navy, font: "Arial" })]
      }),
      ...signatureLine("Scott Carroll  |  Plastic Travel  |  Date"),

      new Paragraph({
        spacing: { before: 120, after: 0 },
        children: [new TextRun({ text: "CLIENT", bold: true, size: 22, color: navy, font: "Arial" })]
      }),
      ...signatureLine("Printed Name  |  Title / Company  |  Date"),
      ...signatureLine("Signature"),

    ]
  }],
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]
    }]
  }
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/scott/projects/plastictravel_docs/Plastic_Travel_Consulting_Agreement.docx", buffer);
  console.log("Done.");
});
