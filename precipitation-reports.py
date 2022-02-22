# -----------------------------------------------------------
# Use streamlit to create a facimile of Crossref Partipation Reports
# for use by Labs group.
# Released under MIT license
# email labs@crossref.org
# -----------------------------------------------------------

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import arrow
import streamlit as st
from requests import Request, get
from settings import (
    API_URI,
    COUNTS_COL_PREFIX,
    COVERAGE_CATEGORIES,
    CR_PRIMARY_COLORS,
    HEADERS,
)
from missing_items_urls import MISSING_ITEM_URLS


def period_dates():
    start_of_this_year = arrow.utcnow().floor("year")

    start_of_current = start_of_this_year.shift(years=-2)
    end_of_backfile = start_of_current.shift(days=-1)

    start_of_current_date = (
        f"{start_of_current.year}-{start_of_current.month}-{start_of_current.day}"
    )
    end_of_backfile_date = (
        f"{end_of_backfile.year}-{end_of_backfile.month}-{end_of_backfile.day}"
    )

    return end_of_backfile_date, start_of_current_date


@st.experimental_memo
def load_content_types():
    return pd.read_parquet("data/types.parquet")


@st.experimental_memo
def load_instructions():
    """read markdown file of instructions"""
    with open("instructions.md") as f:
        return f.read()


@st.experimental_memo
def load_about():
    """read markdown file about this tool"""
    with open("about.md") as f:
        return f.read()


@st.experimental_memo
def create_journal_df():
    return pd.read_parquet("data/annotated_journals.parquet")


@st.experimental_memo
def create_member_list_df():
    return pd.read_parquet("data/annotated_members.parquet")


@st.experimental_memo
def name_list(summarized_members_df):
    # TODO from json instead of df?
    return summarized_members_df["primary-name"].unique().tolist()


@st.experimental_memo
def member_name_to_id(member_name):
    return int(
        summarized_members_df.loc[
            summarized_members_df["primary-name"] == member_name
        ].iloc[0]["id"]
    )


@st.experimental_memo
def type_id_to_label(type_id):
    return content_types_df.loc[content_types_df["id"] == type_id].iloc[0]["label"]


@st.experimental_memo
def type_label_to_id(type_label):
    return content_types_df.loc[content_types_df["label"] == type_label].iloc[0]["id"]


def update_type_selector(selected_member_ids):
    return [
        type_id_to_label(id)
        for id in most_common_member_type_ids(selected_member_ids).keys()
    ]


def filter_cols(filter):
    return [
        col_name
        for col_name in summarized_members_df.columns
        if col_name.startswith(filter)
    ]


def count_type_cols(period="all"):
    return filter_cols(f"counts-type-{period}-")


def member_records(member_ids: list):
    return summarized_members_df[summarized_members_df["id"].isin(member_ids)]


def count_col_to_type_id(count_col):
    return count_col.replace(f"{COUNTS_COL_PREFIX}-", "")


def most_common_member_type_ids(selected_member_ids: list):
    return {
        count_col_to_type_id(k): v
        for k, v in {
            col_name: member_records(selected_member_ids)[col_name].max()
            for col_name in count_type_cols()
        }.items()
        if v > 0
    }


def currently_selected_members():
    return st.session_state.member_names_multiselect


def currently_selected_type():
    return st.session_state.content_type_selectbox_key


def update_selections():
    selected_member_ids = [
        member_name_to_id(name) for name in currently_selected_members()
    ]

    new_options = update_type_selector(selected_member_ids)
    index = 0
    previously_selected_type = currently_selected_type()
    if previously_selected_type:
        index = (
            new_options.index(previously_selected_type)
            if previously_selected_type in new_options
            else 0
        )

    st.session_state.type_options = new_options
    st.session_state.type_index = index


def generate_col_name(category):
    period = st.session_state.period_selector
    content_type = currently_selected_type()
    if not content_type:
        st.write("no type")
        return "id"

    content_type_id = type_label_to_id(content_type)
    return f"coverage-type-{period.lower()}-{content_type_id}-{category}"


def generate_detail_col_name(category):
    period = st.session_state.period_selector
    return f"coverage-type-{period.lower()}-{category}"


def render_gauge(label, stat):
    return go.Figure(
        go.Indicator(
            mode="number+gauge",
            value=stat,
            number={
                "suffix": "%",
                "font": {"color": CR_PRIMARY_COLORS["CR_PRIMARY_YELLOW"], "size": 24},
            },
            gauge={
                "shape": "bullet",
                "axis": {"range": [None, 100]},
                "bar": {
                    "color": CR_PRIMARY_COLORS["CR_PRIMARY_GREEN"],
                    "line": {"width": 0},
                    "thickness": 1,
                },
                "bgcolor": "#ffffff",
            },
            title={
                "text": f"{label}",
                "font": {"color": CR_PRIMARY_COLORS["CR_PRIMARY_YELLOW"], "size": 18},
            },
        ),
        layout={
            "autosize": False,
            "width": 1000,
            "height": 50,
            "margin": dict(l=300, r=10, b=5, t=5, pad=4),
            "paper_bgcolor": CR_PRIMARY_COLORS["CR_PRIMARY_DK_GREY"],
        },
    )


def date_joined(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "date-joined"
    ]


def member_type(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "member-type"
    ]


def annual_fee(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "annual-fee"
    ]


def country_name(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "geonames-country-name"
    ]


def current_dois(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "counts-current-dois"
    ]


def backfile_dois(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "counts-backfile-dois"
    ]


def total_dois(member_id):
    return summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
        "counts-total-dois"
    ]


