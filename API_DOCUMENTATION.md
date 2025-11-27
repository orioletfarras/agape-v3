# Agape V3 - API Documentation

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- MySQL Database (Local or AWS Aurora)
- AWS Account (for S3, SES, SNS)
- Stripe Account (for payments)

### Installation

1. **Clone and setup environment:**
```bash
# Copy environment variables
cp .env.example .env

# Edit .env and configure your credentials

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment variables in `.env`:**
```bash
# Database
DATABASE_URL=mysql+aiomysql://user:password@host:3306/dbname

# JWT Secret (generate a secure random string)
SECRET_KEY=your-super-secret-key-min-32-characters

# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_SES_FROM_EMAIL=noreply@yourdomain.com

# Stripe
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key

# Optional: Expo Push Notifications
EXPO_ACCESS_TOKEN=your_expo_token_if_needed
```

3. **Setup database:**
```bash
# Run migrations
alembic upgrade head
```

4. **Run the application:**
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

5. **Access the API:**
- API Base URL: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📋 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication Header
All protected endpoints require:
```
x-access-token: <JWT_TOKEN>
```

---

## 🔐 Authentication Endpoints

### 1. Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

### 2. Register - Start
```http
POST /api/v1/auth/register-start
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Verification code sent to your email",
  "registration_id": "REG-20250127-ABCD1234"
}
```

### 3. Register - Verify Email
```http
POST /api/v1/auth/register-verify-email
Content-Type: application/json

{
  "registration_id": "REG-20250127-ABCD1234",
  "code": "123456"
}
```

### 4. Register - Complete
```http
POST /api/v1/auth/register-complete
Content-Type: application/json

{
  "registration_id": "REG-20250127-ABCD1234",
  "username": "johndoe",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 5. Send OTP (Email/SMS)
```http
POST /api/v1/auth/send-login-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "method": "email"  // or "sms"
}
```

### 6. Verify OTP
```http
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}
```

### 7. Change Password
```http
POST /api/v1/auth/change-password
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "current_password": "oldPassword123",
  "new_password": "newSecurePass456"
}
```

### 8. Send Reset Code
```http
POST /api/v1/auth/send-reset-code
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### 9. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 10. Validate Token
```http
GET /api/v1/auth/validate-token
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "valid": true,
  "user_id": 1
}
```

### 11. Logout
```http
POST /api/v1/auth/logout
x-access-token: <JWT_TOKEN>
```

---

## 👤 Profile Endpoints

### 1. Get Profile
```http
GET /api/v1/profile
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com",
  "nombre": "John",
  "apellidos": "Doe",
  "profile_image_url": "https://bucket.s3.region.amazonaws.com/profile.jpg",
  "bio": "Software developer",
  "onboarding_completed": true,
  "created_at": "2025-01-27T10:00:00Z"
}
```

### 2. Upload Profile Image
```http
POST /api/v1/upload-profile-image
Content-Type: multipart/form-data
x-access-token: <JWT_TOKEN>

file: <image_file>
```

**Response:**
```json
{
  "success": true,
  "image_url": "https://bucket.s3.region.amazonaws.com/profile-images/uuid.jpg"
}
```

### 3. Update Personal Info
```http
POST /api/v1/update-personal-info
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "nombre": "John",
  "apellidos": "Doe Smith",
  "bio": "Full stack developer passionate about technology"
}
```

### 4. Get Personal Info
```http
GET /api/v1/get-personal-info
x-access-token: <JWT_TOKEN>
```

### 5. Check Nickname Availability
```http
POST /api/v1/check-nickname
Content-Type: application/json

