# Requirements Specification Document

## CityReport - Douala Civic Issue Reporting Platform

**Student:** Fokou Joel  
**Sector:** GovTech / CivicTech  
**Location:** Douala, Cameroon  
**Technology Stack:** Python (Flask), HTML, CSS, vanilla JavaScript, SQLite

## 1. Introduction

### 1.1 Background

Urban infrastructure and public service problems are common in rapidly growing cities. In Douala, citizens may encounter potholes, broken streetlights, and uncollected waste that affect mobility, safety, public health, and the general quality of life. The platform also provides an Other category for reports that do not match the primary issue types. Although citizens observe these problems daily, they often have no simple and reliable channel through which to report them to the responsible city authorities.

Traditional reporting methods may require citizens to visit an office, make a telephone call, or communicate through informal channels. These methods can be slow, difficult to monitor, and unsuitable for maintaining a clear record of complaints. Citizens may also be unable to determine whether their report has been received, which department is responsible for it, or when action is expected.

### 1.2 Problem Statement

Citizens in Douala currently lack a centralized, transparent, and accessible platform for reporting urban issues and following their progress. As a result, important problems can remain unrecorded or unresolved, while city administrators may lack structured information for prioritizing and assigning work. The absence of status visibility can reduce public confidence in municipal services.

CityReport addresses this problem by providing a digital platform where citizens can submit a report, provide its location and hazard information, and monitor the report from submission through resolution.

## 2. Objective

The main objective of CityReport is to create a transparent citizen platform that improves communication between residents and city administration.

The specific objectives are to:

- Provide citizens with a simple way to report potholes, broken streetlights, uncollected waste, or an uncategorised civic issue.
- Capture useful information such as category, description, geographic location, and hazard level.
- Automatically direct reports to the appropriate city department.
- Allow citizens to view their submitted reports from a personal dashboard.
- Provide a clear workflow showing whether a report is submitted, acknowledged, in progress, or resolved.
- Give administrators an operations dashboard for reviewing, filtering, assigning, and updating reports.
- Improve accountability by recording status changes and resolution notes.

## 3. Scope

### 3.1 In Scope

CityReport will provide a web-based interface accessible through a local Flask server. The system will support citizen registration and login, issue reporting, report tracking, and an administrator dashboard. A report may include a category, written description, map location, optional photograph, reporter information, and hazard level. The system will store reports and their status history in a relational database.

The main categories covered by the system are roads and potholes, lighting and energy, sanitation and waste, and Other for uncategorised reports. Department routing will be based on the selected or automatically identified category. Other reports are routed to General Services. The platform will also support status updates and notes entered by an administrator.

### 3.2 Out of Scope

The first version will not provide a native Android or iOS application, online payment processing, automated deployment to a public cloud, or direct integration with municipal work-order systems. The platform will not replace the internal procedures of city departments. It will serve as a structured reporting and tracking system for the project demonstration.

## 4. Stakeholders

### 4.1 Citizen

The citizen is the primary user of the platform. A citizen can create an account, log in, submit an issue, view personal reports, track report status, and read a resolution note when action has been completed.

### 4.2 City Administrator (Admin)

The city administrator manages the operational side of the platform. The administrator can log in securely, view all reports, filter reports, review issue details, update statuses, and add resolution notes. The administrator uses the dashboard to monitor workload and identify unresolved or high-priority issues.

### 4.3 Roads & Potholes Department

This department handles potholes, damaged roads, cracked pavement, and related road infrastructure reports.

### 4.4 Lighting & Energy Department

This department handles broken streetlights, damaged lamps, and public lighting problems.

### 4.5 Sanitation & Waste Department

This department handles uncollected waste, illegal dumping, blocked waste collection points, and related sanitation concerns.

## 5. Functional Requirements

### 5.1 Citizen Requirements

**FR-C01: Citizen registration.** The system shall allow a citizen to create an account using a name, email address, and password. The email address shall be unique.

