import hashlib

import streamlit as st


def _article_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def _severity_color(severity: str) -> str:
    return {"high": "#ff4b4b", "medium": "#ffa500", "low": "#1f77b4"}.get(severity, "#888")


def _render_flagged_sentences(flagged_sentences) -> None:
    if not flagged_sentences:
        st.success("No AI writing tells detected.")
        return
    for fs in flagged_sentences:
        active = {k: v for k, v in fs.labels.items() if v}
        label_parts = [f"**{cat}**: {', '.join(patterns)}" for cat, patterns in active.items()]
        color = _severity_color(fs.severity)
        st.markdown(
            f'<div style="border-left: 4px solid {color}; padding: 8px 12px; margin-bottom: 8px;">'
            f"<small style='color:{color}'>{fs.severity.upper()} · {fs.sentence_id}</small><br>"
            f"<em>{fs.text}</em><br>"
            f"<small>{' &nbsp;|&nbsp; '.join(label_parts)}</small>"
            "</div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="AI Writing Auditor", layout="wide")
    st.title("Local AI Writing Auditor")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Settings")
        model = st.selectbox("Model", ["mistral", "llama3.2:3b", "phi4"])
        mode = st.radio("Mode", ["rewrite", "detect-only"])
        st.divider()
        st.caption("Traces visible in Langfuse after each run.")

    # --- Main panels ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Input")
        text = st.text_area("Paste article text", height=400, placeholder="Paste your article here...")
        run = st.button("Analyze", type="primary")

    with col_right:
        st.subheader("Flagged Sentences")
        flagged_placeholder = st.empty()
        flagged_placeholder.info("Flagged sentences will appear here after analysis.")

    # --- Run pipeline ---
    if run and not text:
        st.warning("Please paste article text before running analysis.")
        return

    if run and text:
        from src.agents.auditor import AuditorAgent
        from src.agents.rewriter import RewriterAgent

        article_id = _article_id(text)

        with st.spinner("Pass 1: Auditing…"):
            auditor = AuditorAgent(model=model)
            audit_report = auditor.run(text=text, article_id=article_id)

        with col_right:
            flagged_placeholder.empty()
            st.caption(
                f"Verdict: **{audit_report.verdict}** · {audit_report.flag_count} flags · {audit_report.category_count} categories"
            )
            _render_flagged_sentences(audit_report.flagged_sentences)

        if mode == "detect-only":
            st.divider()
            st.caption("detect-only mode — rewrite skipped.")
            return

        # --- Rewrite ---
        st.divider()
        with st.spinner(f"Rewriting {len(audit_report.flagged_sentences)} flagged sentences…"):
            rewriter = RewriterAgent(model=model)
            rewrite_report = rewriter.run(
                flagged_sentences=audit_report.flagged_sentences,
                article_id=article_id,
                original_text=text,
            )

        st.subheader("Rewritten Version")
        st.text_area(
            label="Rewritten article",
            value=rewrite_report.full_rewritten_text,
            height=300,
            label_visibility="collapsed",
        )

        if rewrite_report.rewrites:
            with st.expander("What Changed"):
                for r in rewrite_report.rewrites:
                    st.markdown(f"- **{r.sentence_id}**: {r.change_summary}")

        # --- Pass 2 ---
        with st.spinner("Pass 2: Re-auditing rewritten text…"):
            pass2_report = auditor.run(
                text=rewrite_report.full_rewritten_text,
                article_id=f"{article_id}_pass2",
            )

        with st.expander("Second-Pass Audit"):
            if not pass2_report.flagged_sentences:
                st.success("No surviving patterns. Rewrite is clean.")
            else:
                st.warning(f"{pass2_report.flag_count} pattern(s) survived the rewrite:")
                _render_flagged_sentences(pass2_report.flagged_sentences)


if __name__ == "__main__":
    main()
