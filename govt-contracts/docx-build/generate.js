const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, Header, Footer, PageNumber, LevelFormat, UnderlineType,
  ImageRun
} = require("docx");
const fs = require("fs");

const logoData = fs.readFileSync("/home/scott/projects/govt-contracts/brisar-logo-header.png");

const BLUE = "1F4E79";
const LIGHT_BLUE = "D6E4F0";
const DARK_GRAY = "404040";
const RED_ALERT = "C00000";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function heading1(text) {
  return new Paragraph({
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: BLUE, font: "Arial" })]
  });
}

function heading2(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: DARK_GRAY, font: "Arial" })]
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 20, font: "Arial", ...opts })]
  });
}

function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial", bold })]
  });
}

function alertBullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial", bold: true, color: RED_ALERT })]
  });
}

function spacer() {
  return new Paragraph({ spacing: { before: 80, after: 80 }, children: [new TextRun("")] });
}

function divider() {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE } },
    children: [new TextRun("")]
  });
}

function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: { fill: BLUE, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.LEFT,
      children: [new TextRun({ text, bold: true, size: 18, color: "FFFFFF", font: "Arial" })]
    })]
  });
}

function dataCell(text, width, shade = false, bold = false, color = null) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: { fill: shade ? LIGHT_BLUE : "FFFFFF", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      children: [new TextRun({ text, size: 18, font: "Arial", bold, color: color || "000000" })]
    })]
  });
}

// --- STRUCTURES TABLE ---
const structuresTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [800, 2800, 1200, 4560],
  rows: [
    new TableRow({ children: [headerCell("#", 800), headerCell("Structure Name", 2800), headerCell("Size", 1200), headerCell("Notes", 4560)] }),
    new TableRow({ children: [dataCell("1", 800), dataCell("Griffith Dairy Farmhouse", 2800), dataCell("~1,286 SF", 1200), dataCell("Single level + full basement. Electric service present. Built ~1930. Asbestos abatement completed 2019.", 4560)] }),
    new TableRow({ children: [dataCell("2", 800, true), dataCell("Griffith Dairy Gable Barn", 2800, true), dataCell("~912 SF", 1200, true), dataCell("Two-story timber frame on concrete pilings. No utilities. Built early 1930s.", 4560, true)] }),
    new TableRow({ children: [dataCell("3", 800), dataCell("Griffith Dairy Shed", 2800), dataCell("~96 SF", 1200), dataCell("Small stick-built structure. No utilities. Built ~1930.", 4560)] }),
    new TableRow({ children: [dataCell("", 800, false, true), dataCell("TOTAL", 2800, false, true), dataCell("~2,294 SF", 1200, false, true), dataCell("", 4560, false)] }),
  ]
});

// --- WAGE TABLE ---
const wageTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3360, 2000, 2000, 2000],
  rows: [
    new TableRow({ children: [headerCell("Role", 3360), headerCell("Min. Hourly Wage", 2000), headerCell("Fringe / H&W", 2000), headerCell("Total Floor", 2000)] }),
    new TableRow({ children: [dataCell("Laborer", 3360), dataCell("$18.84", 2000), dataCell("$5.55", 2000), dataCell("$24.39", 2000, false, true)] }),
    new TableRow({ children: [dataCell("Heavy Equipment Operator", 3360, true), dataCell("$26.95", 2000, true), dataCell("$5.55", 2000, true), dataCell("$32.50", 2000, true, true)] }),
    new TableRow({ children: [dataCell("Tractor Operator", 3360), dataCell("$24.23", 2000), dataCell("$5.55", 2000), dataCell("$29.78", 2000, false, true)] }),
    new TableRow({ children: [dataCell("Heavy Truck Driver", 3360, true), dataCell("$26.68", 2000, true), dataCell("$5.55", 2000, true), dataCell("$32.23", 2000, true, true)] }),
    new TableRow({ children: [dataCell("General Maintenance Worker", 3360), dataCell("$22.40", 2000), dataCell("$5.55", 2000), dataCell("$27.95", 2000, false, true)] }),
  ]
});

