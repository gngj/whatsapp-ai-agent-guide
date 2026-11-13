# 01 – Meta setup, step by step

This chapter goes from "no Facebook account" to "a permanent token and a verified webhook". Meta renames menu items fairly often, so where a name has changed recently, both names are given. Use the one your dashboard shows.

> **Terminology.** Meta's newer pages say **Messaging account** where older pages and the API say **WhatsApp Business Account (WABA)**. They are the same thing. A **business portfolio** is the newer name for a **Business Manager** account, and you manage it in **Meta Business Suite / Business Settings**.

Keep a scratch note (not in the repo) with the values you'll collect:

| Value | Where you get it | Secret? |
| --- | --- | --- |
| `<APP_ID>` | App Dashboard header | no |
| `<WABA_ID>` | API Setup panel | no |
| `<PHONE_NUMBER_ID>` | API Setup panel (under the *From* number) | no |
| `<VERIFY_TOKEN>` | You make it up (a long random string) | **yes**, keep it private |
| `<APP_SECRET>` | App settings → Basic → App secret → Show | **yes** |
| `<SYSTEM_USER_TOKEN>` | Business Settings → System users → Generate token | **yes** |

The phone number ID is **not** the phone number. It's a long numeric ID, and it's what every API call uses.

---

## Step 1: Create a Facebook account (or use an existing one)

Every Meta developer account sits on top of a Facebook account. A *managed Meta account* also works if your organization has one.

