import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(import.meta.dirname, "..");
const outputPath = path.join(projectRoot, "docs", "project", "PROJECT_GANTT.xlsx");
const previewDir = path.join(os.tmpdir(), "converter-project-gantt");

const day = (value) => new Date(`${value}T12:00:00`);
const addDays = (value, count) => {
  const result = new Date(value);
  result.setDate(result.getDate() + count);
  return result;
};

const tasks = [
  ["P0-01", "Phase 0 - Repository", "Repository organization and documentation baseline", "Codex", "Complete", "High", 5, day("2026-06-01"), 1, "", "ROADMAP Phase 0", "Completed before hardware bring-up"],

  ["P1-01", "Phase 1 - Electrical", "Inventory and photograph RP23CNC kits and PCB revision (E-16)", "Project Owner", "Not Started", "High", 2, day("2026-06-15"), 0, "", "Photo + E-16 lab note", ""],
  ["P1-02", "Phase 1 - Electrical", "Solder and inspect RP23CNC connectors and Ethernet components (E-17)", "Project Owner", "Not Started", "High", 4, day("2026-06-17"), 0, "P1-01", "Photos + continuity results", ""],
  ["P1-03", "Phase 1 - Electrical", "Identify driver, sensor, and module revisions", "Project Owner", "Not Started", "Medium", 2, day("2026-06-17"), 0, "P1-01", "Component photos", ""],
  ["P1-04", "Phase 1 - Electrical", "Verify S-120-12 labels, earth continuity, and no-load output (E-11)", "Project Owner", "Not Started", "High", 2, day("2026-06-22"), 0, "P1-02", "E-11 lab note", ""],
  ["P1-05", "Phase 1 - Electrical", "Measure stepper coil pairs and resistance (E-01)", "Project Owner", "Not Started", "High", 1, day("2026-06-24"), 0, "P1-04", "E-01 results", ""],
  ["P1-06", "Phase 1 - Electrical", "Document TB6600 switches and verify STEP/DIR behavior (E-02/E-03)", "Project Owner", "Not Started", "High", 3, day("2026-06-25"), 0, "P1-05", "E-02/E-03 results", ""],
  ["P1-07", "Phase 1 - Electrical", "Characterize N20 actuator current (E-05/E-06)", "Project Owner", "Not Started", "High", 2, day("2026-06-29"), 0, "P1-04", "E-05/E-06 results", ""],
  ["P1-08", "Phase 1 - Electrical", "Calibrate load cell and characterize HX711 rate/noise (E-07/E-08)", "Project Owner", "Not Started", "High", 4, day("2026-07-01"), 0, "P1-07", "Calibration data", ""],
  ["P1-09", "Phase 1 - Electrical", "Verify TMAG5273 readings and geometry (E-09)", "Project Owner", "Not Started", "Medium", 2, day("2026-07-06"), 0, "P1-08", "E-09 results", ""],
  ["P1-10", "Phase 1 - Electrical", "Configure and load-test 6 V buck converter (E-14/E-15)", "Project Owner", "Not Started", "High", 3, day("2026-07-08"), 0, "P1-07", "E-14/E-15 results", ""],
  ["P1-11", "Phase 1 - Electrical", "Complete power budget, fuses, wire gauges, and wiring evidence", "Project Owner", "Not Started", "High", 4, day("2026-07-13"), 0, "P1-04,P1-10", "BOM + wiring table", ""],
  ["P1-GATE", "Phase 1 - Electrical", "Milestone: electrical characterization gate", "Project Owner", "Not Started", "High", 1, day("2026-07-17"), 0, "P1-11", "Phase 1 checklist", "All compatibility gates resolved"],

  ["P2-01", "Phase 2 - Controller", "Build or obtain RP23CNC-compatible grblHAL firmware", "Codex", "Not Started", "High", 5, day("2026-07-20"), 0, "P1-GATE", "Build record", ""],
  ["P2-02", "Phase 2 - Controller", "Archive source commits, board target, plugins, and options", "Codex", "Not Started", "Medium", 2, day("2026-07-23"), 0, "P2-01", "Firmware README", ""],
  ["P2-03", "Phase 2 - Controller", "Flash board and verify USB/Ethernet communication (F-01)", "Project Owner", "Not Started", "High", 3, day("2026-07-27"), 0, "P2-01", "F-01 result", ""],
  ["P2-04", "Phase 2 - Controller", "Verify converter parser subset and unpowered STEP/DIR (F-02/F-03)", "Project Owner", "Not Started", "High", 3, day("2026-07-30"), 0, "P2-03", "F-02/F-03 results", ""],
  ["P2-05", "Phase 2 - Controller", "Verify limit inputs, M3/M5 output, and settings persistence (F-04/F-05/F-06)", "Project Owner", "Not Started", "High", 4, day("2026-08-03"), 0, "P2-04", "F-04 to F-06 results", ""],
  ["P2-GATE", "Phase 2 - Controller", "Milestone: controller baseline gate", "Project Owner", "Not Started", "High", 1, day("2026-08-07"), 0, "P2-05", "Phase 2 checklist", ""],

  ["P3-01", "Phase 3 - Single Axis", "Configure one TB6600 and connect motor without mechanics", "Project Owner", "Not Started", "High", 2, day("2026-08-10"), 0, "P2-GATE", "Configuration record", ""],
  ["P3-02", "Phase 3 - Single Axis", "Complete low-speed jog and temperature test (M-01)", "Project Owner", "Not Started", "High", 2, day("2026-08-12"), 0, "P3-01", "M-01 result", ""],
  ["P3-03", "Phase 3 - Single Axis", "Ramp rate/acceleration and set conservative margin (M-02)", "Project Owner", "Not Started", "High", 3, day("2026-08-14"), 0, "P3-02", "M-02 result", ""],
  ["P3-04", "Phase 3 - Single Axis", "Install and verify home/limit switch", "Project Owner", "Not Started", "Medium", 2, day("2026-08-19"), 0, "P3-03", "Switch test", ""],
  ["P3-GATE", "Phase 3 - Single Axis", "Milestone: single-axis motion gate", "Project Owner", "Not Started", "High", 1, day("2026-08-21"), 0, "P3-04", "Phase 3 checklist", ""],

  ["P4-01", "Phase 4 - Three Axis", "Bring up X, Y, and A motors and drivers", "Project Owner", "Not Started", "High", 4, day("2026-08-24"), 0, "P3-GATE", "Bring-up notes", ""],
  ["P4-02", "Phase 4 - Three Axis", "Calibrate X/Y steps per mm and A motor degrees (M-03/M-04)", "Project Owner", "Not Started", "High", 4, day("2026-08-28"), 0, "P4-01", "M-03/M-04 results", ""],
  ["P4-03", "Phase 4 - Three Axis", "Verify 12:1 bed ratio and tune rates/acceleration (M-05)", "Project Owner", "Not Started", "High", 3, day("2026-09-03"), 0, "P4-02", "M-05 result", ""],
  ["P4-04", "Phase 4 - Three Axis", "Add homing and soft limits (M-07)", "Project Owner", "Not Started", "High", 3, day("2026-09-08"), 0, "P4-03", "M-07 result", ""],
  ["P4-05", "Phase 4 - Three Axis", "Run coordinated tests and converter sample without tool (M-06)", "Project Owner", "Not Started", "High", 4, day("2026-09-11"), 0, "P4-04", "M-06 result + G-code", ""],
  ["P4-GATE", "Phase 4 - Three Axis", "Milestone: three-axis motion gate", "Project Owner", "Not Started", "High", 1, day("2026-09-17"), 0, "P4-05", "Phase 4 checklist", ""],

  ["P5-01", "Phase 5 - Toolhead", "Finalize toolhead controller placement", "Project Owner", "Not Started", "High", 3, day("2026-09-21"), 0, "P1-GATE", "ADR update", ""],
  ["P5-02", "Phase 5 - Toolhead", "Verify actuator direction and safe travel (T-01)", "Project Owner", "Not Started", "High", 3, day("2026-09-24"), 0, "P5-01", "T-01 result", ""],
  ["P5-03", "Phase 5 - Toolhead", "Implement BOOT/LIFT/SEEK/HOLD/FAULT state machine", "Codex", "Not Started", "High", 8, day("2026-09-28"), 0, "P5-02", "Firmware commit", ""],
  ["P5-04", "Phase 5 - Toolhead", "Add travel, timeout, sensor, and force-limit faults", "Codex", "Not Started", "High", 4, day("2026-10-06"), 0, "P5-03", "Firmware tests", ""],
  ["P5-05", "Phase 5 - Toolhead", "Characterize backlash and implement contact seek (T-02)", "Project Owner", "Not Started", "High", 4, day("2026-10-12"), 0, "P5-04", "T-02 result", ""],
  ["P5-06", "Phase 5 - Toolhead", "Implement and tune force control (T-03)", "Codex", "Not Started", "High", 7, day("2026-10-16"), 0, "P5-05", "T-03 data + firmware", ""],
  ["P5-07", "Phase 5 - Toolhead", "Verify missing-paper, overforce, and disconnect faults (T-04 to T-06)", "Project Owner", "Not Started", "High", 4, day("2026-10-26"), 0, "P5-06", "T-04 to T-06 results", ""],
  ["P5-GATE", "Phase 5 - Toolhead", "Milestone: toolhead bench-loop gate", "Project Owner", "Not Started", "High", 1, day("2026-10-30"), 0, "P5-07", "Phase 5 checklist", ""],

  ["P6-01", "Phase 6 - Integration", "Connect grblHAL M3/M5 to toolhead ENGAGE/LIFT", "Project Owner", "Not Started", "High", 3, day("2026-11-02"), 0, "P4-GATE,P5-GATE", "Interface test", ""],
  ["P6-02", "Phase 6 - Integration", "Verify reset/E-stop safety and G4 dwell timing", "Project Owner", "Not Started", "High", 3, day("2026-11-05"), 0, "P6-01", "Safety test", ""],
  ["P6-03", "Phase 6 - Integration", "Check toolhead workload for lost steps or jitter", "Project Owner", "Not Started", "High", 3, day("2026-11-10"), 0, "P6-02", "Timing measurements", ""],
  ["P6-04", "Phase 6 - Integration", "Complete calibration and theta-heavy drawings", "Project Owner", "Not Started", "High", 5, day("2026-11-13"), 0, "P6-03", "Drawings + photos", ""],
  ["P6-GATE", "Phase 6 - Integration", "Milestone: system integration gate", "Project Owner", "Not Started", "High", 1, day("2026-11-20"), 0, "P6-04", "Phase 6 checklist", ""],

  ["P7-01", "Phase 7 - Validation", "Measure calibration-pattern dimensions and execution time", "Project Owner", "Not Started", "High", 4, day("2026-11-23"), 0, "P6-GATE", "Measurement tables", ""],
  ["P7-02", "Phase 7 - Validation", "Record force error during straight, curved, and rotating moves", "Project Owner", "Not Started", "High", 4, day("2026-11-30"), 0, "P7-01", "Force plots", ""],
  ["P7-03", "Phase 7 - Validation", "Photograph final wiring/mechanics and archive firmware/settings", "Project Owner", "Not Started", "Medium", 3, day("2026-12-04"), 0, "P7-02", "Photos + build archive", ""],
  ["P7-04", "Phase 7 - Validation", "Document results, failures, limitations, and future work", "Codex", "Not Started", "High", 6, day("2026-12-09"), 0, "P7-03", "Report draft", ""],
  ["P7-05", "Phase 7 - Validation", "Complete and export Systems Integration report", "Codex", "Not Started", "High", 8, day("2026-12-17"), 0, "P7-04", "Final report", ""],
  ["P7-GATE", "Phase 7 - Validation", "Milestone: project validation and report complete", "Project Owner", "Not Started", "High", 1, day("2026-12-29"), 0, "P7-05", "Phase 7 checklist", ""],
];

