# CellophoneMail Multi-User SaaS Data Flow

## Actors
- **End User** (Gmail user who wants protection)
- **Email Sender** (anyone sending emails to the user)
- **Postmark** (email service provider)
- **CellophoneMail App** (your Litestar application)
- **Four Horsemen Analyzer** (content filtering)

## Triggers & Data Flow

```
1. USER REGISTRATION
   End User → CellophoneMail App → Database
   
2. EMAIL RECEPTION  
   Email Sender → Postmark → CellophoneMail App → Four Horsemen → End User

3. SHIELD ADDRESS ASSIGNMENT
   CellophoneMail App → Database → End User (via email/UI)
```

## ASCII Diagram

```
                    CELLOPHANEMAIL SAAS ARCHITECTURE
                              
1. REGISTRATION FLOW
   
   End User            CellophoneMail App         Database
   (Gmail)                  (Litestar)            (PostgreSQL)
      |                         |                      |
      |--- POST /register ----->|                      |
      |    {email, username}     |                      |
      |                         |--- INSERT User ----->|
      |                         |    {real_email,      |
      |                         |     shield_prefix}   |
      |<--- 200 OK -------------|                      |
      |    {shield_address:     |<--- User created ----|
      |     "john@cellophane    |                      |
      |     mail.com"}          |                      |


2. EMAIL PROCESSING FLOW

Internet Sender      Postmark Service      CellophoneMail App       End User
     |                     |                      |                  |
     |                     |                      |                  |
     |-- Email to -------->|                      |                  |
     |   john@cellphone    |                      |                  |
     |   mail.com          |                      |                  |
     |                     |                      |                  |
     |              [MX Records Route]            |                  |
     |                     |                      |                  |
     |                     |-- Webhook POST ---->|                  |
     |                     |   {To: "john@cell   |                  |
     |                     |    phonemail.com",  |                  |
     |                     |    From: "sender",  |                  |
     |                     |    Subject: "...",  |                  |
     |                     |    TextBody: "..."}|                  |
     |                     |                     |                  |
     |                     |              [Parse "john" prefix]     |
     |                     |                     |                  |
     |                     |              [Database lookup]        |
     |                     |                     |                  |
     |                     |              [Four Horsemen          |
     |                     |               Analysis]               |
     |                     |                     |                  |
     |                     |              [IF SAFE]               |
     |                     |<-- Postmark API ----|                  |
     |                     |    Send filtered    |                  |
     |                     |    email            |                  |
     |                     |                     |                  |
     |                     |-- Email delivery -->|---------------->|
     |                     |   to real Gmail     |       Gmail      |
     |                     |                     |       Inbox      |

```

## Key Data Flows

**Registration:**
```
User Input → Validation → Shield Assignment → Database Storage → Confirmation
```

**Email Processing:**
```
Inbound Email → Postmark Webhook → User Lookup → Content Analysis → 
Routing Decision → Outbound Delivery → User Notification
```

**Database Queries:**
```
Shield Address "john@cellophonemail.com" → 
Parse prefix "john" → 
SELECT real_email FROM users WHERE shield_prefix = 'john' →
Forward to real_email
```

## Important Note

The **CellophoneMail app** refers to your **Litestar web application**, NOT the local SMTP server. With Postmark, no SMTP server is needed - everything works through HTTP webhooks and API calls.

## Architecture Benefits

This architecture allows unlimited users with their own shield addresses, all processed through a single Postmark webhook endpoint, eliminating the need for any SMTP server infrastructure.