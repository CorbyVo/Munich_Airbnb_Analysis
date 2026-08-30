# n8n Automation

This project uses a local n8n workflow to automate the Munich Airbnb data pipeline.

## Workflow Overview

The n8n workflow contains:

1. Manual Trigger
2. Schedule Trigger
3. Execute Command

The Manual Trigger is used for testing the workflow manually.

The Schedule Trigger is used for weekly automation.

The Execute Command node runs a local Windows batch file, which starts the Python pipeline.

## Command Used by n8n

The Execute Command node runs this command:

```powershell
cmd /c call "D:\PycharmProjects\Munich_Airbnb_Analysis\scripts\run_pipeline_n8n.bat" --force-download
```

The `--force-download` option tells the Python pipeline to download or refresh the latest available Inside Airbnb Munich data before running the analysis.

## What the Workflow Triggers

The n8n workflow does not perform the data analysis itself.

Instead, it triggers the local Python pipeline. The Python pipeline then:

- downloads or refreshes the latest available Inside Airbnb Munich data
- overwrites local raw source files in `data/raw/`
- cleans and transforms the Airbnb listing dataset
- updates the local cleaned SQLite dataset
- runs the exploratory analysis
- runs the budget-vs-distance analysis
- updates generated CSV outputs in `results/`
- updates chart outputs in `images/`
- regenerates `README.md` from `README_template.md`

## Local n8n Setup

n8n is installed locally for this project using npm.

To install the local Node.js dependencies, run:

```powershell
npm install
```

To start n8n locally, run:

```powershell
scripts\start_n8n.bat
```

Then open n8n in the browser:

```text
http://localhost:5678
```

The `start_n8n.bat` script starts n8n with the Execute Command node enabled.

## Workflow File

The exported n8n workflow is stored in:

```text
workflows/munich_airbnb_n8n_workflow.json
```

This makes the automation workflow visible in the GitHub repository.

## Important Limitation

This is a local automation setup.

The scheduled workflow only runs when:

- the laptop is turned on
- n8n is running
- the workflow is active

For always-on automation, n8n would need to run on a server, cloud instance, or background service.