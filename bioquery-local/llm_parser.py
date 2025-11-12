import json
import re

import ollama


class LocalLLMParser:
    """Parse natural language queries using Ollama"""

    def __init__(self, model: str = "phi3:mini") -> None:
        self.model = model
        self.client = ollama.Client()

        # Description of tools for the LLM to choose from
        self.tools_description = """
Available bioinformatics tools:
- translate: Convert DNA to protein sequence
- reverse: Get reverse complement of DNA
- find_orfs: Find open reading frames in DNA
- align: Align two sequences
- pattern: Find specific pattern in sequence
- restriction: Find restriction enzyme sites
- gc_content: Calculate GC content percentage
- sixframe: Translate in all six reading frames
"""

    def parse_query(self, user_query: str) -> dict:
        """
        Use the local LLM to parse a natural-language query into:
        - tool
        - sequence (if present)
        - gene_name (if present)
        - parameters (dict)
        """
        prompt = f"""You are a bioinformatics assistant. Parse this query
and extract:
1. The tool to use (from the list below)
2. The sequence(s) or gene name(s) involved
3. Any additional parameters

{self.tools_description}

User query: {user_query}

Respond in JSON format:
{{
  "tool": "tool_name",
  "sequence": "DNA_or_protein_sequence",
  "gene_name": "gene_if_mentioned",
  "parameters": {{}}
}}

If the query contains a DNA sequence (letters ATCG), extract it.
Be concise and accurate.
"""

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
            )
            response_text = response["response"]

            # Try to extract a JSON object from the model output
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Fallback
            return self.simple_parse(user_query)
        except Exception as e:
            print(f"LLM parsing failed: {e}")
            return self.simple_parse(user_query)

    def simple_parse(self, query: str) -> dict:
        """
        Fallback simple parser if LLM fails:
        - Roughly detect DNA sequence
        - Choose tool based on keywords
        """
        query_lower = query.lower()

        # Extract DNA sequences (>=10 bases)
        seq_pattern = r"[ATCG]{10,}"
        seq_match = re.search(seq_pattern, query.upper())

        result = {
            "tool": None,
            "sequence": seq_match.group() if seq_match else None,
            "gene_name": None,
            "parameters": {},
        }

        if "translate" in query_lower:
            result["tool"] = "translate"
        elif "reverse" in query_lower or "complement" in query_lower:
            result["tool"] = "reverse"
        elif "orf" in query_lower or "reading frame" in query_lower:
            result["tool"] = "find_orfs"
        elif "pattern" in query_lower or "motif" in query_lower:
            result["tool"] = "pattern"
        elif "restriction" in query_lower or "enzyme" in query_lower:
            result["tool"] = "restriction"
        elif "gc" in query_lower:
            result["tool"] = "gc_content"

        return result