const phases = [
  "Phase 0 - Repository",
  "Phase 1 - Electrical",
  "Phase 2 - Controller",
  "Phase 3 - Single Axis",
  "Phase 4 - Three Axis",
  "Phase 5 - Toolhead",
  "Phase 6 - Integration",
  "Phase 7 - Validation",
];

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const gantt = workbook.worksheets.add("Gantt");
const lists = workbook.worksheets.add("Lists");

for (const sheet of [dashboard, gantt, lists]) {
  sheet.showGridLines = false;
}

const navy = "#17324D";
const blue = "#2F75B5";
const paleBlue = "#DDEBF7";
const paleGray = "#F3F5F7";
const green = "#70AD47";
const amber = "#ED7D31";
const red = "#C00000";
const purple = "#8064A2";
const border = "#D5DCE3";
const white = "#FFFFFF";
const text = "#243447";

lists.getRange("A1:C5").values = [
  ["Status", "Priority", "Owner"],
  ["Not Started", "High", "Project Owner"],
  ["In Progress", "Medium", "Codex"],
  ["Blocked", "Low", "Shared"],
  ["Complete", "", ""],
];
lists.getRange("A1:C1").format = { fill: navy, font: { bold: true, color: white } };
lists.getRange("A1:C5").format.borders = { preset: "all", style: "thin", color: border };
lists.getRange("A:C").format.columnWidth = 20;

