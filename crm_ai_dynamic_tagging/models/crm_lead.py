import json
import logging
import re

import requests

from odoo import api, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "zoho.com",
}


class CrmLead(models.Model):
    _inherit = "crm.lead"

    ai_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
        ],
        string="AI Status",
        default="pending",
        copy=False,
        tracking=True,
    )
    ai_processed = fields.Boolean(default=False, copy=False)
    ai_response_raw = fields.Text(copy=False)
    ai_reason = fields.Char(copy=False)
    ai_last_error = fields.Text(copy=False)
    ai_retry_count = fields.Integer(default=0, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)

        icp = self.env["ir.config_parameter"].sudo()
        enabled = icp.get_param("crm_ai_dynamic_tagging.enabled") == "True"
        queue_on_create = icp.get_param("crm_ai_dynamic_tagging.process_on_create") != "False"

        if enabled and queue_on_create:
            leads._queue_for_ai()

        return leads

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get("skip_ai_queue"):
            return res

        trigger_fields = {
            "name",
            "partner_name",
            "email_from",
            "description",
            "team_id",
            "partner_id",
            "website",
            "tag_ids",
            "contact_name",
            "function",
            "city",
            "country_id",
            "x_studio_employee_headcount",
            "x_employee_count",
            "employee_count",
        }

        if trigger_fields.intersection(vals.keys()):
            icp = self.env["ir.config_parameter"].sudo()
            enabled = icp.get_param("crm_ai_dynamic_tagging.enabled") == "True"
            queue_on_write = icp.get_param("crm_ai_dynamic_tagging.process_on_write") != "False"

            if enabled and queue_on_write:
                self._queue_for_ai()

        return res

    def _queue_for_ai(self):
        self.with_context(skip_ai_queue=True).write({
            "ai_status": "pending",
            "ai_last_error": False,
        })

    @api.model
    def cron_process_pending_ai_leads(self, limit=20):
        leads = self.search(
            [("ai_status", "=", "pending")],
            order="write_date asc, id asc",
            limit=limit,
        )
        for lead in leads:
            try:
                lead._run_ai_tagging()
            except Exception as e:
                _logger.exception("AI tagging failed for lead %s: %s", lead.id, e)
                lead.with_context(skip_ai_queue=True).write({
                    "ai_status": "failed",
                    "ai_last_error": str(e),
                    "ai_retry_count": lead.ai_retry_count + 1,
                })

    def action_run_ai_tagging(self):
        for lead in self:
            lead._run_ai_tagging()

    def _run_ai_tagging(self):
        for lead in self:
            if not lead._is_ai_enabled():
                lead.with_context(skip_ai_queue=True).write({
                    "ai_status": "skipped",
                    "ai_last_error": "AI disabled in settings",
                })
                continue

            payload = lead._prepare_ai_payload()
            ai_result = lead._call_ai_api(payload)
            lead._apply_ai_result(ai_result)

    def _is_ai_enabled(self):
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param("crm_ai_dynamic_tagging.enabled") == "True"

    def _prepare_ai_payload(self):
        self.ensure_one()
        return {
            "company_name": self.partner_name or (self.partner_id.name if self.partner_id else "") or "",
            "email": self.email_from or "",
            "opportunity": self.name or "",
            "description": self.description or "",
            "sales_team": self.team_id.name if self.team_id else "",
            "company_website_link": self.partner_id.website if self.partner_id else (self.website or ""),
            "employee_headcount": self._get_employee_count(),
        }

    def _get_employee_count(self):
        self.ensure_one()

        candidate_fields = [
            "x_studio_employee_headcount",
            "x_employee_count",
            "employee_count",
        ]

        for field_name in candidate_fields:
            if field_name in self._fields and self[field_name]:
                try:
                    return int(self[field_name])
                except Exception:
                    return 0

        if self.partner_id:
            partner_fields = [
                "employee",
                "x_studio_employee_headcount",
                "x_employee_count",
            ]
            for field_name in partner_fields:
                if field_name in self.partner_id._fields and self.partner_id[field_name]:
                    try:
                        return int(self.partner_id[field_name])
                    except Exception:
                        return 0

        return 0

    def _get_ai_prompt(self, payload):
        return f"""
You are classifying CRM leads for Odoo.

Return STRICT JSON only.
No markdown.
No explanation.
No code fences.

Input:
- Company Name: {payload.get('company_name', '')}
- Email: {payload.get('email', '')}
- Opportunity: {payload.get('opportunity', '')}
- Description: {payload.get('description', '')}
- Sales Team: {payload.get('sales_team', '')}
- Company Website Link: {payload.get('company_website_link', '')}
- Employee Headcount: {payload.get('employee_headcount', 0)}

Rules:
1. Website:
   - Prefer Company Website Link if present and valid.
   - Else infer from business email domain if possible.
   - Ignore public domains like gmail.com, yahoo.com, outlook.com, hotmail.com.

2. Industry tags:
   Standard tags:
   - Restaurant
   - Supermarket
   - Hospital
   - Software

   You may suggest at most 1 new industry tag if the lead clearly belongs to another industry.

3. Do NOT generate employee bucket tags.
4. Do NOT generate source tags.

Output JSON schema:
{{
  "website": "",
  "tags": [],
  "new_tags": [],
  "reason": ""
}}
""".strip()

    def _call_ai_api(self, payload):
        self.ensure_one()

        icp = self.env["ir.config_parameter"].sudo()
        url = icp.get_param("crm_ai_dynamic_tagging.api_url")
        api_key = icp.get_param("crm_ai_dynamic_tagging.api_key")
        model = icp.get_param("crm_ai_dynamic_tagging.model") or "gpt-4.1-mini"
        timeout = int(icp.get_param("crm_ai_dynamic_tagging.timeout") or 30)

        if not url or not api_key:
            return {
                "website": "",
                "tags": [],
                "new_tags": [],
                "reason": "Missing AI configuration",
            }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": self._get_ai_prompt(payload)},
            ],
            "temperature": 0.1,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=request_body,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "{}")
            )

            self.ai_response_raw = content

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                result = self._extract_json_from_text(content)

            if not isinstance(result, dict):
                result = {
                    "website": "",
                    "tags": [],
                    "new_tags": [],
                    "reason": "AI response is not a JSON object",
                }

            return result

        except Exception as e:
            return {
                "website": "",
                "tags": [],
                "new_tags": [],
                "reason": str(e),
            }

    def _extract_json_from_text(self, text):
        text = text or ""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {
                "website": "",
                "tags": [],
                "new_tags": [],
                "reason": "No JSON object found in AI response",
            }
        try:
            return json.loads(match.group(0))
        except Exception:
            return {
                "website": "",
                "tags": [],
                "new_tags": [],
                "reason": "Unable to parse extracted JSON",
            }

    def _normalize_tag_name(self, tag_name):
        if not tag_name:
            return ""

        cleaned = tag_name.strip()
        key = cleaned.lower()

        mapping = {
            "health care": "Healthcare",
            "healthcare": "Healthcare",
            "saas": "Software",
            "tech": "Software",
            "app development": "Software",
        }
        return mapping.get(key, cleaned)

    def _is_valid_website(self, website):
        if not website:
            return False
        website = website.strip()
        return website.startswith("http://") or website.startswith("https://")

    def _website_from_email(self):
        self.ensure_one()

        email = (self.email_from or "").strip()
        if "@" not in email:
            return ""

        domain = email.split("@", 1)[1].strip().lower()
        domain = domain.strip(">),.; ")

        if not domain or domain in PUBLIC_EMAIL_DOMAINS:
            return ""

        return f"https://{domain}"

    def _apply_ai_result(self, ai_result):
        self.ensure_one()

        Tag = self.env["crm.tag"].sudo()
        icp = self.env["ir.config_parameter"].sudo()
        max_new_tags = int(icp.get_param("crm_ai_dynamic_tagging.max_new_tags") or 1)

        website = (ai_result.get("website") or "").strip()
        tags = ai_result.get("tags") or []
        new_tags = (ai_result.get("new_tags") or [])[:max_new_tags]
        reason = (ai_result.get("reason") or "").strip()

        final_tags = set()

        for tag_name in tags:
            if isinstance(tag_name, str):
                normalized = self._normalize_tag_name(tag_name)
                if normalized:
                    final_tags.add(normalized)

        for tag_name in new_tags:
            if isinstance(tag_name, str):
                normalized = self._normalize_tag_name(tag_name)
                if normalized:
                    final_tags.add(normalized)

        emp = self._get_employee_count()
        if 1000 <= emp <= 5000:
            final_tags.add("1000-5000")
        elif 500 <= emp < 1000:
            final_tags.add("500-1000")
        elif 1 <= emp <= 50:
            final_tags.add("1-50")

        team_name = (self.team_id.name or "").strip().lower() if self.team_id else ""
        if "website" in team_name:
            final_tags.add("inbound")
        elif team_name == "sales":
            final_tags.add("outbound")

        commands = []
        for tag_name in sorted(final_tags):
            tag = Tag.search([("name", "=", tag_name)], limit=1)
            if not tag:
                tag = Tag.create({"name": tag_name})
            if tag not in self.tag_ids:
                commands.append(Command.link(tag.id))

        vals = {
            "ai_processed": True,
            "ai_status": "done",
            "ai_reason": reason or False,
            "ai_last_error": False,
        }

        if commands:
            vals["tag_ids"] = commands

        if self._is_valid_website(website):
            if not self.website:
                vals["website"] = website
        else:
            fallback_website = self._website_from_email()
            if fallback_website and not self.website:
                vals["website"] = fallback_website

        self.with_context(skip_ai_queue=True).write(vals)