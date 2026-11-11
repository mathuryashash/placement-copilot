# Launch Guide — Collecting Honest Feedback

This guide covers how to share the tool with your batch and measure real usage
without compromising privacy.

## Before launching

1. **Informed consent:** Tell users what data is collected before they use the tool.
   Current data collected (server-side):
   - Request counts per endpoint per day (no question text, no IP stored)
   - Thumbs up/down feedback (session ID only; not linked to identity)
   - Nothing else. Student profile is never sent to the server unless eligibility is checked, and even then it is not stored.

2. **Synthetic corpus disclaimer:** Make clear the corpus contains synthetic data only until real notices are ingested.

3. **Data collection statement:** Add a one-line banner to the frontend: "This app collects anonymous usage counts and optional thumbs feedback. No personal data is stored."

## Measuring weekly active users (WAU) honestly

The server does not store user identifiers, so WAU must be approximated:

1. Count unique `session_id` values in the `feedback` table per week.
   These are random IDs generated per browser tab; they are not guaranteed unique per person.
2. Count daily `chat` endpoint hits from `usage_counters`.
3. Report both numbers with the caveat: "session_id is per-tab, not per-person."

```sql
-- Approximate WAU from feedback
SELECT date_trunc('week', created_at) AS week,
       COUNT(DISTINCT session_id) AS approx_wau
FROM feedback
GROUP BY week ORDER BY week;

-- Chat volume
SELECT date, count FROM usage_counters
WHERE endpoint = 'chat'
ORDER BY date DESC LIMIT 30;
```

## Privacy-preserving WAU alternatives

- Use a local analytics tool (Plausible) with IP anonymization and no cross-site tracking.
- Never use Google Analytics (crosses privacy line for academic users).

## Collecting feedback for improvement

The thumbs up/down table gives a signal. To get qualitative feedback:
- Add a "What was wrong?" text field that is NEVER stored server-side (handle client-side only, copy to clipboard, ask user to send via WhatsApp/email).
- Or: collect feedback forms offline.

## What to report honestly

When describing usage in a resume or interview:
- "Shared with N students in my batch; received M feedback responses."
- "X% thumbs-up rate on Y total ratings."
- **Never say "X active users" if you can't verify that number.**