1. Go to [facebook.com](https://www.facebook.com) → **Create new account**. Fill in name, email (or mobile), password, date of birth and gender.
2. Enter the confirmation code Meta sends to your email or phone.
3. Optional: if the account exists only for developer access, lock it down. In **Settings & privacy → Privacy**, turn off search-engine linking and lookup by email/phone, and lock the profile where your region allows it. The account does **not** need friends, posts or any social activity. When Meta says "active account", it means verified and not restricted.

> **New accounts have to wait.** A Facebook account that is only minutes old can usually register as a developer and start creating an app. Creating a **business portfolio** often fails with a message that the account is too new, asking you to try again in about an hour (sometimes several hours). This is a deliberate Meta restriction, not a mistake you made. Wait and retry, or use an older account you already have.

## Step 2: Register as a Meta developer

1. Open [developers.facebook.com](https://developers.facebook.com) and log in with **Continue with Facebook**.
2. Click **Get started** (or **My Apps**, which redirects you to registration if needed).
3. Accept the Platform Terms and Developer Policies.
4. **Verify your account.** Meta asks for a mobile number and sends an SMS code. Use a real phone you control. This can be the same phone you'll test WhatsApp with.
5. Confirm your contact email and pick your role (for example *Developer*). Registration is done when you land on the **Apps** page.

## Step 3: Create an app with the WhatsApp use case

1. **My Apps → Create App**.
2. Enter an **app name** and a contact email. Avoid names containing "WhatsApp", "Facebook", "Meta" or other trademarks, because Meta rejects them.
3. Choose the use case **Connect with customers through WhatsApp**. On older flows, choose app type **Business**, then add the **WhatsApp** product from the product list.
4. **Business portfolio.** Pick an existing one or create a new one.
   - If it says the account is too new, see Step 1 and come back in about an hour.
   - Very short or generic names (a single common word) are often rejected. A more specific name works better, such as "<Your Name> Notifications" or "<Project> Alerts". Non-Latin names are allowed, but if one is rejected, try a transliteration.
5. Review the publishing requirements (usually none yet) and click **Create app**.

You are now in **Use cases → Customize → Connect on WhatsApp → Quickstart** (older dashboards show **WhatsApp → Getting started**).

## Step 4: The free test number

1. Click **Start using the API**. This opens **API Setup**.
2. If asked, accept the **WhatsApp Business Platform / Cloud API terms**.
3. Connect a Messaging account (WABA). If you just created a portfolio, Meta usually creates a **test WhatsApp Business Account** and a **test phone number** (a US number beginning with +1 555) for you.
4. Copy the **Phone number ID** and the **WhatsApp Business Account ID** shown in the panel. Save them as `<PHONE_NUMBER_ID>` and `<WABA_ID>`.

About the test number:

- It's free and doesn't need a payment method.
- It can message **only verified recipients, up to 5**.
- It can't message itself, so the business number and your test phone must be different numbers.
- Meta doesn't document an expiry for it. It stays as long as the app and portfolio exist. What expires quickly is the *temporary* token (Step 6).

## Step 5: Add recipient numbers

1. In **API Setup**, open the **To** dropdown → **Manage phone number list** → **Add phone number**.
2. Enter your WhatsApp number in international format.
3. WhatsApp sends a short verification code to that phone. Enter it in the dialog.
4. Repeat for up to 5 testers.

## Step 6: Send your first message with the temporary token

1. Click **Generate access token** in API Setup. Meta asks you to continue as yourself and grant WhatsApp messaging/management permissions to your app. Approve.
2. With **From** set to the test number and **To** set to your verified number, click **Send message**. The pre-approved `hello_world` template arrives on your phone within about a minute.
3. **Reply to it from your phone** (anything, like "hi"). This opens the **24-hour customer service window**, so you can now send free-form text (see [03 – Outbound](03-outbound.md)).

The temporary token expires in **less than 24 hours**. Use it only for this first test.

## Step 7: Business Settings / Meta Business Suite

Open **[business.facebook.com/settings](https://business.facebook.com/settings)** (also reachable from Meta Business Suite → ⚙ **Settings**, or **Business Settings**), and make sure the portfolio selector at the top shows the portfolio your app belongs to.

Under **Accounts** you should see:

- **Apps**: your app.
- **WhatsApp accounts**: often **two**: one created with your portfolio and a separate **test** account that actually holds the test number. Note which one has the `<WABA_ID>` from Step 4. You'll need it in Step 9.

## Step 8: Create a system user

A system user is a non-human identity owned by the business portfolio. Its token doesn't expire and isn't tied to your personal login.

1. **Users → System users → Add**.
2. Meta may first ask you to accept the **Non-discrimination policy** on behalf of system users. Accept to continue.
3. Name it. Names containing "WhatsApp" (and other trademarks) are rejected. Use something like `my-agent-bot`.
4. Role: **Admin** is simplest. **Employee** works too if you assign assets explicitly (next step).

## Step 9: Assign the app and the WhatsApp account to the system user

1. Select the system user → **Assign assets** (or **Add assets**).
2. **Apps**: select your app and toggle **Manage app** (full control).
3. **WhatsApp accounts**: select the account **with the same ID as `<WABA_ID>`**, not the other one, and give it **Full control / Manage WhatsApp Business accounts**.
   - Partial-access options on a WhatsApp account may cover only templates or analytics. If sending later fails with a permission error, come back here and grant full control.
4. Click **Assign assets** and check that both appear under the system user's assigned assets. Reload the page if the list looks inconsistent.

## Step 10: Generate a permanent token

1. On the system user, click **Generate token** (or **Generate new token**).
2. Select your app.
3. Expiration: **Never**.
4. Permissions: tick **`whatsapp_business_messaging`** and **`whatsapp_business_management`**. Meta's get-started guide also adds `business_management`. Add it if you plan to manage portfolio assets by API.
5. Click **Generate** and **copy the token right away**. Meta shows it once and you can't view it again later. If you lose it, generate a new one.
6. Store it in a secrets manager or a file only your service can read (`chmod 600`). Keep it out of chats, logs, screenshots and git.

Check it (prints only the app/expiry/scopes, not the token):

```bash
curl -s "https://graph.facebook.com/v23.0/debug_token?input_token=$WHATSAPP_TOKEN" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" | jq '.data | {app_id, type, expires_at, is_valid, scopes}'
```

You want `is_valid: true`, `type: "SYSTEM_USER"`, `expires_at: 0` (never), and both WhatsApp scopes.

Then send `hello_world` with the new token to confirm it's assigned to the right WABA:

```bash
curl -s "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"<RECIPIENT_E164_DIGITS>","type":"template",
       "template":{"name":"hello_world","language":{"code":"en_US"}}}'
```

## Step 11: Configure the webhook

You need a public HTTPS endpoint first. See [02 – Inbound webhook](02-inbound-webhook.md). Then:

1. App Dashboard → **Use cases → Customize → Configuration** (older dashboards: **WhatsApp → Configuration**) → **Webhook → Edit**.
2. **Callback URL**: your HTTPS endpoint. **Verify token**: the random string your endpoint expects.
3. Click **Verify and save**. Meta immediately sends `GET ?hub.mode=subscribe&hub.verify_token=…&hub.challenge=…`. If your endpoint returns the challenge with HTTP 200, the dialog saves.
4. Under **Webhook fields**, click **Subscribe** next to **`messages`**. **People miss this step more than any other.** Without it, Meta verifies the URL and then sends nothing. The `messages` field carries inbound messages *and* delivery/read statuses.
5. Click **Test** next to `messages` to send a sample payload. A sample arriving at your endpoint proves the path works. The sample uses fake numbers and the text "this is a text message".
6. Optional: copy **App settings → Basic → App secret** into your endpoint so it can verify the `X-Hub-Signature-256` header on POSTs.

## Step 12: Publish the app (Live mode)

While the app is **Unpublished / in development mode**, Meta's webhook panel warns that **only test webhooks sent from the App Dashboard are delivered**. Real messages from phones are not delivered, even from admins, developers or testers. If the **Test** button works but your phone's messages never arrive, this is why.

To publish:

1. **App settings → Basic**: fill in **Privacy Policy URL** (required), and ideally also Terms of Service URL, app icon, category and a data-deletion instructions URL. The privacy policy has to be a real public page that describes what your app does with message data. A hosted page or a simple static page is fine.
2. Open the **Publish** page (left menu or **Go live**). Meta lists anything still missing. Usually the privacy policy URL is the only blocker.
3. Click **Publish**. The app switches to **Live**.

Notes:

- For an app that only uses **your own** portfolio's WhatsApp account, you generally **don't** need App Review or Advanced Access, even if the permissions page shows "Add to App Review". Those are for Tech Providers serving other businesses.
- **Business verification** is optional for the test number. You'll need it to raise messaging limits or to add your own real business number with a display name.
- To move from the test number to a real number later: **API Setup → Add phone number**, verify it by SMS or voice, set a display name (Meta reviews it), and add a payment method. A number that is currently registered on the WhatsApp consumer or Business app must be removed from it first, unless you use Meta's coexistence onboarding.

Next: [02 – Inbound webhook](02-inbound-webhook.md).
