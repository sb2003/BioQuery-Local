import json

import streamlit as st

from bioquery_local import BioQueryLocal


st.set_page_config(
    page_title="BioQuery Local",
    page_icon="🧬",
    layout="wide",
)

# Initialize session state
if "bq" not in st.session_state:
    st.session_state.bq = BioQueryLocal()
if "history" not in st.session_state:
    st.session_state.history = []
if "query" not in st.session_state:
    st.session_state.query = ""

bq: BioQueryLocal = st.session_state.bq

# Header
st.title("🧬 BioQuery Local")
st.markdown("Natural language bioinformatics — running entirely on your machine!")

# Sidebar
with st.sidebar:
    st.markdown("### 🛠 Available Tools")
    st.markdown(
        """
- **Translate**: DNA to protein
- **Reverse Complement**: Reverse and complement DNA
- **Find ORFs**: Locate open reading frames
- **GC Content**: Calculate GC percentage
- **Restriction Sites**: Find enzyme cut sites
- **Pattern Search**: Find sequence patterns
"""
    )

    st.markdown("### 💡 Example Queries")
    examples = bq.get_examples()
    for ex in examples[:5]:
        if st.button(ex[:30] + "...", key=ex):
            st.session_state.query = ex

    st.markdown("### 📚 Example Sequence")
    if st.button("Load Test DNA (PAE1265)"):
        st.session_state.query = bq.example_sequences["test_dna"]
    #if st.button("Load BRCA1 Fragment"):
    #    st.session_state.query = bq.example_sequences["brca1_fragment"]
    #if st.button("Load P53 Fragment"):
    #    st.session_state.query = bq.example_sequences["p53_fragment"]

# Main interface
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_area(
        "Enter your bioinformatics question or paste a sequence:",
        value=st.session_state.get("query", ""),
        height=120,
        placeholder="Try: 'Translate ATGGCGAAT' or 'Find ORFs in this sequence...'",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    process_button = st.button(
        "🔬 Process Query",
        type="primary",
        use_container_width=True,
    )
    clear_button = st.button("🗑 Clear", use_container_width=True)

if clear_button:
    st.session_state.query = ""
    st.session_state.history = []
    st.rerun()

if process_button and query:
    st.session_state.query = query
    with st.spinner("🤔 Understanding your query with local LLM..."):
        result = bq.process_query(query)
        st.session_state.history.append((query, result))

    if result.get("success"):
        st.success(f"✅ Executed: {result.get('tool')}")

        tab1, tab2, tab3 = st.tabs(
            ["📊 Results", "🔍 How it worked", "📝 Raw Output"]
        )

        with tab1:
            st.markdown("### Results")
            if (
                result.get("tool") == "gc_content"
                and isinstance(result.get("result"), dict)
            ):
                r = result["result"]
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(
                        "Overall GC%",
                        f"{r.get('overall_gc', 0):.2f}%",
                    )
                with c2:
                    st.metric("Sequence Length", r.get("length", 0))
                with c3:
                    st.metric(
                        "Min/Max GC",
                        f"{r.get('min_gc', 0):.1f}% / {r.get('max_gc', 0):.1f}%",
                    )
            else:
                out = result.get("result")
                if isinstance(out, str):
                    st.code(out, language="text")
                else:
                    st.json(out)

        with tab2:
            st.markdown("### Behind the Scenes")
            st.markdown(
                f"""
1. **Query received**: "{query[:100]}..."
2. **LLM parsing**: Local Ollama model identified the intent
3. **Tool selected**: `{result.get('tool')}`
4. **Sequence extracted**: {result.get('sequence')}
5. **EMBOSS/BioPython executed**: Tool ran locally on your machine
6. **Results returned**: Formatted for display
"""
            )
            with st.expander("🧠 LLM Parse Details"):
                st.json(result.get("parsed"))

        with tab3:
            st.markdown("### Raw Output")
            st.text(json.dumps(result, indent=2))
    else:
        st.error(f"❌ {result.get('error')}")
        with st.expander("Debug Information"):
            st.json(result.get("parsed"))

# History
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Query History")
    for i, (q, r) in enumerate(reversed(st.session_state.history[-5:])):
        label = f"Query {len(st.session_state.history) - i}: {q[:50]}..."
        with st.expander(label):
            st.json(r)

st.markdown("---")
st.caption("🏫 BME 110 — Running locally with EMBOSS, BioPython, and Ollama")
