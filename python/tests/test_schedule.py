import time
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from uagents.schedule import Cron


class TestCron(unittest.TestCase):
    def test_every_minute(self):
        delay = next(Cron("* * * * *").delays())
        self.assertGreater(delay, 0)
        self.assertLessEqual(delay, 60)

    def test_timezone(self):
        tz = ZoneInfo("Asia/Kolkata")
        cron = Cron("0 9 * * *", "Asia/Kolkata")
        self.assertEqual(cron.tz, tz)

        now = datetime.now(tz)
        expected = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if expected <= now:
            expected += timedelta(days=1)
        delay = next(cron.delays())
        self.assertAlmostEqual(delay, expected.timestamp() - time.time(), delta=1)

    def test_invalid_timezone(self):
        with self.assertRaises(ValueError):
            Cron("* * * * *", tz="Not/A_Timezone")

    def test_invalid(self):
        for expression in ["* * *", "60 * * * *", "a * * * *", "0 0 30 2 *"]:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                Cron(expression)


if __name__ == "__main__":
    unittest.main()
