#!/usr/bin/env python3
"""
Direct workflow runner for BPDB archive extraction
Bypasses CLI import issues and runs workflow directly
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def run_bpdb_workflow():
    """Run BPDB workflow using direct imports"""

    print("🚀 Starting BPDB Archive Workflow Execution")

    try:
        # Import components directly
        from providers.scrapers.bpdb_archive_provider import BPDBArchiveProvider
        from providers.storage.json_provider import JSONProvider
        from scraper_core.models import InitStepConfig, ExtractStepConfig, ConnectionConfig

        print("✅ Successfully imported scrapper framework components")

        # Load workflow configuration
        workflow_file = "examples/bpdb_simple_test.json"
        print(f"📄 Loading workflow: {workflow_file}")

        with open(workflow_file, 'r') as f:
            workflow_config = json.load(f)

        print(f"✅ Loaded workflow: {workflow_config['metadata']['name']}")

        # Initialize providers
        print("🔧 Initializing providers...")

        # Initialize scraping provider
        scraping_provider = BPDBArchiveProvider()
        print(f"   📊 Scraping provider: {scraping_provider.metadata.name}")

        # Initialize storage provider
        storage_provider = JSONProvider()
        print(f"   💾 Storage provider: {storage_provider.metadata.name}")

        # Connect providers
        connection_config = ConnectionConfig()
        await scraping_provider.initialize(connection_config)

        storage_config = workflow_config.get("storage", {}).get("config", {})
        storage_connection_config = ConnectionConfig()
        await storage_provider.connect(storage_connection_config)

        print("✅ Providers initialized successfully")

        # Execute workflow steps
        print("\n📋 Executing workflow steps...")

        context = None
        all_extracted_data = []

        for step in workflow_config["steps"]:
            step_id = step["id"]
            command = step["command"]
            config = step.get("config", {})

            print(f"\n🔄 Executing step: {step_id} ({command})")

            if command == "init":
                init_config = InitStepConfig(config=config)
                context = await scraping_provider.execute_init(init_config)
                print(f"   ✅ Init completed - found {context.metadata.get('total_pdfs', 0)} PDFs")

            elif command == "extract" and context:
                extract_config = ExtractStepConfig(config=config)
                extracted_data = await scraping_provider.execute_extract(extract_config, context)
                all_extracted_data.extend(extracted_data)
                print(f"   ✅ Extract completed - {len(extracted_data)} elements extracted")

        # Store results
        if all_extracted_data:
            print(f"\n💾 Storing {len(all_extracted_data)} extracted elements...")

            # Convert to storage format
            storage_data = []
            for element in all_extracted_data:
                storage_data.append({
                    "name": element.name,
                    "type": element.element_type,
                    "value": element.value,
                    "attributes": element.attributes
                })

            # Save via storage provider
            output_file = storage_config.get("output_file", "workflow_output.json")
            await storage_provider.store(storage_data)

            print(f"   ✅ Data stored successfully")

            # Also create a summary file
            summary = {
                "workflow_execution": {
                    "workflow_name": workflow_config["metadata"]["name"],
                    "execution_timestamp": "2025-09-14T12:30:00Z",
                    "total_elements": len(all_extracted_data),
                    "elements_by_table": {}
                },
                "elements": storage_data[:5]  # First 5 for preview
            }

            # Count elements by table
            for element in all_extracted_data:
                table_name = element.attributes.get("table_name", "unknown")
                summary["workflow_execution"]["elements_by_table"][table_name] = \
                    summary["workflow_execution"]["elements_by_table"].get(table_name, 0) + 1

            summary_file = "bpdb_workflow_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"   📊 Execution summary saved to: {summary_file}")

        # Cleanup
        await scraping_provider.cleanup()
        await storage_provider.disconnect()

        print(f"\n🎉 BPDB Workflow Execution Completed Successfully!")
        print(f"   📊 Total elements extracted: {len(all_extracted_data)}")
        print(f"   💾 Data saved to: {output_file}")
        print(f"   📋 Summary saved to: {summary_file}")

        # Show some results
        if all_extracted_data:
            print(f"\n📋 Sample Results:")
            sample = all_extracted_data[0]
            print(f"   🏷️  Name: {sample.name}")
            print(f"   📅 Date: {sample.attributes.get('date')}")
            print(f"   🏢 Table: {sample.attributes.get('table_name')}")
            print(f"   📏 Dimensions: {sample.attributes.get('rows')}×{sample.attributes.get('columns')}")
            print(f"   🔗 Source: {sample.attributes.get('source_pdf', 'N/A')[:50]}...")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 The scrapper framework may need to be installed properly")

    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    asyncio.run(run_bpdb_workflow())

if __name__ == "__main__":
    main()