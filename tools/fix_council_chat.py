"""Fix council_chat findings and mitre list types."""
import pathlib

path = pathlib.Path("integrations/hermes/yadro-guard/dashboard/plugin_api.py")
content = path.read_text(encoding="utf-8")

old_block = '''        t1_ru = f"Вердикт: {cv.tier1.verdict} (Риск: {cv.tier1.risk_score}/100, Энтропия: {cv.tier1.entropy:.2f}). "
        if cv.tier1.findings:
            t1_ru += f"Обнаружено: {', '.join(cv.tier1.findings)}. "
        if cv.tier1.is_obfuscated:
            t1_ru += f"Деобфусцировано слоев: {len(cv.tier1.deobfuscated_layers)}. "
        if cv.tier1.false_positives_eliminated:
            t1_ru += f"Исключено ложных срабатываний: {', '.join(cv.tier1.false_positives_eliminated)}. "
        if cv.tier1.reasons:
            t1_ru += f"\\nОбоснование: {'; '.join(cv.tier1.reasons)}"

        t1_en = f"Verdict: {cv.tier1.verdict} (Risk: {cv.tier1.risk_score}/100, Entropy: {cv.tier1.entropy:.2f}). "
        if cv.tier1.findings:
            t1_en += f"Findings: {', '.join(cv.tier1.findings)}. "
        if cv.tier1.reasons:
            t1_en += f"\\nReasons: {'; '.join(cv.tier1.reasons)}"

        t2_ru = f"MITRE ATT&CK: {', '.join(cv.tier2.mitre_techniques) if cv.tier2.mitre_techniques else 'Техники атак не подтверждены'}.\\n"'''

new_block = '''        findings_list = [f.get("title", f.get("type", str(f))) if isinstance(f, dict) else str(f) for f in cv.tier1.findings]
        mitre_ids = [m.get("technique_id") if isinstance(m, dict) else str(m) for m in cv.tier2.mitre_techniques]
        fps_list = [str(x) for x in cv.tier1.false_positives_eliminated]

        t1_ru = f"Вердикт: {cv.tier1.verdict} (Риск: {cv.tier1.risk_score}/100, Энтропия: {cv.tier1.entropy:.2f}). "
        if findings_list:
            t1_ru += f"Обнаружено: {', '.join(findings_list)}. "
        if cv.tier1.is_obfuscated:
            t1_ru += f"Деобфусцировано слоев: {len(cv.tier1.deobfuscated_layers)}. "
        if fps_list:
            t1_ru += f"Исключено ложных срабатываний: {', '.join(fps_list)}. "
        if cv.tier1.reasons:
            t1_ru += f"\\nОбоснование: {'; '.join(cv.tier1.reasons)}"

        t1_en = f"Verdict: {cv.tier1.verdict} (Risk: {cv.tier1.risk_score}/100, Entropy: {cv.tier1.entropy:.2f}). "
        if findings_list:
            t1_en += f"Findings: {', '.join(findings_list)}. "
        if cv.tier1.reasons:
            t1_en += f"\\nReasons: {'; '.join(cv.tier1.reasons)}"

        t2_ru = f"MITRE ATT&CK: {', '.join(mitre_ids) if mitre_ids else 'Техники атак не подтверждены'}.\\n"'''

assert old_block in content, "old_block not found"
content = content.replace(old_block, new_block, 1)

old_t2_en = '''t2_en = f"MITRE ATT&CK: {', '.join(cv.tier2.mitre_techniques) if cv.tier2.mitre_techniques else 'No malicious techniques confirmed'}.\\n"'''
new_t2_en = '''t2_en = f"MITRE ATT&CK: {', '.join(mitre_ids) if mitre_ids else 'No malicious techniques confirmed'}.\\n"'''
assert old_t2_en in content, "old_t2_en not found"
content = content.replace(old_t2_en, new_t2_en, 1)

old_mitre_ret = '"mitre": cv.tier2.mitre_techniques,'
new_mitre_ret = '"mitre": mitre_ids,'
assert old_mitre_ret in content, "old_mitre_ret not found"
content = content.replace(old_mitre_ret, new_mitre_ret, 1)

path.write_text(content, encoding="utf-8")
print("Fixed list formatting in council_chat.")

