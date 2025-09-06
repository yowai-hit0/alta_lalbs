# Alta Data Backend - Project Logic Implementation

## 🎯 Overview

This document describes the comprehensive project logic implementation for the Alta Data Backend, including role-based access control, data management, and workflow processes.

## 🏗️ Project Structure & Roles

### **Project Creation & Ownership**
- **Project Admin/Owner**: User who creates a project automatically becomes the project admin
- **Project Members**: Users invited to the project with specific roles
- **Role Types**: `admin`, `contributor`, `reviewer`

### **Role-Based Permissions**

#### **Project Admin (Owner)**
- ✅ Create and manage projects
- ✅ Invite users as contributors or reviewers
- ✅ Upload and manage all data types
- ✅ Access review queue and approve/reject submissions
- ✅ Modify project settings
- ✅ Delete projects

#### **Contributors**
- ✅ Upload files (documents, voice samples)
- ✅ Create raw text entries (manual data entry)
- ✅ CRUD operations on their own draft data
- ✅ Submit data for review
- ✅ Mass submission of multiple items
- ❌ Cannot see other contributors' draft data
- ❌ Cannot delete submitted data
- ❌ Cannot access review queue
- ❌ Cannot modify project settings

#### **Reviewers**
- ✅ Access review queue for assigned projects
- ✅ Approve, reject, or provide feedback on submissions
- ✅ Read-only access to all submitted data
- ❌ Cannot upload data
- ❌ Cannot modify project settings
- ❌ Cannot access draft data from contributors

## 📊 Data Models & Types

### **Document Model**
```python
class Document(Base):
    id: str
    project_id: str
    uploaded_by_id: str
    original_filename: str
    gcs_uri: str
    ocr_text: str | None
    status: str  # draft|pending_review|approved|rejected
    domain: str | None
    submitted_at: datetime | None
    reviewed_by_id: str | None
    feedback: str | None
    is_raw: bool  # True for manual data entry
    processed: bool  # True if OCR has been processed
    tags: str | None  # JSON string of tags
    metadata: str | None  # JSON string of additional metadata
```

### **Voice Sample Model**
```python
class VoiceSample(Base):
    id: str
    project_id: str
    uploaded_by_id: str
    original_filename: str
    gcs_uri: str
    transcription_text: str | None
    status: str  # draft|pending_review|approved|rejected
    duration_seconds: int | None
    submitted_at: datetime | None
    reviewed_by_id: str | None
    feedback: str | None
    processed: bool  # True if transcription has been processed
    language: str | None  # Language code
    tags: str | None  # JSON string of tags
    metadata: str | None  # JSON string of additional metadata
```

### **Raw Text Model**
```python
class RawText(Base):
    id: str
    project_id: str
    created_by_id: str
    title: str
    content: str
    status: str  # draft|pending_review|approved|rejected
    domain: str | None
    submitted_at: datetime | None
    reviewed_by_id: str | None
    feedback: str | None
    tags: str | None  # JSON string of tags
    metadata: str | None  # JSON string of additional metadata
```

## 🔄 Workflow Process

### **1. Data Upload & Creation**

#### **Document Upload**
```http
POST /api/documents
Query Parameters:
- project_id: string (required)
- domain: string (optional)
- is_raw: boolean (default: false)

Body: multipart/form-data
- file: File (required)
```

**Process:**
1. Validate user has contributor/admin role in project
2. Validate file type and size
3. Upload to Google Cloud Storage
4. Create document record with `status='draft'`
5. If `is_raw=false`, trigger OCR processing via RabbitMQ
6. If `is_raw=true`, mark as `processed=true` (no OCR needed)

#### **Voice Sample Upload**
```http
POST /api/voice
Query Parameters:
- project_id: string (required)

Body: multipart/form-data
- file: File (required)
```

**Process:**
1. Validate user has contributor/admin role in project
2. Validate audio file type and size
3. Upload to Google Cloud Storage
4. Create voice sample record with `status='draft'`
5. Trigger transcription processing via RabbitMQ

#### **Raw Text Creation**
```http
POST /api/raw-text
Body: JSON
{
  "project_id": "string",
  "title": "string",
  "content": "string",
  "domain": "string (optional)",
  "tags": ["string"] (optional),
  "metadata": {} (optional)
}
```

**Process:**
1. Validate user has contributor/admin role in project
2. Create raw text record with `status='draft'`
3. No processing needed (manual entry)

### **2. Draft Management**

#### **Contributor Access**
- Contributors can only see and modify their own draft data
- Full CRUD operations on draft items
- Cannot access other contributors' drafts

#### **Draft Operations**
```http
# Get my drafts
GET /api/my-drafts?project_id={project_id}

# Update document
PUT /api/documents/{document_id}

# Update voice sample
PUT /api/voice/{voice_sample_id}

# Update raw text
PUT /api/raw-text/{raw_text_id}

# Delete document (draft only)
DELETE /api/documents/{document_id}

# Delete voice sample (draft only)
DELETE /api/voice/{voice_sample_id}

# Delete raw text (draft only)
DELETE /api/raw-text/{raw_text_id}
```

### **3. Mass Submission**

#### **Submit Multiple Items**
```http
POST /api/submit
Body: JSON
{
  "document_ids": ["string"] (optional),
  "voice_sample_ids": ["string"] (optional),
  "raw_text_ids": ["string"] (optional)
}
```

**Process:**
1. Validate all items belong to the user
2. Validate all items are in `draft` status
3. Update status to `pending_review`
4. Set `submitted_at` timestamp
5. Items become visible to reviewers

### **4. Review Process**

#### **Review Queue Access**
```http
GET /api/review?project_id={project_id}
```