{
  "nickname": "johndoe"
}
```

**Response:**
```json
{
  "available": true
}
```

### 6. Complete Profile (Onboarding)
```http
POST /api/v1/complete-profile
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "nickname": "johndoe",
  "parish_id": 123
}
```

### 7. Get Primary Organization
```http
GET /api/v1/user/primary-organization
x-access-token: <JWT_TOKEN>
```

### 8. Update Primary Organization
```http
PUT /api/v1/user/primary-organization
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "organization_id": 5
}
```

### 9. Get Current User
```http
GET /api/v1/current_user
x-access-token: <JWT_TOKEN>
```

---

## 🏢 Organizations Endpoints

### 1. List Organizations
```http
GET /api/v1/organizations
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Parroquia San José",
    "image_url": "https://bucket.s3.region.amazonaws.com/org1.jpg"
  }
]
```

### 2. Search Parishes
```http
GET /api/v1/search-parishes?q=San&limit=100
```

**Response:**
```json
{
  "parishes": [
    {
      "id": 1,
      "name": "Parroquia San José",
      "address": "Calle Principal 123"
    }
  ]
}
```

---

## 📝 Posts Endpoints

### 1. Create Post
```http
POST /api/v1/posts
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "channel_id": 1,
  "content": "This is my post content",
  "images": ["https://bucket.s3.amazonaws.com/image1.jpg"],
  "videos": [],
  "event_id": null
}
```

**Requirements:**
- User must be subscribed to the channel
- Returns 403 if not subscribed

### 2. Get Posts Feed
```http
GET /api/v1/posts?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

**Query Parameters:**
- `channel_id` (optional): Filter by channel
- `author_id` (optional): Filter by author
- `event_id` (optional): Filter by event
- `include_hidden` (optional): Include hidden posts (default: false)
- `only_favorites` (optional): Only show favorites (default: false)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**IMPORTANT:** Only returns posts from channels the user is subscribed to

### 3. Get Single Post
```http
GET /api/v1/posts/{post_id}
x-access-token: <JWT_TOKEN>
```

### 4. Update Post
```http
PUT /api/v1/posts/{post_id}
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "content": "Updated content",
  "images": ["https://bucket.s3.amazonaws.com/new-image.jpg"]
}
```

**Requirements:**
- Only the post author can update

### 5. Delete Post
```http
DELETE /api/v1/posts/{post_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Only the post author can delete

### 6. Like/Unlike Post
```http
PATCH /api/v1/posts/{post_id}/like
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "action": "like"  // or "unlike"
}
```

### 7. Pray/Unpray Post
```http
PATCH /api/v1/posts/{post_id}/pray
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "action": "pray"  // or "unpray"
}
```

### 8. Favorite/Unfavorite Post
```http
PATCH /api/v1/posts/{post_id}/favorite
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "action": "favorite"  // or "unfavorite"
}
```

### 9. Hide Post
```http
POST /api/v1/posts/{post_id}/hide
x-access-token: <JWT_TOKEN>
```

### 10. Unhide Post
```http
DELETE /api/v1/posts/{post_id}/hide
x-access-token: <JWT_TOKEN>
```

### 11. Get Post Statistics
```http
GET /api/v1/posts/{post_id}/stats
x-access-token: <JWT_TOKEN>
```

### 12. Get User Favorites
```http
GET /api/v1/posts/favorites/list?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 13. Upload Post Image
```http
POST /api/v1/posts/upload-image
Content-Type: multipart/form-data
x-access-token: <JWT_TOKEN>

file: <image_file>
```

### 14. Upload Post Video
```http
POST /api/v1/posts/upload-video
Content-Type: multipart/form-data
x-access-token: <JWT_TOKEN>

file: <video_file>
```

### 15. Get Channel Posts
```http
GET /api/v1/posts/channel/{channel_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 16. Get User Posts
```http
GET /api/v1/posts/user/{user_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 17. Get Event Posts
```http
GET /api/v1/posts/event/{event_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

---

## 🏢 Channels Endpoints

### 1. Create Channel
```http
POST /api/v1/channels
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "name": "Youth Group",
  "description": "Channel for youth activities",
  "organization_id": 1,
  "image_url": "https://bucket.s3.amazonaws.com/channel.jpg",
  "is_private": false
}
```

### 2. Get Channels List
```http
GET /api/v1/channels?subscribed_only=false&page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 3. Get Channel by ID
```http
GET /api/v1/channels/{channel_id}
x-access-token: <JWT_TOKEN>
```

