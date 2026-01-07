---
date: 2026-01-07T00:00:00+0000
researcher: user
topic: "Android SMS App Development Feasibility"
tags: [prd, android, sms, permissions, default-handler, google-play]
status: complete
last_updated: 2026-01-07
---

# Android SMS App Development is Fully Supported

**Building an SMS filtering app that reads message content is technically feasible and officially supported on Android.** Third-party apps can become the default SMS handler through user selection, gaining full access to read and write SMS content including message bodies. This capability has been a core Android feature since API Level 19 (Android 4.4 KitKat, released October 2013) with well-documented APIs at developer.android.com.

The Android platform explicitly enables this through the android.provider.Telephony API, which provides structured access to SMS data including the `BODY` column containing message text. Default SMS apps receive dangerous permissions (READ_SMS, SEND_SMS, RECEIVE_SMS) automatically when users select them through system settings, and the framework delivers incoming messages directly via SMS_DELIVER_ACTION broadcasts. This architecture was designed to support the exact use case you're planning: third-party messaging apps that need to process SMS content.

## User selection gives third-party apps default status

Android's default handler system allows users to explicitly choose their preferred SMS application through system settings or in-app prompts. When your app requests default status, the system displays a standard dialog asking the user to change their default SMS handler. The technical implementation is straightforward - your app invokes `Telephony.Sms.Intents.ACTION_CHANGE_DEFAULT` with your package name, and Android handles the user interaction.

The official documentation at developer.android.com/guide/topics/permissions/default-handlers states: "Android lets users set default handlers for several core use cases, such as placing phone calls, sending SMS messages, and providing assistive technology capabilities." Critically, apps must request to become the default SMS handler **before** requesting READ_SMS permission, ensuring users understand why the app needs access. Once selected as default, your app automatically receives the necessary permissions and exclusive delivery of incoming messages.

On API Level 29 (Android 10) and above, Android introduced RoleManager as the preferred method with `RoleManager.ROLE_SMS`, though the older ACTION_CHANGE_DEFAULT intent remains functional. You can verify your app's status programmatically using `Telephony.Sms.getDefaultSmsPackage(context)` and comparing it to your package name.

## Default SMS apps have comprehensive read access to message content

**The SMS Provider explicitly includes message body content that default apps can read.** According to developer.android.com/reference/android/provider/Telephony.TextBasedSmsColumns, the SMS database contains a `BODY` column defined as "The body of the message" with type TEXT. This column stores the actual message content, and default SMS apps have full read and write access to query this data.

The READ_SMS permission (android.permission.READ_SMS) is documented at developer.android.com/reference/android/Manifest.permission as: "Allows an application to read SMS messages. Protection level: dangerous." This permission grants access to the entire SMS Provider, including the inbox, sent messages, drafts, and conversations. Apps can query `content://sms/inbox` with columns like `_id`, `address`, `body`, and `date` to retrieve all messages with their complete content.

Default SMS apps receive **exclusive delivery** of incoming messages through SMS_DELIVER_ACTION broadcasts, giving them first access to new messages before any other app. Non-default apps can only receive the non-abortable SMS_RECEIVED_ACTION broadcast for special purposes like reading verification codes, but cannot intercept or modify the message delivery flow. This exclusive access makes default SMS apps ideal for filtering applications, as they can process every incoming message and decide how to handle it before notifying the user.

## The android.provider.Telephony API provides structured SMS access

The primary API for SMS operations is **android.provider.Telephony**, introduced in API Level 19. This class is documented at developer.android.com/reference/android/provider/Telephony and serves as the main provider for phone operation data, specifically SMS and MMS messages. The API includes several nested classes that organize SMS data into logical categories: `Telephony.Sms.Inbox` for received messages, `Telephony.Sms.Sent` for sent messages, `Telephony.Sms.Conversations` for message threads, and similar structures.

The **android.telephony.SmsManager** class (developer.android.com/reference/android/telephony/SmsManager) handles sending operations with methods like `sendTextMessage()` for single messages and `sendMultipartTextMessage()` for longer content that exceeds the 160-character limit. On API Level 31 and above, you obtain the SmsManager instance via `Context.getSystemService(SmsManager.class)` rather than the deprecated `getDefault()` method. The SmsManager also provides `divideMessage()` to split long text into appropriate segments before sending.

