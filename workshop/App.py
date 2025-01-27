import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Web Scraper, Data Cleaner, and Data Analysis", layout="wide")

with st.sidebar:
    selected = option_menu(
        "Menu",
        ["Web Scraping", "Data Cleaning", "Data Analysis"],
        icons=["cloud-download", "line-chart", "bar-chart"],
        menu_icon="cast",
        default_index=0,
    )

def get_all_links(url):
    """Get all links from the given URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = re.sub(r'^(?!http)', f'{url.rstrip("/")}/', a_tag['href'])
        if link.startswith("http"):
            links.add(link)
    return links

def scrape_page(url):
    """Scrape the content of the given URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def scrape_data(url, scrape_headlines, selected_headlines_tags, scrape_links, scrape_images, scrape_media, table_indices):
    soup = scrape_page(url)
    
    tables = soup.find_all("table")
    all_table_data = []
    if tables:
        for i, table in enumerate(tables, 1):
            if table_indices and i not in table_indices:
                continue
            st.write(f"Scraping Table {i}...")
            rows = table.find_all("tr")
            if rows:
                headers = [th.text.strip() for th in rows[0].find_all("th")]
                if not headers:
                    headers = [f"Column {j+1}" for j in range(len(rows[0].find_all("td")))]

                data = []
                for row in rows[1:]:
                    cols = row.find_all(["th", "td"])
                    cols = [col.text.strip() for col in cols]
                    
                    while len(cols) < len(headers):
                        cols.append("")  
                    if len(cols) > len(headers):
                        cols = cols[:len(headers)]  
                    data.append(cols)

                df = pd.DataFrame(data, columns=headers)
                all_table_data.append(df)
    else:
        st.warning("No tables found on this page.")

    headlines = []
    if scrape_headlines:
        if selected_headlines_tags:
            for tag in selected_headlines_tags:
                headline_tags = soup.find_all(tag)
                headlines += [tag.text.strip() for tag in headline_tags]

    links = []
    if scrape_links:
        anchor_tags = soup.find_all("a", href=True)
        links = [a['href'] for a in anchor_tags if a['href'].startswith("http")]

    images = []
    if scrape_images:
        img_tags = soup.find_all("img")
        images = [img['src'] for img in img_tags if 'src' in img.attrs]

    media_files = []
    if scrape_media:
        media_tags = soup.find_all(["audio", "video", "source"])
        media_files = [media['src'] for media in media_tags if 'src' in media.attrs]

    metadata = {
        "title": soup.title.string if soup.title else "No title",
        "description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "No description",
        "keywords": soup.find("meta", {"name": "keywords"})["content"] if soup.find("meta", {"name": "keywords"}) else "No keywords"
    }

    return all_table_data, headlines, links, images, media_files, metadata, None

def start_scraping(url, scrape_headlines, selected_headlines_tags, scrape_links, scrape_images, scrape_media, table_indices):
    with st.spinner("Scraping in progress..."):
        table_data, headlines, links, images, media_files, metadata, error = scrape_data(url, scrape_headlines, selected_headlines_tags, scrape_links, scrape_images, scrape_media, table_indices)
        if error:
            st.error(error)
        else:
            st.success("Data scraped")

            st.session_state['table_data'] = table_data
            st.session_state['headlines'] = headlines
            st.session_state['links'] = links
            st.session_state['images'] = images
            st.session_state['media_files'] = media_files
            st.session_state['metadata'] = metadata

            st.write("### Metadata:")
            st.json(metadata)

            for i, df in enumerate(table_data, 1):
                st.write(f"### Table {i}:")
                st.dataframe(df)
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"Download Table {i} CSV",
                    data=csv,
                    file_name=f"table_{i}.csv",
                    mime="text/csv",
                )

            if headlines:
                st.write("### Headlines Found:")
                headlines_df = pd.DataFrame(headlines, columns=["Headlines"])
                st.dataframe(headlines_df)
                csv_headlines = headlines_df.to_csv(index=False)
                st.download_button(
                    label="Download Headlines CSV",
                    data=csv_headlines,
                    file_name="scraped_headlines.csv",
                    mime="text/csv",
                )

            if links:
                st.write("### Links Found:")
                links_df = pd.DataFrame(links, columns=["Links"])
                st.dataframe(links_df)
                csv_links = links_df.to_csv(index=False)
                st.download_button(
                    label="Download Links CSV", 
                    data=csv_links,
                    file_name="scraped_links.csv",
                    mime="text/csv",
                )

            if images:
                st.write("### Images Found:")
                images_df = pd.DataFrame(images, columns=["Image URLs"])
                st.dataframe(images_df)
                csv_images = images_df.to_csv(index=False)
                st.download_button(
                    label="Download Images CSV",
                    data=csv_images,
                    file_name="scraped_images.csv",
                    mime="text/csv",
                )
                for img_url in images:
                    st.image(img_url, caption=img_url)

            if media_files:
                st.write("### Media Files Found:")
                media_files_df = pd.DataFrame(media_files, columns=["Media URLs"])
                st.dataframe(media_files_df)
                csv_media_files = media_files_df.to_csv(index=False)
                st.download_button(
                    label="Download Media Files CSV",
                    data=csv_media_files,
                    file_name="scraped_media_files.csv",
                    mime="text/csv",
                )