### 4. Update Channel
```http
PUT /api/v1/channels/{channel_id}
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### 5. Delete Channel
```http
DELETE /api/v1/channels/{channel_id}
x-access-token: <JWT_TOKEN>
```

### 6. Subscribe to Channel
```http
POST /api/v1/channels/{channel_id}/subscribe
x-access-token: <JWT_TOKEN>
```

### 7. Unsubscribe from Channel
```http
DELETE /api/v1/channels/{channel_id}/subscribe
x-access-token: <JWT_TOKEN>
```

### 8. Get Channel Subscribers
```http
GET /api/v1/channels/{channel_id}/subscribers?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 9. Get My Subscriptions
```http
GET /api/v1/channels/my/subscriptions?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 10. Add Channel Admin
```http
POST /api/v1/channels/{channel_id}/admins
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "user_id": 123
}
```

### 11. Remove Channel Admin
```http
DELETE /api/v1/channels/{channel_id}/admins/{user_id}
x-access-token: <JWT_TOKEN>
```

### 12. Get Channel Admins
```http
GET /api/v1/channels/{channel_id}/admins
x-access-token: <JWT_TOKEN>
```

### 13. Get Channel Settings
```http
GET /api/v1/channels/{channel_id}/settings
x-access-token: <JWT_TOKEN>
```

### 14. Update Channel Settings
```http
PUT /api/v1/channels/{channel_id}/settings
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "notifications_enabled": true,
  "post_notifications": true,
  "event_notifications": true
}
```

### 15. Hide Channel
```http
POST /api/v1/channels/{channel_id}/hide
x-access-token: <JWT_TOKEN>
```

### 16. Unhide Channel
```http
DELETE /api/v1/channels/{channel_id}/hide
x-access-token: <JWT_TOKEN>
```

### 17. Create Channel Alert
```http
POST /api/v1/channels/{channel_id}/alerts
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "channel_id": 1,
  "title": "Important Announcement",
  "message": "Meeting tomorrow at 6 PM"
}
```

### 18. Get Channel Alerts
```http
GET /api/v1/channels/{channel_id}/alerts?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 19. Get Channel Statistics
```http
GET /api/v1/channels/{channel_id}/stats
x-access-token: <JWT_TOKEN>
```

### 20. Upload Channel Image
```http
POST /api/v1/channels/upload-image
Content-Type: multipart/form-data
x-access-token: <JWT_TOKEN>

file: <image_file>
```

### 21. Get Organization Channels
```http
GET /api/v1/channels/organization/{organization_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 22. Search Channels
```http
GET /api/v1/channels/search/{query}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

---

## 📅 Events Endpoints

### 1. Create Event
```http
POST /api/v1/events
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "channel_id": 1,
  "name": "Youth Retreat 2025",
  "description": "Annual youth retreat",
  "event_date": "2025-06-15T10:00:00Z",
  "end_date": "2025-06-17T16:00:00Z",
  "location": "Mountain Camp",
  "max_attendees": 50,
  "requires_payment": true,
  "price": 150.00,
  "currency": "EUR"
}
```

### 2. Get Events List
```http
GET /api/v1/events?upcoming_only=true&page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 3. Get Event by ID
```http
GET /api/v1/events/{event_id}
x-access-token: <JWT_TOKEN>
```

### 4. Update Event
```http
PUT /api/v1/events/{event_id}
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "name": "Updated Event Name",
  "max_attendees": 60
}
```

### 5. Delete Event
```http
DELETE /api/v1/events/{event_id}
x-access-token: <JWT_TOKEN>
```

### 6. Register for Event
```http
POST /api/v1/events/{event_id}/register
x-access-token: <JWT_TOKEN>
```

### 7. Cancel Registration
```http
DELETE /api/v1/events/{event_id}/register
x-access-token: <JWT_TOKEN>
```

### 8. Get Event Registrations
```http
GET /api/v1/events/{event_id}/registrations?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 9. Create Payment Intent
```http
POST /api/v1/events/{event_id}/payment-intent?discount_code=SUMMER2025
x-access-token: <JWT_TOKEN>
```

