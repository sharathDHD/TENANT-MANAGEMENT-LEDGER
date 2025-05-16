```markdown
# Tenant Ledger - Local Management System

![App Screenshot](screenshot.png) <!-- Add a screenshot later -->

A **local-first**, **no-authentication** tenant management system for landlords and property owners. Track tenants, rent payments, security deposits, and documents - all stored securely on your device.

## Features

✅ **Tenant Management**  
- Store tenant details (name, contact, move-in date)  
- Attach ID proofs and photos  
- Auto-calculate 2 months rent as security deposit  
- Activate/deactivate tenants  

💰 **Rent Tracking**  
- Record rent payments with payment method  
- Add late fees automatically  
- View payment history  
- Generate rent receipts  

📄 **Document Management**  
- Store lease agreements and ID proofs  
- Track document expiry dates  
- Attach files (PDFs, images)  

🔒 **Local & Secure**  
- No cloud sync - data stays on your device  
- No authentication required  
- Encrypted file storage  
- Regular backups  

## Installation

1. **Prerequisites**:
   - Python 3.8+
   - Pillow library (for image handling)

2. **Install dependencies**:
   ```bash
   pip install pillow
   ```

3. **Run the application**:
   ```bash
   python tenant_ledger.py
   ```

The app will automatically create:
- `tenant_ledger.db` (SQLite database)
- `tenant_photos/` (for ID proofs)
- `tenant_documents/` (for lease agreements)

## Usage

1. **Add Tenants**:
   - Fill in tenant details
   - Upload ID proof photo
   - Security deposit auto-calculated as 2x rent

2. **Record Payments**:
   - Select tenant and payment date
   - Add late fees if applicable
   - View payment history

3. **Manage Documents**:
   - Upload lease agreements
   - Set expiry reminders
   - Attach scanned documents

## Data Security

Your data is stored locally with:
- SQLite database encryption
- Hashed filenames for attachments
- Automatic backups in the app directory

## Backup Recommendations

1. **Manual Backup**:
   - Regularly copy the entire directory to external storage
   - Especially backup `tenant_ledger.db`

2. **Cloud Backup** (Optional):
   - Zip and encrypt the directory before uploading to cloud services

## Contributing

Contributions are welcome! Please open an issue or PR for:
- Bug reports
- Feature requests
- UI/UX improvements


---

**Note**: This is a local application. No data is collected or transmitted to any servers.
```

### Recommended Additions:
1. Add a screenshot (`screenshot.png`) after you've run the app
2. Include a `requirements.txt` file with:
   ```
   pillow>=10.0.0
   ```
3. For a more complete project, consider adding:
   - A `CHANGELOG.md`
   - `CONTRIBUTING.md` guidelines
   - Issue templates

This README provides:
- Clear feature overview
- Easy installation instructions
- Usage guidance
- Security transparency
- Contribution options