gantt.getRange("A1:BA1").format.fill = navy;
gantt.getRange("A1:M1").merge();
gantt.getRange("A1").values = [["Theta Pen Plotter Project Gantt"]];
gantt.getRange("A1").format = {
  fill: navy,
  font: { bold: true, color: white, size: 18 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
gantt.getRange("A1:BA1").format.rowHeight = 32;
gantt.getRange("A2:M2").merge();
gantt.getRange("A2").values = [["Editable schedule generated from docs/project/ROADMAP.md. Update task inputs, then keep roadmap evidence/checklists authoritative."]];
gantt.getRange("A2").format = { fill: paleBlue, font: { color: text, italic: true }, wrapText: true };
gantt.getRange("A3:M3").merge();
gantt.getRange("A3").values = [["Edit columns D-H, J-M. End dates and summaries are formula-driven. Timeline bars update from Start, End, and Status."]];
gantt.getRange("A3").format = { fill: paleGray, font: { color: text }, wrapText: true };

const headers = ["ID", "Phase", "Task", "Owner", "Status", "Priority", "Duration", "Start", "End", "Progress", "Predecessor", "Evidence / Exit Proof", "Notes"];
gantt.getRange("A6:M6").values = [headers];
gantt.getRange("A6:M6").format = {
  fill: blue,
  font: { bold: true, color: white },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "all", style: "thin", color: border },
};
gantt.getRange("A6:M6").format.rowHeight = 34;

const firstTaskRow = 7;
const lastTaskRow = firstTaskRow + tasks.length - 1;
const taskValues = tasks.map(([id, phase, task, owner, status, priority, duration, start, progress, predecessor, evidence, notes]) => [
  id, phase, task, owner, status, priority, duration, start, null, progress, predecessor, evidence, notes,
]);
gantt.getRange(`A${firstTaskRow}:M${lastTaskRow}`).values = taskValues;

for (let row = firstTaskRow; row <= lastTaskRow; row += 1) {
  gantt.getRange(`I${row}`).formulas = [[`=IF(OR(H${row}="",G${row}=""),"",H${row}+G${row}-1)`]];
}

gantt.getRange(`H${firstTaskRow}:I${lastTaskRow}`).format.numberFormat = "yyyy-mm-dd";
gantt.getRange(`J${firstTaskRow}:J${lastTaskRow}`).format.numberFormat = "0%";
gantt.getRange(`A${firstTaskRow}:M${lastTaskRow}`).format = {
  font: { color: text, size: 10 },
  verticalAlignment: "center",
  borders: { preset: "all", style: "thin", color: border },
};
gantt.getRange(`B${firstTaskRow}:C${lastTaskRow}`).format.wrapText = true;
gantt.getRange(`K${firstTaskRow}:M${lastTaskRow}`).format.wrapText = true;
gantt.getRange(`D${firstTaskRow}:F${lastTaskRow}`).format.horizontalAlignment = "center";
gantt.getRange(`G${firstTaskRow}:J${lastTaskRow}`).format.horizontalAlignment = "center";
gantt.getRange(`A${firstTaskRow}:M${lastTaskRow}`).format.rowHeight = 32;

gantt.getRange(`D${firstTaskRow}:D${lastTaskRow}`).dataValidation = {
  rule: { type: "list", formula1: "Lists!$C$2:$C$4" },
};
gantt.getRange(`E${firstTaskRow}:E${lastTaskRow}`).dataValidation = {
  rule: { type: "list", formula1: "Lists!$A$2:$A$5" },
};
gantt.getRange(`F${firstTaskRow}:F${lastTaskRow}`).dataValidation = {
  rule: { type: "list", formula1: "Lists!$B$2:$B$4" },
};
gantt.getRange(`J${firstTaskRow}:J${lastTaskRow}`).dataValidation = {
  rule: { type: "decimal", operator: "between", formula1: 0, formula2: 1 },
};

gantt.getRange(`E${firstTaskRow}:E${lastTaskRow}`).conditionalFormats.addCustom(`=$E${firstTaskRow}="Complete"`, { fill: "#E2F0D9", font: { color: "#375623", bold: true } });
gantt.getRange(`E${firstTaskRow}:E${lastTaskRow}`).conditionalFormats.addCustom(`=$E${firstTaskRow}="In Progress"`, { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } });
gantt.getRange(`E${firstTaskRow}:E${lastTaskRow}`).conditionalFormats.addCustom(`=$E${firstTaskRow}="Blocked"`, { fill: "#FCE4D6", font: { color: red, bold: true } });