### 10. Create Discount Code
```http
POST /api/v1/events/{event_id}/discount-codes
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "event_id": 1,
  "code": "SUMMER2025",
  "discount_type": "percentage",
  "discount_value": 20,
  "max_uses": 50,
  "valid_until": "2025-06-01T00:00:00Z"
}
```

### 11. Apply Discount Code
```http
POST /api/v1/events/{event_id}/apply-discount
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "code": "SUMMER2025"
}
```

### 12. Create Event Alert
```http
POST /api/v1/events/{event_id}/alerts
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "event_id": 1,
  "title": "Important Update",
  "message": "Bring warm clothes for the retreat"
}
```

### 13. Get Event Alerts
```http
GET /api/v1/events/{event_id}/alerts?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 14. Get Event Statistics
```http
GET /api/v1/events/{event_id}/stats
x-access-token: <JWT_TOKEN>
```

### 15. Upload Event Image
```http
POST /api/v1/events/upload-image
Content-Type: multipart/form-data
x-access-token: <JWT_TOKEN>

file: <image_file>
```

### 16. Get Channel Events
```http
GET /api/v1/events/channel/{channel_id}?upcoming_only=true&page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

---

## 💬 Comments Endpoints

### 1. Create Comment
```http
POST /api/v1/comments
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "post_id": 1,
  "content": "Great post! This is very helpful."
}
```

**Requirements:**
- Must be authenticated
- Post must exist

### 2. Get Post Comments
```http
GET /api/v1/comments/post/{post_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "comments": [
    {
      "id": 1,
      "post_id": 1,
      "user_id": 2,
      "content": "Great post!",
      "created_at": "2025-01-27T10:00:00Z",
      "updated_at": "2025-01-27T10:00:00Z",
      "user": {
        "id": 2,
        "username": "johndoe",
        "nombre": "John",
        "apellidos": "Doe",
        "profile_image_url": "https://..."
      }
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### 3. Update Comment
```http
PUT /api/v1/comments/{comment_id}
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "content": "Updated comment content"
}
```

**Requirements:**
- Only the comment author can update it

### 4. Delete Comment
```http
DELETE /api/v1/comments/{comment_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Only the comment author can delete it

---

## 👥 Social Endpoints

### 1. Follow User
```http
POST /api/v1/social/follow/{user_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Cannot follow yourself
- Cannot follow the same user twice

**Response:**
```json
{
  "success": true,
  "is_following": true,
  "message": "Successfully followed user"
}
```

### 2. Unfollow User
```http
DELETE /api/v1/social/follow/{user_id}
x-access-token: <JWT_TOKEN>
```

### 3. Get User Followers
```http
GET /api/v1/social/followers/{user_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "users": [
    {
      "id": 2,
      "username": "johndoe",
      "nombre": "John",
      "apellidos": "Doe",
      "profile_image_url": "https://...",
      "bio": "Developer",
      "followers_count": 120,
      "following_count": 85,
      "is_following": false,
      "is_followed_by": true
    }
  ],
  "total": 120,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### 4. Get User Following
```http
GET /api/v1/social/following/{user_id}?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

### 5. Search Users
```http
GET /api/v1/social/search?q=john&page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

**Query Parameters:**
- `q` (required): Search query (username, name, or surname)
- `page` (optional): Page number
- `page_size` (optional): Items per page (max: 100)

### 6. Get Suggested Users
```http
GET /api/v1/social/suggestions?limit=10
x-access-token: <JWT_TOKEN>
```

**Response:**
Returns users that the current user is not following yet

### 7. Get Social Statistics
```http
GET /api/v1/social/stats/{user_id}
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "user_id": 1,
  "followers_count": 120,
  "following_count": 85,
  "posts_count": 42
}
```

---

## 🔔 Notifications Endpoints

### 1. Get Notifications
```http
GET /api/v1/notifications?page=1&page_size=20&unread_only=false
x-access-token: <JWT_TOKEN>
```

**Query Parameters:**
- `unread_only` (optional): Filter only unread notifications
- `page` (optional): Page number
- `page_size` (optional): Items per page (max: 100)

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "user_id": 1,
      "type": "like",
      "title": "New Like",
      "message": "John Doe liked your post",
      "related_id": 123,
      "image_url": "https://...",
      "is_read": false,
      "created_at": "2025-01-27T10:00:00Z"
    }
  ],
  "total": 45,
  "unread_count": 12,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### 2. Get Notification Statistics
