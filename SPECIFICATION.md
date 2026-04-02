# Kudos System Specification

## Functional Requirements

### User Stories

1. As a user, I can select another user from a dropdown list
2. As a user, I can write a message of appreciation (max 250 characters)
3. As a user, I can submit the kudos which gets stored in the database (in-memory for demo)
4. As a user, I can view a feed of recent kudos on the dashboard
5. As an administrator, I can hide or delete inappropriate kudos messages

### Acceptance Criteria

- Users can only select valid colleagues from a predefined list
- Messages are required, max 250 characters, and sanitized for HTML
- Users cannot give kudos to themselves
- Public feed shows only visible kudos (not hidden/deleted)
- Admins can log in, view all kudos, and hide or delete any message
- Hidden kudos are not shown in the public feed but remain in the system for audit
- Deleted kudos are permanently removed
- All moderation actions are logged with timestamp, admin user, action, and kudos ID
- Input validation and error messages are shown for all invalid actions

## Technical Design

### Database Schema (in-memory Python structure)

#### Kudos Table
- id: integer (auto-increment)
- from_user: string
- to_user: string
- message: string
- ts: datetime
- is_visible: boolean (default: true, set to false if hidden)
- moderated_by: string (nullable, admin username)
- moderated_at: datetime (nullable)
- reason_for_moderation: string (nullable)

#### Moderation Log Table
- id: integer (auto-increment)
- kudos_id: integer (foreign key)
- action: string ("hide" or "delete")
- admin_user: string
- timestamp: datetime
- reason: string (nullable)

### API Endpoints

- GET /dashboard: Show public feed
- POST /kudos: Submit new kudos
- GET /admin: Admin login or moderation dashboard
- POST /admin/login: Admin login
- POST /admin/logout: Admin logout
- POST /admin/moderate: Hide or delete kudos (admin only)

### Frontend Components

- Kudos submission form (dropdowns, textarea, submit button)
- Public kudos feed (list of recent visible kudos)
- Admin login form
- Admin moderation dashboard (list of all kudos with hide/delete controls)
- Responsive CSS for desktop/mobile

### Security Considerations

- Simple password-based admin authentication (demo only)
- Input sanitization for all user input
- Only admins can access moderation endpoints

### Performance Considerations

- Feed limited to 20 most recent visible kudos
- In-memory storage for demo; production would use a database

### Error Handling and Logging

- All invalid actions return clear error messages
- Moderation actions are logged in-memory for audit

## Implementation Plan

1. Implement in-memory data structures for kudos and moderation log
2. Build user-facing dashboard and kudos submission form
3. Add public feed display (show only visible kudos)
4. Implement admin login and moderation dashboard
5. Add hide/delete logic and moderation logging
6. Validate all inputs and handle errors
7. Style for responsive design
8. Manual testing of all flows and edge cases

---

This specification is now complete and approved for implementation.
