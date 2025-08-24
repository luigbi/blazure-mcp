import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to find mcp_azure_server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_azure_server.server import get_recommendations, get_subscription_details, get_cost_analysis, get_budgets, get_usage_details, get_price_sheet, get_billing_summary_resource

# Create export directory
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(EXPORT_DIR, exist_ok=True)

async def main():
	# Helper function to export results to text files
	def export_result(filename, result):
		filepath = os.path.join(EXPORT_DIR, filename)
		with open(filepath, "w", encoding="utf-8") as f:
			f.write(str(result))
		print(f"Exported to: {filepath}")


	print("Get a summary of current billing for the subscription.")
	summary_resource = await get_billing_summary_resource()
	print(summary_resource)
	export_result("get_billing_summary_resource.txt", summary_resource)

	print("_______________________________________________________________________")
	print("Subscription details:")
	subscription = await get_subscription_details()
	print(subscription)
	export_result("subscription_details.txt", subscription)

	
	print("_______________________________________________________________________")
	print("\nGet top 10 recommendations for the subscription.")
	recommendations = await get_recommendations()
	print(recommendations)
	export_result("recommendations.txt", recommendations)
	
	
	print("_______________________________________________________________________")
	print("\nGet all budgets for the subscription.")
	budgets = await get_budgets()
	print(budgets)
	export_result("budgets.txt", budgets)

	print("_______________________________________________________________________")
	print("\nGet usage details for the subscription.")
	usage_details = await get_usage_details("2025-01-01", "2025-08-18")
	print(usage_details)
	export_result("usage_details.txt", usage_details)

	print("_______________________________________________________________________")
	print("\nGet cost analysis for the subscription")
	cost_analysis = await get_cost_analysis("Custom", "Daily", None, "2025-01-01", "2025-08-18")
	print(cost_analysis)
	export_result("cost_analysis.txt", cost_analysis)
	
	print("_______________________________________________________________________")
	print("\nGet the price sheet for the subscription.")
	price_sheet = await get_price_sheet()
	print(price_sheet)
	export_result("price_sheet.txt", price_sheet)

	

if __name__ == "__main__":
	asyncio.run(main())