For receiving messages, **Telephony.Sms.Intents** (developer.android.com/reference/android/provider/Telephony.Sms.Intents) defines the broadcast actions your app must handle. The most important is `SMS_DELIVER_ACTION` ("android.provider.Telephony.SMS_DELIVER"), which delivers incoming SMS exclusively to the default app. Your broadcast receiver must specify `android:permission="android.permission.BROADCAST_SMS"` to receive these protected broadcasts. Similarly, `WAP_PUSH_DELIVER_ACTION` handles incoming MMS with MIME type "application/vnd.wap.mms-message".

## Apps must implement four mandatory components to qualify

Eligibility as a default SMS app requires declaring all four of these components in your AndroidManifest.xml:

**First, a broadcast receiver for SMS delivery** that handles `SMS_DELIVER_ACTION` with the `BROADCAST_SMS` permission. This component receives incoming text messages directly from the system before any other app, giving your filtering logic first access to message content.

**Second, a broadcast receiver for MMS delivery** handling `WAP_PUSH_DELIVER_ACTION` with MIME type "application/vnd.wap.mms-message" and the `BROADCAST_WAP_PUSH` permission. Even if your app primarily focuses on SMS, Android requires MMS support for default status.

**Third, an activity responding to ACTION_SENDTO** intents with sms:, smsto:, mms:, and mmsto: URI schemes. This allows other apps to compose messages through your app when users click message links or share content via SMS, making your app a complete messaging solution.

**Fourth, a service for quick responses** handling `ACTION_RESPOND_VIA_MESSAGE` with the `SEND_RESPOND_VIA_MESSAGE` permission. This enables users to decline incoming phone calls with a quick text message, a standard Android feature that all default SMS apps must support.

If any of these four components is missing from your manifest, Android will not offer your app as an eligible default SMS handler. The complete manifest structure and code examples are detailed in the official guide at developer.android.com/guide/topics/permissions/default-handlers.

## Minimum Android version is API Level 19 (KitKat)

The default SMS app feature was introduced in **Android 4.4 KitKat (API Level 19)** in October 2013. Before this version, the SMS APIs were hidden and multiple apps could write to the SMS Provider simultaneously, causing data inconsistency. The KitKat update made these APIs public and established the single default app model to ensure data integrity.

Your app's `minSdkVersion` must be 19 or higher to use the Telephony APIs. This represents over 99% of active Android devices as of 2025, so market reach is not a concern. The official announcement explaining this architectural change is available at android-developers.googleblog.com/2013/10/getting-your-sms-apps-ready-for-kitkat.html, which describes how "Android 4.4 makes the existing APIs public and adds the concept of a default SMS app, which the user can select in system settings."

Subsequent Android versions refined the API. **API Level 26 (Android 8.0)** added `createAppSpecificSmsToken()` for temporary SMS access without becoming the default app. **API Level 29 (Android 10)** introduced the RoleManager approach for requesting default status, though the original intent-based method still works. **API Level 31 (Android 12)** modernized SmsManager instantiation to use the standard system service pattern rather than static methods. These changes are evolutionary rather than breaking, maintaining backward compatibility while improving the API design.

Developers should declare the telephony feature in their manifest: `<uses-feature android:name="android.hardware.telephony" android:required="true" />` or check at runtime using `PackageManager.hasSystemFeature(PackageManager.FEATURE_TELEPHONY_MESSAGING)` for devices like tablets that may lack cellular capabilities.

## Write access is exclusive but read access is broadly available

**Only the default SMS app can write to the SMS Provider** on API Level 19 and above. This restriction prevents data corruption from multiple apps modifying the message database simultaneously. Default apps can mark messages read/unread, delete conversations, save drafts, and write sent messages to the provider. Non-default apps attempting to write will fail silently - the operation is ignored without throwing an exception.

However, **non-default apps retain read access** with READ_SMS permission. This is important for apps that need to read verification codes, backup SMS data, or provide analytics without becoming the full messaging interface. These apps can query the SMS Provider and receive the SMS_RECEIVED_ACTION broadcast, though they cannot intercept message delivery or modify the data.

The system automatically handles sent messages from non-default apps by writing them to the Provider on the app's behalf, ensuring the message history remains complete even when users send SMS through specialized apps like ride-sharing services. This automatic write-back applies only to SMS; MMS sent by non-default apps is not stored in the Provider, creating an asymmetry developers should understand.

For backup and restore scenarios, apps can temporarily request default status, perform their write operations, then restore the previous default app. The pattern involves: save `Telephony.Sms.getDefaultSmsPackage()`, request default status, restore messages, then use ACTION_CHANGE_DEFAULT to restore the original app. This ensures data integrity while allowing legitimate backup tools to function.

