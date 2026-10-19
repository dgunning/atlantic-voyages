"""voyages: a Python library for the SlaveVoyages databases.

See https://www.slavevoyages.org for the source data. Data transcribed
from historical documents is public domain; imputed fields and the
Estimates database are licensed CC BY-NC 4.0 by SlaveVoyages. See NOTICE.
"""

from voyages.citation import citation
from voyages.config import data_dir

__all__ = ["citation", "data_dir", "__version__"]
__version__ = "0.1.0"
