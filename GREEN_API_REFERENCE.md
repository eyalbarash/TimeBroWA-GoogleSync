# Green API Reference Documentation

## Overview
This document contains the key Green API endpoints and methods that we should implement for WhatsApp integration, based on the official Green API Postman collection.

## Base URL Structure
```
https://api.green-api.com/waInstance{idInstance}/{method}/{apiTokenInstance}
```

## Key API Endpoints for WhatsApp Integration

### 1. Authentication & Instance Management
- **Get Settings**: `GET /getSettings` - Get instance settings
- **Get State Instance**: `GET /getStateInstance` - Check WhatsApp connection status
- **Logout**: `POST /logout` - Logout from WhatsApp
- **Reboot**: `POST /reboot` - Restart the instance

### 2. Message Operations
- **Send Message**: `POST /sendMessage` - Send text message
- **Send File**: `POST /sendFile` - Send file (image, document, etc.)
- **Send Location**: `POST /sendLocation` - Send location
- **Send Contact**: `POST /sendContact` - Send contact card
- **Send Link**: `POST /sendLink` - Send link with preview

### 3. Chat & Contact Management
- **Get Contacts**: `GET /getContacts` - Get all contacts
- **Get Contact Info**: `GET /getContactInfo` - Get specific contact info
- **Get Chats**: `GET /getChats` - Get all chats
- **Get Chat Messages**: `GET /getChatMessages` - Get messages from specific chat
- **Get Message**: `GET /getMessage` - Get specific message details

### 4. Group Management
- **Create Group**: `POST /createGroup` - Create new group
- **Get Group Data**: `GET /getGroupData` - Get group information
- **Add Group Participant**: `POST /addGroupParticipant` - Add member to group
- **Remove Group Participant**: `POST /removeGroupParticipant` - Remove member from group
- **Leave Group**: `POST /leaveGroup` - Leave group
- **Set Group Picture**: `POST /setGroupPicture` - Set group profile picture

### 5. File Operations
- **Download File**: `GET /downloadFile` - Download file from message
- **Upload File**: `POST /uploadFile` - Upload file to server

### 6. Webhook Management
- **Set Webhook**: `POST /setWebhook` - Set webhook URL for notifications
- **Get Webhook**: `GET /getWebhook` - Get current webhook settings

## Environment Variables Required
- `idInstance`: Your Green API instance ID
- `apiTokenInstance`: Your Green API token

## Webhook Events
The system can receive webhooks for:
- Incoming messages
- Message status updates
- Group updates
- Contact updates

## Rate Limits
- Standard rate limits apply as per Green API documentation
- Consider implementing retry logic with exponential backoff

## Error Handling
Common HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized (invalid credentials)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `429`: Too Many Requests (rate limited)

## Implementation Notes for Our System

### 1. Credential Management ✅
- We've implemented secure credential storage
- Environment variables are properly managed
- Credentials are encrypted and validated

### 2. Connection Testing ✅
- We've implemented connection testing
- Proper error handling and user feedback
- Detailed troubleshooting information

### 3. Message Synchronization (To Implement)
- Use `getChats` to get all WhatsApp chats
- Use `getChatMessages` to retrieve messages
- Filter messages for calendar-relevant content
- Sync with Google Calendar

### 4. Contact Management (To Implement)
- Use `getContacts` to sync WhatsApp contacts
- Match with existing Google Contacts
- Update contact information as needed

### 5. Webhook Integration (To Implement)
- Set up webhook endpoint for real-time updates
- Process incoming message notifications
- Handle group updates and contact changes

## Next Steps
1. ✅ Implement credential management and testing
2. 🔄 Add message retrieval and filtering
3. 🔄 Add contact synchronization
4. 🔄 Add webhook support for real-time updates
5. 🔄 Add group management features
6. 🔄 Add file handling capabilities

## References
- [Green API Official Documentation](https://green-api.com/en/docs/)
- [Green API Postman Collection](https://www.postman.com/green-api-2991/green-api/overview)
- [Green API Console](https://console.green-api.com/)

## Security Considerations
- All API calls must include proper authentication
- Sensitive data should be encrypted
- Rate limiting should be implemented
- Webhook endpoints should be secured
- Regular credential rotation recommended



















