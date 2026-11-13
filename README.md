[עברית](#hebrew) · [English](#english)

<div dir="rtl" id="hebrew">

# חיבור סוכן AI ל-WhatsApp (WhatsApp Cloud API): התחלה מהירה

המדריך הזה מראה איך לתת לסוכן AI מספר WhatsApp משלו באמצעות ה-**WhatsApp Cloud API** הרשמי של Meta. בסיום התהליך הסוכן יוכל:

- **לקבל** הודעות WhatsApp (טקסט, הודעות קוליות, תמונות, מסמכים) דרך webhook,
- **לשלוח** תשובות והתראות (טקסט חופשי בתוך חלון 24 השעות, ותבניות מאושרות מחוצה לו),
- **לתמלל הודעות קוליות** מקומית עם `ffmpeg` ועם `faster-whisper`.

נעשה שימוש רק ב-API הרשמי של Meta. בלי אוטומציה של WhatsApp Web ובלי לקוחות לא-רשמיים. כדי להתחיל מספיק מספר הבדיקה החינמי של Meta.

> המדריך המלא נמצא ב-[`docs/`](docs/). העמוד הזה הוא הגרסה המקוצרת לעמוד אחד.

## מה צריך

- חשבון Facebook. גם חשבון חדש לגמרי יעבוד, אבל Meta עשויה לדרוש **המתנה של בערך שעה** לפני שהיא מאפשרת ליצור business portfolio.
- טלפון עם WhatsApp לשליחה ולקבלה של הודעות בדיקה. חייב להיות מספר שונה ממספר העסק.
- כתובת **HTTPS** ציבורית ל-webhook: webhook relay מתארח, פונקציית serverless, או מנהרה (tunnel) אל המחשב שלכם.
- `curl`. להודעות קוליות צריך גם Python 3.10+, `ffmpeg` ו-`faster-whisper`.

## עשרת השלבים

1. **חשבון Facebook.** יוצרים אחד חדש, או משתמשים בקיים. מאמתים אותו באימייל.
2. **מפתח Meta.** ב-[developers.facebook.com](https://developers.facebook.com) לוחצים **Get started** ומאמתים מספר נייד ב-SMS.
3. **אפליקציה.** נכנסים ל-**My Apps → Create App**, בוחרים את תרחיש השימוש **Connect with customers through WhatsApp**, ויוצרים business portfolio או בוחרים אחד שכבר יש. אם Meta אומרת שהחשבון חדש מדי, ממתינים בערך שעה ומנסים שוב.
4. **מספר בדיקה.** פותחים **Use cases → Customize → API Setup** (מופיע גם כ-*WhatsApp → API Setup*). Meta נותנת מספר בדיקה חינמי. מעתיקים את ה-**Phone number ID** ואת ה-**WhatsApp Business Account ID** (בדפים חדשים יותר זה נקרא *Messaging account ID*).
5. **נמענים.** בשדה **To** מוסיפים את מספר ה-WhatsApp שלכם ומזינים את הקוד ש-WhatsApp שולח. מספר בדיקה יכול לשלוח הודעות עד חמישה נמענים מאומתים.
6. **הודעה ראשונה.** לוחצים **Generate access token** ואחר כך **Send message**. תבנית `hello_world` אמורה להגיע לטלפון. **עונים לה.** התשובה פותחת את חלון 24 השעות.
7. **טוקן קבוע.** ב-**Business Settings → Users → System users** מוסיפים system user. **Assign assets**: האפליקציה וחשבון ה-WhatsApp *המדויק* שמחזיק את מספר הבדיקה, שניהם עם full control. אחר כך **Generate token** עם `whatsapp_business_messaging` ועם `whatsapp_business_management`, ומגדירים שהוא לא יפוג. שומרים אותו ב-secrets manager או בקובץ עם `chmod 600`. אף פעם לא מדביקים אותו בצ'אטים, בקבצי לוג או בריפו.
8. **Webhook.** מקימים נקודת קצה HTTPS שעונה ל-GET של `hub.challenge` מ-Meta ומקבלת בקשות POST (ראו [`examples/webhook_server.py`](examples/webhook_server.py)). ב-**Configuration → Webhook** מזינים **Callback URL** ו-**Verify token** שהמצאתם, לוחצים **Verify and save**, ואז נרשמים (subscribe) לשדה `messages`.
9. **פרסום האפליקציה.** במצב פיתוח Meta מעבירה רק webhooks מסוג *Test* מהדשבורד, לא הודעות אמיתיות. מוסיפים **Privacy Policy URL** תחת **App settings → Basic** ומעבירים את האפליקציה ל-**Live** (**Publish**).
10. **בדיקה מקצה לקצה.** שולחים הודעת WhatsApp למספר הבדיקה. היא אמורה להגיע ל-webhook, והסוכן יכול לענות:

</div>

<div dir="ltr">

```bash
curl "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"<RECIPIENT_E164_DIGITS>","type":"text","text":{"body":"Hello from my agent"}}'
```

</div>

<div dir="rtl">

## הודעות קוליות בפסקה אחת

ה-webhook לא מכיל את האודיו. יש בו רק `audio.id`. קוראים ל-`GET /<MEDIA_ID>` עם הטוקן כדי לקבל `url` קצר-חיים, שתקף כחמש דקות. אחר כך עושים `GET` לאותו url **עם אותה כותרת Bearer** כדי להוריד את קובץ ה-`.ogg`/opus. ממירים עם `ffmpeg` ל-WAV מונו ב-16 kHz ומתמללים עם `faster-whisper`. [`examples/transcribe_voice_note.py`](examples/transcribe_voice_note.py) מבצע את כל זה, והטוקן לא יוצא מהתהליך.

## המדריך המלא

| מסמך | מה כלול |
| --- | --- |
| [01 – Meta setup, step by step](docs/01-meta-setup.md) | חשבון Facebook, רישום מפתחים, אפליקציה, מספר בדיקה, business portfolio, system user, טוקן קבוע, הגדרת webhook, פרסום |
| [02 – Inbound webhook](docs/02-inbound-webhook.md) | לחיצת היד לאימות, payloads, אפשרויות אירוח (relay, serverless, tunnel) עם יתרונות וחסרונות |
| [03 – Outbound messages](docs/03-outbound.md) | נקודת הקצה `/messages`, חלון 24 השעות ותבניות, שגיאות נפוצות |
| [04 – Voice notes](docs/04-voice-notes.md) | תהליך הורדת המדיה ותמלול מקומי |
| [05 – Testing & troubleshooting](docs/05-testing-troubleshooting.md) | רשימת בדיקה מקצה לקצה והבעיות שאנשים באמת נתקלים בהן |

מצייני המיקום `<PHONE_NUMBER_ID>`, `<WABA_ID>` ו-`<RECIPIENT_E164_DIGITS>` מייצגים ערכים שלכם. דוגמאות ה-API משתמשות ב-Graph API `v23.0`. כל גרסה עדכנית תעבוד, ו[יומן השינויים של Meta](https://developers.facebook.com/docs/graph-api/changelog) מציין את האחרונה.

</div>

---

<a id="english"></a>

# Connect an AI agent to WhatsApp (WhatsApp Cloud API): Quick start

This guide shows how to give an AI agent its own WhatsApp number using Meta's **official WhatsApp Cloud API**. When you're done, the agent can:

- **receive** WhatsApp messages (text, voice notes, images, documents) through a webhook,
- **send** replies and notifications (free text inside the 24-hour window, approved templates outside it),
- **transcribe voice notes** locally with `ffmpeg` and `faster-whisper`.

It uses only Meta's official API. No WhatsApp Web automation or unofficial clients are involved. To get started you only need Meta's free test number.

> The full guide lives in [`docs/`](docs/). This page is the one-page version.

## What you need

- A Facebook account. A brand-new account works, but Meta may make you **wait about an hour** before it lets you create a business portfolio.
- A phone with WhatsApp to send and receive test messages. It must be a different number from the business number.
- A public **HTTPS** URL for the webhook: a hosted webhook relay, a serverless function, or a tunnel to your machine.
- `curl`. For voice notes you also need Python 3.10+, `ffmpeg` and `faster-whisper`.

## The 10 steps

1. **Facebook account.** Create one, or use an existing one. Verify it by email.
2. **Meta developer.** At [developers.facebook.com](https://developers.facebook.com), click **Get started** and verify a mobile number by SMS.
3. **App.** Go to **My Apps → Create App**, pick the **Connect with customers through WhatsApp** use case, and create a business portfolio or pick one you already have. If Meta says the account is too new, wait about an hour and try again.
4. **Test number.** Open **Use cases → Customize → API Setup** (also labeled *WhatsApp → API Setup*). Meta gives you a free test number. Copy the **Phone number ID** and the **WhatsApp Business Account ID** (newer pages call it the *Messaging account ID*).
5. **Recipients.** In the **To** field, add your own WhatsApp number and enter the code WhatsApp sends you. A test number can message up to 5 verified recipients.
6. **First message.** Click **Generate access token** and then **Send message**. The `hello_world` template should arrive on your phone. **Reply to it.** Your reply opens the 24-hour window.
7. **Permanent token.** In **Business Settings → Users → System users**, add a system user. **Assign assets**: the app and the *exact* WhatsApp account that holds your test number, both with full control. Then **Generate token** with `whatsapp_business_messaging` and `whatsapp_business_management`, and set it to never expire. Store it in a secrets manager or a `chmod 600` file. Never paste it into chats, logs or the repo.
8. **Webhook.** Stand up an HTTPS endpoint that answers Meta's `hub.challenge` GET and accepts POSTs (see [`examples/webhook_server.py`](examples/webhook_server.py)). In **Configuration → Webhook**, enter the **Callback URL** and a **Verify token** you made up, click **Verify and save**, and then **subscribe to the `messages` field**.
9. **Publish the app.** In development mode Meta delivers only the dashboard's *Test* webhooks, not real messages. Add a **Privacy Policy URL** under **App settings → Basic** and switch the app to **Live** (**Publish**).
10. **Test end to end.** Send a WhatsApp message to the test number. It should reach your webhook, and your agent can reply:

```bash
curl "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"<RECIPIENT_E164_DIGITS>","type":"text","text":{"body":"Hello from my agent"}}'
```

## Voice notes in one paragraph

The webhook doesn't contain the audio. It only contains `audio.id`. Call `GET /<MEDIA_ID>` with your token to get a short-lived `url`, which is valid for about 5 minutes. Then `GET` that url **with the same Bearer header** to download the `.ogg`/opus file. Convert it with `ffmpeg` to 16 kHz mono WAV and transcribe it with `faster-whisper`. [`examples/transcribe_voice_note.py`](examples/transcribe_voice_note.py) does all of this, and the token never leaves the process.

## Full guide

| Doc | Covers |
| --- | --- |
| [01 – Meta setup, step by step](docs/01-meta-setup.md) | Facebook account, developer registration, app, test number, business portfolio, system user, permanent token, webhook config, publishing |
| [02 – Inbound webhook](docs/02-inbound-webhook.md) | Verification handshake, payloads, hosting options (relay, serverless, tunnel) with pros and cons |
| [03 – Outbound messages](docs/03-outbound.md) | `/messages` endpoint, the 24-hour window and templates, common errors |
| [04 – Voice notes](docs/04-voice-notes.md) | Media download flow and local transcription |
| [05 – Testing & troubleshooting](docs/05-testing-troubleshooting.md) | End-to-end checklist and the problems people actually hit |

Placeholders like `<PHONE_NUMBER_ID>`, `<WABA_ID>` and `<RECIPIENT_E164_DIGITS>` stand for your own values. API examples use Graph API `v23.0`. Any current version works, and [Meta's changelog](https://developers.facebook.com/docs/graph-api/changelog) lists the latest one.