const timelineStart = day("2026-06-01");
const timelineWeeks = 31;
const timelineStartCol = 14;
const colName = (number) => {
  let result = "";
  let value = number;
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
};
const timelineEndColName = colName(timelineStartCol + timelineWeeks - 1);
const weekDates = Array.from({ length: timelineWeeks }, (_, index) => addDays(timelineStart, index * 7));
gantt.getRange(`N6:${timelineEndColName}6`).values = [weekDates];
gantt.getRange(`N6:${timelineEndColName}6`).format = {
  fill: navy,
  font: { bold: true, color: white, size: 9 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  numberFormat: "mmm d",
  borders: { preset: "all", style: "thin", color: "#49647D" },
};
gantt.getRange(`N${firstTaskRow}:${timelineEndColName}${lastTaskRow}`).format = {
  fill: white,
  borders: { preset: "all", style: "thin", color: "#E7EBEF" },
};
const timelineRange = gantt.getRange(`N${firstTaskRow}:${timelineEndColName}${lastTaskRow}`);
timelineRange.conditionalFormats.addCustom(`=AND(N$6<=$I${firstTaskRow},N$6+6>=$H${firstTaskRow},$E${firstTaskRow}="Not Started")`, { fill: blue });
timelineRange.conditionalFormats.addCustom(`=AND(N$6<=$I${firstTaskRow},N$6+6>=$H${firstTaskRow},$E${firstTaskRow}="In Progress")`, { fill: amber });
timelineRange.conditionalFormats.addCustom(`=AND(N$6<=$I${firstTaskRow},N$6+6>=$H${firstTaskRow},$E${firstTaskRow}="Blocked")`, { fill: red });
timelineRange.conditionalFormats.addCustom(`=AND(N$6<=$I${firstTaskRow},N$6+6>=$H${firstTaskRow},$E${firstTaskRow}="Complete")`, { fill: green });
timelineRange.conditionalFormats.addCustom(`=AND(N$6<=$I${firstTaskRow},N$6+6>=$H${firstTaskRow},ISNUMBER(SEARCH("Milestone",$C${firstTaskRow})))`, { fill: purple, border: { top: { style: "medium", color: purple }, bottom: { style: "medium", color: purple } } });

gantt.tables.add(`A6:M${lastTaskRow}`, true, "ProjectTasks").style = "TableStyleMedium2";
gantt.freezePanes.freezeRows(6);
gantt.freezePanes.freezeColumns(13);
const widths = { A: 12, B: 23, C: 52, D: 16, E: 15, F: 11, G: 10, H: 12, I: 12, J: 11, K: 18, L: 25, M: 26 };
for (const [column, width] of Object.entries(widths)) gantt.getRange(`${column}:${column}`).format.columnWidth = width;
gantt.getRange(`N:${timelineEndColName}`).format.columnWidth = 10;

dashboard.getRange("A1:L1").merge();
dashboard.getRange("A1").values = [["Theta Pen Plotter Project Dashboard"]];
dashboard.getRange("A1").format = {
  fill: navy,
  font: { bold: true, color: white, size: 18 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
dashboard.getRange("A1:L1").format.rowHeight = 34;
dashboard.getRange("A2:L2").merge();
dashboard.getRange("A2").values = [["Schedule baseline: 2026-06-01 through 2026-12-29. Change dates and statuses on the Gantt sheet."]];
dashboard.getRange("A2").format = { fill: paleBlue, font: { italic: true, color: text } };

dashboard.getRange("A4:B4").merge();
dashboard.getRange("D4:E4").merge();
dashboard.getRange("G4:H4").merge();
dashboard.getRange("J4:K4").merge();
dashboard.getRange("A4").values = [["TOTAL TASKS"]];
dashboard.getRange("D4").values = [["COMPLETE"]];
dashboard.getRange("G4").values = [["IN PROGRESS"]];
dashboard.getRange("J4").values = [["BLOCKED"]];
for (const range of ["A4:B4", "D4:E4", "G4:H4", "J4:K4"]) {
  dashboard.getRange(range).format = { fill: blue, font: { bold: true, color: white }, horizontalAlignment: "center" };
}
dashboard.getRange("A5:B5").merge();
dashboard.getRange("D5:E5").merge();
dashboard.getRange("G5:H5").merge();
dashboard.getRange("J5:K5").merge();
dashboard.getRange("A5").formulas = [[`=COUNTA(Gantt!$A$${firstTaskRow}:$A$${lastTaskRow})`]];
dashboard.getRange("D5").formulas = [[`=COUNTIF(Gantt!$E$${firstTaskRow}:$E$${lastTaskRow},"Complete")`]];
dashboard.getRange("G5").formulas = [[`=COUNTIF(Gantt!$E$${firstTaskRow}:$E$${lastTaskRow},"In Progress")`]];
dashboard.getRange("J5").formulas = [[`=COUNTIF(Gantt!$E$${firstTaskRow}:$E$${lastTaskRow},"Blocked")`]];
dashboard.getRange("A5:K5").format = { fill: paleGray, font: { bold: true, color: navy, size: 18 }, horizontalAlignment: "center", borders: { preset: "outside", style: "thin", color: border } };

dashboard.getRange("A7:D7").values = [["Phase", "Tasks", "Complete", "Average Progress"]];
dashboard.getRange("A7:D7").format = { fill: navy, font: { bold: true, color: white }, horizontalAlignment: "center" };
dashboard.getRange("A8:A15").values = phases.map((phase) => [phase]);
for (let row = 8; row <= 15; row += 1) {
  dashboard.getRange(`B${row}`).formulas = [[`=COUNTIF(Gantt!$B$${firstTaskRow}:$B$${lastTaskRow},A${row})`]];
  dashboard.getRange(`C${row}`).formulas = [[`=COUNTIFS(Gantt!$B$${firstTaskRow}:$B$${lastTaskRow},A${row},Gantt!$E$${firstTaskRow}:$E$${lastTaskRow},"Complete")`]];
  dashboard.getRange(`D${row}`).formulas = [[`=IFERROR(AVERAGEIF(Gantt!$B$${firstTaskRow}:$B$${lastTaskRow},A${row},Gantt!$J$${firstTaskRow}:$J$${lastTaskRow}),0)`]];
}
dashboard.getRange("A8:D15").format = { borders: { preset: "all", style: "thin", color: border }, font: { color: text } };
dashboard.getRange("D8:D15").format.numberFormat = "0%";
dashboard.getRange("D8:D15").conditionalFormats.add("dataBar", { color: blue, gradient: true });

dashboard.getRange("A18:F18").merge();
dashboard.getRange("A18").values = [["Current Focus"]];
dashboard.getRange("A18").format = { fill: blue, font: { bold: true, color: white } };
dashboard.getRange("A19:F22").merge();
dashboard.getRange("A19").values = [[
  "Complete the Phase 1 bench worksheet before connecting motors or the toolhead to RP23CNC. Record evidence in lab notes, then update ROADMAP.md and this workbook together.",
]];
dashboard.getRange("A19").format = { fill: paleGray, font: { color: text }, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: border } };

dashboard.getRange("A24:F24").merge();
dashboard.getRange("A24").values = [["Status Legend"]];
dashboard.getRange("A24").format = { fill: navy, font: { bold: true, color: white } };
dashboard.getRange("A25:D25").values = [["Not Started", "In Progress", "Blocked", "Complete"]];
dashboard.getRange("A25").format.fill = blue;
dashboard.getRange("B25").format.fill = amber;
dashboard.getRange("C25").format.fill = red;
dashboard.getRange("D25").format.fill = green;
dashboard.getRange("A25:D25").format.font = { bold: true, color: white };
dashboard.getRange("A25:D25").format.horizontalAlignment = "center";

dashboard.getRange("A:D").format.columnWidth = 20;
dashboard.getRange("E:F").format.columnWidth = 16;
dashboard.getRange("G:L").format.columnWidth = 14;
dashboard.getRange("A19:F22").format.rowHeight = 24;

const chart = dashboard.charts.add("bar", dashboard.getRange("A7:C15"));
chart.title = "Tasks by Phase";
chart.hasLegend = true;
chart.xAxis = { axisType: "textAxis", textStyle: { fontSize: 9 } };
chart.yAxis = { numberFormatCode: "0" };
chart.setPosition("G7", "L22");

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const dashboardPreview = await workbook.render({ sheetName: "Dashboard", range: "A1:L25", scale: 1.5, format: "png" });
await fs.writeFile(path.join(previewDir, "dashboard.png"), new Uint8Array(await dashboardPreview.arrayBuffer()));
const ganttPreview = await workbook.render({ sheetName: "Gantt", range: `A1:${timelineEndColName}20`, scale: 1, format: "png" });
await fs.writeFile(path.join(previewDir, "gantt.png"), new Uint8Array(await ganttPreview.arrayBuffer()));
const listsPreview = await workbook.render({ sheetName: "Lists", range: "A1:C5", scale: 1.5, format: "png" });
await fs.writeFile(path.join(previewDir, "lists.png"), new Uint8Array(await listsPreview.arrayBuffer()));

const keyRange = await workbook.inspect({
  kind: "table",
  range: "Dashboard!A1:L25",
  include: "values,formulas",
  tableMaxRows: 25,
  tableMaxCols: 12,
  maxChars: 5000,
});
await fs.writeFile(path.join(previewDir, "inspect-dashboard.ndjson"), keyRange.ndjson, "utf8");
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(previewDir, "formula-errors.ndjson"), errors.ndjson, "utf8");

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(`Created ${outputPath}`);
