# Github Actions Analytics

![Last Commit](https://img.shields.io/github/last-commit/neulabscom/github-actions-analytics/main)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/neulabscom/github-actions-analytics/blob/main/LICENSE)

This application allows you to view GitHub's "Usage Report" data.

It gives a generic overview of which users and repositories use actions the most and allows each repository to see how many and when workflows are executed.

It is built with [Streamlit](https://streamlit.io/), a Python library for building data apps, and pandas, a Python library for data analysis.

*GitHub Actions Analytics is in beta.*

## How does it work?

**Requirements**:

- Python >= 3.8

**Run the following command to start the application**:

```bash

$ chmod +x scripts/setup.sh && ./scripts/setup.sh

$ # *Download Github report and save in `src/reports/`

$ streamlit run src/main.py
```

* Read the [GitHub Docs](https://docs.github.com/en/billing/managing-billing-for-github-actions/viewing-your-github-actions-usage) for download "Usage Report"
