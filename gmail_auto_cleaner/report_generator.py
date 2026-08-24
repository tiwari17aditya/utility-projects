"""
HTML & Text Report Generator for Gmail Category Inspection
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

class InspectionReportGenerator:
    @staticmethod
    def generate_html_report(account_email: str, email_records: List[Dict[str, Any]], output_filepath: str) -> str:
        total_scanned = len(email_records)
        retain_records = [r for r in email_records if r.get("action") == "RETAIN"]
        delete_records = [r for r in email_records if r.get("action") == "DELETE"]

        # Category stats
        cat_stats = {}
        for r in email_records:
            cat = r.get("folder", "Unknown")
            if cat not in cat_stats:
                cat_stats[cat] = {"total": 0, "retain": 0, "delete": 0}
            cat_stats[cat]["total"] += 1
            if r.get("action") == "RETAIN":
                cat_stats[cat]["retain"] += 1
            else:
                cat_stats[cat]["delete"] += 1

        rows_html = []
        for idx, r in enumerate(email_records, 1):
            action = r.get("action", "DELETE")
            badge_class = "bg-green-100 text-green-800" if action == "RETAIN" else "bg-red-100 text-red-800"
            badge_icon = "🛡️ KEEP" if action == "RETAIN" else "🗑️ DELETE"
            
            subject = r.get("subject", "(No Subject)")
            sender = r.get("from", "(Unknown)")
            folder = r.get("folder", "")
            date_str = r.get("date", "")
            reason = r.get("reason", "")
            confidence = r.get("confidence", 50)

            rows_html.append(f"""
            <tr class="hover:bg-slate-50 border-b border-slate-100 text-sm">
                <td class="px-4 py-3 text-slate-500 font-mono">{idx}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold {badge_class}">
                        {badge_icon} ({confidence}%)
                    </span>
                </td>
                <td class="px-4 py-3 font-medium text-slate-900">{subject}</td>
                <td class="px-4 py-3 text-slate-600 max-w-xs truncate" title="{sender}">{sender}</td>
                <td class="px-4 py-3"><span class="px-2 py-1 rounded bg-slate-100 text-slate-700 text-xs font-mono">{folder}</span></td>
                <td class="px-4 py-3 text-slate-500 text-xs">{date_str}</td>
                <td class="px-4 py-3 text-slate-500 text-xs italic">{reason}</td>
            </tr>
            """)

        cat_cards_html = []
        for cat_name, stats in cat_stats.items():
            cat_cards_html.append(f"""
            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <h4 class="font-semibold text-slate-700">{cat_name}</h4>
                <div class="mt-2 flex justify-between items-center text-sm">
                    <span class="text-slate-500">Total: <strong>{stats['total']}</strong></span>
                    <span class="text-green-600 font-medium">Keep: {stats['retain']}</span>
                    <span class="text-red-600 font-medium">Delete: {stats['delete']}</span>
                </div>
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gmail Category Inspection - {account_email}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 p-6 min-h-screen">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <span class="px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-full uppercase tracking-wider">Dry-Run Inspection</span>
                <h1 class="text-2xl font-bold text-slate-900 mt-1">Gmail Category Recommendations</h1>
                <p class="text-slate-500 text-sm mt-0.5">Account: <strong class="text-slate-700">{account_email}</strong> | Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            <div class="flex gap-3">
                <div class="px-4 py-2 bg-green-50 border border-green-200 rounded-xl text-center">
                    <div class="text-xs text-green-600 font-semibold uppercase">Retain</div>
                    <div class="text-xl font-bold text-green-700">{len(retain_records)}</div>
                </div>
                <div class="px-4 py-2 bg-red-50 border border-red-200 rounded-xl text-center">
                    <div class="text-xs text-red-600 font-semibold uppercase">Delete Candidate</div>
                    <div class="text-xl font-bold text-red-700">{len(delete_records)}</div>
                </div>
                <div class="px-4 py-2 bg-slate-100 border border-slate-200 rounded-xl text-center">
                    <div class="text-xs text-slate-500 font-semibold uppercase">Total Scanned</div>
                    <div class="text-xl font-bold text-slate-800">{total_scanned}</div>
                </div>
            </div>
        </div>

        <!-- Category Summaries -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {"".join(cat_cards_html)}
        </div>

        <!-- Details Table -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                <h3 class="font-bold text-slate-800">Email Title & Classification Summary</h3>
                <span class="text-xs text-slate-500">Excludes Primary Folder</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                            <th class="px-4 py-3">#</th>
                            <th class="px-4 py-3">Recommendation</th>
                            <th class="px-4 py-3">Subject / Title</th>
                            <th class="px-4 py-3">From</th>
                            <th class="px-4 py-3">Label</th>
                            <th class="px-4 py-3">Date</th>
                            <th class="px-4 py-3">Reasoning</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(rows_html) if rows_html else '<tr><td colspan="7" class="p-8 text-center text-slate-400">No category emails fetched.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</body>
</html>
"""
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_filepath