def dois_by_issued_year(member_id):
    val = json.loads(
        summarized_members_df[summarized_members_df["id"].isin([member_id])].iloc[0][
            "breakdowns-dois-by-issued-year"
        ]
    )
    return {"years": [item[0] for item in val], "counts": [item[1] for item in val]}


def display_overview():
    st.header("Overview")
    for member_name in st.session_state.member_names_multiselect:
        member_id = member_name_to_id(member_name)
        with st.expander(label=f"{member_name}"):
            member_vitals(member_id)


def publication_history_chart(member_id):
    data = dois_by_issued_year(member_id)
    chart_df = pd.DataFrame(data)
    d_fig = px.bar(
        chart_df,
        x="years",
        y="counts",
        color_discrete_sequence=["#000000"],
        title="Publications per year",
    )
    d_fig.update_traces(marker_color="#3eb1c8")
    return d_fig


def member_vitals(member_id):
    st.markdown(f"**Date joined:** {date_joined(member_id)}")
    st.markdown(f"**Member type:** {member_type(member_id)}")
    st.markdown(f"**Annual fee:** {annual_fee(member_id):,} USD")
    st.markdown(f"**Location:** {country_name(member_id)}")
    st.markdown(f"**Current DOIs:** {current_dois(member_id):,}")
    st.markdown(f"**Backfile DOIs:** {backfile_dois(member_id):,}")
    st.markdown(f"**Total DOIs:** {total_dois(member_id):,}")
    st.write(publication_history_chart(member_id))


def title_details(member_name, category):
    member_id = member_name_to_id(member_name)
    col_name = generate_detail_col_name(category)
    detail = journals_df[journals_df["member"].isin([member_id])][["title", col_name]]
    # TODO figure out how to format as percentage and keep sort working.
    detail[col_name] = pd.Series(
        [round(val * 100, 2) for val in detail[col_name]], index=detail.index
    )

    return detail


def show_sample(member_id, category):
    st.write("Downloading sample")


@st.experimental_memo
def get_sample(member_id, category):
    with st.spinner("Getting sample of non-conforming DOIs"):
        path = f"members/{member_id}/works"
        params = MISSING_ITEM_URLS.get(category, None)
        if params:
            params = params | {"sample": 100, "select": "DOI"}
            res = get(f"{API_URI}/{path}", params=params, headers=HEADERS).json()
            return json.dumps(res)

    return None


def display_coverage():
    st.header("Coverage")
    st.markdown(
        f"**Content type:** {currently_selected_type()} / **Period:** {st.session_state.period_selector}"
    )

    for category, category_lable in COVERAGE_CATEGORIES.items():

        st.subheader(f"{category_lable}")
        col_name = generate_col_name(category)
        # Get average for all members first
        mean = summarized_members_df[col_name].mean()
        st.write(render_gauge("Average for Crossref members", mean * 100))
        for member_name in st.session_state.member_names_multiselect:
            stat = summarized_members_df[
                summarized_members_df["primary-name"].isin([member_name])
            ].iloc[0][col_name]
            st.write(render_gauge(member_name, stat * 100))

            # title details
            if st.session_state.show_title_detail and type_label_to_id(
                currently_selected_type()
            ) in ["journal-article"]:
                with st.expander(
                    label=f"{member_name} title-level details", expanded=False
                ):
                    st.write("title details")
                    st.dataframe(title_details(member_name, category))
            # debug exceptions
            if st.session_state.show_example_links:
                member_id = member_name_to_id(member_name)
                params = MISSING_ITEM_URLS.get(category, None)
                if params:
                    path = f"members/{member_id}/works"
                    params = {**params, **{"sample": 100, "select": "DOI"}}
                    url = (
                        Request("GET", f"{API_URI}/{path}", params=params).prepare().url
                    )
                    st.markdown(
                        f"[Show sample DOIs that are missing {category}]({url})"
                    )


def init_sidebar():

    st.sidebar.image("https://assets.crossref.org/logo/crossref-logo-landscape-200.png")

    st.sidebar.header("Crossref Precipitation Reports")

    member_names = name_list(summarized_members_df)

    st.sidebar.multiselect(
        "Who are your favorite Crossref members?",
        member_names,
        [],
        key="member_names_multiselect",
        on_change=update_selections,
        help="Type in the member name or initials (e.g. OUP, ACM, IEEE)",
    )

    if "type_options" not in st.session_state:
        # st.write("resseting type session state")
        st.session_state.type_options = []
        st.session_state.type_index = 0

    st.sidebar.selectbox(
        "Content type",
        options=st.session_state.type_options,
        index=st.session_state.type_index,
        key="content_type_selectbox_key",
        help="Select the content type you want to focus on",
    )

    if "selected_period" not in st.session_state:
        st.session_state.selected_period = ["All", "Current", "Backfile"]

    end_of_backfile, start_of_curent = period_dates()
    period_help_text = f"backfile <= {end_of_backfile} / current >= {start_of_curent}"
    st.sidebar.selectbox(
        "Period",
        options=st.session_state.selected_period,
        key="period_selector",
        help=period_help_text,
    )

    with st.sidebar.expander(label="Preferences"):
        st.checkbox(label="Show title detail", key="show_title_detail")
        st.checkbox(label="Show example links", key="show_example_links")

    st.sidebar.markdown(load_instructions())


## Starts here


content_types_df = load_content_types()
summarized_members_df = create_member_list_df()
journals_df = create_journal_df()


init_sidebar()

if len(st.session_state.member_names_multiselect) == 0:
    st.markdown(load_about())
else:
    display_overview()
    display_coverage()

    # # Creating a list of member ids from the currently selected members.
    selected_member_ids = [
        member_name_to_id(member_name) for member_name in currently_selected_members()
    ]