def data_cleaning():
    st.title("Data Cleaning")
    st.markdown("""
        This page allows you to clean the scraped data.
        
        Select the cleaning options below.
    """)

    if 'table_data' in st.session_state and st.session_state['table_data']:
        for i, df in enumerate(st.session_state['table_data'], 1):
            st.write(f"### Table {i}:")
            st.dataframe(df)

            if st.checkbox(f"Remove duplicates from Table {i}"):
                df = df.drop_duplicates()
                st.write(f"### Table {i} after removing duplicates")
                st.dataframe(df)

            if st.checkbox(f"Drop missing values from Table {i}"):
                df = df.dropna()
                st.write(f"### Table {i} after dropping missing values")
                st.dataframe(df)

            if st.checkbox(f"Normalize text in Table {i} (lowercase)"):
                df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
                st.write(f"### Table {i} after normalizing text")
                st.dataframe(df)

            csv_cleaned = df.to_csv(index=False)
            st.download_button(
                label=f"Download Cleaned Table {i} CSV",
                data=csv_cleaned,
                file_name=f"cleaned_table_{i}.csv",
                mime="text/csv",
            )

    if 'headlines' in st.session_state and st.session_state['headlines']:
        st.write("### Headlines Found:")
        headlines_df = pd.DataFrame(st.session_state['headlines'], columns=["Headlines"])
        st.dataframe(headlines_df)

        if st.checkbox("Remove duplicates from Headlines"):
            headlines_df = headlines_df.drop_duplicates()
            st.write("### Headlines after removing duplicates")
            st.dataframe(headlines_df)

        if st.checkbox("Normalize text in Headlines (convert to lowercase)"):
            headlines_df = headlines_df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
            st.write("### Headlines after normalizing text")
            st.dataframe(headlines_df)

        csv_cleaned_headlines = headlines_df.to_csv(index=False)
        st.download_button(
            label="Download Cleaned Headlines CSV",
            data=csv_cleaned_headlines,
            file_name="cleaned_headlines.csv",
            mime="text/csv",
        )

    if 'links' in st.session_state and st.session_state['links']:
        st.write("### Links Found:")
        links_df = pd.DataFrame(st.session_state['links'], columns=["Links"])
        st.dataframe(links_df)

        if st.checkbox("Remove duplicates from Links"):
            links_df = links_df.drop_duplicates()
            st.write("### Links after removing duplicates")
            st.dataframe(links_df)

        csv_cleaned_links = links_df.to_csv(index=False)
        st.download_button(
            label="Download Cleaned Links CSV",
            data=csv_cleaned_links,
            file_name="cleaned_links.csv",
            mime="text/csv",
        )

    if 'images' in st.session_state and st.session_state['images']:
        st.write("### Images Found:")
        images_df = pd.DataFrame(st.session_state['images'], columns=["Image URLs"])
        st.dataframe(images_df)
        for img_url in st.session_state['images']:
            st.image(img_url, caption=img_url)

    if 'media_files' in st.session_state and st.session_state['media_files']:
        st.write("### Media Files Found:")
        media_files_df = pd.DataFrame(st.session_state['media_files'], columns=["Media URLs"])
        st.dataframe(media_files_df)

