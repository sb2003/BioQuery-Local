from typing import Optional, Dict, Any, List

from Bio import Entrez, SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction


class BioTools:
    """Additional tools using BioPython"""

    def __init__(self, email: str = "sbatory@ucsc.edu") -> None:
        Entrez.email = email

    def fetch_sequence(self, gene_name: str, db: str = "nucleotide") -> Optional[str]:
        """Fetch sequence from NCBI (if internet available)"""
        try:
            handle = Entrez.esearch(db=db, term=gene_name, retmax=1)
            record = Entrez.read(handle)
            handle.close()

            if not record["IdList"]:
                return None

            seq_id = record["IdList"][0]
            handle = Entrez.efetch(
                db=db,
                id=seq_id,
                rettype="fasta",
                retmode="text",
            )
            sequence = SeqIO.read(handle, "fasta")
            handle.close()
            return str(sequence.seq)
        except Exception:
            return None

    def gc_content(self, sequence: str) -> Dict[str, Any]:
        """Calculate GC content and simple sliding-window GC"""
        seq = Seq(sequence.upper().replace("\n", ""))
        # gc_fraction returns 0–1, so multiply by 100
        gc_percent = gc_fraction(seq) * 100.0

        window_size = 10
        gc_windows: List[float] = []
        for i in range(0, len(seq) - window_size):
            window = seq[i : i + window_size]
            gc_windows.append(gc_fraction(window) * 100.0)

        return {
            "overall_gc": gc_percent,
            "length": len(seq),
            "gc_windows": gc_windows,
            "min_gc": min(gc_windows) if gc_windows else 0,
            "max_gc": max(gc_windows) if gc_windows else 0,
        }

    def sequence_stats(self, sequence: str) -> Dict[str, Any]:
        """Get basic sequence statistics"""
        seq = Seq(sequence.upper().replace("\n", ""))
        gc_percent = gc_fraction(seq) * 100.0
        return {
            "length": len(seq),
            "a_count": seq.count("A"),
            "t_count": seq.count("T"),
            "g_count": seq.count("G"),
            "c_count": seq.count("C"),
            "gc_content": gc_percent,
            "at_content": 100.0 - gc_percent,
        }

