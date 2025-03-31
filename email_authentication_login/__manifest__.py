# -*- coding: utf-8 -*-
{
    "name": "Email OTP Authentication",
    "version": "17.0.1.0",
    "author": "Mayank Prajapati",
    "category": "Extra Tools",
    "summary": """
        Secure OTP-based authentication for user login & signup in Odoo.
    """,
    "description": """
        Email OTP Authentication Module for Odoo 17
        ===========================================
        This module enhances the security of Odoo authentication by allowing users to verify their identity using a One-Time Password (OTP) sent via email. It supports both login and signup authentication.

        Key Features:
        -------------
        - OTP-based login verification.
        - OTP-based signup verification.
        - Secure and user-friendly authentication process.
        - Automatic OTP generation and email sending.
        - Supports email templates with a professional design.
        - Fully integrated with Odoo's authentication system.
        - Customizable email content for OTP delivery.
        - Scheduled cleanup for expired OTPs via cron jobs.

        Technical Details:
        ------------------
        - Built on top of Odoo's `auth_signup` module.
        - Uses Odoo's mail system to send OTPs.
        - Includes access control for OTP verification records.

        This module is ideal for organizations looking to add an extra layer of security to their authentication process.
    """,
    "depends": ["base", "mail", "web", "website", "auth_signup"],
    "data": [
        "security/ir.model.access.csv",
        "security/security_group.xml",
        "views/otp_verification.xml",
        "views/login_view.xml",
        "views/otp_signup.xml",
        "data/cron.xml"
    ],
    "price": 20,
    "currency": "USD",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "images": ["static/description/banner.png"]
}
