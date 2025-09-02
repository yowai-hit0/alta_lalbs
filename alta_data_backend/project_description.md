TheAlta Data: Project Description tt

1. Project Overview
Alta Data is a comprehensive platform designed for the collection, annotation, and labeling of text and audio data. The system facilitates efficient management of data files and datasets, ensuring a streamlined workflow from data acquisition to the creation of high-quality, structured datasets.

2. Dashboard Features
The main dashboard will provide a centralized hub for all platform activities, offering robust tools for data management and analytics. The dashboard will be accessible to all users and will provide a clear overview of the platform's activities. The dashboard will be customized based on the user role and permission.

2.1. Data Collection & Management
File Management: Users can upload, organize, and manage text and audio files. The system will support various file formats and provide a clear directory structure for the uploaded data.
Dataset Management: Collected and high quality datasets, organize, and manage text and audio files. The system will support various file formats and provide a clear directory structure for the OCR and Transcription datasets.

Text Data Collection:
   PDF Scanning with OCR: Upload PDF documents to be scanned using Optical Character Recognition (OCR) to extract raw text.
   Manual Text Entry: A rich text editor for direct data entry and annotation.

Audio Data Collection: Tools for uploading and managing audio files for transcription or other labeling tasks.



2.2. Annotation & Labeling
Text Categorization: After text is collected (either via OCR or manual entry), it can be categorized based on predefined domains (e.g., Gospel, History, Science, etc.).
Review & Approval Workflow: To ensure data quality, all collected data goes through a review process. Reviewers can approve, reject, or provide feedback on submitted data. If no reviewer assigned on the project the collected data can be automatically approved

2.3. Analytics & Metrics
The analytics section offers precise, actionable insights into data operations, powered by dedicated API endpoints. A timeFrame query parameter (7d, 30d, 365d) should be supported where applicable.

Global Metrics (Super Admin Only)
Endpoint: GET /api/analytics/summary
Total Users: Count of all records in the users table.
Total Projects: Count of all records in the projects table.
Document Status Breakdown: Counts of documents grouped by status (pending_review, approved, rejected).
User Signup Trends: Daily new user counts based on users.created_at.
Storage Utilization: Total storage used across the platform, calculated via getTotalStorageUsed().
Top Contributors: Top 5 users by number of documents submitted within the selected timeframe.
Project-Specific Metrics (Project Manager & Super Admin)
Endpoint: GET /api/analytics/summary?projectId=[id]
Document Counts: Status breakdown (pending_review, approved, rejected) for the specific project.
Contribution Activity: Daily count of new documents submitted to the project.
Project Storage: Total storage used by the specific project, via getStorageUsed(projectId).
Member Activity: Count of active members and new members over the timeframe.
User-Specific Metrics (Visible to Project Managers & Admins)
Endpoint: GET /api/analytics/user/[userId]
Total Contributions: Count of all documents submitted by the user.
Contribution History: A time-series graph of the user's submission activity.
Approval Rate: Percentage of the user's submissions that have been approved.
Project Involvement: List of projects the user is a member of.
Contributor & Reviewer Metrics
For Contributors: The dashboard will now feature metrics for Pending Submissions, Approved Submissions, Rejected Submissions, and a personal Contribution History.
For Reviewers: Their dashboard will include metrics for the Review Queue, Total Items Reviewed, Personal Approval Rate, and Average Review Time.

3. Existing Technical Stack

Alta Data is built on these technology stack:

Frontend: Next.js (React) I will keep using this for my frontend
Backend: fast API Routes
Database: PostgreSQL 
Authentication: JWT-based sessions with passkey support (WebAuthn)
Cloud Services: Google Cloud for Document AI (OCR), Speech-to-Text, and Cloud Storage

4. User Management, Authentication & User Roles

Alta Data features a role-based access control (RBAC) system grounded in the codebase to manage user permissions securely. The roles are defined in schema/database and enforced in API routes.

