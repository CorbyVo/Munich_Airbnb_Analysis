# n8n Automation

This project uses a local n8n workflow to automate the Munich Airbnb data pipeline.

## Workflow

The workflow contains:

1. Manual Trigger
2. Schedule Trigger
3. Execute Command

The Manual Trigger is used for testing.
The Schedule Trigger is used for automatic refreshes.

## Command Used

```powershell
cmd /c call "D:\PycharmProjects\Munich_Airbnb_Analysis\scripts\run_pipeline_n8n.bat" --force-download