**FR-C02: Citizen login.** The system shall authenticate registered citizens using their email and password. Invalid credentials shall produce an appropriate error message without revealing sensitive information.

**FR-C03: Report an issue.** The system shall allow an authenticated citizen to submit an issue containing a category, description, geographic location, and hazard level. A photograph may be attached where available.

**FR-C04: Category selection.** The system shall support roads and potholes, lighting and energy, sanitation and waste, and Other for irrelevant or uncategorised reports. The system may use automated classification assistance to suggest an appropriate category.

**FR-C05: Location capture.** The system shall allow the citizen to identify the issue location on a map using latitude and longitude. An address or location description may also be stored.

**FR-C06: Hazard information.** The report shall include a hazard or priority level, such as low, medium, or high, to help administrators prioritize work.

**FR-C07: View My Reports.** After logging in, a citizen shall be able to view a dashboard containing the reports associated with that account. The dashboard shall show the report reference, category, current status, and submission date.

**FR-C08: Track report status.** The system shall provide a report tracking page accessible through a unique reference code. The page shall display the report workflow and status history.

**FR-C09: See resolution note.** When an administrator resolves a report, the citizen shall be able to view the resolution note and the date of the latest update.

### 5.2 Administrator Requirements

**FR-A01: Administrator login.** The administrator shall log in through a protected staff login page. Administrator credentials shall be stored using a secure password hash rather than plain text.

**FR-A02: Operations dashboard.** The system shall provide an operations dashboard summarizing reports using the following values: Total, Submitted, In Progress, and Resolved.

**FR-A03: View all reports.** The administrator shall be able to view all reports submitted through the platform, including their reference, category, department, hazard level, description, status, and filing date.

**FR-A04: Filter reports.** The dashboard shall provide STATUS and CATEGORY filters. The filters shall update the visible table rows using vanilla JavaScript without requiring a full page reload.

**FR-A05: Change status.** The administrator shall be able to change a report through the workflow: Submitted -> Acknowledged -> In Progress -> Resolved. Each change shall be validated by the server.

**FR-A06: Assign department automatically.** The system shall assign a department according to the report category. Roads and potholes shall route to Roads & Potholes, lighting issues to Lighting & Energy, waste issues to Sanitation & Waste, and Other reports to General Services.

**FR-A07: Add resolution note.** The administrator shall be able to add a note describing the action taken or the resolution of a report. The note shall be stored with the report or its status history and shown to the citizen where appropriate.

**FR-A08: View report details.** The administrator shall be able to open a report and inspect its description, location, photograph, hazard level, reporter information, status history, assigned department, and resolution information.

## 6. Non-Functional Requirements

**NFR-01: Usability.** The user interface shall be simple and understandable for citizens with different levels of technical experience. Labels, buttons, forms, and status information shall be clearly presented.

**NFR-02: Responsiveness.** The platform shall adapt to desktop, tablet, and mobile screen sizes. Core workflows such as login, reporting, and tracking shall remain usable on smaller screens.

**NFR-03: Security.** Passwords shall be hashed before storage. Protected administrator and citizen pages shall require authentication. Users shall only access the reports permitted by their role. Uploaded files shall be restricted to approved image formats and sizes.

**NFR-04: Performance.** Normal page requests and dashboard operations shall respond quickly on a local development machine. Client-side filtering shall occur without a page reload.

**NFR-05: Availability.** The application shall run on localhost at `127.0.0.1:5000` using the Flask development server. The default database shall be SQLite, requiring no separate database server for demonstration.

**NFR-06: Maintainability.** The application shall use a modular structure separating Flask routes, database models, templates, stylesheets, and JavaScript files. The code shall use standard Python and web technologies without unnecessary external libraries.

**NFR-07: Data integrity.** Every report shall have a unique reference code. Required values such as description and location shall be validated before saving. Status changes shall be recorded in chronological order.

## 7. Use Case Diagram Description