**Returns:**
- All pending documents, voice samples, and raw texts
- Sorted by submission date
- Includes metadata (type, title, submitted_at, uploaded_by_id)

#### **Review Decision**
```http
PATCH /api/review/{item_id}?item_type={document|voice|raw_text}
Body: JSON
{
  "decision": "approve|reject",
  "feedback": "string (optional)"
}
```

**Process:**
1. Validate reviewer has access to project
2. Update item status to `approved` or `rejected`
3. Set `reviewed_by_id` and `feedback`
4. Log audit event

### **5. Processing Management**

#### **Manual OCR Trigger**
```http
POST /api/processing/ocr?document_id={document_id}
```

#### **Manual Transcription Trigger**
```http
POST /api/processing/transcribe?voice_sample_id={voice_sample_id}
```

#### **Batch Processing**
```http
POST /api/processing/batch-ocr
Query: document_ids=["id1", "id2", ...]

POST /api/processing/batch-transcribe
Query: voice_sample_ids=["id1", "id2", ...]
```

#### **Processing Status**
```http
GET /api/processing/status/{item_id}?item_type={document|voice}
```

## 🔒 Access Control Implementation

### **Project Access Validation**
```python
async def validate_project_access(
    project_id: str,
    user_id: str,
    required_roles: list,
    db: AsyncSession
) -> bool:
    """Validate user has required role in project"""
    member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.role.in_(required_roles)
        )
    )
    return member.scalar_one_or_none() is not None
```

### **Data Ownership Validation**
```python
async def validate_data_ownership(
    item_id: str,
    user_id: str,
    item_type: str,
    db: AsyncSession
) -> bool:
    """Validate user owns the data item"""
    if item_type == 'document':
        item = await db.execute(
            select(Document).where(
                Document.id == item_id,
                Document.uploaded_by_id == user_id
            )
        )
    elif item_type == 'voice':
        item = await db.execute(
            select(VoiceSample).where(
                VoiceSample.id == item_id,
                VoiceSample.uploaded_by_id == user_id
            )
        )
    elif item_type == 'raw_text':
        item = await db.execute(
            select(RawText).where(
                RawText.id == item_id,
                RawText.created_by_id == user_id
            )
        )
    
    return item.scalar_one_or_none() is not None
```

## 🗂️ File Management & Cleanup

### **Graceful Deletion**
When deleting draft items:
1. Delete from Google Cloud Storage
2. Delete from database
3. Handle GCS deletion errors gracefully
4. Continue with database deletion even if GCS fails

### **Storage Management**
- **Documents**: 50MB limit, PDF, images, Office docs
- **Voice Samples**: 100MB limit, WAV, MP3, MP4, AAC, OGG, FLAC
- **Raw Text**: 100KB limit, plain text content

## 🔄 Background Processing

### **RabbitMQ Integration**
- **OCR Processing**: Automatic for non-raw documents
- **Transcription**: Automatic for voice samples
- **Email Sending**: For notifications and invitations
- **Outbox Pattern**: Ensures reliable message delivery

### **Processing Flags**
- **`processed`**: Indicates if OCR/transcription is complete
- **`is_raw`**: Indicates manual data entry (no processing needed)
- **Status Tracking**: `draft` → `pending_review` → `approved/rejected`

## 📋 API Endpoints Summary

### **Data Management**
- `POST /api/documents` - Upload document
- `POST /api/voice` - Upload voice sample
- `POST /api/raw-text` - Create raw text
- `GET /api/my-drafts` - Get user's drafts
- `PUT /api/documents/{id}` - Update document
- `PUT /api/voice/{id}` - Update voice sample
- `PUT /api/raw-text/{id}` - Update raw text
- `DELETE /api/documents/{id}` - Delete document
- `DELETE /api/voice/{id}` - Delete voice sample
- `DELETE /api/raw-text/{id}` - Delete raw text

### **Submission & Review**
- `POST /api/submit` - Mass submission
- `GET /api/review` - Get review queue
- `PATCH /api/review/{id}` - Review decision

### **Processing**
- `POST /api/processing/ocr` - Trigger OCR
- `POST /api/processing/transcribe` - Trigger transcription
- `POST /api/processing/batch-ocr` - Batch OCR
- `POST /api/processing/batch-transcribe` - Batch transcription
- `GET /api/processing/status/{id}` - Get processing status

## 🎯 Key Features

### **1. Role-Based Access Control**
- ✅ Project admins have full control
- ✅ Contributors can manage their own data
- ✅ Reviewers have read-only access to submitted data
- ✅ Proper isolation between user data

### **2. Draft Management**
- ✅ Contributors can edit their drafts
- ✅ Cannot modify submitted data
- ✅ Cannot see other contributors' drafts
- ✅ Mass submission capability

### **3. Processing Control**
- ✅ Automatic processing via RabbitMQ
- ✅ Manual processing triggers
- ✅ Batch processing support
- ✅ Processing status tracking
- ✅ Raw text support (no processing needed)

### **4. Review Workflow**
- ✅ Unified review queue for all data types
- ✅ Approve/reject with feedback
- ✅ Audit logging for all decisions
- ✅ Reviewer access control

### **5. File Management**
- ✅ Graceful deletion with GCS cleanup
- ✅ File type and size validation
- ✅ Storage optimization
- ✅ Error handling for storage operations

### **6. Data Integrity**
- ✅ Transaction-based operations
- ✅ Outbox pattern for reliable processing
- ✅ Audit logging for all operations
- ✅ Proper error handling and rollback

This implementation provides a comprehensive, production-ready project management system with proper role-based access control, data management, and workflow processes! 🚀
