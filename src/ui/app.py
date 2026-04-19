import streamlit as st


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

    with st.sidebar:
        st.header("Settings")
        model = st.selectbox("Model", ["mistral", "llama3.2:3b", "phi4"])
        mode = st.radio("Mode", ["rewrite", "detect-only"])
        st.divider()
        st.caption("Traces visible in Langfuse after each run.")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Input")
        text = st.text_area("Paste article text", height=400, placeholder="Paste your article here...")
        run = st.button("Analyze", type="primary")

    with col_right:
        st.subheader("Flagged Sentences")
        flagged_placeholder = st.empty()
        flagged_placeholder.info("Flagged sentences will appear here after analysis.")

    if run and not text:
        st.warning("Please paste article text before running analysis.")
        return

    if run and text:
        from src.pipeline import run_detect_only, run_full_pipeline

        if mode == "detect-only":
            with st.spinner("Pass 1: Auditing…"):
                result = run_detect_only(text=text, model=model)

            with col_right:
                flagged_placeholder.empty()
                st.caption(
                    f"Verdict: **{result.pass1.verdict}** · "
                    f"{result.pass1.flag_count} flags · {result.pass1.category_count} categories"
                )
                _render_flagged_sentences(result.pass1.flagged_sentences)

            st.divider()
            st.caption("detect-only mode — rewrite skipped.")
            return

        with st.spinner("Running full pipeline (pass 1 → rewrite → pass 2)…"):
            result = run_full_pipeline(text=text, model=model)

        with col_right:
            flagged_placeholder.empty()
            st.caption(
                f"Verdict: **{result.pass1.verdict}** · "
                f"{result.pass1.flag_count} flags · {result.pass1.category_count} categories"
            )
            _render_flagged_sentences(result.pass1.flagged_sentences)

        st.divider()
        st.subheader("Rewritten Version")
        st.text_area(
            label="Rewritten article",
            value=result.rewrite.full_rewritten_text,
            height=300,
            label_visibility="collapsed",
        )

        if result.rewrite.rewrites:
            with st.expander("What Changed"):
                for r in result.rewrite.rewrites:
                    st.markdown(f"- **{r.sentence_id}**: {r.change_summary}")

        with st.expander("Second-Pass Audit"):
            if not result.pass2.flagged_sentences:
                st.success("No surviving patterns. Rewrite is clean.")
            else:
                st.warning(f"{result.pass2.flag_count} pattern(s) survived the rewrite:")
                _render_flagged_sentences(result.pass2.flagged_sentences)


if __name__ == "__main__":
    main()