```http
GET /api/v1/notifications/stats
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "total_count": 45,
  "unread_count": 12,
  "read_count": 33
}
```

### 3. Mark Notification as Read
```http
PATCH /api/v1/notifications/{notification_id}/read
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Only the notification owner can mark it as read

### 4. Mark All as Read
```http
PATCH /api/v1/notifications/read-all
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "success": true,
  "message": "Marked 12 notifications as read"
}
```

### 5. Delete Notification
```http
DELETE /api/v1/notifications/{notification_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Only the notification owner can delete it

### 6. Delete All Notifications
```http
DELETE /api/v1/notifications
x-access-token: <JWT_TOKEN>
```

### 7. Get Unread Count
```http
GET /api/v1/notifications/unread/count
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "unread_count": 12
}
```

---

## 💬 Messaging Endpoints

### 1. Create Conversation
```http
POST /api/v1/messaging/conversations
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "user_id": 2
}
```

**Response:**
Creates new direct conversation or returns existing one between users

```json
{
  "id": 1,
  "type": "direct",
  "title": null,
  "image_url": null,
  "channel_id": null,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z",
  "unread_count": 0,
  "last_message": null,
  "participants": [
    {
      "id": 1,
      "username": "user1",
      "nombre": "User",
      "apellidos": "One",
      "profile_image_url": "https://..."
    },
    {
      "id": 2,
      "username": "user2",
      "nombre": "User",
      "apellidos": "Two",
      "profile_image_url": "https://..."
    }
  ]
}
```

### 2. Get Conversations
```http
GET /api/v1/messaging/conversations?page=1&page_size=20
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "conversations": [
    {
      "id": 1,
      "type": "direct",
      "unread_count": 3,
      "last_message": {
        "id": 45,
        "content": "Hello!",
        "created_at": "2025-01-27T10:00:00Z",
        "sender": {
          "id": 2,
          "username": "user2"
        }
      },
      "participants": [...]
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

### 3. Get Conversation by ID
```http
GET /api/v1/messaging/conversations/{conversation_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- User must be a participant in the conversation

### 4. Delete Conversation
```http
DELETE /api/v1/messaging/conversations/{conversation_id}
x-access-token: <JWT_TOKEN>
```

### 5. Mark Conversation as Read
```http
PATCH /api/v1/messaging/conversations/{conversation_id}/read
x-access-token: <JWT_TOKEN>
```

**Response:**
```json
{
  "success": true,
  "message": "Conversation marked as read"
}
```

### 6. Send Message
```http
POST /api/v1/messaging/messages
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "conversation_id": 1,
  "content": "Hello! How are you?",
  "reply_to_message_id": null
}
```

**Requirements:**
- User must be a participant in the conversation
- Automatically increments unread count for other participants

**Response:**
```json
{
  "success": true,
  "message": {
    "id": 46,
    "conversation_id": 1,
    "sender_id": 1,
    "content": "Hello! How are you?",
    "message_type": "text",
    "reply_to_message_id": null,
    "is_deleted": false,
    "created_at": "2025-01-27T10:00:00Z",
    "edited_at": null,
    "sender": {
      "id": 1,
      "username": "user1",
      "profile_image_url": "https://..."
    }
  }
}
```

### 7. Get Messages
```http
GET /api/v1/messaging/conversations/{conversation_id}/messages?page=1&page_size=50
x-access-token: <JWT_TOKEN>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Messages per page (default: 50, max: 100)

**Response:**
Returns messages in descending order (newest first)

### 8. Update Message
```http
PUT /api/v1/messaging/messages/{message_id}
Content-Type: application/json
x-access-token: <JWT_TOKEN>

{
  "content": "Updated message content"
}
```

**Requirements:**
- Only the message sender can update it

### 9. Delete Message
```http
DELETE /api/v1/messaging/messages/{message_id}
x-access-token: <JWT_TOKEN>
```

**Requirements:**
- Only the message sender can delete it
- Soft delete (message marked as deleted, not removed from database)

---

## 🔧 Testing with cURL

### Login Example
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Get Profile Example
```bash
curl -X GET http://localhost:8000/api/v1/profile \
  -H "x-access-token: YOUR_JWT_TOKEN"
```

### Upload Image Example
```bash
curl -X POST http://localhost:8000/api/v1/upload-profile-image \
  -H "x-access-token: YOUR_JWT_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

---

## 🚨 Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## 📊 Implementation Status

### ✅ Completed Endpoints: 109/152 (72%)

#### Authentication (15 endpoints) ✅
- Login, Register (3-step), OTP, Password management, Token operations

#### Profile (10 endpoints) ✅
- Get/Update profile, Image upload, Settings, Onboarding

#### Organizations (2 endpoints) ✅
- List organizations, Search parishes

#### Posts (17 endpoints) ✅
- Create, Read, Update, Delete posts
- Reactions (like, pray, favorite)
- Hide/unhide posts
- Get posts feed (filtered by subscribed channels only)
- Get channel/user/event posts
- Upload images/videos
- Get favorites and statistics

#### Channels (22 endpoints) ✅
- Create, Read, Update, Delete channels
- Subscribe/unsubscribe to channels
- Channel admins management
- Channel settings (notifications)
- Hide/unhide channels
- Channel alerts for subscribers
- Get subscribers, subscriptions, admins
- Channel statistics
- Upload channel images
- Search and filter channels

#### Events (16 endpoints) ✅
- Create, Read, Update, Delete events
- Event registration and cancellation
- Payment integration with Stripe
- Discount codes system
- Event alerts for attendees
- Get registrations and statistics
- Events filtered by subscribed channels
- Upload event images

#### Comments (4 endpoints) ✅
- Create, Read, Update, Delete comments
- Get comments for posts with pagination
- Only comment author can update/delete
- Author information included in responses

#### Social (7 endpoints) ✅
- Follow/unfollow users
- Get followers and following lists
- Search users by username/name
- Get suggested users to follow
- Social statistics (followers, following, posts count)
- Relationship status (is_following, is_followed_by)

#### Notifications (7 endpoints) ✅
- Get notifications (with unread filter)
- Mark notification(s) as read
- Delete notification(s)
- Get notification statistics
- Get unread count
- Supports multiple notification types (like, comment, follow, event, post, channel)

#### Messaging (9 endpoints) ✅
- Create/get direct conversations
- Get user conversations list
- Send, update, delete messages
- Get conversation messages (paginated)
- Mark conversation as read
- Unread count tracking
- Message replies support
- Soft delete for messages

### 🔄 Pending:
- Others (43 endpoints)

---

## 🎯 Features

### Implemented:
✅ JWT Authentication with access & refresh tokens
✅ Email verification with OTP
✅ SMS verification with OTP
✅ Password hashing with bcrypt
✅ Image upload to AWS S3 with optimization
✅ Email sending via AWS SES
✅ SMS sending via AWS SNS
✅ Stripe payment processing (service ready)
✅ Expo push notifications (service ready)

### Architecture:
✅ Clean layered architecture
✅ SQLAlchemy 2.0 async
✅ Pydantic validation
✅ FastAPI best practices
✅ Repository pattern
✅ Dependency injection

---

## 📝 Notes

- All services are **real implementations** - no mocks or placeholders
- AWS credentials must be configured for S3, SES, and SNS
- Stripe keys must be configured for payment features
- Database migrations are managed with Alembic
- All endpoints include proper validation and error handling

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check database connection
alembic current

# Reset database
alembic downgrade base
alembic upgrade head
```

### AWS Services
- Verify AWS credentials in `.env`
- Check S3 bucket permissions (public-read for uploads)
- Verify SES email is verified in AWS console
- Check SNS SMS spending limits

### JWT Token Issues
- Tokens expire after 30 minutes by default
- Use refresh token to get new access token
- Ensure `SECRET_KEY` is at least 32 characters

---

For more information, visit: http://localhost:8000/docs
