"""메인: 수집 -> 중복 제거 -> Markdown + 이메일 발송.

GitHub Actions 환경에서 실행됨. 이메일 자격증명은 환경변수(GitHub Secrets)에서 읽음:
  EMAIL_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO, SUBJECT_PREFIX
"""
import html as html_lib
import os
import sys
from datetime import datetime
from collections import defaultdict

import yaml

from fetch import fetch_all
from mailer import send_digest


def load_seen(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_seen(path, dois):
    with open(path, "a", encoding="utf-8") as f:
        for d in dois:
            f.write(d + "\n")


def email_config(config):
    """config.yaml의 email 설정을 환경변수로 덮어쓰기 (GitHub Secrets 지원)."""
    cfg = dict(config.get("email") or {})
    env = os.environ
    if env.get("EMAIL_ENABLED"):
        cfg["enabled"] = env["EMAIL_ENABLED"].lower() in ("1", "true", "yes")
    mapping = {
        "user": "SMTP_USER",
        "password": "SMTP_PASSWORD",
        "to": "EMAIL_TO",
        "smtp_host": "SMTP_HOST",
        "smtp_port": "SMTP_PORT",
        "subject_prefix": "SUBJECT_PREFIX",
    }
    for key, envname in mapping.items():
        if env.get(envname):
            cfg[key] = env[envname]
    return cfg


def build_markdown(date_str, papers):
    lines = [f"# 논문 구독 다이제스트 — {date_str}\n", f"새 논문: {len(papers)}편\n"]
    by_journal = defaultdict(list)
    for p in papers:
        by_journal[p["journal"]].append(p)
    for jname, jps in by_journal.items():
        lines.append(f"\n---\n\n## {jname} ({len(jps)}편)\n")
        for i, p in enumerate(jps, 1):
            link_md = f"[{p['doi']}]({p['link']})" if p["link"] else p["doi"]
            lines += [
                f"\n### {i}. {p['title']}\n",
                f"- 저자: {p['authors']}  |  게재: {p['date']}\n",
                f"- 링크: {link_md}\n",
            ]
            if p["abstract"]:
                lines += ["\n**초록:**\n", p["abstract"].strip() + "\n"]
            else:
                lines.append("\n_(초록 없음)_\n")
    return "".join(lines)


def build_html(date_str, papers):
    rows = []
    for p in papers:
        link = (f'<a href="{html_lib.escape(p["link"])}">{html_lib.escape(p["doi"])}</a>'
                if p["link"] else html_lib.escape(p["doi"]))
        abstract = (f'<p><b>초록:</b> {html_lib.escape(p["abstract"])}</p>'
                    if p["abstract"] else "<p><i>(초록 없음)</i></p>")
        rows.append(
            f'<h3>{html_lib.escape(p["title"])}</h3>'
            f'<p>저자: {html_lib.escape(p["authors"])} | 게재: {html_lib.escape(p["date"])} | {link}</p>'
            f'{abstract}'
        )
    return (f"<html><body><h1>논문 구독 다이제스트 — {date_str}</h1>"
            f"<p>새 논문: {len(papers)}편</p>{''.join(rows)}</body></html>")


def main(config_path="config.yaml"):
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    os.makedirs(config["output_dir"], exist_ok=True)
    seen = load_seen(config["seen_cache"])

    papers = fetch_all(config)
    new_papers = [p for p in papers if p["doi"] and p["doi"] not in seen]
    if not new_papers:
        print("새 논문이 없습니다.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    md = build_markdown(date_str, new_papers)
    html = build_html(date_str, new_papers)

    out_path = os.path.join(config["output_dir"], f"digest-{date_str}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown 저장: {out_path}")

    mail = email_config(config)
    if mail.get("enabled"):
        try:
            subj = f"{mail.get('subject_prefix', '[논문구독]')} {date_str} - {len(new_papers)}편"
            send_digest(mail, subj, md, html)
            print("이메일 발송 완료")
        except Exception as e:
            print(f"이메일 발송 실패: {e}")
    else:
        print("이메일 미활성화 (EMAIL_ENABLED 비어있음). Markdown만 저장.")

    save_seen(config["seen_cache"], [p["doi"] for p in new_papers])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