1. Super Admin (super_admin)
Permissions: Unrestricted access to all platform features, settings, users, and data across all projects. This role is for platform-level administration.
Capabilities:
Manage user accounts, roles, and system-wide configurations.
Create, view, update, and delete any project.
Access global analytics dashboards (/api/analytics/summary).
View and manage all documents and voice samples, regardless of project.
Code Reference: Checks for this role often bypass other permissions.
2. Project Manager (admin at project level)
Permissions: Full control over projects they create or are assigned to as an admin. This role is scoped to specific projects.
Capabilities:
Create new projects (POST /api/projects), becoming the default admin for that project.
Invite users to their projects and assign Contributor or Reviewer roles (POST /api/projects/[projectId]/invitations).
Upload documents and data to their projects.
Access review workflows (/api/projects/[projectId]/review) to approve or reject submissions.
View project-specific analytics.
Edge Cases & Clarifications:
Visibility: A Project Manager can see all documents and activity within their assigned projects only.
Naming: The UI term "Project Manager" corresponds to the admin role in the existing table.
3. Contributor (contributor at project level)
Permissions: Can add data to projects they are a member of.
Capabilities:
Upload files, perform OCR, and enter text manually within their assigned projects (POST /api/projects/[projectId]/documents).
View and manage only their own submitted data.
Submit collected data for review.
They can even have access to perform CRUD operations if the files is not yet submitted for review
Edge Cases & Clarifications:
Deletion: Contributors cannot delete data once it is submitted to a project. This prevents accidental data loss. A "retract submission" feature could be added for items not yet under review.
Isolation: They cannot see data submitted by other contributors in the same project.
4. Reviewer (reviewer at project level)
Permissions: Can review and assess the quality of data submitted by contributors within their assigned projects.
Capabilities:
Access the review queue for their assigned projects (GET /api/projects/[projectId]/review).
Approve or reject data submissions based on quality guidelines (PATCH /api/projects/[projectId]/review/[documentId]).
Provide feedback on submissions.
Edge Cases & Clarifications:
Read-Only Access: Reviewers can view all data submitted for review within their project but cannot upload new data or modify project settings.
Project Scope: Their permissions are strictly confined to the projects they are assigned to.





User Activity Logs: A Two-Tier Approach
    The system will implement a detailed, two-level logging strategy to ensure both operational visibility and a secure audit trail.
1. Access Logs (Operational Monitoring)
Scope: Log every API request at the infrastructure level.
Content: Timestamp, Request ID, HTTP Method, Path, Status Code, Latency, User ID (if authenticated), IP Address.
Purpose: For debugging, performance monitoring, and identifying unusual traffic patterns. These logs are high-volume and have a shorter retention period.
Implementation: Handled by the Winston logger (src/lib/logger.ts) and the web server/cloud provider.
2. Audit Logs (Security & Compliance)
Scope: Log only critical, business-relevant events that represent a state change or a significant action.
Content: A dedicated audit_logs table will store immutable records with the following fields:
actor_user_id: Who performed the action.
action: A descriptive action name (e.g., USER_LOGIN_SUCCESS, PROJECT_CREATED, DOCUMENT_APPROVED).
resource_type: The entity affected (e.g., Project, Document, UserInvitation).
resource_id: The ID of the affected entity.
status: success or failure.
metadata: A JSONB field for context (e.g., old/new role, project name).
ip_address, user_agent.
Events to Log:
Authentication: Login success/failure, logout, password change, passkey registration.
Project Management: Project created/deleted, user invited, invitation accepted, member role changed.
Data Lifecycle: Document uploaded, submitted for review, approved, rejected.
Admin Actions: User role changed, system setting modified.
Purpose: To provide a clear, permanent audit trail for security investigations, compliance, and accountability. Accessible only to Super Admins.

4.1. Passkey Authentication Flow

For enhanced security and user convenience, Alta Data supports passkey authentication. This allows users to log in without a password, using their device's built-in biometrics (like fingerprint or face ID) or a physical security key.

Registration: During signup or from their profile settings, users can register a new passkey. The browser will prompt them to create one, which is then securely stored on their device and linked to their account.
Login: When logging in, users can choose the passkey option. The platform will issue a challenge, and the user's device will use the stored passkey to sign the challenge, verifying their identity without sending any secrets over the network.

ADDITIONAL INFORMATION

External Services:
  Google Cloud Storage: For storing uploaded documents and audio files.
  Google Document AI: For performing OCR on PDF files.
  Google Speech-to-Text: For transcribing audio files.

5. Data Models & Relationships

The database schema (`src/lib/db/schema.ts`) defines the core entities of the system.

users: Stores user information, including credentials and roles.
sessions: Manages active user sessions.
passkeyCredentials: Stores WebAuthn credentials for passwordless login, linked to the `users` table.
projects: Represents a workspace for data collection and annotation.
projectMembers: A join table linking `users` and `projects`, defining a user's role within a specific project.
documents: Stores metadata for uploaded text-based files, including their storage path in GCS and OCR status.
voiceSamples: Stores metadata for uploaded audio files, including storage path, transcription status, and duration.
userInvitations & projectInvitations: Manage tokens for inviting new users to the platform or to specific projects.

Key Relationships:
A user can be a member of multiple projects through the projectMembers table.
Each document and voiceSample is uploaded by a user and can be associated with a project.

6. Core Features & API Endpoints
Below is a breakdown of the core backend features and their corresponding API endpoints.

Key API Endpoints
/api/auth/: Handles user registration, login (password, Google, Passkey), and session management.
/api/projects/: Manages project creation, updates, and membership.
/api/documents/ & /api/text/ocr/: Governs document uploads and OCR processing.
/api/voice/ & /api/voice/transcribe/: Manages audio uploads and transcription.
/api/analytics/: Provides data for the analytics dashboard.

