from datetime import datetime
from typing import Any

import pytz

class TimeUtil:
    @staticmethod
    def now() -> datetime:
        return datetime.now(pytz.timezone('America/Los_Angeles'))

    @staticmethod
    def localize(dt: Any) -> datetime:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, '%Y-%m-%d')
        
        # Use localize() instead of replace() for proper timezone handling
        pacific_tz = pytz.timezone('America/Los_Angeles')
        if dt.tzinfo is None:
            # For naive datetime, use localize() to properly set timezone
            return pacific_tz.localize(dt)
        else:
            # For aware datetime, convert to Pacific timezone
            return dt.astimezone(pacific_tz)

