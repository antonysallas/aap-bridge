"""AAP Bridge - Migrate from source AAP to target AAP."""

import logging
import warnings

__version__ = "0.1.0"
__author__ = "AAP Migration Team"
__license__ = "Apache-2.0"

# Suppress verbose third-party library logging
# These libraries generate excessive console output that clutters migration progress
logging.getLogger("awxkit").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("alembic").setLevel(logging.WARNING)

# Suppress common warnings from third-party libraries
warnings.filterwarnings("ignore", module="awxkit")
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="httpx")
