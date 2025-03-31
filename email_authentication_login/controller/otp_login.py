from random import choice
import string

from odoo.addons.web.controllers.home import Home, ensure_db
from odoo import http, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from datetime import datetime


class OtpLoginHome(Home):

    @http.route(website=True)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        qcontext = request.params.copy()

        if request.httprequest.method == 'GET':
            if "otp_login" in kw and "otp" in kw:
                if kw["otp_login"] and kw["otp"]:
                    return request.render("email_authentication_login.custom_login_template", {'otp': True, 'otp_login': True})
            elif "otp_login" in kw and kw["otp_login"]:
                return request.render("email_authentication_login.custom_login_template", {'otp_login': True})
            else:
                return super(OtpLoginHome, self).web_login(redirect, **kw)
        else:
            if kw.get('login'):
                request.params['login'] = kw.get('login').strip()
            if kw.get('password'):
                request.params['password'] = kw.get('password').strip()
            return super(OtpLoginHome, self).web_login(redirect, **kw)

        return request.render("email_authentication_login.custom_login_template", {})

    @http.route('/web/otp/login', type='http', auth='public', website=True, csrf=False)
    def web_otp_login(self, **kw):
        qcontext = request.params.copy()
        email = str(qcontext.get('login'))
        user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)

        if user:
            otp_code = self.generate_otp(6)
            email_content = self._prepare_email_content(user.name, otp_code)

            mail = request.env['mail.mail'].sudo().create({
                'subject': _('Verify Your Odoo Account - OTP Required'),
                'email_from': user.company_id.email,
                'author_id': user.partner_id.id,
                'email_to': email,
                'body_html': email_content,
            })
            mail.send()

            request.env['otp.verification'].sudo().create({
                'otp': otp_code,
                'email': email
            })

            return request.render("email_authentication_login.custom_login_template", {
                'otp': True,
                'otp_login': True,
                'login': qcontext["login"],
                'otp_no': otp_code
            })
        else:
            return request.render("email_authentication_login.custom_login_template", {
                'otp': False,
                'otp_login': True,
                'login_error': True
            })

    @http.route('/web/otp/verify', type='http', auth='public', website=True, csrf=False)
    def web_otp_verify(self, *args, **kw):
        qcontext = request.params.copy()
        email = str(kw.get('login'))
        otp_record = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)

        try:
            otp_input = str(kw.get('otp'))
            if otp_record.otp == otp_input:
                otp_record.state = 'verified'
                user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                request.env.cr.execute(
                    "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                    [user.id]
                )
                hashed_password = request.env.cr.fetchone()[0]
                qcontext.update({
                    'login': user.sudo().login,
                    'name': user.sudo().partner_id.name,
                    'password': hashed_password + 'mobile_otp_login'
                })
                request.params.update(qcontext)
                return self.web_login(*args, **kw)
            else:
                otp_record.state = 'rejected'
                return request.render('email_authentication_login.custom_login_template', {
                    'otp': True,
                    'otp_login': True,
                    'login': email
                })
        except UserError as e:
            qcontext['error'] = e.name or e.value

        return request.render('email_authentication_login.custom_login_template', {
            'otp': True,
            'otp_login': True,
            'login': email
        })

    def generate_otp(self, number_of_digits):
        return ''.join(choice(string.digits) for _ in range(number_of_digits))

    def _prepare_email_content(self, user_name, otp_code):
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
                    <div class="header"><b>Mayank Odoo Tech - Account Verification</b></div>
                    <div class="content">
                        <p>Dear <b>{}</b>,</p>
                        <p>To complete the verification process for your <b>Mayank Odoo Tech</b> account, please use the following One-Time Password (OTP):</p>
                        <p class="otp"><b>{}</b></p>
                        <p>If you did not request this verification, please ignore this email.</p>
                        <p>Thank you.</p>
                    </div>
                    <div class="footer">
                        &copy; {} Mayank Odoo Tech. All Rights Reserved. | 
                        <a href="https://youtube.com/@mayankodootech?si=zVpSDbPAWdy1Q_su">Visit Our Website</a>
                    </div>
                </div>
            </body>
        </html>
        """.format(user_name, otp_code, datetime.now().year)