The system has two primary actors: **Citizen** and **City Administrator**. The Citizen actor interacts with the system through the citizen web interface. The City Administrator actor interacts through the protected operations dashboard.

The Citizen actor is associated with the following use cases:

- Register account.
- Log in.
- Submit civic issue report.
- Select category and location.
- View personal reports.
- Track a report by reference.
- View status history and resolution note.
- Log out.

The City Administrator actor is associated with the following use cases:

- Log in to the administration area.
- View operations dashboard.
- View all reports.
- Filter reports by status and category.
- View report details.
- Review hazard level and location.
- Change report status.
- Assign or confirm the responsible department.
- Add a resolution note.
- Log out.

The `Submit civic issue report` use case includes category, description, location, and hazard information. The `Change report status` use case includes recording a status event. The `View personal reports` and `Track a report` use cases depend on successful citizen authentication.

## 8. Database Design

The initial design uses SQLite because it is lightweight, portable, and suitable for a final year project demonstration. The database contains user, report, and status-history information. A deployment may use a compatible MySQL database without changing the main application concepts.

### 8.1 Users Table

| Field | Type | Description |
|---|---|---|
| id | Integer, primary key | Unique user identifier |
| name | String | Citizen or administrator display name |
| email | String, unique | Login email address |
| password_hash | String | Securely hashed password |
| role | String | Citizen or administrator role |
| created_at | DateTime | Account creation date |

### 8.2 Reports Table

| Field | Type | Description |
|---|---|---|
| id | Integer, primary key | Unique report identifier |
| reference | String, unique | Public tracking code, for example CR-XXXXXXX |
| user_id | Integer, foreign key | Citizen who submitted the report |
| category | String | Issue category |
| description | Text | Citizen's issue description |
| location_lat | Decimal/Float | Latitude of the issue |
| location_lng | Decimal/Float | Longitude of the issue |
| address | String | Optional readable location |
| hazard_level | String | Low, medium, or high |
| department | String | Automatically assigned department |
| photo_filename | String | Optional uploaded image filename |
| status | String | Submitted, acknowledged, in progress, or resolved |
| resolution_note | Text | Administrator's resolution explanation |
| created_at | DateTime | Date the report was submitted |
| updated_at | DateTime | Date of the latest update |

A status-history table is recommended to record every transition. It contains an id, report_id, status, note, and created_at field. The relationship between one user and many reports is one-to-many. The relationship between one report and many status events is also one-to-many.

## 9. Workflow

The main workflow is:

**Report -> Submitted -> Acknowledged -> In Progress -> Resolved**

1. A citizen registers or logs in and opens the report form.
2. The citizen enters the issue category, description, location, and hazard information, then submits the form.
3. The platform generates a unique reference code and stores the report with the Submitted status.
4. The system assigns the report to the appropriate department according to its category.
5. A city administrator reviews the report and changes the status to Acknowledged.
6. When work begins, the administrator changes the status to In Progress and may add an operational note.
7. After the issue has been addressed, the administrator changes the status to Resolved and records a resolution note.
8. The citizen views the current status, history, and resolution note through the personal dashboard or tracking page.

The workflow creates a visible record of progress and helps prevent reports from disappearing without feedback.

## 10. Conclusion

CityReport is a GovTech and CivicTech platform designed to improve the way citizens of Douala communicate urban infrastructure and public service problems to city administration. By combining citizen accounts, map-based reporting, automatic department routing, administrative review, and transparent status tracking, the system provides a practical digital response to the absence of a centralized reporting channel.

The requirements defined in this document establish the expected behavior and quality of the platform. Citizens receive a simple way to report and follow issues, while administrators receive structured information for organizing and monitoring municipal responses. The use of Flask, standard web technologies, and SQLite keeps the system affordable, understandable, and suitable for academic development. Future versions could extend the platform with mobile applications, notifications, public analytics, municipal integrations, and deployment to a production server.