Detailed API Endpoints


6.1. Authentication
POST /api/auth/register: New user registration.
POST /api/auth/login: Traditional email/password login.
POST /api/auth/logout: Terminates the user session.
GET /api/auth/me: Retrieves the current authenticated user's profile.
GET /api/auth/google: Initiates Google OAuth2 login flow.

Passkeys (WebAuthn):
 POST /api/auth/passkeys/register: Generates a challenge for passkey registration.
 POST /api/auth/passkeys/register/verify: Verifies the signed challenge and saves the new credential.
 POST /api/auth/passkeys/login: Generates a challenge for passkey login.
 POST /api/auth/passkeys/login/verify: Verifies the login challenge.

6.2. User & Project Management
GET, POST /api/projects: Create and list projects.
GET, PUT /api/projects/[projectId]: Retrieve and update a specific project.
GET /api/admin/users: (Admin) List all users on the platform.
POST /api/projects/[projectId]/invitations: Invite a user to a project.
POST /api/invitations/[token]/accept: Accept a project or platform invitation.

6.3. Data Ingestion & Processing
POST /api/documents: Uploads a document, saves metadata to the documents table, and stores the file in GCS.
POST /api/text/ocr: Triggers the OCR process for a given document using Google Document AI.
POST /api/voice: Uploads an audio file, saves metadata to the voiceSamples table, and stores the file in GCS.
POST /api/voice/transcribe: Triggers the transcription process for a given audio file using Google Speech-to-Text.

6.4. Review & Analytics
POST /api/projects/[projectId]/review: Submit data for review.
GET /api/analytics/summary: Get platform-wide statistics.
GET /api/analytics/contributions: View contribution metrics.
GET /api/analytics/user/[userId]: Fetch analytics for a specific user.

7. Other Recommendations
To ensure the platform is scalable, secure, and maintainable, the following enterprise-grade practices should be adopted:

Centralized RBAC Middleware: Implement a single, robust middleware layer responsible for handling all permission checks across API routes. This approach minimizes code duplication, enforces consistent authorization logic, and simplifies future permission modifications.
Soft Deletes: For critical data entities such as documents, projects, and user accounts, implement a soft delete strategy. Instead of permanently removing records, introduce a deleted_at timestamp column. This allows for data recovery, maintains historical integrity, and facilitates auditing.
Idempotency for Mutations: To prevent unintended side effects from network retries, critical write operations (e.g., document uploads, data submissions) should support idempotency. This can be achieved by utilizing an Idempotency-Key header, ensuring that identical requests processed multiple times result in the same outcome.
Background Job Processing: Offload long-running and resource-intensive tasks, such as Optical Character Recognition (OCR) and audio transcription, to a dedicated asynchronous job processing system. Options include self-hosted solutions like BullMQ with Redis, or leveraging managed cloud services such as Azure Functions. This improves API responsiveness, enhances system reliability, and allows for better resource utilization.
Configuration & Secrets Management: Adopt a secure and centralized solution for managing application configurations and sensitive secrets (e.g., API keys, database credentials). Instead of storing these in .env files, utilize a dedicated secrets management service. This practice enhances security by preventing secrets from being exposed in source code repositories and provides better control over access.
Structured, Correlated Logging: Implement a comprehensive logging strategy where all logs (both operational access logs and security audit logs) are structured and correlated. Each log entry should include a unique requestId that traces an operation through its entire lifecycle across different services and components. This enables easier debugging, performance analysis, and security incident investigation.
Automated Testing Strategy: Implement a comprehensive testing strategy including unit, integration, and end-to-end tests to ensure code quality and prevent regressions. This should be integrated into the CI/CD pipeline.
API Versioning: Implement API versioning (e.g., /api/v1/projects) to allow for backward compatibility and graceful evolution of the API without breaking existing client applications.
Rate Limiting & Throttling: Protect against abuse and ensure fair usage by implementing rate limiting on API endpoints to restrict the number of requests a user or IP address can make within a given time frame.
Health Checks & Monitoring: Implement robust health check endpoints and integrate with monitoring tools to track the health, performance, and availability of the platform's services.
Containerization (Docker): Package the application and its dependencies into Docker containers to ensure consistent environments across development, testing, and production, facilitating easier deployment and scaling.
Infrastructure as Code (IaC): Manage and provision infrastructure (e.g., Azure resources) using tools like Terraform or Bicep to ensure consistency, repeatability, and version control of the infrastructure setup.(Not Priority Just want to keep to not forget it in the future)
Disaster Recovery & Backup Strategy: Establish a clear strategy for data backups and disaster recovery to ensure business continuity and minimize data loss in case of system failures.(Not Priority Just want to keep to not forget it in the future)

NB: Domains to use we will discuss it well as the whole deployment will be done on azure.