## Google Play enforces default handler requirements for SMS permissions

If you distribute on Google Play and want to access SMS content, **your app must be the default SMS handler** unless it qualifies for specific exceptions. Google's SMS and Call Log permissions policy (support.google.com/googleplay/android-developer/answer/10208820) restricts these dangerous permissions to apps that are default handlers or fit narrow exception cases like backup services, companion device managers, or carrier-provided account management tools.

The policy requires that you perform the core functionality your app claims to provide. For an SMS filtering app, this means actually sending and receiving messages as a complete messaging solution, not just reading messages in the background. You must provide a privacy policy explaining how you handle SMS data, and your Play Store description must clearly explain the SMS functionality.

Critically, Google requires that apps **request to become the default handler before requesting associated permissions** like READ_SMS. This ensures users understand the context when granting permission. Apps that request READ_SMS without first offering to become the default handler may be rejected or removed from the Play Store. You must also submit a Permissions Declaration Form explaining your use of sensitive permissions, and Google reviews apps periodically to ensure ongoing compliance.

This policy effectively means SMS filtering apps on Google Play must be full-featured messaging applications, not background-only filters. Your app needs a UI for reading, composing, and managing conversations to meet Google's requirements, though the filtering functionality can remain your core value proposition.

## Key permissions required for SMS app functionality

Default SMS apps need six primary permissions, all with "dangerous" protection level requiring runtime user consent:

**READ_SMS** (android.permission.READ_SMS) allows reading the SMS Provider database including message bodies, sender addresses, timestamps, and metadata. **SEND_SMS** (android.permission.SEND_SMS) enables sending text messages via SmsManager methods. **RECEIVE_SMS** (android.permission.RECEIVE_SMS) allows receiving the broadcast when new SMS messages arrive. **RECEIVE_MMS** (android.permission.RECEIVE_MMS) permits monitoring incoming MMS messages. **WRITE_SMS** (android.permission.WRITE_SMS) grants write access to the SMS Provider, functional only when your app is the default handler. **RECEIVE_WAP_PUSH** (android.permission.RECEIVE_WAP_PUSH) handles WAP push messages used for MMS delivery.

When users select your app as their default SMS handler, Android automatically grants these permissions if they're declared in your manifest. This automatic grant simplifies the user experience - they don't face six separate permission dialogs. However, you must still declare the permissions in your manifest and handle the runtime permission system properly on API Level 23+.

Additionally, your broadcast receivers and services must declare required permissions as attributes: `android:permission="android.permission.BROADCAST_SMS"` on your SMS receiver, `android:permission="android.permission.BROADCAST_WAP_PUSH"` on your MMS receiver, and `android:permission="android.permission.SEND_RESPOND_VIA_MESSAGE"` on your quick reply service. These permissions protect the components from unauthorized access by other apps.

## Official documentation confirms complete feasibility

The research confirms with official Android documentation that building an SMS filtering app is fully supported. The key sources are:

**Primary implementation guide:** developer.android.com/guide/topics/permissions/default-handlers - comprehensive explanation of default SMS app concepts, user selection process, required components, and Google Play requirements.

**Core API reference:** developer.android.com/reference/android/provider/Telephony - complete documentation of the Telephony provider including Sms, Mms, Threads classes, and intent constants.

**SMS column definitions:** developer.android.com/reference/android/provider/Telephony.TextBasedSmsColumns - explicit documentation of the BODY column and other message fields you can query.

**SmsManager operations:** developer.android.com/reference/android/telephony/SmsManager - methods for sending messages and managing multi-part messages.

**Permission specifications:** developer.android.com/reference/android/Manifest.permission - definitions of READ_SMS, SEND_SMS, and related dangerous permissions.

**Historical context:** android-developers.googleblog.com/2013/10/getting-your-sms-apps-ready-for-kitkat.html - official blog post explaining the architectural changes in Android 4.4 that introduced default SMS apps.

**Play Store policy:** support.google.com/googleplay/android-developer/answer/10208820 - requirements for using SMS permissions on Google Play, including default handler obligations.

These sources collectively confirm that third-party apps can become default SMS handlers, read complete message content including bodies, send messages, and filter incoming SMS - exactly the capabilities needed for your filtering application. The Android platform was explicitly designed to support this use case while protecting user privacy through the default handler model and permission system.
