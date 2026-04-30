// Google Apps Script — paste into Extensions > Apps Script in your Google Sheet.
//
// Setup:
//   1. Paste this code
//   2. Run setGitHubToken() once and enter your GitHub Personal Access Token when prompted
//   3. Reload the sheet — a "GitHub Sync" menu will appear in the menu bar
//   4. Click "GitHub Sync > Push events & guides to GitHub" whenever you want to update the app
//
// REPO_OWNER + REPO_NAME must be the SAME GitHub repo Streamlit Community Cloud deploys from,
// or pushes will update the wrong place and the app will never see new events.json / workshops.json.
//
// Guides & answer keys: set SHEET_GUIDES to your tab name. That tab is exported to workshops.json.
// Required column: Workshop (or Workshop name). Guide URL / Answer Key URL optional — leave blank
// for "Coming soon" on the app (optional Guide placeholder / Answer Key placeholder columns override).
// Optional: Guide link text, Answer Key link text. Set SHEET_GUIDES to "" to skip workshops.json.
//
// Optional column: "Badges issued" — Yes/TRUE = badges sent; No/FALSE = not yet; blank = unknown (Badge status page).
// Optional columns (archive tab recommended): "Event Date"; "Issued Date" (or "Date Issued", etc.) — Badge status table (YYYY-MM-DD when parsed as dates).
//
// Archive: set SHEET_ARCHIVE to your archive tab name so expired rows stay in events.json (e.g. badge status).
// Main tab order is preserved; archived events appear after, only if not already on the main tab.
// Each row gets JSON "Archived": false (main tab) or true (archive tab only) — Badge status page lists archived only.

var SHEET_MAIN = "";       // "" = whichever tab is active when you push (legacy). Or e.g. "Events" to always use that tab.
var SHEET_ARCHIVE = "";    // e.g. "Archive" — same columns as main (Event Name, Final URL, optional Badges issued). "" = off.
var SHEET_GUIDES = ""; // e.g. "Guides & Answer Keys" — tab exported to workshops.json. "" = skip (repo file unchanged).

var REPO_OWNER = "sfc-gh-kenguyen";
var REPO_NAME  = "NorthstarAutograder";
var FILE_PATH  = "events.json";
var WORKSHOPS_FILE_PATH = "workshops.json";
var BRANCH     = "main";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("GitHub Sync")
    .addItem("Push events & guides to GitHub", "pushEventsToGitHub")
    .addToUi();
}

function setGitHubToken() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.prompt(
    "GitHub Token Setup",
    "Paste your GitHub Personal Access Token (needs repo scope):",
    ui.ButtonSet.OK_CANCEL
  );
  if (result.getSelectedButton() === ui.Button.OK) {
    PropertiesService.getScriptProperties().setProperty("GITHUB_TOKEN", result.getResponseText().trim());
    ui.alert("Token saved successfully.");
  }
}

function pushEventsToGitHub() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var mainSheet = getMainSheet_(ss);
  if (!mainSheet) {
    return;
  }

  var mainEvents;
  try {
    mainEvents = sheetToEvents_(mainSheet);
  } catch (e) {
    SpreadsheetApp.getUi().alert(String(e.message || e));
    return;
  }

  var archiveEvents = [];
  if (SHEET_ARCHIVE && String(SHEET_ARCHIVE).trim()) {
    var arch = ss.getSheetByName(String(SHEET_ARCHIVE).trim());
    if (!arch) {
      SpreadsheetApp.getUi().alert(
        "Archive tab not found: \"" + SHEET_ARCHIVE + "\". Fix SHEET_ARCHIVE or set it to \"\" to push without archive."
      );
      return;
    }
    try {
      archiveEvents = sheetToEvents_(arch);
    } catch (e) {
      SpreadsheetApp.getUi().alert(String(e.message || e));
      return;
    }
  }

  var events = mergeEventsMainThenArchive_(mainEvents, archiveEvents);

  var json = JSON.stringify(events, null, 2) + "\n";
  var token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");

  if (!token) {
    SpreadsheetApp.getUi().alert("No GitHub token found. Run setGitHubToken() first.");
    return;
  }

  var evRes = putRepoFile_(token, FILE_PATH, json, "Update events from Google Sheet");
  if (evRes.code !== 200 && evRes.code !== 201) {
    SpreadsheetApp.getUi().alert(
      "GitHub API error (events.json, " + evRes.code + "): " + evRes.body
    );
    return;
  }

  var guidesMsg = "";
  if (SHEET_GUIDES && String(SHEET_GUIDES).trim()) {
    var guidesSheet = ss.getSheetByName(String(SHEET_GUIDES).trim());
    if (!guidesSheet) {
      guidesMsg =
        "\n\nWorkshops tab not found: \"" +
        SHEET_GUIDES +
        "\" — workshops.json was not updated. Events push succeeded.";
    } else {
      var workshops;
      try {
        workshops = sheetToWorkshops_(guidesSheet);
      } catch (e2) {
        SpreadsheetApp.getUi().alert(String(e2.message || e2));
        return;
      }
      var wjson = JSON.stringify(workshops, null, 2) + "\n";
      var wRes = putRepoFile_(token, WORKSHOPS_FILE_PATH, wjson, "Update workshops from Google Sheet");
      if (wRes.code !== 200 && wRes.code !== 201) {
        SpreadsheetApp.getUi().alert(
          "events.json OK, but workshops.json failed (" +
            wRes.code +
            "). Check tab columns and try again.\n" +
            wRes.body
        );
        return;
      }
      guidesMsg = "\n\nGuides & answer keys (workshops.json) updated.";
    }
  }

  SpreadsheetApp.getUi().alert(
    "Pushed to GitHub successfully! The app will redeploy in ~1-2 minutes." + guidesMsg
  );
}

