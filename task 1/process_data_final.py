#!/usr/bin/env python3
"""
Data Processing Script for Customer Analytics
This script processes customer transaction data and generates reports.
"""

import argparse
import csv
import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes customer transaction data and generates analytics reports."""

    def __init__(self, input_file: str):
        """Initialize the data processor with input file path."""
        self.input_file = input_file
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.transactions: List[Dict[str, Any]] = []

    def _parse_decimal(self, value: str, context: str = "amount") -> Optional[Decimal]:
        try:
            return Decimal(value.strip())
        except (InvalidOperation, AttributeError):
            logger.warning(f"Invalid {context}: {value}")
            return None

    def _validate_customer_row(self, row: Dict[str, str]) -> bool:
        required = ["customer_id", "name", "email", "join_date"]
        missing = [field for field in required if not row.get(field)]
        if missing:
            logger.warning(f"Skipping customer row with missing fields: {missing}")
            return False
        return True

    def _validate_transaction_row(self, row: Dict[str, str]) -> bool:
        required = ["transaction_id", "customer_id", "amount", "date", "category"]
        missing = [field for field in required if not row.get(field)]
        if missing:
            logger.warning(f"Skipping transaction row with missing fields: {missing}")
            return False
        if self._parse_decimal(row.get("amount", ""), "transaction amount") is None:
            logger.warning(f"Skipping transaction with invalid amount: {row.get('amount')}")
            return False
        return True

    def load_data(self) -> bool:
        """Load customer and transaction data from CSV files."""
        try:
            # Load customer data
            with open(self.input_file, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not self._validate_customer_row(row):
                        continue
                    customer_id = row["customer_id"].strip()
                    self.customers[customer_id] = {
                        "name": row["name"].strip(),
                        "email": row["email"].strip(),
                        "join_date": row["join_date"].strip(),
                        "total_spent": Decimal("0.00"),
                        "transaction_count": 0,
                    }
            logger.info(f"Loaded {len(self.customers)} customers")
            return True
        except FileNotFoundError:
            logger.error(f"Input file {self.input_file} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def process_transactions(self, transaction_file: str) -> bool:
        """Process transaction data and update customer records."""
        try:
            with open(transaction_file, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not self._validate_transaction_row(row):
                        continue
                    amount = self._parse_decimal(row["amount"], "transaction amount")
                    if amount is None:
                        continue
                    transaction = {
                        "transaction_id": row["transaction_id"].strip(),
                        "customer_id": row["customer_id"].strip(),
                        "amount": amount,
                        "date": row["date"].strip(),
                        "category": row["category"].strip(),
                    }
                    self.transactions.append(transaction)

                    # Update customer totals
                    customer_id = transaction["customer_id"]
                    if customer_id in self.customers:
                        self.customers[customer_id]["total_spent"] += amount
                        self.customers[customer_id]["transaction_count"] += 1
                    else:
                        logger.warning(
                            f"Transaction for unknown customer: {customer_id}"
                        )

            logger.info(f"Processed {len(self.transactions)} transactions")
            return True
        except FileNotFoundError:
            logger.error(f"Transaction file {transaction_file} not found")
            return False
        except Exception as e:
            logger.error(f"Error processing transactions: {e}")
            return False

    def calculate_customer_metrics(self) -> Dict[str, Any]:
        """Calculate various customer metrics and statistics."""
        if not self.customers:
            logger.error("No customer data available")
            return {}

        total_revenue = sum(cust["total_spent"] for cust in self.customers.values())
        metrics = {
            "total_customers": len(self.customers),
            "total_transactions": len(self.transactions),
            "total_revenue": float(total_revenue),
            "average_transaction_value": 0.0,
            "top_customers": [],
            "category_breakdown": {},
        }

        # Calculate average transaction value
        if metrics["total_transactions"] > 0:
            metrics["average_transaction_value"] = float(
                total_revenue / Decimal(metrics["total_transactions"])
            )

        # Find top customers by total spent
        customer_list = [
            {
                "customer_id": cid,
                "name": data.get("name"),
                "total_spent": float(data.get("total_spent", Decimal("0.0"))),
                "transaction_count": data.get("transaction_count", 0),
            }
            for cid, data in self.customers.items()
        ]
        customer_list.sort(key=lambda x: x["total_spent"], reverse=True)
        metrics["top_customers"] = customer_list[:10]

        # Calculate category breakdown
        for transaction in self.transactions:
            category = transaction["category"]
            if category not in metrics["category_breakdown"]:
                metrics["category_breakdown"][category] = 0
            metrics["category_breakdown"][category] += 1

        return metrics

    def find_matches(
        self, search_term: str, field: str = "name"
    ) -> List[Dict[str, Any]]:
        """Find customers matching the search term in the specified field."""
        matches = []
        search_term_lower = search_term.lower()

        for customer_id, customer_data in self.customers.items():
            if field in customer_data:
                field_value = str(customer_data[field]).lower()
                if search_term_lower in field_value:
                    matches.append({"customer_id": customer_id, **customer_data})

        return matches

    def generate_report(self, report_type: str, output_file: str) -> bool:
        """Generate various types of reports and save to file."""
        try:
            if report_type == "customer_summary":
                report_data = {
                    "generated_at": datetime.now().isoformat(),
                    "customers": list(self.customers.values()),
                }
            elif report_type == "metrics":
                report_data = {
                    "generated_at": datetime.now().isoformat(),
                    "metrics": self.calculate_customer_metrics(),
                }
            elif report_type == "transactions":
                report_data = {
                    "generated_at": datetime.now().isoformat(),
                    "transactions": self.transactions,
                }
            else:
                logger.error(f"Unknown report type: {report_type}")
                return False

            # Save report to file
            with open(output_file, "w") as file:
                json.dump(report_data, file, indent=2)

            logger.info(f"Generated {report_type} report: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False

    def export_customer_data(self, output_file: str, format: str = "csv") -> bool:
        """Export customer data in specified format."""
        try:
            if format == "csv":
                with open(output_file, "w", newline="", encoding="utf-8") as file:
                    if self.customers:
                        fieldnames = ["customer_id"] + list(
                            next(iter(self.customers.values())).keys()
                        )
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()

                        for customer_id, data in self.customers.items():
                            safe_data = data.copy()
                            if isinstance(safe_data.get("total_spent"), Decimal):
                                safe_data["total_spent"] = float(safe_data["total_spent"])
                            row = {"customer_id": customer_id, **safe_data}
                            writer.writerow(row)
            elif format == "json":
                with open(output_file, "w", encoding="utf-8") as file:
                    json.dump(
                        {cid: {
                            **{
                                k: (float(v) if isinstance(v, Decimal) else v)
                                for k, v in data.items()
                            }
                        } for cid, data in self.customers.items()},
                        file,
                        indent=2,
                    )
            else:
                logger.error(f"Unsupported format: {format}")
                return False

            logger.info(f"Exported customer data to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False


def main():
    """Main function to run the data processing pipeline."""
    parser = argparse.ArgumentParser(description="Customer data analytics pipeline")
    parser.add_argument("--customers", default="customers.csv", help="Customer CSV input file")
    parser.add_argument("--transactions", default="transactions.csv", help="Transaction CSV input file")
    parser.add_argument("--output-dir", default=".", help="Directory for output files")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processor = DataProcessor(str(args.customers))

    if not processor.load_data():
        logger.error("Failed to load customer data")
        return

    if not processor.process_transactions(str(args.transactions)):
        logger.error("Failed to process transactions")
        return

    processor.generate_report("customer_summary", str(output_dir / "customer_summary.json"))
    processor.generate_report("metrics", str(output_dir / "metrics.json"))
    processor.generate_report("transactions", str(output_dir / "transactions.json"))

    processor.export_customer_data(str(output_dir / "customers_export.csv"), "csv")
    processor.export_customer_data(str(output_dir / "customers_export.json"), "json")

    logger.info("Data processing completed successfully")


if __name__ == "__main__":
    main()
