import os
import sys

import pandas as pd
import streamlit as st


def load(report_path: str):
    if not os.path.isfile(report_path):
        raise FileNotFoundError(f'Report not found: {report_path}')

    dataset = pd.read_csv(report_path)
    dataset['Actions Workflow'] = dataset['Actions Workflow'].map(
        lambda x: x.split('/')[-1] if type(x) == str else x)
    dataset.drop(dataset[dataset.Product != 'Actions'].index, inplace=True)

    return dataset


def stats(filename_selected):
    def _all_users():
        data = dataset.groupby(['Username']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    def _all_repositories():
        data = dataset.groupby(['Repository Slug']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    def _by_action_workflow(name: str):
        data = dataset.where(dataset['Repository Slug'] == name).groupby(
            ['Actions Workflow']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity', 'Repository Slug']
        )
        return chart

    def _by_date(name: str):
        data = dataset.where(dataset['Repository Slug'] == name).groupby(
            ['Date']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity', 'Repository Slug']
        )
        return chart

    def _by_username(name: str):
        data = dataset.where(dataset['Repository Slug'] == name).groupby(
            ['Username']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    dataset = load(f'src/reports/{filename_selected}')

    st.write('## Overview')
    overview_users, overview_repositories = st.tabs(
        ['🗃 All Users', '📈 All Repositories'])
    overview_users.bar_chart(_all_users())
    overview_repositories.area_chart(_all_repositories())

    for name, value in dataset.groupby(['Repository Slug']).all().iterrows():
        st.write('## Repository ' + name)
        workflow, timestamp, users = st.tabs(
            ['🗃 Actions', '📈 Date', '👩‍💻 Users'])

        workflow.write('**Usage of workflows for the repository**')
        workflow.bar_chart(_by_action_workflow(name))

        timestamp.write('**Usage of workflows for the repository by date**')
        timestamp.line_chart(_by_date(name))

        users.write('**Usage of workflows for the repository by users**')
        users.area_chart(_by_username(name))


def homepage():
    st.write('# GitHub Actions Analytics 📊')

    st.markdown(
        """
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

    """
    )

    st.write('## Report')
    reports = [file for file in os.listdir(
        'src/reports') if file.endswith('.csv')]
    filename_selected = st.selectbox(
        'How would you like to be contacted?', reports)
    if filename_selected:
        st.write('You selected:', filename_selected)
        stats(filename_selected)


def main():
    page_names_to_funcs = {
        'Home': homepage,
        'Stats': stats,
    }

    selectbox = st.sidebar.selectbox('Select page', page_names_to_funcs.keys())
    page_names_to_funcs[selectbox]()


if __name__ == '__main__':
    sys.exit(main())
