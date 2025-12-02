import re
from typing import Any, Dict

from emboss_wrapper import EMBOSSWrapper
from llm_parser import LocalLLMParser
from bio_tools import BioTools

# Accept DNA/RNA + IUPAC ambiguity codes
_IUPAC = set("ACGTURYKMSWBDHVN")

def _clean_seq_line(s: str) -> str:
    # keep letters only; convert U->T
    s = "".join(ch for ch in s.upper() if ch.isalpha())
    s = s.replace("U", "T")
    return "".join(ch for ch in s if ch in _IUPAC)

def extract_sequences_from_text(text: str) -> list[str]:
    """
    Extract sequences whether the user pasted FASTA anywhere in the message
    or included bare multi-line DNA. Returns 0..N sequences.
    """
    seqs: list[str] = []

    # --- FASTA mode (handles prose before/after FASTA) ---
    in_rec = False
    cur: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if cur:
                seqs.append("".join(cur))
                cur = []
            in_rec = True
            continue
        if in_rec:
            cleaned = _clean_seq_line(line)
            if cleaned:
                cur.append(cleaned)
    if cur:
        seqs.append("".join(cur))

    # --- Bare DNA mode (if no FASTA found) ---
    if not seqs:
        for m in re.finditer(r"[ACGTURYKMSWBDHVN]{10,}", text, flags=re.I):
            seqs.append(_clean_seq_line(m.group(0)))

    # Filter very short/empty
    seqs = [s for s in seqs if len(s) >= 10]
    return seqs

def mask_text_for_llm(text: str) -> str:
    """
    Mask long sequence runs & FASTA headers so the LLM only decides the tool.
    """
    # Mask FASTA header lines anywhere
    masked = re.sub(r"^\s*>.*$", ">[HEADER]", text, flags=re.M)
    # Mask long contiguous sequence runs
    masked = re.sub(r"[ACGTURYKMSWBDHVN]{20,}", "[SEQUENCE]", masked, flags=re.I)
    return masked

class BioQueryLocal:
    """Main application combining all components"""

    def __init__(self) -> None:
        self.emboss = EMBOSSWrapper()
        self.llm = LocalLLMParser()
        self.biotools = BioTools()

        # Example sequences for testing
        self.example_sequences = {
            "test_dna": "ATGGCGAATTACGTAGCTAGCTAGCGCGCTATAGCGCGCTAA",
            "brca1_fragment": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCA",
            "p53_fragment": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGA",
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query"""

        # Extract sequences (handles prose + FASTA anywhere in the text)
        seqs = extract_sequences_from_text(query)

        # Mask long sequences so the LLM focuses on intent words
        masked_query = mask_text_for_llm(query)

        # Parse query with LLM using the masked text
        parsed = self.llm.parse_query(masked_query)

        # Prefer our extractor over the LLM’s guess
        # (choose the first sequence; or use max(seqs, key=len) if you prefer the longest)
        sequence = seqs[0] if seqs else parsed.get("sequence")


        # If gene name was identified, try fetching from NCBI
        gene_name = parsed.get("gene_name")
        if not sequence and gene_name:
            fetched = self.biotools.fetch_sequence(gene_name)
            if fetched:
                sequence = fetched
            else:
                # Fallback: see if gene name matches our examples
                gene_lower = gene_name.lower()
                for key, seq in self.example_sequences.items():
                    if gene_lower in key.lower():
                        sequence = seq
                        break

        # If still no sequence, try to directly pull a DNA stretch from the query
        if not sequence:
            seq_match = re.search(r"[ATCG]{10,}", query.upper())
            if seq_match:
                sequence = seq_match.group()

        if not sequence:
            return {
                "success": False,
                "error": "No sequence found. Please provide a DNA sequence or gene name.",
                "parsed": parsed,
            }

        # Execute the appropriate tool
        tool = parsed.get("tool")
        result: Any

        if tool == "translate":
            result = self.emboss.translate(sequence)
        elif tool == "reverse":
            result = self.emboss.reverse_complement(sequence)
        elif tool == "find_orfs":
            result = self.emboss.find_orfs(sequence)
        elif tool == "pattern":
            # Try LLM-provided motif first
            pattern = parsed.get("parameters", {}).get("pattern")

            if not pattern:
                # Pull a motif directly from the user text (3–20 bp; allow IUPAC codes)
                cands = re.findall(r"[ACGTURYKMSWBDHVN]{3,20}", query, flags=re.I)
                # Prefer short motifs (avoid the whole pasted sequence)
                cands = [c.upper() for c in cands if 3 <= len(c) <= 20]
                if cands:
                    pattern = cands[0]  # or max(cands, key=len) if you prefer the longest

            # Final fallback
            if not pattern:
                pattern = "ATG"

            result = self.emboss.find_pattern(sequence, pattern)

        elif tool == "restriction":
            result = self.emboss.restriction_sites(sequence)
        elif tool == "gc_content":
            result = self.biotools.gc_content(sequence)
        elif tool == "sixframe":
            result = self.emboss.sixframe(sequence)
        else:
            result = f"Unknown tool: {tool}"

        short_seq = (
            sequence[:50] + "..."
            if len(sequence) > 50
            else sequence
        )

        return {
            "success": True,
            "tool": tool,
            "sequence": short_seq,
            "result": result,
            "parsed": parsed,
        }

    def get_examples(self) -> list[str]:
        """Return example queries for users"""
        return [
            "Translate the sequence ATGGCGAATTACGTAGCT",
            "What is the reverse complement of ATCGATCGATCG?",
            "Find open reading frames in "
            + self.example_sequences["test_dna"],
            "Calculate GC content of GCGCGCATATATATGCGCGC",
            "Find restriction sites in GAATTCGCGGCCGCTCTAGAACTAGTGGATC",
            "Find ATG patterns in ATGATGATGATGATGATG",
            "Translate BRCA1 fragment",
            "Get six-frame translation of p53_fragment",
        ]
