import streamlit as st


def main() -> None:
    st.set_page_config(page_title="AI Writing Auditor", layout="wide")
    st.title("Local AI Writing Auditor")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Settings")
        model = st.selectbox("Model", ["mistral", "llama3.2:3b", "phi4"])
        mode = st.radio("Mode", ["rewrite", "detect-only"])
        st.divider()
        st.caption("Token stats will appear here during inference.")

    # --- Main panels ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Input")
        text = st.text_area("Paste article text", height=400, placeholder="Paste your article here...")
        run = st.button("Analyze", type="primary")

    with col_right:
        st.subheader("Flagged Sentences")
        st.info("Flagged sentences with tell category labels will appear here after analysis.")

    # --- Rewrite panel ---
    if run and text:
        st.divider()
        st.subheader("Rewritten Version")
        st.info("Rewritten article text will appear here.")

        with st.expander("Second-Pass Audit"):
            st.info("Patterns that survived the first rewrite will be listed here.")

    elif run and not text:
        st.warning("Please paste article text before running analysis.")

    # Suppress unused variable warnings — wired in implementation phase
    _ = model, mode


if __name__ == "__main__":
    main()