/**
 * @param {string} token
 * @param {string} repoPath — path within repo, e.g. events.json
 * @param {string} bodyText — file contents (UTF-8)
 * @param {string} commitMessage
 * @returns {{ code: number, body: string }}
 */
function putRepoFile_(token, repoPath, bodyText, commitMessage) {
  var sha = getFileSha_(token, repoPath);
  var url = "https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NAME + "/contents/" + repoPath;
  var payload = {
    message: commitMessage,
    content: Utilities.base64Encode(bodyText, Utilities.Charset.UTF_8),
    branch: BRANCH
  };
  if (sha) {
    payload.sha = sha;
  }
  var options = {
    method: "put",
    contentType: "application/json",
    headers: { "Authorization": "token " + token },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  var response = UrlFetchApp.fetch(url, options);
  return { code: response.getResponseCode(), body: response.getContentText() };
}

/**
 * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} ss
 * @returns {GoogleAppsScript.Spreadsheet.Sheet|null}
 */
function getMainSheet_(ss) {
  var name = String(SHEET_MAIN || "").trim();
  if (!name) {
    return ss.getActiveSheet();
  }
  var sh = ss.getSheetByName(name);
  if (!sh) {
    SpreadsheetApp.getUi().alert("Main tab not found: \"" + SHEET_MAIN + "\". Fix SHEET_MAIN or set it to \"\" to use the active tab.");
    return null;
  }
  return sh;
}

/**
 * Match sheet header (trim, collapse spaces, ignore NBSP, case-insensitive).
 * @param {Array} headers
 * @param {Array<string>} candidates — first match wins
 * @returns {number}
 */
function findHeaderCol_(headers, candidates) {
  function norm(s) {
    return String(s)
      .replace(/\u00a0/g, " ")
      .trim()
      .replace(/\s+/g, " ")
      .toLowerCase();
  }
  var norms = [];
  var j;
  for (j = 0; j < headers.length; j++) {
    norms.push(norm(headers[j]));
  }
  var c;
  for (c = 0; c < candidates.length; c++) {
    var want = norm(candidates[c]);
    for (j = 0; j < norms.length; j++) {
      if (norms[j] === want) {
        return j;
      }
    }
  }
  return -1;
}

/**
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet
 * @returns {Object[]} event rows for JSON
 */
function sheetToEvents_(sheet) {
  var data = sheet.getDataRange().getValues();
  if (!data || data.length < 2) {
    return [];
  }
  var headers = data[0];
  var nameCol = headers.indexOf("Event Name");
  var urlCol = headers.indexOf("Final URL");
  var badgeCol = headers.indexOf("Badges issued");
  var eventDateCol = findHeaderCol_(headers, ["Event Date", "event date"]);
  var issuedDateCol = findHeaderCol_(headers, [
    "Issued Date",
    "Issued date",
    "Date Issued",
    "date issued",
    "Badge issued date",
    "Badge Issued Date",
    "Badge issue date",
  ]);

  if (nameCol === -1 || urlCol === -1) {
    throw new Error("Tab \"" + sheet.getName() + "\" must have columns: Event Name, Final URL");
  }

  var events = [];
  for (var i = 1; i < data.length; i++) {
    var rowName = String(data[i][nameCol]).trim();
    if (!rowName) continue;
    var url = String(data[i][urlCol]).trim();
    var row = {
      "Event Name": rowName,
      "Final URL": url || null
    };
    if (badgeCol !== -1) {
      row["Badges issued"] = parseBadgesIssued_(data[i][badgeCol]);
    }
    if (eventDateCol !== -1) {
      row["Event Date"] = formatDateCell_(data[i][eventDateCol]);
    }
    if (issuedDateCol !== -1) {
      row["Issued Date"] = formatDateCell_(data[i][issuedDateCol]);
    }
    events.push(row);
  }
  return events;
}

/**
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet — Guides & Answer Keys tab
 * @returns {Object[]} rows for workshops.json (keys match Python workshops.py)
 */
function sheetToWorkshops_(sheet) {
  var data = sheet.getDataRange().getValues();
  if (!data || data.length < 2) {
    return [];
  }
  var headers = data[0];
  var wCol = findHeaderCol_(headers, ["Workshop", "Workshop name", "workshop name"]);
  var gCol = findHeaderCol_(headers, ["Guide URL", "Guide url", "guide url"]);
  var aCol = findHeaderCol_(headers, [
    "Answer Key URL",
    "Answer key URL",
    "answer key url",
    "Answer Key url"
  ]);
  var glCol = findHeaderCol_(headers, ["Guide link text", "Guide Link Text", "guide link text"]);
  var alCol = findHeaderCol_(headers, [
    "Answer Key link text",
    "Answer key link text",
    "answer key link text"
  ]);
  var gpCol = findHeaderCol_(headers, [
    "Guide placeholder",
    "Guide status",
    "guide placeholder",
    "guide status"
  ]);
  var akpCol = findHeaderCol_(headers, [
    "Answer Key placeholder",
    "Answer key placeholder",
    "answer key placeholder",
    "Answer Key status",
    "Answer key status"
  ]);

  if (wCol === -1) {
    throw new Error(
      'Tab "' + sheet.getName() + '" must have a Workshop column (or Workshop name).'
    );
  }

  var rows = [];
  var i;
  for (i = 1; i < data.length; i++) {
    var rowName = String(data[i][wCol]).trim();
    if (!rowName) {
      continue;
    }
    var guideUrl = gCol === -1 ? "" : String(data[i][gCol]).trim();
    var answerUrl = aCol === -1 ? "" : String(data[i][aCol]).trim();
    var obj = {
      Workshop: rowName,
      "Guide URL": guideUrl || "",
      "Answer Key URL": answerUrl || ""
    };
    if (glCol !== -1) {
      var gl = String(data[i][glCol]).trim();
      if (gl) {
        obj["Guide link text"] = gl;
      }
    }
    if (alCol !== -1) {
      var al = String(data[i][alCol]).trim();
      if (al) {
        obj["Answer Key link text"] = al;
      }
    }
    if (gpCol !== -1) {
      var gp = String(data[i][gpCol]).trim();
      if (gp) {
        obj["Guide placeholder"] = gp;
      }
    }
    if (akpCol !== -1) {
      var akp = String(data[i][akpCol]).trim();
      if (akp) {
        obj["Answer Key placeholder"] = akp;
      }
    }
    rows.push(obj);
  }
  return rows;
}

/**
 * @param {*} cell
 * @returns {string|null} ISO-style date or trimmed text; null if empty
 */
function formatDateCell_(cell) {
  if (cell === "" || cell === null || cell === undefined) {
    return null;
  }
  if (Object.prototype.toString.call(cell) === "[object Date]" && !isNaN(cell)) {
    return Utilities.formatDate(cell, Session.getScriptTimeZone(), "yyyy-MM-dd");
  }
  if (typeof cell === "number" && isFinite(cell)) {
    var epoch = new Date(1899, 11, 30);
    var d = new Date(epoch.getTime() + cell * 86400000);
    if (!isNaN(d.getTime())) {
      return Utilities.formatDate(d, Session.getScriptTimeZone(), "yyyy-MM-dd");
    }
  }
  var s = String(cell).trim();
  return s || null;
}

/** Main list first (order kept); then archive rows whose Event Name is not already present. Tags Archived for the app. */
function mergeEventsMainThenArchive_(mainEvents, archiveEvents) {
  var seen = {};
  var out = [];
  var i;
  for (i = 0; i < mainEvents.length; i++) {
    var n = mainEvents[i]["Event Name"];
    seen[n] = true;
    out.push(Object.assign({}, mainEvents[i], { Archived: false }));
  }
  for (i = 0; i < archiveEvents.length; i++) {
    var n2 = archiveEvents[i]["Event Name"];
    if (!seen[n2]) {
      seen[n2] = true;
      out.push(Object.assign({}, archiveEvents[i], { Archived: true }));
    }
  }
  return out;
}

/**
 * @param {*} cell — sheet value for "Badges issued"
 * @returns {boolean|null} true = issued, false = not yet, null = unknown / empty
 */
function parseBadgesIssued_(cell) {
  if (cell === "" || cell === null || cell === undefined) {
    return null;
  }
  if (typeof cell === "boolean") {
    return cell;
  }
  if (typeof cell === "number") {
    if (cell === 1) return true;
    if (cell === 0) return false;
    return null;
  }
  var s = String(cell).trim().toLowerCase();
  if (!s) return null;
  if (s === "yes" || s === "true" || s === "y" || s === "1" || s === "issued") {
    return true;
  }
  if (s === "no" || s === "false" || s === "n" || s === "0" || s === "not yet" || s === "pending") {
    return false;
  }
  return null;
}

/**
 * @param {string} token
 * @param {string} repoPath — path within repo
 * @returns {string|null}
 */
function getFileSha_(token, repoPath) {
  var url =
    "https://api.github.com/repos/" +
    REPO_OWNER +
    "/" +
    REPO_NAME +
    "/contents/" +
    repoPath +
    "?ref=" +
    BRANCH;
  var options = {
    method: "get",
    headers: { "Authorization": "token " + token },
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() === 200) {
    return JSON.parse(response.getContentText()).sha;
  }
  return null;
}
