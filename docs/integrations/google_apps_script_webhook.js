/**
 * CRBCL Public Intake — Google Forms Apps Script Webhook Integration
 * 
 * Instructions for Deployment:
 * 1. Open your target Google Form in Google Forms.
 * 2. Click the three dots menu (⋮) -> Script editor.
 * 3. Paste this script into Code.gs.
 * 4. Go to Project Settings (gear icon) -> Script Properties:
 *    - Add property: CRBCL_WEBHOOK_SECRET
 *    - Value: [Your Secret Token configured in CRBCL environment]
 *    - Add property: CRBCL_WEBHOOK_URL
 *    - Value: https://api.crbcl.ca/api/v1/front-desk/ingest/google-form (or your staging endpoint)
 * 5. Set up the trigger:
 *    - In Apps Script, click Triggers (alarm clock icon on the left).
 *    - Click "+ Add Trigger".
 *    - Function to run: onFormSubmit
 *    - Event source: From form
 *    - Event type: On form submit
 *    - Failure notification settings: Notify me immediately
 *    - Save.
 */

function onFormSubmit(e) {
  var scriptProperties = PropertiesService.getScriptProperties();
  var webhookUrl = scriptProperties.getProperty('CRBCL_WEBHOOK_URL') || 'https://api.crbcl.ca/api/v1/front-desk/ingest/google-form';
  var webhookSecret = scriptProperties.getProperty('CRBCL_WEBHOOK_SECRET');

  if (!webhookSecret) {
    console.error('CRBCL Webhook Error: Missing CRBCL_WEBHOOK_SECRET script property. Ingestion aborted.');
    return;
  }

  // Obtain form response details
  var formResponse = e ? e.response : null;
  if (!formResponse) {
    console.error('CRBCL Webhook Error: No form response object in event.');
    return;
  }

  var responseId = formResponse.getId(); // Google Form unique response ID (Idempotency key)
  var timestamp = formResponse.getTimestamp() ? formResponse.getTimestamp().toISOString() : new Date().toISOString();

  // Extract question answers
  var itemResponses = formResponse.getItemResponses();
  var responsesMap = {
    form_title: formResponse.getForm ? formResponse.getForm().getTitle() : 'Public Intake Form',
    submitted_at: timestamp
  };

  var submitterName = null;
  var submitterEmail = null;
  var submitterPhone = null;
  var inquirySummary = null;
  var inquiryDetails = null;

  for (var i = 0; i < itemResponses.length; i++) {
    var item = itemResponses[i];
    var title = item.getItem().getTitle();
    var responseVal = item.getResponse();
    responsesMap[title] = responseVal;

    // Optional field classification for common question labels
    var cleanTitle = title.toLowerCase().trim();
    if (cleanTitle.indexOf('name') !== -1 && !submitterName) {
      submitterName = String(responseVal);
    } else if (cleanTitle.indexOf('email') !== -1 && !submitterEmail) {
      submitterEmail = String(responseVal);
    } else if ((cleanTitle.indexOf('phone') !== -1 || cleanTitle.indexOf('contact') !== -1) && !submitterPhone) {
      submitterPhone = String(responseVal);
    } else if ((cleanTitle.indexOf('concern') !== -1 || cleanTitle.indexOf('summary') !== -1 || cleanTitle.indexOf('reason') !== -1) && !inquirySummary) {
      inquirySummary = String(responseVal);
    } else if ((cleanTitle.indexOf('detail') !== -1 || cleanTitle.indexOf('description') !== -1) && !inquiryDetails) {
      inquiryDetails = String(responseVal);
    }
  }

  // Build JSON payload
  var payload = {
    response_id: responseId, // Critical: Enforces idempotency on CRBCL backend
    source: 'google_form',
    submitter_name: submitterName,
    submitter_email: submitterEmail,
    submitter_phone: submitterPhone,
    summary: inquirySummary || ('Public submission from ' + (submitterName || 'Anonymous')),
    details: inquiryDetails,
    responses: responsesMap
  };

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'X-CRBCL-Webhook-Secret': webhookSecret
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  // Retry with exponential backoff
  var maxRetries = 3;
  var attempt = 0;
  var delivered = false;

  while (attempt < maxRetries && !delivered) {
    attempt++;
    try {
      var response = UrlFetchApp.fetch(webhookUrl, options);
      var statusCode = response.getResponseCode();

      if (statusCode === 200 || statusCode === 201) {
        console.log('CRBCL Webhook Delivered: Response ID ' + responseId + ' (HTTP ' + statusCode + ', attempt ' + attempt + ')');
        delivered = true;
      } else {
        console.warn('CRBCL Webhook Non-200 Response: HTTP ' + statusCode + ' on attempt ' + attempt + '. Body: ' + response.getContentText().slice(0, 200));
        if (attempt < maxRetries) {
          Utilities.sleep(Math.pow(2, attempt) * 1000); // Backoff 2s, 4s
        }
      }
    } catch (err) {
      console.error('CRBCL Webhook Network Error on attempt ' + attempt + ': ' + err.toString());
      if (attempt < maxRetries) {
        Utilities.sleep(Math.pow(2, attempt) * 1000);
      }
    }
  }

  if (!delivered) {
    console.error('CRBCL Webhook Delivery FAILED after ' + maxRetries + ' attempts for Response ID ' + responseId);
  }
}
