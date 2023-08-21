import json
import os
import unittest

from uagents.storage import KeyValueStore


class TestStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.name = "test"
        self.filename = os.path.join(os.getcwd(), f"{self.name}_data.json")
        return super().setUp()

    def test_key_value_store(self):
        storage = KeyValueStore(self.name)

        self.assertEqual(
            os.path.isfile(self.filename), False, "file should not be created yet"
        )

        key = "key"
        value = "value"
        store = {key: value}
        storage.set(key, value)

        self.assertEqual(os.path.isfile(self.filename), True, "file should exist now")
        self.assertEqual(storage.get(key), value)

        with open(self.filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.assertEqual(data, store)

        new_value = "new_value"
        store[key] = new_value
        storage.set(key, new_value)

        storage = KeyValueStore(self.name)
        self.assertEqual(storage.get(key), new_value)

        storage.remove(key)
        self.assertIsNone(storage.get(key))

    def tearDown(self) -> None:
        os.remove(self.filename)
        return super().tearDown()


if __name__ == "__main__":
    unittest.main()
