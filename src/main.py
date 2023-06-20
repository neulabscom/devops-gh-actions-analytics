import os
import sys

import pandas as pd
import streamlit as st


def upload():
    uploaded_file = st.file_uploader('Choose a file')
    if uploaded_file is None:
        return

    df = parser(pd.read_csv(uploaded_file))

    stats(df)


def fromfile():
    st.write('## From Report')

    basepath = 'reports'

    reports = [file for file in os.listdir(basepath) if file.endswith('.csv')]

    reports.insert(0, None)

    filename_selected = st.selectbox(
        'How would you like to be contacted?', reports, 0)

    if not filename_selected:
        return None

    st.write('You selected:', filename_selected)

    report_path = os.path.join(basepath, filename_selected)

    if not os.path.isfile(report_path):
        raise FileNotFoundError(f'Report not found: {report_path}')

    df = parser(pd.read_csv(report_path))

    stats(df)


def parser(df: pd.DataFrame):
    df['Actions Workflow'] = df['Actions Workflow'].map(
        lambda x: x.split('/')[-1] if type(x) == str else x)
    df.drop(df[df.Product != 'Actions'].index, inplace=True)

    return df


def stats(df: pd.DataFrame):
    def _all_users():
        data = df.groupby(['Username']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    def _all_repositories():
        data = df.groupby(['Repository Slug']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    def _by_action_workflow(name: str):
        data = df.where(df['Repository Slug'] == name).groupby(
            ['Actions Workflow']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity', 'Repository Slug']
        )
        return chart

    def _by_date(name: str):
        data = df.where(df['Repository Slug'] == name).groupby(
            ['Date']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity', 'Repository Slug']
        )
        return chart

    def _by_username(name: str):
        data = df.where(df['Repository Slug'] == name).groupby(
            ['Username']).sum('Quantity')
        chart = pd.DataFrame(
            data,
            columns=['Quantity']
        )
        return chart

    st.write('## Overview')
    overview_users, overview_repositories = st.tabs(
        ['🗃 All Users', '📈 All Repositories'])
    overview_users.bar_chart(_all_users())
    overview_repositories.area_chart(_all_repositories())

    for name, value in df.groupby(['Repository Slug']).all().iterrows():
        st.write('## Repository ' + name)
        workflow, timestamp, users = st.tabs(
            ['🗃 Actions', '📈 Date', '👩‍💻 Users'])

        workflow.write('**Usage of workflows for the repository**')
        workflow.bar_chart(_by_action_workflow(name))

        timestamp.write('**Usage of workflows for the repository by date**')
        timestamp.line_chart(_by_date(name))

        users.write('**Usage of workflows for the repository by users**')
        users.area_chart(_by_username(name))


def config():
    st.set_page_config(
        page_title='GitHub Actions Analytics',
        page_icon='📊',
        initial_sidebar_state='expanded'
    )


def homepage():
    def _head():
        st.write('# GitHub Actions Analytics 📊')
        st.markdown(
            """
    ![Last Commit](https://img.shields.io/github/last-commit/neulabscom/github-actions-analytics/main)
    [![License](https://img.shields.io/github/license/neulabscom/github-actions-analytics)](https://github.com/neulabscom/github-actions-analytics/blob/main/LICENSE)

    This application allows you to view GitHub's "Usage Report" data.

    It gives a generic overview of which users and repositories use actions the most and allows each repository to see how many and when workflows are executed.

    It is built with [Streamlit](https://streamlit.io/), a Python library for building data apps, and pandas, a Python library for data analysis.


    Read the [GitHub Docs](https://docs.github.com/en/billing/managing-billing-for-github-actions/viewing-your-github-actions-usage) for download "Usage Report"

    *GitHub Actions Analytics is in beta.*
        """
        )

    def _content():
        upload()
        fromfile()

    def _footer():
        st.markdown(
            """
    ----

    #### Run from local?

    **Requirements**:

    - Python >= 3.8

    **Run the following command to start the application**:

    ```bash

    $ chmod +x scripts/setup.sh && ./scripts/setup.sh

    $ # Download Github report and save in `reports/` folder

    $ streamlit run src/main.py
    ```

    #### Powered by **Neulabs**

    Website: [neulabs.com](https://neulabs.com)

    Repository: [GitHub](https://github.com/neulabscom)

        """
        )

    _head()
    _content()
    _footer()


def main():
    config()
    homepage()


if __name__ == '__main__':
    sys.exit(main())
