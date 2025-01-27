import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# Custom CSS for grey gradient background
st.markdown(
    """

    <style>
    .main {
        background: linear-gradient(to bottom, #e0e0e0, #a0a0a0);
    }
    body {
        background-color: #f0f0f0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def scrape_wikipedia_data(url, scrape_headlines, selected_headlines_tags, scrape_links):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        tables = soup.find_all("table", {"class": "wikitable"})
        all_table_data = []
        if tables:
            for i, table in enumerate(tables, 1):
                st.write(f"Scraping Table {i}...")
                rows = table.find_all("tr")
                headers = [th.text.strip() for th in rows[0].find_all("th")]

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

        return all_table_data, headlines, links, None

    except Exception as e:
        return None, None, None, f"Error occurred: {str(e)}"

def start_scraping(url, scrape_headlines, selected_headlines_tags, scrape_links):
    table_data, headlines, links, error = scrape_wikipedia_data(url, scrape_headlines, selected_headlines_tags, scrape_links)
    
    if error:
        st.error(error)
    else:
        st.success("Data scraped successfully!")

        for i, df in enumerate(table_data, 1):
            st.write(f"Table {i}:")
            st.write(df)
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"Download Table {i} CSV",
                data=csv,
                file_name=f"table_{i}.csv",
                mime="text/csv",
            )

        if headlines:
            st.write("Headlines Found:")
            for headline in headlines:
                st.write(f"- {headline}")

        if links:
            st.write("Links Found:")
            for link in links:
                st.write(f"- {link}")

            links_df = pd.DataFrame(links, columns=["Links"])
            
            csv_links = links_df.to_csv(index=False)
             
            st.download_button(
                label="Download Links CSV", 
                data=csv_links,
                file_name="scraped_links.csv",
                mime="text/csv",
            )

st.title("Data Scraper - SAASTRA TECH 2025")
st.write("Table, Headline, and Link Scraper")

url = st.text_input("Enter the URL:")

scrape_headlines = st.checkbox("Scrape Headlines")

headline_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
selected_headlines_tags = st.multiselect("Select headlines to scrape:", headline_tags)

scrape_links = st.checkbox("Scrape Links")

if st.button("Start Scraping"):
    start_scraping(url, scrape_headlines, selected_headlines_tags, scrape_links)