def data_analysis():
    st.title("Data Analysis")
    st.markdown("""
        This page allows you to perform deeper analysis on the scraped data using Seaborn.
        Select the analysis options below.
    """)

    data_type = st.selectbox("Select data type to analyze", ["Tables", "Headlines", "Links", "Images", "Media Files"])

    if data_type == "Tables" and 'table_data' in st.session_state and st.session_state['table_data']:
        table_indices = list(range(1, len(st.session_state['table_data']) + 1))
        selected_table_index = st.selectbox("Select table to analyze", table_indices)
        df = st.session_state['table_data'][selected_table_index - 1]

        st.write(f"### Table {selected_table_index}:")
        st.dataframe(df)

        st.write(f"### Analysis for Table {selected_table_index}:")
        analysis_type = st.selectbox(f"Select analysis type for Table {selected_table_index}", ["Correlation Heatmap", "Pairplot", "Distribution Plot"])

        if analysis_type == "Correlation Heatmap":
            st.write("#### Correlation Heatmap")
            corr = df.corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr, ax=ax, annot=True, cmap="coolwarm")
            st.pyplot(fig)

        elif analysis_type == "Pairplot":
            st.write("#### Pairplot")
            fig = sns.pairplot(df)
            st.pyplot(fig)

        elif analysis_type == "Distribution Plot":
            st.write("#### Distribution Plot")
            column = st.selectbox(f"Select column for distribution plot in Table {selected_table_index}", df.columns)
            fig, ax = plt.subplots()
            sns.histplot(df[column], ax=ax, kde=True)
            st.pyplot(fig)

    elif data_type == "Headlines" and 'headlines' in st.session_state and st.session_state['headlines']:
        st.write("### Headlines Found:")
        headlines_df = pd.DataFrame(st.session_state['headlines'], columns=["Headlines"])
        st.dataframe(headlines_df)

        st.write("### Analysis for Headlines:")
        analysis_type = st.selectbox("Select analysis type for Headlines", ["Word Frequency"])

        if analysis_type == "Word Frequency":
            st.write("#### Word Frequency")
            word_freq = headlines_df['Headlines'].str.split(expand=True).stack().value_counts()
            st.bar_chart(word_freq)

    elif data_type == "Links" and 'links' in st.session_state and st.session_state['links']:
        st.write("### Links Found:")
        links_df = pd.DataFrame(st.session_state['links'], columns=["Links"])
        st.dataframe(links_df)

        st.write("### Analysis for Links:")
        analysis_type = st.selectbox("Select analysis type for Links", ["Domain Frequency"])

        if analysis_type == "Domain Frequency":
            st.write("#### Domain Frequency")
            domain_freq = links_df['Links'].apply(lambda x: re.findall(r'https?://([^/]+)', x)[0]).value_counts()
            st.bar_chart(domain_freq)

    elif data_type == "Images" and 'images' in st.session_state and st.session_state['images']:
        st.write("### Images Found:")
        images_df = pd.DataFrame(st.session_state['images'], columns=["Image URLs"])
        st.dataframe(images_df)
        for img_url in st.session_state['images']:
            st.image(img_url, caption=img_url)

    elif data_type == "Media Files" and 'media_files' in st.session_state and st.session_state['media_files']:
        st.write("### Media Files Found:")
        media_files_df = pd.DataFrame(st.session_state['media_files'], columns=["Media URLs"])
        st.dataframe(media_files_df)

if selected == "Web Scraping":
    st.title("Web Scraper")
    st.markdown("""
        Scrape tables, Headlines, Links, Images, Media files, and Metadata from a website.
        
        Enter the URL and select the options below to start scraping.
    """)

    url = st.text_input("Enter the URL:")

    scrape_headlines = st.checkbox("Scrape Headlines")

    headline_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
    selected_headlines_tags = st.multiselect("Select headlines to scrape:", headline_tags)

    scrape_links = st.checkbox("Scrape Links")
    scrape_images = st.checkbox("Scrape Images")
    scrape_media = st.checkbox("Scrape Media Files")

    table_indices = st.text_input("Enter table indices to scrape :")
    table_indices = [int(i.strip()) for i in table_indices.split(",") if i.strip().isdigit()]

    if st.button("Start Scraping"):
        start_scraping(url, scrape_headlines, selected_headlines_tags, scrape_links, scrape_images, scrape_media, table_indices)

elif selected == "Data Cleaning":
    data_cleaning()

elif selected == "Data Analysis":
    data_analysis()