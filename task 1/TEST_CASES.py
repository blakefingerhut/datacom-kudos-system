import os
import unittest
from process_data_final import DataProcessor

class BrokenKeysDict(dict):
    @property
    def keys(self):
        raise AttributeError("'dict' object has no attribute 'keys'")

class TestDataProcessorExportBug(unittest.TestCase):
    def test_export_customer_data_raises_dict_keys_error(self):
        """
        Reproduce old bug path:
        if value is a dict whose keys() is broken, export_customer_data should
        fail (old error log: 'dict' object has no attribute 'keys').
        """
        processor = DataProcessor("does_not_matter.csv")
        processor.customers = {
            "cust-1": BrokenKeysDict(
                name="Alice",
                email="alice@example.com",
                join_date="2024-01-01",
                total_spent=0,
                transaction_count=0,
            )
        }

        out_file = "tmp_customers_export.csv"
        if os.path.exists(out_file):
            os.remove(out_file)

        result = processor.export_customer_data(out_file, format="csv")

        # Bug reproduction check (old behavior is failure path).
        self.assertFalse(result, "Expected CSV export to fail due to keys() error")
        self.assertFalse(os.path.exists(out_file), "No output file should be written on failure")

        if os.path.exists(out_file):
            os.remove(out_file)

if __name__ == "__main__":
    unittest.main()