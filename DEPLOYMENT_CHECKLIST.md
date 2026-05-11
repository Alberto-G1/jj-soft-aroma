# J&J Soft Aroma Deployment Checklist

## Must do before going live
1. Rotate all credentials that were ever stored in `.env`, including database password, email app password, Africa's Talking API key, admin password, and SECRET_KEY.
2. Do not upload `.env`, `.git`, `__pycache__`, or local database files to production.
3. Set environment variables in the hosting dashboard.
4. Use `gunicorn app:app` in production, not `flask run` with debug mode.
5. Run the app once against the production database and confirm `/health` returns OK.
6. Test admin login, product add/edit/delete, category add/edit/delete, cart, checkout, contact form, and order status updates.
