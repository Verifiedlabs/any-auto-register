"""TempMail Malghz — custom mailbox driver for tempmail.malghz.my.id"""
from core.base_mailbox import BaseMailbox, MailboxAccount
from providers.registry import register_provider
import requests
import random
import string
import re
import time


class TempMailMalghzMailbox(BaseMailbox):

    def __init__(self, api_url: str = "https://tempmail.malghz.my.id",
                 domain: str = "malghz.my.id", admin_token: str = "", proxy: str = None):
        self.api = api_url.rstrip("/")
        self.domain = domain
        self.admin_token = admin_token
        self.proxy = {"http": proxy, "https": proxy} if proxy else None

    def _headers(self) -> dict:
        h = {"accept": "application/json", "content-type": "application/json"}
        if self.admin_token:
            h["Authorization"] = f"Bearer {self.admin_token}"
        return h

    def get_email(self) -> MailboxAccount:
        name = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        address = f"{name}@{self.domain}"
        r = requests.post(f"{self.api}/api/addresses",
            json={"address": address},
            headers=self._headers(),
            proxies=self.proxy, timeout=15)
        print(f"[TempMailMalghz] create status={r.status_code} resp={r.text[:200]}")
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create address: {r.status_code} {r.text[:200]}")
        return MailboxAccount(
            email=address,
            account_id=address,
            extra={
                "provider_resource": {
                    "provider_type": "mailbox",
                    "provider_name": "tempmail_malghz",
                    "resource_type": "mailbox",
                    "resource_identifier": address,
                    "handle": address,
                    "display_name": address,
                    "metadata": {"email": address, "api_url": self.api, "domain": self.domain},
                },
            },
        )

    def _get_mails(self, email: str) -> list:
        r = requests.get(f"{self.api}/api/inbox/{email}",
            headers=self._headers(), proxies=self.proxy, timeout=10)
        data = r.json()
        mails = data if isinstance(data, list) else data.get("results", [])
        for mail in mails:
            if not mail.get("raw"):
                detail = requests.get(f"{self.api}/api/email/{mail.get('id')}",
                    headers=self._headers(), proxies=self.proxy, timeout=10)
                if detail.status_code == 200:
                    d = detail.json()
                    mail["raw"] = d.get("body_text") or d.get("body_html") or ""
        return mails

    def get_current_ids(self, account: MailboxAccount) -> set:
        try:
            mails = self._get_mails(account.email)
            return {str(m.get("id", "")) for m in mails}
        except Exception:
            return set()

    def wait_for_code(self, account: MailboxAccount, keyword: str = "",
                      timeout: int = 120, before_ids: set = None, code_pattern: str = None) -> str:
        seen = set(before_ids or [])
        start = time.time()
        while time.time() - start < timeout:
            try:
                mails = self._get_mails(account.email)
                for mail in sorted(mails, key=lambda x: x.get("id", 0), reverse=True):
                    mid = str(mail.get("id", ""))
                    if not mid or mid in seen:
                        continue
                    seen.add(mid)
                    raw = str(mail.get("raw", mail.get("body", mail.get("text", ""))))
                    subject = str(mail.get("subject", ""))
                    search_text = raw or subject
                    if keyword and keyword.lower() not in search_text.lower():
                        continue
                    code_m = re.search(r'<span[^>]*>\s*(\d{6})\s*</span>', search_text)
                    if code_m:
                        return code_m.group(1)
                    body_start = search_text.find('\r\n\r\n')
                    body = search_text[body_start:] if body_start != -1 else search_text
                    body = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', body)
                    body = re.sub(r'm=\+\d+\.\d+', '', body)
                    body = re.sub(r'\bt=\d+\b', '', body)
                    m = re.search(code_pattern or r'(?<!#)(?<!\d)(\d{6})(?!\d)', body)
                    if m:
                        return m.group(1) if m.groups() else m.group(0)
            except Exception:
                pass
            time.sleep(3)
        raise TimeoutError(f"Verification code timeout ({timeout}s)")

    def wait_for_link(self, account: MailboxAccount, keyword: str = "",
                      timeout: int = 120, before_ids: set = None) -> str:
        seen = set(before_ids or [])
        start = time.time()
        while time.time() - start < timeout:
            try:
                mails = self._get_mails(account.email)
                for mail in sorted(mails, key=lambda x: x.get("id", 0), reverse=True):
                    mid = str(mail.get("id", ""))
                    if not mid or mid in seen:
                        continue
                    seen.add(mid)
                    raw = str(mail.get("raw", mail.get("body", mail.get("text", ""))))
                    links = re.findall(r'https?://[^\s<>"\']+', raw)
                    for link in links:
                        if keyword and keyword.lower() not in link.lower():
                            continue
                        return link
                    if not keyword and links:
                        return links[0]
            except Exception:
                pass
            time.sleep(3)
        raise TimeoutError(f"Verification link timeout ({timeout}s)")


register_provider("mailbox", "tempmail_malghz")(TempMailMalghzMailbox)
