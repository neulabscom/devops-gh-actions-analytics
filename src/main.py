import datetime
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

    df['date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

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

    def _print_invoces_cost(name: str, data: object, date: object):
        st.write(f'**{name}**')

        col_minute, col_total, col_difference = st.columns(3)
        col_minute.metric('Minutes', f"{data['invoce']['latest']['minute']} min",
                          f"{data['delta']['minute']} min", delta_color='inverse')
        col_total.metric('Total cost', f"{data['invoce']['latest']['total']}$",
                         f"{data['delta']['total']}$", delta_color='inverse')
        col_difference.metric(
            'Cost difference', f"{data['delta']['percent']} %", f'', delta_color='off')

        if not (data['invoce']['latest']['minute'] == 0 and data['invoce']['before_latest']['minute'] == 0):
            st.write(f'''
        Selected range
        - From {date["selected"][0].strftime("%Y-%m-%d")} to {date["selected"][1].strftime("%Y-%m-%d")}
        - Minutes included: {data["invoce"]["latest"]["minute_included"]}
        - Minutes runned: {data["invoce"]["latest"]["minute"]}
        - Total cost: {data["invoce"]["latest"]["total"]}$ ({data["invoce"]["latest"]["minute"] - data["invoce"]["latest"]["minute_included"]} * {data["invoce"]["latest"]["price"]} price per minute)
        ''')
            st.write(f'''
        {date['difference_in_day']} days before range
        - From {date["before"][0].strftime("%Y-%m-%d")} to {date["before"][1].strftime("%Y-%m-%d")}
        - Minutes included: {data["invoce"]["before_latest"]["minute_included"]}
        - Minutes runned: {data["invoce"]["before_latest"]["minute"]}
        - Total cost: {data["invoce"]["before_latest"]["total"]}$ ({data["invoce"]["before_latest"]["minute"] - data["invoce"]["before_latest"]["minute_included"]} * {data["invoce"]["before_latest"]["price"]} price per minute)
        ''')
            merged_data = pd.merge(data['invoce']['latest']['chart'], data['invoce']['before_latest']
                                   ['chart'], on='Date', suffixes=(' Latest', ' Before'), how='outer')
            st.line_chart(merged_data, use_container_width=True)

    def _cost_date_range():
        def _by_compute(latest_invoce_data: pd.DataFrame, before_invoce_data: pd.DataFrame, price: float, minute_included: int = 0):
            latest_invoce_result = latest_invoce_data.where(df['Price Per Unit ($)'] == price).groupby([
                'Date']).sum('Quantity').filter(['Quantity'])
            before_invoce_result = before_invoce_data.where(df['Price Per Unit ($)'] == price).groupby([
                'Date']).sum('Quantity').filter(['Quantity'])

            chart = pd.DataFrame(
                latest_invoce_result,
                columns=['Quantity']
            )
            before_chart = pd.DataFrame(
                before_invoce_result,
                columns=['Quantity']
            )

            minute = round(latest_invoce_result.values.sum(), 2)
            total = 0 if minute_included >= minute else round(
                (minute - minute_included) * price, 2)

            before_minute = round(before_invoce_result.values.sum(), 2)
            before_total = 0 if minute_included >= before_minute else round(
                (before_minute - minute_included) * price, 2)

            return {
                'invoce': {
                    'latest': {
                        'minute_included': minute_included,
                        'minute': minute,
                        'price': price,
                        'total': total,
                        'chart': chart,
                    },
                    'before_latest': {
                        'minute_included': minute_included,
                        'minute': before_minute,
                        'price': price,
                        'total': before_total,
                        'chart': before_chart,
                    }
                },
                'delta': {
                    'minute': round(minute - before_minute, 2),
                    'total': round(total - before_total, 2),
                    'percent': round(((total - before_total) / before_total) * 100, 2) if before_total != 0 else 0
                }
            }

        today = datetime.datetime.now()
        if today.day >= 15:
            day_start = datetime.date(today.year, today.month - 1, 15)
            day_end = datetime.date(today.year, today.month, 15)
        else:
            day_start = datetime.date(today.year, today.month - 2, 15)
            day_end = datetime.date(today.year, today.month - 1, 15)
        day_max = datetime.date(today.year, today.month, today.day)
        # Github report max 180 days ago
        day_min = day_max - datetime.timedelta(180)

        date_range = st.date_input(
            'Select invoce date range (Github billing cycle is 15th to 15th of each month)',
            (day_start, day_end),
            day_min,
            day_max
        )

        if len(date_range) == 2:
            date_range_start, date_range_end = date_range
        else:
            date_range_start = date_range[0]
            date_range_end = day_end

        date_range_difference_in_day = (
            date_range_end - date_range_start).days - 1

        st.warning(
            f'Latest invoce from {day_start} to {day_end} (selected {date_range_difference_in_day} days: {date_range_start} to {date_range_end})')

        latest_invoce_data = df.loc[(df['Date'] >= date_range_start.strftime('%Y-%m-%d'))
                                    & (df['Date'] < date_range_end.strftime('%Y-%m-%d'))]

        before_invoce_day_start = date_range_start - \
            datetime.timedelta(date_range_difference_in_day)
        before_invoce_day_end = date_range_end - \
            datetime.timedelta(date_range_difference_in_day + 1)
        before_invoce_data = df.loc[(df['Date'] >= before_invoce_day_start.strftime('%Y-%m-%d'))
                                    & (df['Date'] < before_invoce_day_end.strftime('%Y-%m-%d'))]

        ubuntu = _by_compute(latest_invoce_data,
                             before_invoce_data, 0.008, 3000)
        mac = _by_compute(latest_invoce_data, before_invoce_data, 0.016)
        windows = _by_compute(latest_invoce_data, before_invoce_data, 0.08)

        invoces_cost = {
            'ubuntu': ubuntu,
            'mac': mac,
            'windows': windows,
            'date': {
                'selected': (date_range_start, date_range_end),
                'before': (before_invoce_day_start, before_invoce_day_end),
                'difference_in_day': date_range_difference_in_day
            }
        }

        _print_invoces_cost(
            'Ubuntu', invoces_cost['ubuntu'], invoces_cost['date'])
        _print_invoces_cost('Mac', invoces_cost['mac'], invoces_cost['date'])
        _print_invoces_cost(
            'Windows', invoces_cost['windows'], invoces_cost['date'])

        return invoces_cost

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

    st.write('## Actions runner Costs')

    _cost_date_range()

    st.write('## Overview')

    st.write('**Actions runner by Users**')
    quantity = df.groupby(['Username', 'Repository Slug']).sum(
        'Quantity').filter(['Quantity'])
    st.write(quantity)
    overview_users, overview_repositories = st.tabs(
        ['🗃 Users', '📈 All Repositories'])

    overview_users.write('**Total usage of workflows by users**')
    overview_users.bar_chart(_all_users())
    overview_repositories.write('**Total usage of workflows by repositories**')
    overview_repositories.bar_chart(
        _all_repositories(), use_container_width=True, )

    for name, value in df.groupby(['Repository Slug']).all().iterrows():
        st.write('## Repository ' + name)
        workflow, timestamp, users = st.tabs(
            ['🗃 Actions', '📈 Date', '👩‍💻 Users'])

        workflow.write('**Usage of workflows for the repository**')
        workflow.bar_chart(_by_action_workflow(name), use_container_width=True)

        timestamp.write('**Usage of workflows for the repository by date**')
        timestamp.line_chart(_by_date(name), use_container_width=True)

        users.write('**Usage of workflows for the repository by users**')
        users.bar_chart(_by_username(name), use_container_width=True)


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

    $ source .activate

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
