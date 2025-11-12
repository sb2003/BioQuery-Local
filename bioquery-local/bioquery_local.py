import re
from typing import Any, Dict

from emboss_wrapper import EMBOSSWrapper
from llm_parser import LocalLLMParser
from bio_tools import BioTools


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

        # Parse query with LLM
        parsed = self.llm.parse_query(query)

        # Get sequence (from LLM parse)
        sequence = parsed.get("sequence")

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
            pattern = parsed.get("parameters", {}).get("pattern", "ATG")
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

