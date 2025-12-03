**BioQuery Local — README**

**What it is** <br />
BioQuery Local is a tiny Streamlit app that lets you run common bioinformatics tasks on your laptop using EMBOSS, Biopython, and a local LLM via Ollama. No cloud calls. You can paste raw DNA/FASTA and ask in plain English.

**What it does** <br />
• Translate DNA to protein (EMBOSS transeq) <br />
• Reverse complement (EMBOSS revseq)<br />
• Find ORFs (EMBOSS getorf; default min ORF 75 aa)<br />
• GC content (overall and sliding window = 10)<br />
• Pattern search with mismatches (EMBOSS fuzznuc; forward + reverse)<br />
• Six-frame translation (transeq -frame 6; headers relabeled to +1,+2,+3,-1,-2,-3)<br />
• Restriction sites (built-in scanner for common enzymes: EcoRI, NotI, XbaI, BamHI, HindIII, KpnI, PstI, XhoI, NheI, SpeI, SacI). <br />

**What you need installed** <br />
• Conda (Miniforge/Anaconda) <br />
• Homebrew (for Ollama) <br />
• Ollama running locally, with the model phi3:mini pulled <br />
• EMBOSS (via conda)<br />
• Python packages: biopython, streamlit, ollama (Python client)<br />

**How to install and run** <br />

Copy this folder:<br />
  git clone https://github.com/sb2003/bioquery-local.git<br />
  cd bioquery-local<br />

Create the conda env:<br />
  conda env create -f environment.yml<br />
  conda activate bioquery<br />
  
Install bioinformatics tools:<br />
  conda install -c bioconda emboss biopython<br />
  conda install -c conda-forge streamlit pandas<br />
  pip install ollama<br />

Install and start Ollama, then pull the model:<br />
  brew install ollama<br />
  brew services start ollama<br />
  ollama pull phi3:mini<br />

First-run quick test (recommended right after activation):<br />
  conda activate bioquery<br />
  cd bioquery-local<br />
  python test_bioquery.py<br />

**Launch the app:** <br />
streamlit run app.py<br />

Make sure you are in /bioquery_local and (bioquery) conda environment <br />

**Model choice** <br />
By default the LLM parser uses phi3:mini. You can switch models by editing llm_parser.py (the LocalLLMParser init “model” argument).<br />

**Using the app** <br />
You can paste plain DNA or full FASTA anywhere in the text box (the app auto-extracts sequences and ignores headers). <br /> It’s fine to mix a command and a FASTA header on the same line; the app normalizes that for you.<br /><br /> _Examples:_<br />
Translate ATGGCGAATTACGTAGCT<br />
Find ORFs in >myseq … <FASTA…><br />
Find pattern GAATTC mismatch 1 in <sequence…><br />
Find restriction sites in <sequence…><br />
GC content of <sequence…><br />
Six-frame translation of <sequence…><br />

**Notes and limitations** <br />
• Restriction sites: uses a built-in list of common enzymes; for full enzyme catalogs use EMBOSS restrict with REBASE configured (not included here).<br />
• GC content window size is fixed at 10 bases in this build.<br />
• Everything runs locally; if Ollama isn’t running or the model isn’t pulled, parsing will fall back to a simple keyword parser.<br />

**Troubleshooting** <br />
• “LLM parsing failed” or it hangs at “Understanding your query”: make sure Ollama is running (brew services start ollama) and that you’ve pulled phi3:mini.<br />
• “EMBOSS not found”: ensure you activated the bioquery conda env and that emboss=6.6.0 is installed via environment.yml.<br />

**Project structure (key files)** <br />
app.py — Streamlit UI<br />
bioquery_local.py — query processing pipeline and sequence extraction<br />
emboss_wrapper.py — thin wrappers over EMBOSS tools and the built-in restriction scanner<br />
llm_parser.py — local LLM (Ollama) parser with a simple fallback<br />
bio_tools.py — small helpers (e.g., GC content)<br />
