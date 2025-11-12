import subprocess
import tempfile
import os
from pathlib import Path


class EMBOSSWrapper:
    """Wrapper for common EMBOSS tools"""

    def __init__(self) -> None:
        # Map natural language-ish names to EMBOSS commands
        self.tool_map = {
            "translate": "transeq",
            "reverse": "revseq",
            "orf": "getorf",
            "align": "needle",
            "pattern": "fuzznuc",
            "restriction": "restrict",
            "shuffle": "shuffleseq",
            "info": "infoseq",
            "sixframe": "sixpack",
        }
        self.check_emboss()

    def check_emboss(self) -> bool:
        """Verify EMBOSS tools are available"""
        try:
            result = subprocess.run(
                ["embossversion"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"EMBOSS found: {result.stdout.strip()}")
            return True
        except Exception:
            print(
                "EMBOSS not found. Install with: conda install -c bioconda emboss"
            )
            return False

    def run_emboss_tool(self, tool: str, input_seq: str, **kwargs) -> str:
        """
        Generic EMBOSS tool runner.

        Writes the input sequence to a temporary FASTA file,
        calls the EMBOSS tool, reads the output file,
        and then cleans up temp files.
        """
        # temp input / output files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fasta", delete=False
        ) as f_in:
            f_in.write(f">Query\n{input_seq}\n")
            f_in.flush()
            input_path = f_in.name

        with tempfile.NamedTemporaryFile(
            mode="r", suffix=".out", delete=False
        ) as f_out:
            output_path = f_out.name

        cmd = [tool, input_path, output_path]

        # Add additional EMBOSS parameters as -key value
        for key, value in kwargs.items():
            cmd.extend([f"-{key}", str(value)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return f"Error running {tool}:\n{result.stderr}"

            # Read output file
            with open(output_path, "r") as out_f:
                output_text = out_f.read()
            return output_text
        except Exception as e:
            return f"Error running {tool}: {e}"
        finally:
            # Clean up temp files
            try:
                os.unlink(input_path)
            except OSError:
                pass
            try:
                os.unlink(output_path)
            except OSError:
                pass

    def translate(self, sequence: str, frame: int = 1) -> str:
        """Translate DNA to protein using transeq, with no header"""
        raw = self.run_emboss_tool("transeq", sequence, frame=frame)
        # strip FASTA header lines and blanks
        lines = [
                line.strip()
                for line in raw.splitlines()
                if line.strip() and not line.startswith(">")
        ]
        return "\n".join(lines)

    def sixframe(self, sequence: str) -> str:
        """Six-frame translation using EMBOSS transeq (-frame 6) (Sixpack was hanging). 
        Automatically relabels frames in output headers."""
        raw_output = self.run_emboss_tool("transeq", sequence, frame="6")

        # Replace generic >Query_N headers with clearer Frame labels
        replacements = {
            ">Query_1": ">Frame +1",
            ">Query_2": ">Frame +2",
            ">Query_3": ">Frame +3",
            ">Query_4": ">Frame -1",
            ">Query_5": ">Frame -2",
            ">Query_6": ">Frame -3",
        }

        for old, new in replacements.items():
            raw_output = raw_output.replace(old, new)

        return raw_output

    def reverse_complement(self, sequence: str) -> str:
        """Get reverse complement using revseq, with a nicer header"""
        raw = self.run_emboss_tool("revseq", sequence)

        # Split into non-empty lines
        lines = [line.strip() for line in raw.splitlines() if line.strip()]

        # Drop the EMBOSS header if present (e.g. ">Query Reversed:")
        if lines and lines[0].startswith(">"):
            lines = lines[1:]

        seq = "\n".join(lines)
        return f"Reverse complement:\n{seq}"

    def find_orfs(self, sequence: str, minsize: int = 75) -> str:
        """Find ORFs using getorf"""
        return self.run_emboss_tool("getorf", sequence, minsize=minsize)

    def find_pattern(self, sequence: str, pattern: str) -> str:
        """Find sequence pattern using fuzznuc"""
        return self.run_emboss_tool("fuzznuc", sequence, pattern=pattern)

    def restriction_sites(self, sequence: str) -> str:
        """
        Find restriction sites without using EMBOSS restrict (which was veeeeery broken).
        We scan for a few common enzymes: EcoRI, NotI, XbaI, BamHI.
        """
        seq = sequence.upper().replace("\n", "")

        sites = {
            "EcoRI": "GAATTC",
            "NotI":  "GCGGCCGC",
            "XbaI":  "TCTAGA",
            "BamHI": "GGATCC",
        }

        hits = []
        for name, motif in sites.items():
            start = 0
            while True:
                i = seq.find(motif, start)
                if i == -1:
                    break
                # 1-based index for biologist-friendly coordinates
                hits.append(f"{name} ({motif}) at position {i + 1}")
                start = i + 1

        if not hits:
            return "No EcoRI/NotI/XbaI/BamHI sites found in the given sequence."

        return "\n".join(hits)