// --- HEADER INFO BOX ---
const infoTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2200, 7160],
  rows: [
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Project", bold: true, size: 18, color: "FFFFFF", font: "Arial" })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Cole Ranch Farmhouse Demolition", size: 18, font: "Arial" })] })] }),
    ]}),
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: "FFFFFF", type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Location", bold: true, size: 18, font: "Arial", color: DARK_GRAY })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "670 Cole Ranch Rd, Durango, CO 81303  |  San Juan National Forest / La Plata County", size: 18, font: "Arial" })] })] }),
    ]}),
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Prime Contractor", bold: true, size: 18, font: "Arial", color: DARK_GRAY })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Brisar Investments LLC", size: 18, font: "Arial", bold: true })] })] }),
    ]}),
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: "FFFFFF", type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Project Period", bold: true, size: 18, font: "Arial", color: DARK_GRAY })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "June 8, 2026 – July 8, 2026  (30 calendar days)", size: 18, font: "Arial" })] })] }),
    ]}),
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Work Hours", bold: true, size: 18, font: "Arial", color: DARK_GRAY })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "7:00 AM – 5:00 PM, Monday–Friday only (no federal holidays)", size: 18, font: "Arial" })] })] }),
    ]}),
    new TableRow({ children: [
      new TableCell({ width: { size: 2200, type: WidthType.DXA }, borders, shading: { fill: RED_ALERT, type: ShadingType.CLEAR }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Quote Deadline", bold: true, size: 18, color: "FFFFFF", font: "Arial" })] })] }),
      new TableCell({ width: { size: 7160, type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "May 22, 2026  |  Scott Carroll  |  scottqcarroll@gmail.com", size: 18, font: "Arial", bold: true, color: RED_ALERT })] })] }),
    ]}),
  ]
});

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 540, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE } },
            spacing: { after: 100 },
            children: [
              new ImageRun({
                type: "png",
                data: logoData,
                transformation: { width: 200, height: 60 },
                altText: { title: "Brisar Investments LLC", description: "Brisar Logo", name: "BrisarLogo" }
              }),
              new TextRun({ text: "     SUBCONTRACTOR SCOPE OF WORK  —  CONFIDENTIAL", size: 18, color: DARK_GRAY, font: "Arial" }),
            ]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: BLUE } },
          spacing: { before: 120 },
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Brisar Investments LLC  |  USDA Forest Service, San Juan National Forest  |  Page ", size: 16, color: DARK_GRAY, font: "Arial" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: DARK_GRAY, font: "Arial" }),
          ]
        })]
      })
    },
    children: [
      // TITLE BLOCK
      new Paragraph({
        spacing: { before: 160, after: 120 },
        alignment: AlignmentType.CENTER,
        children: [
          new ImageRun({
            type: "png",
            data: logoData,
            transformation: { width: 320, height: 96 },
            altText: { title: "Brisar Investments LLC", description: "Brisar Logo", name: "BrisarLogoMain" }
          })
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "SUBCONTRACTOR SCOPE OF WORK  &  REQUEST FOR QUOTE", bold: true, size: 32, color: BLUE, font: "Arial" })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 240 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Cole Ranch Farmhouse Demolition  |  USDA Forest Service", size: 22, color: DARK_GRAY, font: "Arial" })]
      }),

      // INFO TABLE
      infoTable,
      spacer(),
      divider(),

      // SECTION 1
      heading1("SECTION 1: PROJECT OVERVIEW"),
      body("Brisar Investments LLC is the prime contractor on a USDA Forest Service contract requiring the complete demolition and removal of three (3) structures on Forest Service property at Cole Ranch outside Durango, CO."),
      spacer(),
      body("Asbestos abatement was completed in 2019. Historic preservation (SHPO) clearance has been obtained for all three structures. No asbestos or historic preservation work is required of the subcontractor."),
      spacer(),
      body("We are requesting a firm fixed-price quote from your company to perform all demolition, debris removal, and site restoration work described below.", { bold: true }),
      divider(),

      // SECTION 2
      heading1("SECTION 2: STRUCTURES TO BE DEMOLISHED"),
      spacer(),
      structuresTable,
      spacer(),
      divider(),

      // SECTION 3
      heading1("SECTION 3: SCOPE OF WORK"),

      heading2("3.1  Pre-Work Requirements"),
      bullet("Attend a mandatory pre-work site meeting with the Forest Service COR before any demolition begins"),
      bullet("Perform a site visit to assess conditions and confirm scope"),
      bullet("Obtain all required dig permits and utility locates prior to any excavation"),
      bullet("Coordinate utility disconnection with applicable service providers (electric at Farmhouse)"),
      spacer(),

      heading2("3.2  Utility Disconnection"),
      bullet("Locate, disconnect, isolate, and cap all overhead and underground utilities at the Farmhouse (electric service present)"),
      bullet("Cap and plug all utilities to a minimum of 3 feet below finished grade"),
      bullet("Confirm all utility services are disconnected back to the utility source before demolition begins on any structure"),
      bullet("Coordinate with utility provider and notify the COR during execution"),
      spacer(),

      heading2("3.3  Demolition — All Three Structures"),
      bullet("Complete structural demolition of all three structures including roofs, walls, floors, foundations, concrete slabs, and all appurtenances"),
      bullet("Remove all above and below-ground structure materials to a minimum depth of 3 feet below finished grade"),
      bullet("Segregate materials for recycling where practical (metal, clean concrete)"),
      bullet("Control dust, noise, and vibration at all times; prevent offsite migration of debris"),
      spacer(),

      heading2("3.4  Septic System"),
      bullet("If septic tanks are encountered: tanks still in use shall not be damaged; tanks no longer in use shall be pumped dry, crushed, and backfilled in accordance with federal, state, and local regulations"),
      bullet("All dig permits and utility locates must be completed and approved before any digging begins"),
      spacer(),

      heading2("3.5  Debris Removal & Disposal"),
      bullet("Remove 100% of demolition debris from federal property"),
      bullet("Transport and dispose of all materials at a licensed and permitted disposal facility"),
      bullet("Provide signed manifests and receipts identifying the disposal facility name, address, and quantities — these are required by the government and must be turned over to Brisar upon completion"),
      spacer(),

      heading2("3.6  Site Restoration — Backfill & Grading"),
      bullet("Backfill all foundation voids and basement with common fill material, compacted to match adjacent grades"),
      bullet("Farmhouse basement requires approximately 200 cubic yards of common fill material — include material, delivery, placement, and compaction in your quote", true),
      bullet("Ensure positive drainage away from all backfilled areas"),
      bullet("Remove all above-grade remnants, foundation materials, and temporary site facilities"),
      bullet("All restored areas shall be smoothly and evenly dressed and sloped to drain"),
      bullet("Repair any damage to roads, ditches, culverts, or gates caused by operations"),
      bullet("NOTE: Seeding/revegetation is NOT required", true),
      spacer(),

      heading2("3.7  Safety & Site Management"),
      bullet("Install fencing or barricades as needed for public and animal safety throughout the project"),
      bullet('Post "Construction Area – Keep Out" signage'),
      bullet("Maintain orderly staging area; no overnight waste accumulation outside containers"),
      bullet("Continuously evaluate structural conditions before, during, and after demolition and take immediate action to protect all personnel"),
      bullet("No structural element shall be left standing without sufficient bracing, shoring, or lateral support while workers are in the area"),
      spacer(),

      heading2("3.8  Special Site Conditions"),
      alertBullet("ACTIVE HORSE BARN is located on the property — staging, laydown areas, and all operations must protect livestock at all times"),
      bullet("Install drip pans under all stationary equipment"),
      bullet("Use only approved staging and laydown areas; protect all soils and vegetation outside the work zone"),
      bullet("Dust suppression: use water or approved suppressants to prevent fugitive dust from leaving the property"),
      bullet("Fire prevention: no equipment idling that risks ignition; obtain hot work permits as applicable; maintain fire extinguishers on site at all times"),
      bullet("Site security: remove keys from all equipment when unattended; lock all gates per direction of the Forest Service"),
      bullet("Weather shutdowns: suspend operations if conditions pose safety or environmental risk (high winds, heavy precipitation)"),
      divider(),

      // SECTION 4 - WAGE COMPLIANCE
      heading1("SECTION 4: WAGE & LABOR COMPLIANCE REQUIREMENTS"),
      body("This contract is subject to the Service Contract Act (SCA), FAR 52.222-41. The following wage determination issued by the U.S. Department of Labor applies to ALL work performed under this subcontract:"),
      spacer(),
      new Paragraph({
        spacing: { before: 80, after: 80 },
        children: [
          new TextRun({ text: "Wage Determination No. 2015-5435, Revision 30 (dated 3/30/2026)", bold: true, size: 22, color: BLUE, font: "Arial" }),
        ]
      }),
      body("Covers: La Plata County, Colorado"),
      spacer(),
      body("As a subcontractor on a federal contract, you are legally required to pay all employees performing work on this project no less than the following minimum rates:"),
      spacer(),
      wageTable,
      spacer(),
      body("Fringe benefits may be paid as cash in addition to the hourly wage or through a bona fide benefits plan. The health & welfare rate is $5.55 per hour, up to 40 hours per week ($222.00/week or $962.00/month)."),
      spacer(),
      body("Paid Sick Leave is required under Executive Order 13706 — employees must accrue 1 hour of paid sick leave for every 30 hours worked on this contract, up to 56 hours per year."),
      spacer(),
      new Paragraph({
        spacing: { before: 80, after: 80 },
        shading: { fill: "FFF2CC", type: ShadingType.CLEAR },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: RED_ALERT } },
        indent: { left: 200 },
        children: [new TextRun({ text: "By submitting a quote and accepting a subcontract, your company certifies that all workers assigned to this project will be compensated in full compliance with WD 2015-5435 Rev 30. Your quote MUST reflect these labor rates. Quotes based on lower labor costs will not be accepted. Brisar Investments LLC reserves the right to request certified payroll records to verify compliance.", size: 20, font: "Arial", bold: true })]
      }),
      divider(),

      // SECTION 5
      heading1("SECTION 5: SITE ACCESS"),
      bullet("Address: 670 Cole Ranch Rd, Durango, CO 81303"),
      bullet("Access via Coal Ranch Road off US Highway 160"),
      bullet("Gate access provided by Forest Service Yale Key (furnished by government to prime contractor)"),
      bullet("Site must be locked and secured at the end of each work day"),
      divider(),

      // SECTION 6
      heading1("SECTION 6: WHAT BRISAR WILL PROVIDE"),
      bullet("Forest Service gate key for site access"),
      bullet("Point of contact with the Forest Service COR"),
      bullet("All required project documentation coordination (QCP, safety plan, manifests)"),
      bullet("Prime contractor oversight and government compliance management"),
      divider(),

      // SECTION 7
      heading1("SECTION 7: QUOTE REQUIREMENTS"),
      body("Please provide a firm fixed-price lump sum quote covering ALL of the following. Quotes that do not address all items will not be considered:"),
      spacer(),
      bullet("Mobilization and demobilization"),
      bullet("Pre-work site visit and utility coordination"),
      bullet("Demolition of all 3 structures (complete, to 3 ft below grade)"),
      bullet("Septic tank handling if encountered"),
      bullet("All debris hauling and licensed disposal (with signed manifests)"),
      bullet("Approximately 200 CY common fill material, delivery, placement, and compaction for Farmhouse basement"),
      bullet("Site grading and restoration"),
      bullet("Dust control, safety fencing, and signage throughout"),
      bullet("All equipment, labor, and supervision for full project duration"),
      spacer(),
      body("Please also include with your quote:", { bold: true }),
      bullet("Estimated crew size and daily schedule"),
      bullet("Name and brief experience summary of your Site Foreman"),
      bullet("References for 1–2 similar demolition projects"),
      bullet("Proof of insurance (general liability and workers compensation)"),
      divider(),

      // SECTION 8
      heading1("SECTION 8: IMPORTANT NOTES"),
      bullet("Work must be completed within 30 calendar days of contract start (June 8 – July 8, 2026)"),
      bullet("Work hours are 7:00 AM – 5:00 PM Monday–Friday ONLY — no weekend or holiday work"),
      bullet("No seeding or revegetation required"),
      bullet("All disposal must be at licensed/permitted facilities — documentation provided to Brisar"),
      bullet("Subcontractor must comply with all USDA/USFS site rules at all times"),
      alertBullet("QUOTE DEADLINE: Must be received by May 22, 2026"),
      divider(),

      // CONTACT FOOTER
      new Paragraph({
        spacing: { before: 200, after: 80 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Questions? Contact:", bold: true, size: 22, color: BLUE, font: "Arial" })]
      }),
      new Paragraph({
        spacing: { before: 60, after: 60 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Scott Carroll  —  Brisar Investments LLC", bold: true, size: 22, font: "Arial" })]
      }),
      new Paragraph({
        spacing: { before: 40, after: 120 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "scottqcarroll@gmail.com", size: 20, font: "Arial", color: BLUE })]
      }),
      new Paragraph({
        spacing: { before: 80, after: 80 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "This subcontract is issued under a federal prime contract with the USDA Forest Service, San Juan National Forest. All work is subject to applicable federal regulations including the Service Contract Act (FAR 52.222-41) and Wage Determination No. 2015-5435 Rev 30.", size: 16, color: "888888", font: "Arial" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/scott/projects/govt-contracts/cole-ranch-sub-scope.docx", buffer);
  console.log("Document created successfully.");
}).catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
