from random import choice
import string

from odoo.addons.web.controllers.home import Home, ensure_db
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime


class OtpSignupHome(Home):

    @http.route(website=True)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        return super(OtpSignupHome, self).web_auth_signup(*args, **kw)

    @http.route('/web/signup/otp', type='http', auth='public', website=True, sitemap=False)
    def web_signup_otp(self, **kw):
        qcontext = request.params.copy()
        otp_code = self.generate_otp(4)

        if "login" in qcontext and qcontext["login"] and qcontext["password"] == qcontext["confirm_password"]:
            existing_user = request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))])
            if existing_user:
                qcontext["error"] = _("Another user is already registered using this email address.")
                return request.render('email_authentication_login.custom_otp_signup', qcontext)

            email = str(qcontext.get('login'))
            name = str(qcontext.get('name'))
            email_from = request.env.company.email

            # Prepare email content
            mail_body = self._prepare_signup_email_content(name, otp_code)

            # Create and send the email
            mail = request.env['mail.mail'].sudo().create({
                'subject': _('Verify Your Odoo Account - OTP Required'),
                'email_from': email_from,
                'email_to': email,
                'body_html': mail_body,
            })
            mail.send()

            # Store OTP verification details
            request.env['otp.verification'].sudo().create({
                'otp': otp_code,
                'email': email
            })

            return request.render('email_authentication_login.custom_otp_signup', {
                'otp': True,
                'otp_login': True,
                'login': qcontext["login"],
                'otp_no': otp_code,
                'name': qcontext["name"],
                'password': qcontext["password"],
                'confirm_password': qcontext["confirm_password"]
            })
        else:
            qcontext["error"] = _("Passwords do not match, please retype them.")
            return request.render('email_authentication_login.custom_otp_signup', qcontext)

    @http.route('/web/signup/otp/verify', type='http', auth='public', website=True, sitemap=False)
    def web_otp_signup_verify(self, *args, **kw):
        qcontext = request.params.copy()
        email = str(kw.get('login'))
        otp_record = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)
        name = str(kw.get('name'))
        password = str(qcontext.get('password'))
        confirm_password = str(qcontext.get('confirm_password'))

        try:
            otp_input = str(kw.get('otp'))
            if otp_record.otp == otp_input:
                otp_record.state = 'verified'
                return self.web_auth_signup(*args, **kw)
            else:
                otp_record.state = 'rejected'
                return request.render('email_authentication_login.custom_otp_signup', {
                    'otp': True,
                    'otp_login': True,
                    'login': email,
                    'name': name,
                    'password': password,
                    'confirm_password': confirm_password
                })
        except UserError as e:
            qcontext['error'] = e.name or e.value

        return request.render('email_authentication_login.custom_otp_signup', {
            'otp': True,
            'otp_login': True,
            'login': email,
            'name': name,
            'password': password,
            'confirm_password': confirm_password
        })

    def generate_otp(self, number_of_digits):
        """Generate a random OTP of specified digit length."""
        return ''.join(choice(string.digits) for _ in range(number_of_digits))

    def _prepare_signup_email_content(self, user_name, otp_code):
        """Prepare the HTML content for the signup OTP email."""
        return """\
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 0;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 20px auto;
                        background: #ffffff;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: #007bff;
                        color: #ffffff;
                        text-align: center;
                        padding: 15px;
                        font-size: 22px;
                        font-weight: bold;
                        border-top-left-radius: 8px;
                        border-top-right-radius: 8px;
                    }}
                    .content {{
                        padding: 20px;
                        font-size: 16px;
                        color: #333;
                        text-align: center;
                    }}
                    .otp {{
                        font-size: 24px; 
                        font-weight: bold;
                        color: #007bff;
                        padding: 10px;
                        display: inline-block;
                        margin: 10px auto;
                        border-radius: 5px;
                        background: #f8f9fa;
                    }}
                    .footer {{
                        background: #f1f1f1;
                        text-align: center;
                        padding: 10px;
                        font-size: 14px;
                        color: #555;
                        border-bottom-left-radius: 8px;
                        border-bottom-right-radius: 8px;
                    }}
                    .footer a {{
                        color: #007bff;
                        text-decoration: none;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">Welcome to Mayank Odoo Tech - Signup OTP</div>
                    <div class="content">
                        <p>Dear <b>{}</b>,</p>
                        <p>Thank you for signing up with <b>Mayank Odoo Tech</b>!</p>
                        <p>To complete your account registration, please use the following One-Time Password (OTP):</p>
                        <p class="otp">{}</p>
                        <p>This OTP is valid for a limited time. If you did not request this, please ignore this email.</p>
                        <p>We are excited to have you on board!</p>
                    </div>
                    <div class="footer">
                        &copy; {} Mayank Odoo Tech. All Rights Reserved. | 
                        <a href="https://youtube.com/@mayankodootech?si=zVpSDbPAWdy1Q_su">Visit Our Website</a>
                    </div>
                </div>
            </body>
        </html>
        """.format(user_name, otp_code, datetime.now().year)