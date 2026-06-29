from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


OUT = Path("docs/NutriGuard_PRD_Day1.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def attrs(items):
    return "".join(f' {key}="{escape(str(value), quote=True)}"' for key, value in items.items())


def run(text, bold=False, italic=False, color=None, size=None):
    rpr = []
    if bold:
        rpr.append("<w:b/>")
    if italic:
        rpr.append("<w:i/>")
    if color:
        rpr.append(f'<w:color w:val="{color}"/>')
    if size:
        rpr.append(f'<w:sz w:val="{int(size * 2)}"/><w:szCs w:val="{int(size * 2)}"/>')
    rpr_xml = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""
    return f"<w:r>{rpr_xml}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def paragraph(parts=None, style=None, before=None, after=None, line=276, num_id=None, ilvl=0):
    parts = parts or []
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if num_id is not None:
        ppr.append(f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>')
    spacing = []
    if before is not None:
        spacing.append(f'w:before="{before}"')
    if after is not None:
        spacing.append(f'w:after="{after}"')
    if line:
        spacing.append(f'w:line="{line}" w:lineRule="auto"')
    if spacing:
        ppr.append(f"<w:spacing {' '.join(spacing)}/>")
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr_xml}{''.join(parts)}</w:p>"


def text_para(text, **kwargs):
    return paragraph([run(text)], **kwargs)


def bullet(text):
    return paragraph([run(text)], num_id=1, after=80)


def numbered(text):
    return paragraph([run(text)], num_id=2, after=80)


def table(rows, widths):
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    body = []
    for idx, row in enumerate(rows):
        cells = []
        for text, width in zip(row, widths):
            fill = '<w:shd w:fill="F8F9FA"/>' if idx == 0 else ""
            bold = idx == 0
            cells.append(
                "<w:tc>"
                f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{fill}'
                '<w:tcMar><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/>'
                '<w:start w:w="120" w:type="dxa"/><w:end w:w="120" w:type="dxa"/></w:tcMar></w:tcPr>'
                f"{paragraph([run(text, bold=bold)], after=0)}"
                "</w:tc>"
            )
        body.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (
        "<w:tbl>"
        '<w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="DADCE0"/>'
        '<w:left w:val="single" w:sz="4" w:color="DADCE0"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="DADCE0"/>'
        '<w:right w:val="single" w:sz="4" w:color="DADCE0"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="DADCE0"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="DADCE0"/></w:tblBorders>'
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/>'
        '<w:start w:w="120" w:type="dxa"/><w:end w:w="120" w:type="dxa"/></w:tblCellMar>'
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{''.join(body)}</w:tbl>"
    )


def document_xml():
    blocks = [
        paragraph([run("NutriGuard AI — Product Requirements Document", size=26)], before=0, after=60),
        paragraph([run("Day 1 focus: define a scoped, launch-ready PRD for a profile-aware daily nutrition analysis product.", italic=True, color="555555")], after=160),
        text_para("Day 1 at a glance", style="Heading1"),
        text_para("Seven deliverables move the project from idea to implementation-ready scope.", after=120),
        table(
            [
                ["#", "Deliverable", "NutriGuard output"],
                ["1", "Problem statement", "Define the user need around meal timing, deficiencies, supplements, and daily context."],
                ["2", "Project type", "Profile-aware recommender and summarizer for nutrition risk guidance."],
                ["3", "Architecture", "Frontend, backend API, outbox publisher, AI orchestrator, agent workflow, Postgres."],
                ["4", "Tech stack", "React/Vite, FastAPI, SQLAlchemy, Postgres, LangGraph-style agents, Gemini."],
                ["5", "Team & roles", "Frontend, backend, AI/orchestration, product QA, documentation owner."],
                ["6", "GitHub repo", "Modular source structure, environment files, local dev guide, issue/PR workflow."],
                ["7", "Docs", "PRD, local setup, architecture notes, agent behavior notes, demo script."],
            ],
            [720, 2160, 6480],
        ),
        text_para("", after=80),
        paragraph([run("Goal of Day 1: ", bold=True), run("lock the product scope before adding more code. Every later implementation decision should trace back to this PRD.")], after=160),
        text_para("1. Problem statement", style="Heading1"),
        paragraph([run("Users who track meals, supplements, and health conditions often miss timing-based interactions. ", bold=True), run("A person with iron deficiency may drink tea, take an iron tablet, and eat a calcium-rich meal in a short window without realizing that the combination can reduce absorption or create avoidable risk.")]),
        text_para("NutriGuard should help users capture a whole-day meal timeline and produce profile-aware guidance that considers food, drinks, supplements, medical context, and timing gaps.", after=120),
        text_para("Strong statement checklist", style="Heading2"),
        numbered("User and context: health-conscious users managing deficiencies, supplements, or diet goals."),
        numbered("Need and pain: they need daily-level interpretation, not isolated single-meal reports."),
        numbered("Proposed solution: a profile-aware nutrition timeline with AI-generated progressive reports."),
        numbered("Success measure: users can log meals and see day-level warnings and recommendations by date."),
        numbered("Data source: user profile, uploaded/pasted health report text, detailed meal logs, timestamps, and daily reports."),
        numbered("Scope fence: educational guidance only; no diagnosis or replacement for medical advice."),
        text_para("2. Product summary", style="Heading1"),
        text_para("NutriGuard is a local-first web app for logging meals and generating AI-assisted daily nutrition reports. It combines user profile context with meal timing so the system can reason about interactions across breakfast, lunch, snacks, dinner, drinks, and supplements."),
        text_para("Target users", style="Heading2"),
        bullet("Users managing deficiencies such as iron, vitamin D, B12, calcium, or protein intake."),
        bullet("Users who take supplements or medicines near meals and want timing-aware reminders."),
        bullet("Users who prefer a daily combined report instead of separate reports for every meal."),
        bullet("Developers/demo reviewers evaluating a multi-service AI application."),
        text_para("3. Project type", style="Heading1"),
        table(
            [
                ["Archetype", "Fit for NutriGuard"],
                ["Recommender", "Suggests better meal pairings, timing gaps, and deficiency-aware improvements."],
                ["Summariser", "Turns a full-day meal timeline into a clear daily report."],
                ["Profile-aware assistant", "Uses diet type, goals, conditions, deficiencies, supplements, and report text."],
            ],
            [2400, 6960],
        ),
        text_para("4. Functional requirements", style="Heading1"),
        text_para("Authentication and profile", style="Heading2"),
        bullet("Users can sign up and log in with email and password."),
        bullet("Users can update profile information from the profile menu."),
        bullet("Users can select diet type and multiple goals."),
        bullet("Users can enter health conditions, deficiencies, supplements, and health report text in natural language."),
        bullet("System stores both raw text and normalized structured values for API and agent use."),
        text_para("Meal logging", style="Heading2"),
        bullet("Users can log meal type, meal time, foods, drinks, supplements/medicine, notes, and optional combined description."),
        bullet("System preserves detailed fields so reports can show foods and drinks instead of “not provided.”"),
        bullet("System supports supplements as a meal-like timeline event."),
        text_para("Daily reports", style="Heading2"),
        bullet("Users can view reports by date."),
        bullet("After each meal, the report should include the individual meal analysis and the combined report up to that point."),
        bullet("The full daily report should identify timing issues, short gaps, and supplement-food-drink interactions."),
        bullet("History should keep prior dates accessible."),
        text_para("5. Agent behavior requirements", style="Heading1"),
        bullet("Analyze the whole day timeline, not only the current meal."),
        bullet("Detect tea or coffee near iron-rich meals or iron supplements."),
        bullet("Detect calcium/dairy foods such as milk, curd/dahi, paneer, yogurt, and calcium supplements near iron supplements."),
        bullet("Flag meals that are too close together or mixed into one ambiguous event."),
        bullet("Use user profile conditions, deficiencies, goals, diet type, and report text to personalize guidance."),
        bullet("Keep outputs educational and include a safety note where supplements or medical context appear."),
        text_para("6. Architecture", style="Heading1"),
        table(
            [
                ["Layer", "Responsibility"],
                ["Frontend", "React/Vite UI for auth, profile, meal logging, daily reports, history, theme, and responsive navigation."],
                ["Backend API", "FastAPI service for users, profiles, meal logs, reports, CORS, schema maintenance, and persistence."],
                ["Database", "Postgres for users, profiles, meal logs, nutrition flags, daily reports, and outbox events."],
                ["Publisher", "Backend background worker publishes meal events from outbox to the orchestrator."],
                ["AI orchestrator", "FastAPI service coordinating analyzer, health-risk, and report agents."],
                ["LLM client", "Gemini client with rule/mock fallback behavior for local resilience."],
            ],
            [2160, 7200],
        ),
        text_para("7. Tech stack", style="Heading1"),
        bullet("Frontend: React, Vite, modular components/pages, CSS split by feature area."),
        bullet("Backend: FastAPI, SQLAlchemy, Postgres."),
        bullet("AI: Gemini API client, agent modules, report generation fallback logic."),
        bullet("Local infrastructure: Docker Compose Postgres on host port 5434; services on 8000 and 8001; frontend on localhost:3000."),
        bullet("Configuration: service-level .env files and Vite VITE_API_BASE_URL for frontend API base."),
        text_para("8. Non-functional requirements", style="Heading1"),
        bullet("No CORS errors for local frontend-backend communication."),
        bullet("Frontend must be responsive: desktop keeps side navigation visible; small screens use a drawer menu while profile/theme stay in header."),
        bullet("The UI supports light and dark modes with readable contrast."),
        bullet("Sensitive health information must be handled carefully in local development documentation and logs."),
        bullet("Agent output should be deterministic enough to demo even when Gemini is unavailable."),
        text_para("9. Success criteria", style="Heading1"),
        bullet("A user can sign up, complete profile, log meals throughout a day, and view a combined daily report by date."),
        bullet("Reports show meal details including foods, drinks, supplements, and notes."),
        bullet("The system flags the example scenario: tea, iron tablet, and dairy/calcium-heavy lunch too close together."),
        bullet("The README documents local ports, setup, and end-to-end flow."),
        bullet("Frontend code is modular enough for future maintenance."),
        text_para("10. Open questions", style="Heading1"),
        bullet("Should health report uploads support PDFs/images, or only text files for the first release?"),
        bullet("Should the product store supplement schedules separately from meal logs?"),
        bullet("Should reports be generated automatically after each meal, on demand, or both?"),
        bullet("What disclaimer language should appear for supplement and medical guidance?"),
        text_para("11. Day 1 acceptance checklist", style="Heading1"),
        bullet("Problem statement is specific and scoped."),
        bullet("Project type is chosen: recommender + summarizer + profile-aware assistant."),
        bullet("Architecture and service boundaries are documented."),
        bullet("Tech stack and local ports are documented."),
        bullet("Core user journey is defined from signup to daily report."),
        bullet("Demo scenario is defined for meal timing and supplement interaction."),
        bullet("Repo documentation targets are listed."),
    ]
    body = "".join(blocks)
    sect = (
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>{body}{sect}</w:body></w:document>'


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="000000"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="400" w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="40"/><w:szCs w:val="40"/><w:color w:val="000000"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:color w:val="000000"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
  <w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="●"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
  <w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
  <w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>'''


def content_types():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


def rels():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def doc_rels():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>'''


def core_props():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>NutriGuard AI Product Requirements Document</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def app_props():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex</Application></Properties>'''


def settings():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="{W_NS}"><w:zoom w:percent="100"/><w:defaultTabStop w:val="720"/></w:settings>'''


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types())
        z.writestr("_rels/.rels", rels())
        z.writestr("word/document.xml", document_xml())
        z.writestr("word/_rels/document.xml.rels", doc_rels())
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/numbering.xml", numbering_xml())
        z.writestr("word/settings.xml", settings())
        z.writestr("docProps/core.xml", core_props())
        z.writestr("docProps/app.xml", app_props())
    print(OUT)


if __name__ == "__main__":
    build()
